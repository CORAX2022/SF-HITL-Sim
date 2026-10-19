"""生成复现对比图（保存到 results/repro/）。

用法：
    py -3.13 scripts/plot_nlogo_repro.py
"""

from __future__ import annotations

import collections
import csv
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = (ROOT / "an-agent-based-simulation-model-of-pedestrian-evacuation-"
          "based-on-bayesian-nash-equilibrium_v1.0.0/results/"
          "experiment1-3patterns-table.csv")
MINE = ROOT / "_nlogo_run/repro_experiment1.csv"
OUT = ROOT / "results" / "repro"
PATTERNS = ["Shortest route", "Random follow", "BNE (mixed with RF)"]
COLORS = {"Shortest route": "#d95f02", "Random follow": "#1b9e77",
          "BNE (mixed with RF)": "#7570b3"}

# 中文字体
for f in ("Microsoft YaHei", "SimHei", "DengXian"):
    try:
        matplotlib.font_manager.findfont(f, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [f]
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False


def load(path: Path):
    rows = list(csv.reader(open(path, encoding="utf-8", errors="replace")))
    hi = next(i for i, r in enumerate(rows)
              if r and r[0].strip().strip('"') in ("[run number]", "Run number"))
    head = [c.strip().strip('"') for c in rows[hi]]
    data = [dict(zip(head, r)) for r in rows[hi + 1:] if len(r) == len(head)]
    return head, data


def series(data, head, pattern):
    """返回 {run: [(step, n)]} 与 {run: [(step, density)]}。"""
    c_run = next(c for c in head if "run number" in c.lower())
    c_step = next(c for c in head if c.lower() in ("[step]", "step"))
    c_n = next(c for c in head if c == "count turtles")
    # 同一指标在两份文件里列名不同：
    #   作者 -> "Max density per patch"
    #   复现 -> "max ([ count turtles-here ] of patches)"
    c_d = next(c for c in head
               if "density" in c.lower() or "turtles-here" in c.lower())
    counts, dens = collections.defaultdict(list), collections.defaultdict(list)
    for r in data:
        if r["moving-pattern"] != pattern:
            continue
        s = int(float(r[c_step]))
        counts[r[c_run]].append((s, float(r[c_n])))
        dens[r[c_run]].append((s, float(r[c_d])))
    for d in (counts, dens):
        for k in d:
            d[k].sort()
    return counts, dens


def exit_times(counts):
    return [max(s for s, _ in v) for v in counts.values()]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ha, da = load(AUTHOR)
    hm, dm = load(MINE)

    # ---- 图 1：三模式剩余人数曲线（作者 vs 复现） ----
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6), sharey=True)
    for ax, pat in zip(axes, PATTERNS):
        for data, head, style, lab in ((da, ha, "-", "作者原始"),
                                       (dm, hm, "--", "本次复现")):
            counts, _ = series(data, head, pat)
            # 对齐到固定长度网格后取均值
            L = max(len(v) for v in counts.values())
            grid = np.full((len(counts), L), np.nan)
            for i, v in enumerate(counts.values()):
                arr = np.array([n for _, n in v])
                grid[i, :len(arr)] = arr
            mean = np.nanmean(grid, axis=0)
            sd = np.nanstd(grid, axis=0)
            x = np.arange(len(mean))
            ax.plot(x, mean, style, color=COLORS[pat], label=lab, linewidth=1.8)
            if lab == "本次复现":
                ax.fill_between(x, mean - sd, mean + sd, color=COLORS[pat],
                                alpha=0.15)
        ax.set_title(pat, fontsize=11)
        ax.set_xlabel("步 (step)")
        ax.grid(alpha=0.3)
        ax.set_xlim(0, 220)
    axes[0].set_ylabel("剩余人数 (count turtles)")
    axes[0].legend(fontsize=9)
    fig.suptitle("隧道疏散：三种决策模式的剩余人数演化（作者 vs 复现，2000 人，50 次重复）",
                 fontsize=13)
    fig.tight_layout()
    p1 = OUT / "fig1_剩余人数曲线对比.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    print("saved:", p1)

    # ---- 图 2：出口时间箱线图 ----
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.36
    for k, (data, head, lab, off) in enumerate(
            ((da, ha, "作者原始", -width / 2), (dm, hm, "本次复现", width / 2))):
        positions, values, colors = [], [], []
        for i, pat in enumerate(PATTERNS):
            counts, _ = series(data, head, pat)
            positions.append(i + off)
            values.append(exit_times(counts))
            colors.append(COLORS[pat])
        bp = ax.boxplot(values, positions=positions, widths=width * 0.9,
                        patch_artist=True, showmeans=True,
                        medianprops=dict(color="black"))
        for patch, c in zip(bp["boxes"], colors):
            patch.set_facecolor(c)
            patch.set_alpha(0.45 if lab == "本次复现" else 0.85)
        for i, v in enumerate(values):
            ax.text(positions[i], max(v) + 4, f"{statistics.mean(v):.0f}",
                    ha="center", fontsize=9)
    ax.set_xticks(range(len(PATTERNS)))
    ax.set_xticklabels(PATTERNS)
    ax.set_ylabel("出口时间 / 疏散完成步数")
    ax.set_title("出口时间分布：作者原始（左）vs 本次复现（右）")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p2 = OUT / "fig2_出口时间箱线图.png"
    fig.savefig(p2, dpi=150)
    plt.close(fig)
    print("saved:", p2)

    # ---- 图 3：峰值密度 ----
    fig, ax = plt.subplots(figsize=(9, 5))
    for data, head, lab, off in ((da, ha, "作者原始", -width / 2),
                                 (dm, hm, "本次复现", width / 2)):
        positions, values = [], []
        for i, pat in enumerate(PATTERNS):
            _, dens = series(data, head, pat)
            positions.append(i + off)
            values.append([max(d for _, d in v) for v in dens.values()])
        bp = ax.boxplot(values, positions=positions, widths=width * 0.9,
                        patch_artist=True, showmeans=True,
                        medianprops=dict(color="black"))
        for patch, pat in zip(bp["boxes"], PATTERNS):
            patch.set_facecolor(COLORS[pat])
            patch.set_alpha(0.45 if lab == "本次复现" else 0.85)
    ax.set_xticks(range(len(PATTERNS)))
    ax.set_xticklabels(PATTERNS)
    ax.set_ylabel("单格峰值密度（人/patch）")
    ax.set_title("峰值密度分布：作者原始（左）vs 本次复现（右）")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p3 = OUT / "fig3_峰值密度对比.png"
    fig.savefig(p3, dpi=150)
    plt.close(fig)
    print("saved:", p3)

    # ---- 图 4：出口时间均值对照柱状 ----
    fig, ax = plt.subplots(figsize=(8, 4.6))
    x = np.arange(len(PATTERNS))
    a_vals, m_vals = [], []
    for pat in PATTERNS:
        a_vals.append(statistics.mean(exit_times(series(da, ha, pat)[0])))
        m_vals.append(statistics.mean(exit_times(series(dm, hm, pat)[0])))
    ax.bar(x - 0.2, a_vals, 0.4, label="作者原始", color="#888888")
    ax.bar(x + 0.2, m_vals, 0.4, label="本次复现", color="#2c7fb8")
    for i, (a, m) in enumerate(zip(a_vals, m_vals)):
        ax.text(i - 0.2, a + 3, f"{a:.0f}", ha="center", fontsize=9)
        ax.text(i + 0.2, m + 3, f"{m:.0f}", ha="center", fontsize=9)
        ax.text(i, max(a, m) + 18, f"{m - a:+.1f} ({(m-a)/a*100:+.1f}%)",
                ha="center", fontsize=8, color="#b30000")
    ax.set_xticks(x)
    ax.set_xticklabels(PATTERNS)
    ax.set_ylabel("出口时间均值（步）")
    ax.set_title("出口时间均值对照与相对偏差")
    ax.legend()
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    p4 = OUT / "fig4_出口时间均值对照.png"
    fig.savefig(p4, dpi=150)
    plt.close(fig)
    print("saved:", p4)


if __name__ == "__main__":
    main()
