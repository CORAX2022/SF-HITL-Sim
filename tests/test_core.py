"""守恒性、约束与闭环正确性的单元测试。

运行：
    py -3.13 -m pytest tests/ -v
或（无 pytest 时）：
    py -3.13 tests/test_core.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core import (  # noqa: E402
    ConservationError,
    Decision,
    FlowModel,
    FlowParams,
    SimulationKernel,
    SpaceGraph,
    SpaceUnit,
)

SCENARIO = ROOT / "configs" / "scenarios" / "demo_plaza.json"


# ----------------------------------------------------------------------
# 测试夹具
# ----------------------------------------------------------------------
def tiny_graph() -> SpaceGraph:
    """极小空间图，便于精确断言。

    A(entry) -> B(stay) -> C(exit)，另 A->C 直连。
    """
    g = SpaceGraph([
        SpaceUnit("A", type="entry", capacity=100, mobility=0.5, attract=0.5),
        SpaceUnit("B", type="stay", capacity=100, mobility=0.5, attract=1.0),
        SpaceUnit("C", type="exit", capacity=100, mobility=0.5, attract=0.8, exit_rate=0.1),
    ])
    g.add_edges([("A", "B", 1.0), ("B", "C", 1.0), ("A", "C", 2.0)])
    return g


# ----------------------------------------------------------------------
# 空间图
# ----------------------------------------------------------------------
def test_duplicate_unit_id_rejected():
    try:
        SpaceGraph([SpaceUnit("A"), SpaceUnit("A")])
    except ValueError as e:
        assert "重复" in str(e)
    else:
        raise AssertionError("重复 id 应被拒绝")


def test_invalid_edge_reference_rejected():
    spec = {
        "units": [{"id": "A", "type": "entry"}, {"id": "B", "type": "exit"}],
        "edges": [{"src": "A", "dst": "ZZZ"}],
    }
    try:
        SpaceGraph.from_dict(spec)
    except ValueError as e:
        assert "未知单元" in str(e)
    else:
        raise AssertionError("未定义单元的边应被拒绝")


def test_scenario_loads_and_validates():
    g = SpaceGraph.from_json(SCENARIO)
    assert g.n == 12
    assert g.adjacency.sum() == 46
    problems = g.validate()
    assert problems == [], f"演示场景结构自检未通过: {problems}"


def test_neighbors_and_reachability():
    g = tiny_graph()
    assert set(g.neighbors("A")) == {"B", "C"}
    assert g.is_reachable("B", "C")
    assert not g.is_reachable("C", "A")


# ----------------------------------------------------------------------
# 重力流（数学模型规范 §3.1）
# ----------------------------------------------------------------------
def test_gravity_flow_respects_mobility_and_adjacency():
    g = tiny_graph()
    m = FlowModel(g, FlowParams(beta=0.0))  # β=0 -> 效用只看吸引力
    stock = np.array([100.0, 0.0, 0.0])
    f = m.gravity_flows(stock)

    # 不可达处必须为 0
    assert f[1, 0] == 0.0 and f[2, 0] == 0.0 and f[2, 1] == 0.0
    # A 的可移动量 = 100 * 0.5 = 50，全部分配出去
    assert np.isclose(f[0].sum(), 50.0), f"A 的流出量应为 50，得到 {f[0].sum()}"
    # β=0 时按吸引力分配：B(1.0) : C(0.8)
    assert f[0, 1] > f[0, 2] > 0


def test_gravity_flow_zero_when_no_mobility():
    g = tiny_graph()
    g.units[0].mobility = 0.0
    m = FlowModel(g, FlowParams())
    f = m.gravity_flows(np.array([100.0, 0.0, 0.0]))
    assert f.sum() == 0.0


def test_cost_sensitivity_reduces_distant_flow():
    """β 越大，高成本目的地分到的流量越少（成本敏感度生效）。"""
    g = tiny_graph()
    stock = np.array([100.0, 0.0, 0.0])
    low = FlowModel(g, FlowParams(beta=0.1)).gravity_flows(stock)
    high = FlowModel(g, FlowParams(beta=5.0)).gravity_flows(stock)
    # A->C 成本 2.0 高于 A->B 成本 1.0；β 增大时 C 的份额应下降
    share_low = low[0, 2] / low[0].sum()
    share_high = high[0, 2] / high[0].sum()
    assert share_high < share_low, f"β 增大未降低远端份额: {share_low} -> {share_high}"


# ----------------------------------------------------------------------
# 守恒投影（数学模型规范 §4.2）
# ----------------------------------------------------------------------
def test_projection_scales_overflow_proportionally():
    flow = np.array([[0.0, 60.0, 40.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    stock = np.array([50.0, 0.0, 0.0])
    f, dropped = FlowModel.project_conservation(flow, stock)
    assert np.isclose(f[0].sum(), 50.0), "投影后流出应等于存量"
    assert np.isclose(dropped, 50.0), f"削减量应为 50，得到 {dropped}"
    # 比例保持：60:40 -> 30:20
    assert np.isclose(f[0, 1], 30.0) and np.isclose(f[0, 2], 20.0)


def test_projection_noop_when_within_bounds():
    flow = np.array([[0.0, 30.0], [0.0, 0.0]])
    stock = np.array([100.0, 0.0])
    f, dropped = FlowModel.project_conservation(flow, stock)
    assert np.allclose(f, flow)
    assert dropped == 0.0


def test_projection_ignores_self_loop():
    """自环不消耗存量，不应触发投影削减。"""
    flow = np.array([[90.0, 30.0], [0.0, 0.0]])
    stock = np.array([100.0, 0.0])
    f, dropped = FlowModel.project_conservation(flow, stock)
    assert dropped == 0.0, "自环被误计入流出"
    assert np.isclose(f[0, 1], 30.0)


# ----------------------------------------------------------------------
# 容量约束（数学模型规范 §4.1）
# ----------------------------------------------------------------------
def test_hard_capacity_blocks_inflow():
    g = tiny_graph()
    m = FlowModel(g, FlowParams(hard_block=True))
    stock = np.array([10.0, 200.0, 0.0])  # B 容量 100，硬上限 150 -> 200 应被阻挡
    cost, blocked = m.effective_cost(stock)
    assert blocked[1], "B 超出硬容量却未被标记阻挡"
    assert np.isinf(cost[0, 1]), "进入 B 的边应被禁用"


def test_crowding_penalty_raises_cost():
    """拥挤惩罚独立于硬阻挡：关闭 hard_block 以隔离惩罚效果。"""
    g = tiny_graph()
    m = FlowModel(g, FlowParams(gamma=2.0, crowding_penalty=True, hard_block=False))
    # B 容量 100，存量 200 -> 超容量 1.0，惩罚因子 1+2*1=3
    cost, blocked = m.effective_cost(np.array([0.0, 200.0, 0.0]))
    assert not blocked.any(), "已关闭 hard_block，不应有硬阻挡"
    assert np.isclose(cost[0, 1], 3.0), f"拥挤惩罚应为 3.0，得到 {cost[0, 1]}"

    m_off = FlowModel(g, FlowParams(crowding_penalty=False, hard_block=False))
    cost_off, _ = m_off.effective_cost(np.array([0.0, 200.0, 0.0]))
    assert np.isclose(cost_off[0, 1], 1.0), "关闭惩罚后成本应保持原值"


def test_crowding_penalty_rises_with_utilization():
    """惩罚随利用率单调上升（负反馈闭环的数学基础）。"""
    g = tiny_graph()
    m = FlowModel(g, FlowParams(gamma=2.0, hard_block=False))
    c_empty, _ = m.effective_cost(np.array([0.0, 0.0, 0.0]))
    c_full, _ = m.effective_cost(np.array([0.0, 100.0, 0.0]))
    c_over, _ = m.effective_cost(np.array([0.0, 175.0, 0.0]))
    assert c_empty[0, 1] < c_over[0, 1]
    # 未超容量时无惩罚
    assert np.isclose(c_full[0, 1], c_empty[0, 1]), "恰好等于容量时不应施加惩罚"
    assert c_over[0, 1] > c_full[0, 1]


# ----------------------------------------------------------------------
# 决策聚合（统一决策协议）
# ----------------------------------------------------------------------
def test_decision_aggregation_by_type():
    g = tiny_graph()
    m = FlowModel(g)
    decs = [
        Decision("h1", "human", "A", "B", weight=1.0),
        Decision("h2", "human", "A", "B", weight=2.0),
        Decision("l1", "llm", "A", "C", weight=1.5),
    ]
    total, human, llm = m.decision_flows(decs)
    assert np.isclose(total[0, 1], 3.0)
    assert np.isclose(total[0, 2], 1.5)
    assert np.isclose(human[0, 1], 3.0) and human[0, 2] == 0.0
    assert np.isclose(llm[0, 2], 1.5) and llm[0, 1] == 0.0
    # 总量 = 人类 + 合成体
    assert np.allclose(total, human + llm)


def test_unreachable_choice_rejected():
    g = tiny_graph()
    m = FlowModel(g)
    try:
        m.decision_flows([Decision("h1", "human", "C", "A")])  # C->A 不存在
    except ValueError as e:
        assert "不可达" in str(e)
    else:
        raise AssertionError("不可达选择应被拒绝")


def test_stay_and_exit_do_not_create_internal_flow():
    g = tiny_graph()
    m = FlowModel(g)
    total, _, _ = m.decision_flows([
        Decision("h1", "human", "A", "STAY"),
        Decision("h2", "human", "A", "EXIT"),
    ])
    assert total.sum() == 0.0, "STAY/EXIT 不应计入单元间流量"
    d = m.exit_decisions([Decision("h2", "human", "A", "EXIT", weight=3.0)])
    assert np.isclose(d[0], 3.0)


# ----------------------------------------------------------------------
# 内核：守恒性与非负性（数学模型规范 §2.3）
# ----------------------------------------------------------------------
def test_kernel_conserves_mass_without_boundary():
    """封闭系统中（无进出），总人数必须严格守恒。"""
    g = tiny_graph()
    p = FlowParams(external_inflow_total=0.0)
    for u in g.units:
        u.exit_rate = 0.0
    k = SimulationKernel(g, p)
    k.reset({"A": 300.0})
    total0 = k.total_people
    for t in range(100):
        k.step([])
    assert np.isclose(k.total_people, total0, atol=1e-8), (
        f"封闭系统总量不守恒: {total0} -> {k.total_people}"
    )


def test_kernel_conservation_with_boundary():
    """开放系统：总量变化必须等于净边界流入。"""
    g = tiny_graph()
    k = SimulationKernel(g, FlowParams(external_inflow_total=10.0, beta=1.0))
    k.reset({"A": 50.0})
    for t in range(50):
        rec = k.step([])
        delta = rec.total_people - float(rec.stock_before.sum())
        expected = rec.flows["_net_boundary"]
        assert abs(delta - expected) < 1e-8, (
            f"第 {rec.round} 轮: Δ={delta} 与净边界流入={expected} 不符"
        )


def test_kernel_stock_never_negative():
    g = SpaceGraph.from_json(SCENARIO)
    k = SimulationKernel(g, FlowParams(external_inflow_total=50.0, gamma=3.0))
    k.reset({"entry_w": 10.0})
    for t in range(120):
        k.step([])
        assert np.all(k.stock >= -1e-9), f"第 {t} 轮出现负存量: {k.stock.min()}"
    assert min(r.stock.min() for r in k.history) >= -1e-9


def test_human_decisions_change_system_state():
    """闭环有效性：注入人类决策必须改变轨迹。"""
    g = tiny_graph()

    def run(with_human: bool):
        k = SimulationKernel(g, FlowParams(external_inflow_total=0.0, beta=1.0))
        g2 = k.g
        for u in g2.units:
            u.exit_rate = 0.0
        k.reset({"A": 200.0})
        for t in range(30):
            decs = []
            if with_human:
                decs = [Decision(f"h{i}", "human", "A", "C", weight=1.0, round=t)
                        for i in range(10)]
            k.step(decs)
        return k.stock.copy()

    base = run(False)
    with_h = run(True)
    assert not np.allclose(base, with_h), "注入人类决策后状态未改变，闭环失效"
    # 人类都选了 C，C 的存量应更高
    assert with_h[2] > base[2], f"人类选择 C 却未提升 C 的存量: {base[2]} -> {with_h[2]}"


def test_llm_and_human_are_computationally_identical():
    """同构接口原则：仅 actor_type 不同，不得影响系统演化。"""
    g = tiny_graph()

    def run(actor_type: str):
        k = SimulationKernel(g, FlowParams(external_inflow_total=0.0))
        for u in k.g.units:
            u.exit_rate = 0.0
        k.reset({"A": 200.0})
        for t in range(30):
            k.step([Decision("x", actor_type, "A", "B", weight=1.0, round=t)])
        return k.stock.copy()

    assert np.allclose(run("human"), run("llm")), (
        "actor_type 影响了系统演化——违反'单一世界+同构接口'原则"
    )


def test_snapshot_exposes_aggregates_only():
    """回传快照只应含聚合量，不得含任何个体身份信息。"""
    g = tiny_graph()
    k = SimulationKernel(g, FlowParams())
    k.reset({"A": 10.0})
    snap = k.state_snapshot()
    assert "round" in snap and "units" in snap and "edges" in snap
    for u in snap["units"]:
        assert set(u) >= {"id", "stock", "capacity", "utilization"}
    # 序列化后不得出现 actor 个人标识
    import json as _json
    blob = _json.dumps(snap, ensure_ascii=False)
    assert "actor_id" not in blob and "participant" not in blob


# ----------------------------------------------------------------------
# 场景文件自检
# ----------------------------------------------------------------------
def test_scenario_units_have_unique_positions():
    g = SpaceGraph.from_json(SCENARIO)
    coords = [(u.x, u.y) for u in g.units]
    assert len(coords) == len(set(coords)), "存在坐标重复的单元"


def test_all_units_reachable_from_entry():
    g = SpaceGraph.from_json(SCENARIO)
    entries = [u.id for u in g.units if u.is_entry]
    reached = g._bfs_reachable(entries)
    assert reached == set(g.ids), f"存在从入口不可达的单元: {set(g.ids) - reached}"


# ----------------------------------------------------------------------
# 无 pytest 时的直接运行入口
# ----------------------------------------------------------------------
def _run_all() -> int:
    tests = [
        (n, f) for n, f in sorted(globals().items())
        if n.startswith("test_") and callable(f)
    ]
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except Exception as e:  # noqa: BLE001
            failed.append((name, e))
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} 通过")
    if failed:
        print("失败项:")
        for n, e in failed:
            print(f"  - {n}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(_run_all())
