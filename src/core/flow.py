"""流量生成与约束投影。

对应数学模型规范 §3（三类驱动）与 §4（约束与拥挤处理）。

设计要点：本模块是"人-AI 混合"的技术接口。人类被试与 LLM 合成智能体的
选择在数学上完全同构——都表现为一个 (origin, choice, weight) 三元组，
最终被聚合进同一个流量矩阵。仿真内核不区分二者的来源。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .space import SpaceGraph


@dataclass
class Decision:
    """一个决策者的选择（统一决策协议，架构文档 §3）。

    人类与合成智能体产出同一种结构。actor_type 仅用于分组分析，
    内核计算逻辑不得因其改变。
    """

    actor_id: str
    actor_type: str  # "human" | "llm" | "scripted"
    origin_unit: str
    choice: str  # 目标单元 id | "STAY" | "EXIT"
    weight: float = 1.0
    round: int = 0
    latency_ms: int = 0
    confidence: int | None = None
    reason: str = ""
    timed_out: bool = False
    issued_at: str = ""

    TYPES = ("human", "llm", "scripted")

    def __post_init__(self) -> None:
        if self.actor_type not in self.TYPES:
            raise ValueError(
                f"actor_type={self.actor_type!r} 非法，应为 {self.TYPES}"
            )
        if self.weight < 0:
            raise ValueError("weight 不能为负")

    def to_dict(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "round": self.round,
            "origin_unit": self.origin_unit,
            "choice": self.choice,
            "weight": self.weight,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "reason": self.reason,
            "timed_out": self.timed_out,
            "issued_at": self.issued_at,
        }


@dataclass
class FlowResult:
    """一次流量推进的中间量，便于审计与论文复现。"""

    flow: np.ndarray              # f_ij，最终流量矩阵
    inflow: np.ndarray            # b_i
    outflow: np.ndarray           # d_i
    gravity: np.ndarray           # f^bg
    from_human: np.ndarray        # f^human
    from_llm: np.ndarray          # f^llm
    dropped_by_conservation: float = 0.0   # 守恒投影削减量
    blocked_by_capacity: np.ndarray | None = None
    hard_blocked: np.ndarray | None = None

    def summary(self) -> dict:
        f = self.flow.copy()
        np.fill_diagonal(f, 0.0)
        # 净边界变化：外部流入 − 外部流出。总量变化必须等于该值。
        net_boundary = float(self.inflow.sum() - self.outflow.sum())
        return {
            "total_flow": float(f.sum()),
            "gravity_share": float(self.gravity.sum()),
            "human_share": float(self.from_human.sum()),
            "llm_share": float(self.from_llm.sum()),
            "inflow_total": float(self.inflow.sum()),
            "outflow_total": float(self.outflow.sum()),
            "_net_boundary": net_boundary,
            "dropped_by_conservation": self.dropped_by_conservation,
            "hard_blocked_units": (
                int(np.sum(self.hard_blocked)) if self.hard_blocked is not None else 0
            ),
        }


@dataclass
class FlowParams:
    """流量生成参数。"""

    #: 成本敏感度 β（离散选择/重力模型的尺度参数）
    beta: float = 1.0
    #: 拥挤惩罚系数 γ（数学模型规范 §4.1）
    gamma: float = 2.0
    #: 是否应用拥挤惩罚
    crowding_penalty: bool = True
    #: 是否应用硬容量阻挡
    hard_block: bool = True
    #: 移动倾向的全局缩放（情景控制旋钮）
    mobility_scale: float = 1.0
    #: 外部流入曲线 D(t)/base；base 为参考流入总量
    external_inflow_total: float = 0.0
    #: 进入单元之间的分配权重（None 表示按 entry 单元吸引力的比例）
    inflow_split: dict[str, float] = field(default_factory=dict)


class FlowModel:
    """存量-流量的流量生成与约束投影。

    无状态（除参数外），便于单元测试与批量情景扫描。
    """

    def __init__(self, graph: SpaceGraph, params: FlowParams | None = None) -> None:
        self.g = graph
        self.p = params or FlowParams()
        self._validate()

    def _validate(self) -> None:
        n = self.g.n
        if np.any(np.isinf(self.g.cost[self.g.adjacency])) and self.g.adjacency.sum() > 0:
            # 邻接为真但成本为 inf 属于内部不一致
            bad = self.g.adjacency & np.isinf(self.g.cost)
            if bad.any():
                raise ValueError("存在邻接为真但通行成本为 inf 的边")

    # ------------------------------------------------------------------
    # §3.1 结构化驱动：重力/熵最大化流量
    # ------------------------------------------------------------------
    def gravity_flows(self, stock: np.ndarray, *, mobility: np.ndarray | None = None,
                      attract: np.ndarray | None = None,
                      cost: np.ndarray | None = None) -> np.ndarray:
        """计算背景流 f^bg。

            f_ij^bg = x_i · p_i · Attr_j · exp(−β·c_ij)
                      ─────────────────────────────────
                      Σ_{k∈N(i)} Attr_k · exp(−β·c_ik)
        """
        n = self.g.n
        if mobility is None:
            mobility = self.g.mobility
        if attract is None:
            attract = self.g.attract
        if cost is None:
            cost = self.g.cost

        beta = self.p.beta
        # 效用项 w_ij = Attr_j · exp(−β·c_ij)，不可达处为 0
        with np.errstate(over="ignore", invalid="ignore"):
            util = attract[None, :] * np.exp(-beta * cost)
        util[~self.g.adjacency] = 0.0
        util[~np.isfinite(util)] = 0.0

        row_sum = util.sum(axis=1, keepdims=True)
        safe = np.where(row_sum > 0, row_sum, 1.0)
        prob = util / safe  # 每行归一化，Σ_j prob_ij = 1

        # 可移动人数 = x_i · p_i · mobility_scale
        movable = stock * mobility * self.p.mobility_scale
        return prob * movable[:, None]

    # ------------------------------------------------------------------
    # §3.2 / §3.3 决策驱动：人类与合成智能体
    # ------------------------------------------------------------------
    def decision_flows(self, decisions: list[Decision]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """把决策列表聚合为流量矩阵。

        返回 (all_decisions, human_only, llm_only) 三个矩阵，便于分组分析。

        - choice == 目标单元：计入 f_ij
        - choice == "STAY"：留在原地，不计入任何流出（但仍记录决策数据）
        - choice == "EXIT"：计入外部流出 d_i
        """
        n = self.g.n
        total = np.zeros((n, n), dtype=float)
        human = np.zeros((n, n), dtype=float)
        llm = np.zeros((n, n), dtype=float)

        for d in decisions:
            if d.weight == 0:
                continue
            i = self.g.index(d.origin_unit)
            target = total if d.actor_type != "llm" else llm
            if d.actor_type == "human":
                human[i, :] += 0  # 保持形状语义清晰
            if d.choice == "STAY":
                continue
            if d.choice == "EXIT":
                continue  # 由 external_outflow 处理
            j = self.g.index(d.choice)
            if not self.g.adjacency[i, j]:
                raise ValueError(
                    f"决策非法：{d.actor_id} 从 {d.origin_unit!r} 选择了不可达的 "
                    f"{d.choice!r}（(i,j) ∉ E）"
                )
            total[i, j] += d.weight
            if d.actor_type == "human":
                human[i, j] += d.weight
            elif d.actor_type == "llm":
                llm[i, j] += d.weight
            else:
                # scripted 背景体的决策也计入总量，但不属于 human/llm 分组
                pass
        return total, human, llm

    def exit_decisions(self, decisions: list[Decision]) -> np.ndarray:
        """统计选择离场者的外部流出 d_i。"""
        d = np.zeros(self.g.n, dtype=float)
        for dec in decisions:
            if dec.choice == "EXIT" and dec.weight > 0:
                d[self.g.index(dec.origin_unit)] += dec.weight
        return d

    # ------------------------------------------------------------------
    # 外部边界（数学模型规范 §2.4）
    # ------------------------------------------------------------------
    def external_inflow(self, inflow_total: float | None = None) -> np.ndarray:
        """按配置在入口单元间分配外部流入 b_i。"""
        b = np.zeros(self.g.n, dtype=float)
        total = self.p.external_inflow_total if inflow_total is None else inflow_total
        if total <= 0:
            return b

        entries = [u for u in self.g.units if u.is_entry]
        if not entries:
            raise ValueError("配置要求外部流入，但空间图中没有 entry 类型单元")

        if self.p.inflow_split:
            weights = np.array(
                [self.p.inflow_split.get(u.id, 0.0) for u in entries], dtype=float
            )
            if weights.sum() <= 0:
                raise ValueError("inflow_split 权重全为 0")
            weights = weights / weights.sum()
        else:
            weights = np.array([u.attract for u in entries], dtype=float)
            weights = weights / weights.sum()

        for u, w in zip(entries, weights):
            b[self.g.index(u.id)] = total * w
        return b

    def external_outflow(self, stock: np.ndarray, extra: np.ndarray | None = None) -> np.ndarray:
        """外部流出 d_i = 出口单元的离开倾向 × 存量（加上显式 EXIT 决策）。"""
        rate = self.g.exit_rate
        d = stock * rate
        if extra is not None:
            d = d + extra
        return d

    # ------------------------------------------------------------------
    # §4.1 容量约束与拥挤惩罚
    # ------------------------------------------------------------------
    def effective_cost(self, stock: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """返回 (有效通行成本, 硬阻挡掩码)。

        拥挤惩罚：c_ji ← c_ji · (1 + γ · max(0, x_i/C_i − 1))
        注意惩罚施加在**进入方向**——拥挤的是目的地 i。
        硬阻挡：x_i ≥ C_i · hard_factor 时，任何进入 i 的边被禁用。
        """
        n = self.g.n
        capacities = self.g.capacities
        util_ratio = np.divide(
            stock, capacities, out=np.zeros(n, dtype=float), where=capacities > 0
        )
        over = np.maximum(0.0, util_ratio - 1.0)  # 超出容量部分

        cost = self.g.cost.copy()
        if self.p.crowding_penalty:
            # 惩罚因子作用于列（目的地 j）
            penalty = 1.0 + self.p.gamma * over
            cost = cost * penalty[None, :]

        hard_blocked = np.zeros(n, dtype=bool)
        if self.p.hard_block:
            hard_blocked = stock >= self.g.hard_capacities
            if hard_blocked.any():
                cost = cost.copy()
                cost[:, hard_blocked] = np.inf

        cost[~self.g.adjacency] = np.inf
        return cost, hard_blocked

    # ------------------------------------------------------------------
    # §4.2 守恒投影
    # ------------------------------------------------------------------
    @staticmethod
    def project_conservation(flow: np.ndarray, stock: np.ndarray) -> tuple[np.ndarray, float]:
        """比例投影到可行域，确保 Σ_{j≠i} f_ij ≤ x_i。

        注意：自环 (i,i) 不消耗存量，故从流出和中排除。
        """
        f = flow.copy()
        n = f.shape[0]
        np.fill_diagonal(f, 0.0)  # 自环单独处理，不参与守恒
        outflow = f.sum(axis=1)
        excess = outflow - stock
        mask = excess > 1e-12
        dropped = 0.0
        if mask.any():
            scale = np.ones(n, dtype=float)
            scale[mask] = stock[mask] / outflow[mask]
            f = f * scale[:, None]
            dropped = float(np.sum(outflow[mask] - stock[mask]))
        # 置回自环
        diag = np.diag(flow).copy()
        np.fill_diagonal(f, diag)
        return f, dropped

    # ------------------------------------------------------------------
    # 单步聚合：把三类驱动合成最终流量
    # ------------------------------------------------------------------
    def compose(
        self,
        stock: np.ndarray,
        decisions: list[Decision] | None = None,
        *,
        inflow_total: float | None = None,
        keep_internal: bool = False,
    ) -> FlowResult:
        """合成一类完整流量并施加全部约束。

        keep_internal=True 时保留单元内自环流量（STAY 的加权形式），
        默认不产生自环。
        """
        decisions = decisions or []
        n = self.g.n

        # 有效成本（含拥挤惩罚与硬阻挡）
        eff_cost, hard_blocked = self.effective_cost(stock)

        # ① 背景流：使用有效成本，拥挤时自动绕行
        gravity = self.gravity_flows(stock, cost=eff_cost)

        # ②③ 决策流：先按可达性聚合，再叠加
        dec_total, dec_human, dec_llm = self.decision_flows(decisions)

        flow = gravity + dec_total

        # ④ 边界
        b = self.external_inflow(inflow_total)
        d = self.external_outflow(stock, self.exit_decisions(decisions))

        # ⑤ 守恒投影：注意可流出上限还要扣掉显式离场者
        available = np.maximum(0.0, stock - d)
        flow, dropped = self.project_conservation(flow, available)

        # 硬阻挡：清除进入被阻挡单元的流量
        if hard_blocked.any():
            flow[:, hard_blocked] = 0.0

        # 重新投影（硬阻挡可能改变流出和，只会减少，故安全）
        flow, dropped2 = self.project_conservation(flow, available)
        dropped += dropped2

        return FlowResult(
            flow=flow,
            inflow=b,
            outflow=d,
            gravity=gravity,
            from_human=dec_human,
            from_llm=dec_llm,
            dropped_by_conservation=dropped,
            hard_blocked=hard_blocked,
            blocked_by_capacity=None,
        )
