"""空间图模型：空间单元与邻接结构。

对应数学模型规范 §2.1。单元是互不重叠的空间分区（广场分区、街区、看台区块），
邻接关系是有向图，允许不对称与自环。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

# 单元类型（数学模型规范 §2.1）
UNIT_TYPES = ("entry", "exit", "corridor", "stay", "mixed")


@dataclass
class SpaceUnit:
    """一个空间单元。"""

    id: str
    name: str = ""
    type: str = "mixed"
    area: float = 100.0
    capacity: float = 100.0
    #: 硬容量倍数：x_i >= capacity * hard_factor 时禁止再进入
    hard_factor: float = 1.5
    #: 基础吸引力 Attr_j（目的地效用），影响重力流分配
    attract: float = 1.0
    #: 移动倾向 p_i：该单元内"将要移动"的比例
    mobility: float = 0.15
    #: 是否为外部入口（可接受外部流入 b_i）
    is_entry: bool = False
    #: 是否为外部出口（可产生外部流出 d_i）
    is_exit: bool = False
    #: 离开倾向：位于出口单元者离场的概率系数
    exit_rate: float = 0.0
    #: 可视化坐标（可选）
    x: float = 0.0
    y: float = 0.0

    def __post_init__(self) -> None:
        if self.type not in UNIT_TYPES:
            raise ValueError(
                f"单元 {self.id!r} 的 type={self.type!r} 非法，应为 {UNIT_TYPES}"
            )
        if self.area <= 0:
            raise ValueError(f"单元 {self.id!r} 的 area 必须为正")
        if self.capacity <= 0:
            raise ValueError(f"单元 {self.id!r} 的 capacity 必须为正")
        if not 0.0 <= self.mobility <= 1.0:
            raise ValueError(f"单元 {self.id!r} 的 mobility 必须在 [0,1]")
        if not 0.0 <= self.exit_rate <= 1.0:
            raise ValueError(f"单元 {self.id!r} 的 exit_rate 必须在 [0,1]")
        if self.hard_factor < 1.0:
            raise ValueError(f"单元 {self.id!r} 的 hard_factor 必须 >= 1.0")
        # type 与 entry/exit 标志的一致性
        if self.type == "entry":
            self.is_entry = True
        if self.type == "exit":
            self.is_exit = True

    @property
    def hard_capacity(self) -> float:
        """硬容量上限。"""
        return self.capacity * self.hard_factor


@dataclass
class Edge:
    """有向邻接边 (i -> j)。"""

    src: str
    dst: str
    #: 通行成本 c_ij（距离/时间/拥挤代价）
    cost: float = 1.0

    def __post_init__(self) -> None:
        if self.cost <= 0:
            raise ValueError(f"边 {self.src}->{self.dst} 的 cost 必须为正")


@dataclass
class SpaceGraph:
    """空间图：单元集合 + 有向邻接结构。

    内部用稠密矩阵存储，因为 N 通常在 10–100 量级（数学模型规范 §2.1）。
    """

    units: list[SpaceUnit] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._index: dict[str, int] = {}
        self._rebuild_index()

    # ---- 构建 -------------------------------------------------------------

    def _rebuild_index(self) -> None:
        ids = [u.id for u in self.units]
        if len(ids) != len(set(ids)):
            dupes = sorted({i for i in ids if ids.count(i) > 1})
            raise ValueError(f"空间单元 id 重复: {dupes}")
        self._index = {u.id: k for k, u in enumerate(self.units)}

        n = len(self.units)
        # 邻接与成本矩阵（默认不可达 -> cost = inf）
        self.adjacency = np.zeros((n, n), dtype=bool)
        self.cost = np.full((n, n), np.inf, dtype=float)

    def add_unit(self, unit: SpaceUnit) -> None:
        self.units.append(unit)
        self._rebuild_index()

    def add_edge(self, src: str, dst: str, cost: float = 1.0) -> None:
        edge = Edge(src, dst, cost)  # 校验
        self.adjacency[self.index(edge.src), self.index(edge.dst)] = True
        self.cost[self.index(edge.src), self.index(edge.dst)] = edge.cost

    def add_edges(self, specs: Iterable[tuple[str, str, float]]) -> None:
        for src, dst, cost in specs:
            self.add_edge(src, dst, cost)

    def add_bidirectional(
        self, a: str, b: str, cost: float = 1.0, cost_ba: float | None = None
    ) -> None:
        """添加双向边；cost_ba 允许反向成本不同（如扶梯、单行坡道）。"""
        self.add_edge(a, b, cost)
        self.add_edge(b, a, cost if cost_ba is None else cost_ba)

    # ---- 查询 -------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.units)

    @property
    def n(self) -> int:
        return len(self.units)

    @property
    def ids(self) -> list[str]:
        return [u.id for u in self.units]

    def index(self, unit_id: str) -> int:
        try:
            return self._index[unit_id]
        except KeyError:
            raise KeyError(f"未知空间单元: {unit_id!r}") from None

    def unit(self, unit_id: str) -> SpaceUnit:
        return self.units[self.index(unit_id)]

    def neighbors(self, unit_id: str) -> list[str]:
        """单元 i 的出边邻居集合 N(i)。"""
        k = self.index(unit_id)
        return [self.units[j].id for j in np.nonzero(self.adjacency[k])[0]]

    def is_reachable(self, src: str, dst: str) -> bool:
        return bool(self.adjacency[self.index(src), self.index(dst)])

    def validate(self) -> list[str]:
        """结构自检，返回问题列表（空列表表示通过）。"""
        problems: list[str] = []
        for u in self.units:
            if len(self.neighbors(u.id)) == 0:
                problems.append(f"单元 {u.id!r} 没有任何出边，将成为吸收态")
        if not any(u.is_entry for u in self.units):
            problems.append("没有 entry 类型单元，系统无法接受外部流入")
        if not any(u.is_exit for u in self.units):
            problems.append("没有 exit 类型单元，系统无法向外流出")
        # 孤立检测：是否存在无法从入口到达的单元
        entries = [u.id for u in self.units if u.is_entry]
        if entries:
            reached = self._bfs_reachable(entries)
            unreachable = sorted(set(self.ids) - reached)
            if unreachable:
                problems.append(f"以下单元从入口不可达（忽略边方向前的连通性检查）: {unreachable}")
        return problems

    def _bfs_reachable(self, sources: list[str]) -> set[str]:
        """无向可达性，用于发现孤岛单元。"""
        seen = set(sources)
        stack = list(sources)
        undirected = self.adjacency | self.adjacency.T
        while stack:
            cur = stack.pop()
            for j in np.nonzero(undirected[self.index(cur)])[0]:
                nid = self.units[j].id
                if nid not in seen:
                    seen.add(nid)
                    stack.append(nid)
        return seen

    # ---- 序列化 -----------------------------------------------------------

    @classmethod
    def from_dict(cls, spec: dict) -> "SpaceGraph":
        """从场景配置字典构建空间图。

        允许单元携带额外的溯源字段（如转换器写入的 `_sumo`）：
        这些字段不是 SpaceUnit 的构造参数，将被忽略而不会导致加载失败。
        """
        allowed = set(SpaceUnit.__dataclass_fields__)
        units = []
        for u in spec["units"]:
            known = {k: v for k, v in u.items() if k in allowed}
            units.append(SpaceUnit(**known))
        g = cls(units)
        unit_ids = set(g.ids)
        for e in spec.get("edges", []):
            src, dst = e["src"], e["dst"]
            if src not in unit_ids:
                raise ValueError(f"边引用了未知单元: {src!r}")
            if dst not in unit_ids:
                raise ValueError(f"边引用了未知单元: {dst!r}")
            g.add_edge(src, dst, float(e.get("cost", 1.0)))
        return g

    @classmethod
    def from_json(cls, path: str | Path) -> "SpaceGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        edges = []
        n = self.n
        for i in range(n):
            for j in range(n):
                if self.adjacency[i, j]:
                    edges.append(
                        {
                            "src": self.units[i].id,
                            "dst": self.units[j].id,
                            "cost": float(self.cost[i, j]),
                        }
                    )
        return {
            "units": [u.__dict__.copy() for u in self.units],
            "edges": edges,
        }

    # ---- 向量化属性 -------------------------------------------------------

    @property
    def capacities(self) -> np.ndarray:
        return np.array([u.capacity for u in self.units], dtype=float)

    @property
    def hard_capacities(self) -> np.ndarray:
        return np.array([u.hard_capacity for u in self.units], dtype=float)

    @property
    def mobility(self) -> np.ndarray:
        return np.array([u.mobility for u in self.units], dtype=float)

    @property
    def attract(self) -> np.ndarray:
        return np.array([u.attract for u in self.units], dtype=float)

    @property
    def exit_rate(self) -> np.ndarray:
        return np.array([u.exit_rate for u in self.units], dtype=float)

    def __repr__(self) -> str:
        return f"SpaceGraph(n={self.n}, edges={int(self.adjacency.sum())})"
