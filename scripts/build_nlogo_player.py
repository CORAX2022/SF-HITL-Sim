"""把 NetLogo 逐帧空间导出（spatial_table.csv）转成自包含的 HTML 播放器。

用法：
    py -3.13 scripts/build_nlogo_player.py
输出：
    results/repro/nlogo_播放器.html   （单文件、离线可用、无需服务器）
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "_nlogo_run" / "spatial_table.csv"
OUT = ROOT / "results" / "repro" / "nlogo_播放器.html"

HEX = "0123456789abcdef"


def load() -> dict:
    """解析 BehaviorSpace 表，重建每个模式的逐帧热力图与 agent 坐标。"""
    rows = list(csv.reader(open(SRC, encoding="utf-8", errors="replace")))
    hi = None
    for i, r in enumerate(rows):
        cells = [c.strip().strip('"') for c in r]
        if cells and cells[0].lower().startswith(("[run number]", "run number")):
            hi = i
            header = cells
            break
    if hi is None:
        raise SystemExit("未找到表头")

    # 定位列（记位置，按位置取值）
    i_run = next(i for i, c in enumerate(header) if "run number" in c.lower())
    i_pat = header.index(next(c for c in header if c == "moving-pattern"))
    i_step = next(i for i, c in enumerate(header)
                  if c.lower() in ("[step]", "step"))
    i_n = header.index("count turtles")
    i_heat = next(i for i, c in enumerate(header) if "viz-heat" in c.lower())
    i_ag = next(i for i, c in enumerate(header) if "viz-agents" in c.lower())

    # 世界边界：元数据是「键行 + 值行」两行一组，如
    #   "min-pxcor","max-pxcor","min-pycor","max-pycor"
    #   "-34","34","-10","10"
    meta = {}
    for i, r in enumerate(rows[:hi]):
        cells = [c.strip().strip('"') for c in r]
        if "min-pxcor" in cells and i + 1 < len(rows):
            vals = [c.strip().strip('"') for c in rows[i + 1]]
            for k, v in zip(cells, vals):
                if k in ("min-pxcor", "max-pxcor", "min-pycor", "max-pycor"):
                    meta[k] = int(float(v))
    for k in ("min-pxcor", "max-pxcor", "min-pycor", "max-pycor"):
        if k not in meta:
            raise SystemExit(f"未能从文件头解析世界边界 {k}")
    w = meta["max-pxcor"] - meta["min-pxcor"] + 1
    h = meta["max-pycor"] - meta["min-pycor"] + 1

    out: dict[str, dict] = {}
    for r in rows[hi + 1:]:
        if len(r) != len(header):
            continue
        pat = r[i_pat]
        entry = out.setdefault(pat, {"frames": []})
        heat = r[i_heat]
        # 每 2 个十六进制字符 = 一个 patch 的占用数
        cells = [int(heat[i:i + 2], 16) for i in range(0, len(heat) - 1, 2)]
        # agent 坐标：每 4 个字符 = (x+100, y+100)
        ag = r[i_ag]
        pts = []
        for i in range(0, len(ag) - 3, 4):
            x = int(ag[i:i + 2], 16) - 100
            y = int(ag[i + 2:i + 4], 16) - 100
            pts.append((x, y))
        entry["frames"].append({
            "t": int(float(r[i_step])),
            "n": int(float(r[i_n])),
            "heat": cells,
            "pts": pts,
        })

    return {
        "world": {"minx": meta["min-pxcor"], "miny": meta["min-pycor"], "w": w, "h": h},
        "patterns": out,
    }


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>NetLogo 疏散仿真播放器 — BNE 行人疏散模型</title>
<style>
  :root { --bg:#0f1115; --panel:#171a21; --line:#2a2f3a; --fg:#e6e9ef; --dim:#9aa3b2; }
  * { box-sizing: border-box; }
  body { margin:0; padding:20px; background:var(--bg); color:var(--fg);
         font:14px/1.5 "Microsoft YaHei",-apple-system,"Segoe UI",sans-serif; }
  h1 { font-size:18px; margin:0 0 4px; }
  .sub { color:var(--dim); font-size:12px; margin-bottom:16px; }
  .wrap { display:flex; gap:20px; flex-wrap:wrap; }
  .stage { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px; }
  canvas { display:block; background:#0b0d11; border-radius:6px; image-rendering:pixelated; }
  .side { min-width:320px; flex:1; max-width:420px; }
  .row { margin-bottom:12px; }
  label { display:block; color:var(--dim); font-size:12px; margin-bottom:4px; }
  select, input[type=range], button { width:100%; }
  select, button { background:#222733; color:var(--fg); border:1px solid var(--line);
                   border-radius:6px; padding:7px 9px; font:inherit; cursor:pointer; }
  button:hover { background:#2b3242; }
  button.primary { background:#2f6fd0; border-color:#2f6fd0; }
  button.primary:hover { background:#3a7de0; }
  .btns { display:flex; gap:8px; }
  .stats { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
  .card { background:#1d222c; border:1px solid var(--line); border-radius:8px; padding:9px 11px; }
  .card .k { color:var(--dim); font-size:11px; }
  .card .v { font-size:19px; font-weight:600; font-variant-numeric:tabular-nums; }
  .legend { margin-top:12px; font-size:12px; color:var(--dim); }
  .bar { height:10px; border-radius:5px; margin-top:5px;
         background:linear-gradient(90deg,#12233f,#1f5fa8,#39a0d8,#f2c14e,#e8663d,#c1272d); }
  .note { margin-top:14px; font-size:12px; color:var(--dim); border-left:3px solid #2f6fd0;
          padding-left:10px; }
</style>
</head>
<body>
<h1>隧道行人疏散仿真播放器</h1>
<div class="sub">模型：ABM of pedestrian evacuation based on Bayesian Nash Equilibrium
  （Wang, Ge &amp; Comber, University of Leeds，CC BY-SA 4.0）·
  由 NetLogo 7.0.4 headless 导出逐帧空间数据</div>

<div class="wrap">
  <div class="stage">
    <canvas id="cv" width="828" height="252"></canvas>
    <div class="legend">
      单格人数
      <div class="bar"></div>
      <div style="display:flex;justify-content:space-between">
        <span>0</span><span>由浅到深＝越拥挤</span><span>15+</span>
      </div>
    </div>
  </div>

  <div class="side">
    <div class="row">
      <label>决策模式</label>
      <select id="pat"></select>
    </div>
    <div class="row">
      <label>时间步 <span id="tlab"></span></label>
      <input type="range" id="t" min="0" max="0" value="0">
    </div>
    <div class="btns row">
      <button id="play" class="primary">▶ 播放</button>
      <button id="reset">⟲ 重置</button>
    </div>
    <div class="row">
      <label>速度</label>
      <select id="speed">
        <option value="240">慢</option>
        <option value="120" selected>中</option>
        <option value="60">快</option>
        <option value="25">极快</option>
      </select>
    </div>
    <div class="stats">
      <div class="card"><div class="k">剩余人数</div><div class="v" id="vn">–</div></div>
      <div class="card"><div class="k">已疏散</div><div class="v" id="ve">–</div></div>
      <div class="card"><div class="k">当前时间步</div><div class="v" id="vt">–</div></div>
      <div class="card"><div class="k">疏散进度</div><div class="v" id="vp">–</div></div>
    </div>
    <div class="note" id="note"></div>
  </div>
</div>

<script>
const DATA = __DATA__;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const world = DATA.world;
// 用正方形像素单元，保持隧道真实比例（69 x 21）
const CELL = 12;
cv.width = world.w * CELL;
cv.height = world.h * CELL;
const CW = CELL, CH = CELL;
const patterns = Object.keys(DATA.patterns);
const selPat = document.getElementById('pat');
patterns.forEach(p => { const o = document.createElement('option'); o.value = o.textContent = p; selPat.appendChild(o); });

let frames = [], idx = 0, timer = null, N0 = 1;

const COLOR = (v) => {
  if (v <= 0)  return '#0b0d11';
  if (v === 1) return '#1f3a5f';
  if (v === 2) return '#1f5fa8';
  if (v <= 4)  return '#2f8fd0';
  if (v <= 6)  return '#39a0d8';
  if (v <= 8)  return '#7cc4d8';
  if (v <= 10) return '#f2c14e';
  if (v <= 13) return '#e8663d';
  return '#c1272d';
};

function loadPattern(p) {
  frames = DATA.patterns[p].frames;
  N0 = frames[0].n || 1;
  const t = document.getElementById('t');
  t.max = frames.length - 1; t.value = 0; idx = 0;
  draw();
}

function draw() {
  const f = frames[idx]; if (!f) return;
  ctx.fillStyle = '#0b0d11'; ctx.fillRect(0, 0, cv.width, cv.height);
  const { minx, miny } = world;
  // 热力图
  for (let j = 0; j < world.h; j++) {
    for (let i = 0; i < world.w; i++) {
      const v = f.heat[j * world.w + i] || 0;
      ctx.fillStyle = COLOR(v);
      ctx.fillRect(i * CW, (world.h - 1 - j) * CH, CW, CH);
    }
  }
  // agent 覆盖点
  ctx.fillStyle = 'rgba(255,255,255,.85)';
  for (const [x, y] of f.pts) {
    const i = x - minx, j = y - miny;
    if (i < 0 || j < 0 || i >= world.w || j >= world.h) continue;
    ctx.fillRect(i * CW + CW * 0.28, (world.h - 1 - j) * CH + CH * 0.28, CW * 0.44, CH * 0.44);
  }
  // 出口标记（左右两端）
  ctx.fillStyle = 'rgba(120,220,140,.9)';
  ctx.fillRect(0, 0, 3, cv.height); ctx.fillRect(cv.width - 3, 0, 3, cv.height);

  document.getElementById('t').value = idx;
  document.getElementById('tlab').textContent = 't = ' + f.t + ' / ' + frames[frames.length - 1].t;
  document.getElementById('vn').textContent = f.n;
  document.getElementById('ve').textContent = (N0 - f.n);
  document.getElementById('vt').textContent = f.t;
  document.getElementById('vp').textContent = ((N0 - f.n) / N0 * 100).toFixed(1) + '%';
}

function stop() { if (timer) { clearInterval(timer); timer = null; } document.getElementById('play').textContent = '▶ 播放'; }

function play() {
  if (timer) { stop(); return; }
  document.getElementById('play').textContent = '⏸ 暂停';
  const sp = +document.getElementById('speed').value;
  timer = setInterval(() => {
    if (idx >= frames.length - 1) { stop(); return; }
    idx++; draw();
  }, sp);
}

selPat.onchange = () => { stop(); loadPattern(selPat.value); };
document.getElementById('play').onclick = play;
document.getElementById('reset').onclick = () => { stop(); idx = 0; draw(); };
document.getElementById('t').oninput = (e) => { stop(); idx = +e.target.value; draw(); };
document.getElementById('speed').onchange = () => { if (timer) { stop(); play(); } };

const note = document.getElementById('note');
const summary = patterns.map(p => {
  const fr = DATA.patterns[p].frames;
  return p + '：' + fr[fr.length - 1].t + ' 步';
}).join(' ｜ ');
note.innerHTML = '<b>三种模式的疏散时长</b><br>' + summary +
  '<br><br>白色方块＝行人；底色＝单格密度。可见 BNE 模式人流更分散、出口更少排队。';

loadPattern(patterns[0]);
</script>
</body>
</html>
"""


def main() -> None:
    data = load()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(HTML.replace("__DATA__", json.dumps(data, separators=(",", ":"))),
                   encoding="utf-8")
    n = sum(len(v["frames"]) for v in data["patterns"].values())
    print(f"写入 {OUT}")
    print(f"  世界: {data['world']['w']} x {data['world']['h']}")
    for p, v in data["patterns"].items():
        f = v["frames"]
        print(f"  {p:24} 帧数={len(f):3}  疏散完成 t={f[-1]['t']}")
    print(f"  合计帧数: {n}  文件大小: {OUT.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
