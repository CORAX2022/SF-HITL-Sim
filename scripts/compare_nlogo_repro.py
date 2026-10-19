"""把 NetLogo 复现结果与作者原始结果做逐指标对比。

用法：
    py -3.13 scripts/compare_nlogo_repro.py
"""

from __future__ import annotations

import collections
import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = (ROOT / "an-agent-based-simulation-model-of-pedestrian-evacuation-"
          "based-on-bayesian-nash-equilibrium_v1.0.0/results/"
          "experiment1-3patterns-table.csv")
MINE = ROOT / "_nlogo_run/repro_experiment1.csv"

PATTERNS = ["Shortest route", "Random follow", "BNE (mixed with RF)"]


def load(path: Path) -> tuple[list[str], list[dict]]:
    """读 BehaviorSpace 表，自动定位表头（带或不带元数据行）。"""
    rows = list(csv.reader(open(path, encoding="utf-8", errors="replace")))
    hi = None
    for i, r in enumerate(rows):
        cells = [c.strip().strip('"') for c in r]
        if cells and cells[0] in ("[run number]", "Run number"):
            hi = i
            header = cells
            break
    if hi is None:
        raise SystemExit(f"未找到表头: {path}")
    data = []
    for r in rows[hi + 1:]:
        if len(r) != len(header):
            continue
        data.append({h: v for h, v in zip(header, r)})
    return header, data


def col(d: dict, *names: str) -> str:
    for n in names:
        if n in d:
            return n
    raise KeyError(names)


def summarize(data: list[dict], header: list[str], label: str) -> dict:
    c_run = col(data[0], "[run number]", "Run number")
    c_pat = col(data[0], "moving-pattern")
    c_step = col(data[0], "[step]", "Step")
    c_n = col(data[0], "count turtles")
    c_dens = col(data[0], "max ([ count turtles-here ] of patches)",
                 "Max density per patch")

    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in data:
        per[r[c_pat]][r[c_run]].append(
            (int(float(r[c_step])), float(r[c_n]), float(r[c_dens]))
        )

    out = {"label": label, "patterns": {}}
    for pat in PATTERNS:
        runs = per.get(pat)
        if not runs:
            continue
        init = statistics.mean(v[0][1] for v in runs.values())
        evac = [max(s[0] for s in v) for v in runs.values()]
        peaks = [max(s[2] for s in v) for v in runs.values()]
        out["patterns"][pat] = {
            "runs": len(runs),
            "initial_agents": init,
            "exit_time_mean": statistics.mean(evac),
            "exit_time_sd": statistics.pstdev(evac) if len(evac) > 1 else 0.0,
            "exit_time_min": min(evac),
            "exit_time_max": max(evac),
            "peak_density_mean": statistics.mean(peaks),
            "peak_density_max": max(peaks),
        }
    return out


def main() -> None:
    h_a, d_a = load(AUTHOR)
    h_m, d_m = load(MINE)
    a = summarize(d_a, h_a, "作者原始结果")
    m = summarize(d_m, h_m, "本次复现 (NetLogo 7.0.4)")

    print("=" * 78)
    print("NetLogo 模型复现对比：ABM of pedestrian evacuation based on BNE")
    print("=" * 78)
    print(f"作者数据: {len(d_a):,} 行, 列 {len(h_a)}")
    print(f"复现数据: {len(d_m):,} 行, 列 {len(h_m)}")
    print(f"作者列: {h_a}")
    print(f"复现列: {h_m}")
    print()
    print(f"{'模式':<24}{'指标':<16}{'作者':>12}{'复现':>12}{'差异':>10}")
    print("-" * 78)
    for pat in PATTERNS:
        pa, pm = a["patterns"].get(pat), m["patterns"].get(pat)
        if not pa or not pm:
            print(f"{pat:<24} 缺失")
            continue
        rows = [
            ("run 数", pa["runs"], pm["runs"], ""),
            ("初始人数", pa["initial_agents"], pm["initial_agents"], ""),
            ("出口时间均值", pa["exit_time_mean"], pm["exit_time_mean"], "num"),
            ("出口时间 SD", pa["exit_time_sd"], pm["exit_time_sd"], "num"),
            ("出口时间 max", pa["exit_time_max"], pm["exit_time_max"], ""),
            ("峰值密度均值", pa["peak_density_mean"], pm["peak_density_mean"], "num"),
        ]
        for name, va, vm, kind in rows:
            if kind == "num":
                diff = f"{vm - va:+.1f}"
                print(f"{pat:<24}{name:<16}{va:>12.1f}{vm:>12.1f}{diff:>10}")
            else:
                print(f"{pat:<24}{name:<16}{va:>12.0f}{vm:>12.0f}{'':>10}")
        print()

    print("=" * 78)
    print("趋势一致性（论文核心结论：BNE 优于 SR 与 RF）")
    print("=" * 78)
    for src, tag in ((a, "作者"), (m, "复现")):
        p = src["patterns"]
        sr = p["Shortest route"]["exit_time_mean"]
        rf = p["Random follow"]["exit_time_mean"]
        bne = p["BNE (mixed with RF)"]["exit_time_mean"]
        order = "BNE < RF < SR" if bne < rf < sr else f"其它: {bne:.0f}/{rf:.0f}/{sr:.0f}"
        print(f"  {tag}: SR={sr:.0f}  RF={rf:.0f}  BNE={bne:.0f}  -> 排序 {order}")


if __name__ == "__main__":
    main()
