"""闭环演示与守恒性验证。

运行：
    py -3.13 examples/run_loop.py

本脚本做四件事，全部输出可核验的数值：
  1. 加载演示场景，跑 200 轮纯背景流，检查守恒性与非负性；
  2. 注入"人类被试"决策，验证人的选择确实改变流量分布（闭环有效性）；
  3. 对比 纯背景 / 含人类 / 混合 三种条件下的演化差异（人机混合实验的最小雏形）；
  4. 把结果写入 data/ 下的 CSV/JSON，供后续分析。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Windows 控制台默认 GBK，会导致中文输出乱码；强制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.actors import ScriptedActor  # noqa: E402
from src.core import Decision, FlowParams, SimulationKernel, SpaceGraph  # noqa: E402

SCENARIO = ROOT / "configs" / "scenarios" / "demo_plaza.json"
OUTDIR = ROOT / "data" / "demo"


def load_graph() -> SpaceGraph:
    g = SpaceGraph.from_json(SCENARIO)
    problems = g.validate()
    print(f"[场景] {len(g)} 个单元, {int(g.adjacency.sum())} 条有向边")
    if problems:
        print("[场景] 结构告警:")
        for p in problems:
            print(f"        - {p}")
    else:
        print("[场景] 结构自检通过")
    return g


def check_run(kernel: SimulationKernel, label: str) -> dict:
    """逐轮检验守恒性与非负性。"""
    bad = []
    for rec in kernel.history:
        problems = kernel.check_conservation(rec)
        if problems:
            bad.append((rec.round, problems))
    # 逐轮独立复核：Δ总量 == 净边界流入
    drift = []
    for rec in kernel.history:
        delta = rec.total_people - float(rec.stock_before.sum())
        expected = rec.flows.get("_net_boundary", 0.0)
        drift.append(abs(delta - expected))
    max_drift = max(drift) if drift else 0.0

    neg = min((float(r.stock.min()) for r in kernel.history), default=0.0)
    status = "PASS" if (not bad and max_drift < 1e-6 and neg >= -1e-9) else "FAIL"
    print(
        f"[{label}] 守恒检验 {status} | 最大总量漂移={max_drift:.3e} | "
        f"最小存量={neg:.3e} | 硬阻挡事件={sum(len(r.hard_blocked_units) for r in kernel.history)}"
    )
    return {
        "label": label,
        "status": status,
        "max_drift": max_drift,
        "min_stock": neg,
        "rounds": len(kernel.history),
        "hard_block_events": sum(len(r.hard_blocked_units) for r in kernel.history),
        "conservation_violations": len(bad),
    }


def condition_a_pure_background(g: SpaceGraph) -> SimulationKernel:
    """条件 A：纯背景重力流，无人参与。"""
    k = SimulationKernel(g, FlowParams(beta=1.0, gamma=2.0, external_inflow_total=25.0))
    k.reset({"entry_w": 40.0, "plaza_c": 120.0, "plaza_n": 80.0, "plaza_s": 60.0})
    for _ in range(200):
        k.step([])
    return k


def condition_b_with_human(g: SpaceGraph, scripted_human_choice: str = "fountain") -> SimulationKernel:
    """条件 B：每轮注入固定的'人类被试'选择。

    模拟 20 名真人被试每轮都选择去喷泉观景区——这是"人的决策作为外生流量输入"
    的最小演示。若系统响应了该输入，fountain 的存量应显著高于条件 A。
    """
    k = SimulationKernel(g, FlowParams(beta=1.0, gamma=2.0, external_inflow_total=25.0))
    k.reset({"entry_w": 40.0, "plaza_c": 120.0, "plaza_n": 80.0, "plaza_s": 60.0})
    for t in range(200):
        decs = [
            Decision(
                actor_id=f"p{i:02d}",
                actor_type="human",
                origin_unit="plaza_c",
                choice=scripted_human_choice,
                weight=1.0,
                round=t,
                latency_ms=800 + i * 37,
                confidence=4,
                reason="想靠近喷泉看景",
            )
            for i in range(20)
        ]
        k.step(decs)
    return k


def condition_c_mixed(g: SpaceGraph) -> SimulationKernel:
    """条件 C：混合——背景规则体 + 人类 + LLM 合成体。

    三类决策者接入同一世界、同一接口。这是"人机混合实验"的最小可行形态。

    注意：人类决策必须满足 (i,j) ∈ E。本函数显式从空间图取可达目标，
    以演示"前端只应提供可达选项"的正确用法——内核会用异常拒绝非法选择。
    """
    k = SimulationKernel(g, FlowParams(beta=1.0, gamma=2.0, external_inflow_total=25.0))
    k.reset({"entry_w": 40.0, "plaza_c": 120.0, "plaza_n": 80.0, "plaza_s": 60.0})

    background = ScriptedActor(actor_id="bg", count=80, seed=42)
    llm = ScriptedActor(actor_id="llm", count=30, seed=7)  # 占位：真实 LLM 实现见 docs/architecture

    # 预先算出每个起点真正可达的目标，前端应据此渲染可选按钮
    reach = {uid: g.neighbors(uid) for uid in g.ids}

    for t in range(200):
        decs = background.decide(t, k.state_snapshot())
        decs += llm.decide(t, k.state_snapshot())
        # 人类被试：每轮 15 人，起点与目标都保证可达
        for i in range(15):
            origin = "plaza_c" if i % 2 == 0 else "plaza_n"
            dests = reach[origin]
            choice = dests[i % len(dests)]
            decs.append(
                Decision(
                    actor_id=f"h{i:02d}",
                    actor_type="human",
                    origin_unit=origin,
                    choice=choice,
                    weight=1.0,
                    round=t,
                    latency_ms=900 + i * 53,
                    confidence=3,
                    reason="跟随人群/避开拥挤",
                )
            )
        k.step(decs)
    return k


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    g = load_graph()

    print("\n=== 条件 A：纯背景重力流（无人） ===")
    ka = condition_a_pure_background(g)
    ra = check_run(ka, "A-pure-background")

    print("\n=== 条件 B：注入 20 名'人类被试'（每轮都选 fountain） ===")
    kb = condition_b_with_human(g)
    rb = check_run(kb, "B-human-injected")

    print("\n=== 条件 C：人机混合（背景 80 + LLM 30 + 人类 15） ===")
    kc = condition_c_mixed(g)
    rc = check_run(kc, "C-mixed")

    # ---- 闭环有效性：人的决策是否真的改变了系统状态 ----
    ua = {u.id: v for u, v in zip(g.units, ka.history[-1].stock)}
    ub = {u.id: v for u, v in zip(g.units, kb.history[-1].stock)}
    uc = {u.id: v for u, v in zip(g.units, kc.history[-1].stock)}

    print("\n=== 闭环有效性：条件 B 相对条件 A 的存量变化（人类决策的影响） ===")
    print(f"{'单元':<10} {'A(无人)':>10} {'B(有人)':>10} {'变化':>10} {'变化率':>9}")
    deltas = {}
    for uid in g.ids:
        d = ub[uid] - ua[uid]
        rate = (d / ua[uid] * 100) if ua[uid] > 1e-9 else float("nan")
        deltas[uid] = {"A": ua[uid], "B": ub[uid], "delta": d, "pct": rate}
        print(f"{uid:<10} {ua[uid]:>10.2f} {ub[uid]:>10.2f} {d:>+10.2f} {rate:>8.1f}%")

    effect = ua["fountain"] and (ub["fountain"] - ua["fountain"])
    print(f"\n[结论] 人类选择注入使 fountain 存量变化 {effect:+.2f} 人 "
          f"({(effect/ua['fountain']*100):+.1f}%)")
    print("[结论] 人的空间选择确实作为外生流量输入改变了系统演化 -> 闭环有效"
          if abs(effect) > 1e-6 else
          "[结论] 未观测到变化 -> 闭环存在问题，需排查")

    # ---- 三类决策者的贡献分解（条件 C 某一轮） ----
    print("\n=== 条件 C 第 200 轮的流量来源分解 ===")
    last = kc.history[-1]
    print(json.dumps(last.flows, indent=2, ensure_ascii=False))

    # ---- 落盘 ----
    summary = {
        "scenario": str(SCENARIO.name),
        "checks": [ra, rb, rc],
        "final_stock": {"A_pure": ua, "B_human": ub, "C_mixed": uc},
        "human_effect": deltas,
        "kernel_summary": {"A": ka.summary(), "B": kb.summary(), "C": kc.summary()},
    }
    (OUTDIR / "loop_demo_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # CSV：三种条件每轮的存量轨迹
    lines = ["round,condition," + ",".join(g.ids)]
    for cond, k in (("A_pure", ka), ("B_human", kb), ("C_mixed", kc)):
        for rec in k.history:
            vals = ",".join(f"{v:.4f}" for v in rec.stock)
            lines.append(f"{rec.round},{cond},{vals}")
    (OUTDIR / "stock_trajectories.csv").write_text("\n".join(lines), encoding="utf-8")

    print(f"\n[输出] {OUTDIR / 'loop_demo_summary.json'}")
    print(f"[输出] {OUTDIR / 'stock_trajectories.csv'}")

    all_pass = all(r["status"] == "PASS" for r in (ra, rb, rc))
    print(f"\n=== 总体判定: {'ALL PASS' if all_pass else 'FAIL'} ===")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
