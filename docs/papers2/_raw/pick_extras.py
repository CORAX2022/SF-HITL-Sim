# -*- coding: utf-8 -*-
"""Print compact info for candidate non-downloaded additions (English journal + Chinese)."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

STRONG_A = ["system dynamics", "stock and flow", "stock-flow", "causal loop", "urban metabolism",
            "mobility flow", "flow generation", "urban flow", "land use change", "spatial interaction",
            "aggregate model", "flow model", "material flow", "land-use", "spatial dynamics"]
BADV = ["plastics", "protein", "cancer", "covid", "river ecosystem", "nursing", "teaching",
        "medical", "wastewater", "battery", "crop", "soil", "landslide", "earthquake"]

oa = json.load(open(os.path.join(BASE, "openalex_raw.json"), encoding="utf-8"))["rows"]
valid = json.load(open(os.path.join(BASE, "valid_pdfs.json"), encoding="utf-8"))
have = set()
ni = json.load(open(os.path.join(BASE, "notes_input.json"), encoding="utf-8"))
for r in ni:
    if r.get("source_id"):
        have.add(r["source_id"].lower())

picks = []
for r in oa:
    t = (r.get("title") or "").lower()
    ab = (r.get("abstract") or "").lower()
    d = (r.get("doi") or "").lower()
    if not d or d in have:
        continue
    if any(b in t for b in BADV):
        continue
    hits = [k for k in STRONG_A if k in t]
    if len(hits) < 1:
        continue
    if r["theme"] != "A":
        continue
    if len(t) < 20:
        continue
    picks.append((len(hits) + (2 if hits else 0), r.get("cited_by") or 0, r))
picks.sort(key=lambda x: (-x[0], -x[1]))
seen = set()
n = 0
for s, cb, r in picks:
    k = re.sub(r"[^a-z0-9]+", "", (r.get("title") or "").lower())[:60]
    if k in seen:
        continue
    seen.add(k)
    n += 1
    print("---")
    print("DOI:", r.get("doi"), "| YEAR:", r.get("year"), "| CITED:", cb, "| OA:", r.get("is_oa"), r.get("oa_status"))
    print("TITLE:", r.get("title"))
    print("AUTH:", ", ".join((r.get("authors") or [])[:3]))
    print("VENUE:", r.get("venue"))
    print("ABS:", (r.get("abstract") or "")[:700])
    if n >= 14:
        break

print("\n========== CHINESE (NAPSTIC) ==========")
cn = json.load(open(os.path.join(BASE, "cn_final.json"), encoding="utf-8"))
sel = [c for c in cn if c["top_journal"]]
sel.sort(key=lambda x: (-x["score"], -x["year"]))
m = 0
for c in sel:
    if not any(t in c["journal"] for t in ["城市规划", "国际城市规划", "地理", "城市发展研究",
                                           "现代城市研究", "规划师", "交通运输", "系统工程",
                                           "人文地理", "经济地理", "地球信息", "风景园林", "建筑"]):
        continue
    m += 1
    print("---")
    print("TITLE:", c["title"])
    print("AUTH:", ", ".join(c["authors"][:3]), "| JOURNAL:", c["journal"], "| YEAR:", c["year"],
          "| VOL/ISSUE:", c.get("volume"), c.get("issue"), "| PAGES:", c.get("pages"))
    print("ORIGIN_ID:", c.get("origin_id"), "| KEYWORDS:", "、".join([k for k in c["keywords"] if k][:5]))
    print("ABS:", (c["abstract"] or "")[:420])
    if m >= 16:
        break
