"""存量-流量仿真内核。

对应数学模型规范 §2（状态与守恒更新）与 §5（闭环时序）。

内核只关心三件事：
  1. 持有唯一的世界状态 x(t)；
  2. 每轮把状态广播出去，收集决策，推进状态；
  3. 保证每一步都不破坏守恒性与非负性。

它**不区分**决策者是人类还是合成智能体——这是"单一世界 + 同构接口"
原则在代码层面的落实。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

import numpy as np

from .flow import Decision, FlowModel, FlowParams, FlowResult
from .space import SpaceGraph


class ConservationError(RuntimeError):
    """守恒性或非负性被破坏——属于必须立即暴露的严重错误。"""


@dataclass
class RoundRecord:
    """一轮的完整记录，落盘后可完整回放。"""

    round: int
    stock: np.ndarray                       # x(t+1)，推进后的状态
    stock_before: np.ndarray                # x(t)，推进前
    flows: dict                             # FlowResult.summary()
    utilization: np.ndarray                 # x/C
    decisions: list[dict] = field(default_factory=list)
    total_people: float = 0.0
    hard_blocked_units: list[str] = field(default_factory=list)

    def to_dict(self, unit_ids: list[str]) -> dict:
        return {
            "round": self.round,
            "stock": {u: float(v) for u, v in zip(unit_ids, self.stock)},
            "stock_before": {u: float(v) for u, v in zip(unit_ids, self.stock_before)},
            "utilization": {u: float(v) for u, v in zip(unit_ids, self.utilization)},
            "flows": self.flows,
            "total_people": self.total_people,
            "hard_blocked_units": self.hard_blocked_units,
            "decisions": self.decisions,
        }


class SimulationKernel:
    """存量-流量仿真内核。

    用法：
        g = SpaceGraph.from_json("scenarios/demo.json")
        kernel = SimulationKernel(g, FlowParams(external_inflow_total=20))
        kernel.reset(initial_stock={"plaza": 200})
        for t in range(200):
            kernel.step([Decision(...), ...])
    """

    def __init__(
        self,
        graph: SpaceGraph,
        params: FlowParams | None = None,
        *,
        strict: bool = True,
    ) -> None:
        self.g = graph
        self.model = FlowModel(graph, params)
        self.strict = strict
        self.stock = np.zeros(graph.n, dtype=float)
        self.round = 0
        self.history: list[RoundRecord] = []
        #: 每轮可选的钩子：接收 (kernel, FlowResult) —— 用于状态回传（闭环②）
        self.on_round_complete: Callable[["SimulationKernel", FlowResult], None] | None = None

    # ------------------------------------------------------------------
    def reset(self, initial_stock: dict[str, float] | np.ndarray | None = None) -> None:
        """重置状态。initial_stock 可为 {unit_id: 人数} 或长度 N 的向量。"""
        if initial_stock is None:
            self.stock = np.zeros(self.g.n, dtype=float)
        elif isinstance(initial_stock, dict):
            x = np.zeros(self.g.n, dtype=float)
            for uid, val in initial_stock.items():
                x[self.g.index(uid)] = float(val)
            self.stock = x
        else:
            arr = np.asarray(initial_stock, dtype=float)
            if arr.shape != (self.g.n,):
                raise ValueError(f"initial_stock 形状应为 ({self.g.n},)，得到 {arr.shape}")
            self.stock = arr.copy()

        if np.any(self.stock < 0):
            raise ValueError("初始存量不能为负")
        self.round = 0
        self.history.clear()

    # ------------------------------------------------------------------
    # 闭环①：状态回传
    # ------------------------------------------------------------------
    def state_snapshot(self) -> dict:
        """供回传给参与者与合成智能体的状态快照（数学模型规范 §5 / §3）。

        只暴露聚合量，绝不泄露其他参与者的个人身份信息。
        """
        util = self.utilization()
        return {
            "round": self.round,
            "total_people": float(self.stock.sum()),
            "units": [
                {
                    "id": u.id,
                    "name": u.name or u.id,
                    "stock": float(self.stock[k]),
                    "capacity": float(u.capacity),
                    "utilization": float(util[k]),
                    "type": u.type,
                    "x": u.x,
                    "y": u.y,
                }
                for k, u in enumerate(self.g.units)
            ],
            "edges": [
                {"src": self.g.units[i].id, "dst": self.g.units[j].id}
                for i in range(self.g.n)
                for j in range(self.g.n)
                if self.g.adjacency[i, j]
            ],
        }

    def utilization(self) -> np.ndarray:
        caps = self.g.capacities
        return np.divide(
            self.stock, caps, out=np.zeros(self.g.n, dtype=float), where=caps > 0
        )

    # ------------------------------------------------------------------
    # 闭环②③④：采集决策 → 聚合 → 推进
    # ------------------------------------------------------------------
    def step(
        self,
        decisions: Iterable[Decision] | None = None,
        *,
        inflow_total: float | None = None,
    ) -> RoundRecord:
        """推进一个时间步，返回本轮记录。"""
        decisions = list(decisions or [])
        self._validate_decisions(decisions)

        stock_before = self.stock.copy()
        result = self.model.compose(
            self.stock, decisions, inflow_total=inflow_total
        )

        # 守恒更新：x(t+1) = x − 行和 + 列和 + b − d
        # 注意 project_conservation 已将自环从行和排除，此处需排除对角
        f = result.flow.copy()
        np.fill_diagonal(f, 0.0)
        outflow = f.sum(axis=1)
        inflow = f.sum(axis=0)
        new_stock = self.stock - outflow + inflow + result.inflow - result.outflow

        # 数值清理：消除浮点误差导致的微小负值
        tiny = new_stock < 0
        if tiny.any():
            worst = float(new_stock.min())
            if self.strict and worst < -1e-6:
                raise ConservationError(
                    f"第 {self.round} 轮出现负存量，最小值 {worst:.6g}。"
                    "这表明守恒投影或边界处理存在缺陷。"
                )
            new_stock = np.maximum(new_stock, 0.0)

        self.stock = new_stock
        self.round += 1

        # 记录
        blocked = [
            self.g.units[k].id
            for k in np.nonzero(result.hard_blocked)[0]
        ] if result.hard_blocked is not None else []

        record = RoundRecord(
            round=self.round,
            stock=self.stock.copy(),
            stock_before=stock_before,
            flows=result.summary(),
            utilization=self.utilization().copy(),
            decisions=[d.to_dict() for d in decisions],
            total_people=float(self.stock.sum()),
            hard_blocked_units=blocked,
        )
        self.history.append(record)

        if self.on_round_complete is not None:
            self.on_round_complete(self, result)

        return record

    def _validate_decisions(self, decisions: list[Decision]) -> None:
        for d in decisions:
            self.g.index(d.origin_unit)  # 抛 KeyError
            if d.choice not in ("STAY", "EXIT"):
                self.g.index(d.choice)

    # ------------------------------------------------------------------
    # 守恒自检（供测试与运行时断言）
    # ------------------------------------------------------------------
    def check_conservation(self, record: RoundRecord, tol: float = 1e-6) -> list[str]:
        """检验单轮守恒：Δ总量 应等于 流入 − 流出。"""
        problems: list[str] = []
        delta = record.total_people - float(record.stock_before.sum())
        expected = record.flows.get("_net_boundary", None)
        if expected is not None and abs(delta - expected) > tol:
            problems.append(
                f"总量变化 {delta:.8f} 与边界净流入 {expected:.8f} 不符"
            )
        if np.any(record.stock < -tol):
            problems.append(f"存在负存量: {record.stock.min():.6g}")
        return problems

    # ------------------------------------------------------------------
    def run(
        self,
        rounds: int,
        decision_provider: Callable[[int, dict], list[Decision]] | None = None,
        *,
        inflow_total: float | None = None,
    ) -> list[RoundRecord]:
        """跑多轮。decision_provider(round, snapshot) -> decisions。"""
        records: list[RoundRecord] = []
        for _ in range(rounds):
            snapshot = self.state_snapshot()
            decs = decision_provider(self.round, snapshot) if decision_provider else []
            records.append(self.step(decs, inflow_total=inflow_total))
        return records

    # ------------------------------------------------------------------
    @property
    def total_people(self) -> float:
        return float(self.stock.sum())

    def summary(self) -> dict:
        if not self.history:
            return {"rounds": 0}
        last = self.history[-1]
        peak = max(r.utilization.max() for r in self.history)
        return {
            "rounds": len(self.history),
            "total_people": last.total_people,
            "peak_utilization": float(peak),
            "final_utilization": {
                u.id: float(v) for u, v in zip(self.g.units, last.utilization)
            },
            "hard_block_events": sum(len(r.hard_blocked_units) for r in self.history),
        }
