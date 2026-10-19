"""决策者实现：人类、LLM 合成智能体、规则背景体。

三类决策者都实现同一个接口（统一决策协议，架构文档 §3）：

    decide(round_no: int, snapshot: dict) -> list[Decision] | list[Choice]

关于"同构"的设计约束：
    本模块中的 ScriptedActor 是**合成体行为的下界基线**（无智能的随机/规则体），
    用于在未接入真人或 LLM 时验证内核闭环。它产出的 Decision 与真人、LLM
    完全同构——actor_type 只影响分组统计，不影响内核计算。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from .core.flow import Decision


class Actor(Protocol):
    """决策者协议。人类前端、LLM 智能体、脚本体都实现它。"""

    actor_id: str
    actor_type: str

    def decide(self, round_no: int, snapshot: dict) -> list[Decision]:
        ...


@dataclass
class ScriptedActor:
    """规则背景体：按"倾向最近的低拥挤单元"启发式行动。

    它是"零智能基线"——用于验证闭环能否在不引入任何智能的情况下稳定运行，
    并为真人/LLM 的实验结果提供对照参考。
    """

    actor_id: str = "bot"
    count: int = 50
    actor_type: str = "scripted"
    #: 决策时参考的可达邻居数量上限
    candidate_limit: int = 6
    #: 随机扰动强度（0 = 完全确定性）
    noise: float = 0.15
    seed: int = 0

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def decide(self, round_no: int, snapshot: dict) -> list[Decision]:
        """为每个"虚拟个体"产出一个决策。

        注意：这里为保持接口同构，背景体也逐个产出 Decision，
        但 weight 可以 > 1 以代表聚合人数。
        """
        units = {u["id"]: u for u in snapshot["units"]}
        edges: dict[str, list[str]] = {}
        for e in snapshot["edges"]:
            edges.setdefault(e["src"], []).append(e["dst"])

        decisions: list[Decision] = []
        # 按当前存量比例把虚拟个体分配到单元中
        total = sum(units[k]["stock"] for k in units) or 1.0
        per_actor = max(1.0, self.count / max(1, len(units)))

        for uid, u in units.items():
            n_here = u["stock"] * (self.count / total)
            if n_here < 0.5:
                continue
            dests = edges.get(uid, [])
            if not dests:
                continue
            # 选一个：偏好利用率低的目标，加噪声
            scored = []
            for d in dests:
                util = units[d]["utilization"]
                score = -util + self._rng.uniform(-self.noise, self.noise)
                scored.append((score, d))
            scored.sort(reverse=True)
            best = scored[0][1]
            if self._rng.random() < u["utilization"] * 0.5:
                decisions.append(Decision(
                    actor_id=f"{self.actor_id}_{uid}",
                    actor_type=self.actor_type,
                    origin_unit=uid,
                    choice="EXIT" if units[uid]["type"] == "exit" else "STAY",
                    weight=n_here,
                    round=round_no,
                    latency_ms=self._rng.randint(50, 400),
                    reason="crowding-avoidance heuristic",
                ))
            else:
                decisions.append(Decision(
                    actor_id=f"{self.actor_id}_{uid}",
                    actor_type=self.actor_type,
                    origin_unit=uid,
                    choice=best,
                    weight=n_here,
                    round=round_no,
                    latency_ms=self._rng.randint(50, 400),
                    reason=f"least-crowded neighbor -> {best}",
                ))
        return decisions
