"""存量-流量空间建模 + 人机混合参与式仿真内核。

模块结构：
    space   空间单元与邻接图
    flow    流量生成（重力流/人类/合成体）与约束投影
    kernel  仿真内核（状态、轮次、守恒）

快速开始：
    from src.core import SpaceGraph, SimulationKernel, FlowParams, Decision

    g = SpaceGraph.from_json("configs/scenarios/demo_plaza.json")
    k = SimulationKernel(g, FlowParams(external_inflow_total=20.0))
    k.reset({"entry_w": 60})
    for t in range(200):
        k.step([Decision("p01", "human", "plaza_c", "fountain", round=t)])
"""

from .flow import Decision, FlowModel, FlowParams, FlowResult
from .kernel import ConservationError, RoundRecord, SimulationKernel
from .space import Edge, SpaceGraph, SpaceUnit

__all__ = [
    "SpaceUnit",
    "Edge",
    "SpaceGraph",
    "Decision",
    "FlowParams",
    "FlowResult",
    "FlowModel",
    "SimulationKernel",
    "RoundRecord",
    "ConservationError",
]

__version__ = "0.1.0"
