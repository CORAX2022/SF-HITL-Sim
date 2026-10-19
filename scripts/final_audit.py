"""最终交付核验：汇总本阶段所有产出，并做一致性交叉检查。"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VAULT = Path(r"C:\Users\22181\Documents\Obsidian Vault\Research\sf-hitl-sim")


def ok(v):
    return "OK" if v else "MISSING"


print("=" * 62)
print("1. 文献（Lane P）")
print("=" * 62)
a = json.loads((ROOT / "docs/papers/index.json").read_text(encoding="utf-8"))
b = json.loads((ROOT / "docs/papers2/index.json").read_text(encoding="utf-8"))
print(f"  首批 index.json      : {len(a)} 条")
print(f"  近5年 index.json     : {len(b)} 条  (已下载 {sum(1 for e in b if e.get('downloaded'))}, "
      f"已核实 {sum(1 for e in b if e.get('verified'))})")
print(f"  合计条目             : {len(a) + len(b)}")
for f in ("index.json", "文献清单.md", "中文文献.md"):
    p = ROOT / "docs/papers2" / f
    print(f"  {f:20} : {ok(p.exists())}"
          + (f" ({p.stat().st_size/1024:.0f} KB)" if p.exists() else ""))
n_notes = len(list((ROOT / "docs/papers2/notes").glob("*.md")))
print(f"  逐篇笔记             : {n_notes} 篇")
yrs = [e["year"] for e in b if isinstance(e.get("year"), int)]
print(f"  年份范围             : {min(yrs)}–{max(yrs)}  (2021 前: {sum(1 for y in yrs if y < 2021)})")
themes = {}
for e in b:
    for t in e.get("themes", []):
        themes[t] = themes.get(t, 0) + 1
print(f"  主题分布             : {dict(sorted(themes.items()))}")

print()
print("=" * 62)
print("2. 仓库调研（Lane R）")
print("=" * 62)
d = json.loads((ROOT / "docs/repos-survey/repos.json").read_text(encoding="utf-8"))
print(f"  仓库总数             : {len(d)}")
print(f"  最低 star            : {min(r['stars'] for r in d)}  (>100: {all(r['stars'] > 100 for r in d)})")
print(f"  重复 full_name       : {len(d) - len({r['full_name'] for r in d})}")
print(f"  覆盖类别             : {len({r['category'] for r in d})}/7")
for f in ("项目汇总.md", "统计.md", "repos.json"):
    p = ROOT / "docs/repos-survey" / f
    print(f"  {f:20} : {ok(p.exists())}"
          + (f" ({p.stat().st_size/1024:.0f} KB)" if p.exists() else ""))

print()
print("=" * 62)
print("3. 选型与建设计划（Lane T）")
print("=" * 62)
for f in ("可用项目与建设计划.md", "快速启动清单.md", "许可证风险.md"):
    p = ROOT / "docs/tooling" / f
    print(f"  {f:20} : {ok(p.exists())}"
          + (f" ({p.stat().st_size/1024:.0f} KB)" if p.exists() else ""))

print()
print("=" * 62)
print("4. Obsidian 文献库")
print("=" * 62)
notes = list((VAULT / "Sources/Papers").glob("*.md"))
reg = (VAULT / "_system/registry.md").read_text(encoding="utf-8")
reg_rows = [l for l in reg.splitlines() if l.startswith("|") and len(l) > 70]
print(f"  来源笔记             : {len(notes)} 篇")
print(f"  登记表数据行         : {len(reg_rows)}")
print(f"  笔记数 == 登记行数   : {len(notes) == len(reg_rows)}")
hub = VAULT / "00-Hub.md"
print(f"  00-Hub.md            : {ok(hub.exists())}")
total = sum(p.stat().st_size for p in VAULT.rglob("*") if p.is_file())
print(f"  库内占用             : {total/1024/1024:.1f} MB")

print()
print("=" * 62)
print("5. 交叉一致性")
print("=" * 62)
ids_a = {e["id"] for e in a}
ids_b = {e["id"] for e in b}
print(f"  两批 id 交集         : {len(ids_a & ids_b)}")
print(f"  全部条目均含可核验 source_id: "
      f"{all(e.get('source_id') for e in b)}")
