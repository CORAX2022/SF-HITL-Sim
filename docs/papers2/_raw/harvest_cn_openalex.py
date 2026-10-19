# -*- coding: utf-8 -*-
"""Harvest Chinese-language journal articles from OpenAlex.
Filters: language=zh OR CJK title, primary location source is a known CN journal or CJK-named source.
-> cn_openalex_raw.json"""
import json, os, re, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cn_openalex_raw.json")
MAIL = "research@example.org"
CJK = re.compile(r"[\u3400-\u9fff]")

QUERIES = [
    ("A", "系统动力学 城市"), ("A", "存量 流量 城市 空间"), ("A", "因果回路图 城市"),
    ("A", "城市代谢 物质流"), ("A", "城市空间 流量 模型"),
    ("B", "参与式规划 仿真"), ("B", "人在回路 仿真"), ("B", "规划支持系统"),
    ("B", "公众参与 城市规划 决策"), ("B", "交互式 仿真 实验 主体"),
    ("C", "大语言模型 智能体"), ("C", "生成式人工智能 城市"), ("C", "人工智能 规划 智能体 仿真"),
    ("C", "人机协同 实验"),
    ("D", "行人流 仿真"), ("D", "人群仿真 元胞自动机"), ("D", "城市数字孪生"),
    ("D", "交通 出行 分布 模型"), ("D", "客流 预测 城市"),
]


def fetch(q, per=50, page=1):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
           + "&filter=from_publication_date:2021-10-01&per-page=%d&page=%d&mailto=%s" % (per, page, MAIL))
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def inv(inv_d):
    if not inv_d:
        return ""
    pos = sorted((i, w) for w, idxs in inv_d.items() for i in idxs)
    return " ".join(w for _, w in pos)


def main():
    rows, seen, log = [], set(), []
    for theme, q in QUERIES:
        try:
            d = fetch(q)
            res = d.get("results") or []
        except Exception as exc:  # noqa: BLE001
            log.append({"query": q, "error": repr(exc)[:200]})
            time.sleep(1.0)
            continue
        new = 0
        for w in res:
            title = (w.get("title") or "").strip()
            if not title or len(CJK.findall(title)) < 4:
                continue
            lang = w.get("language") or ""
            loc = w.get("primary_location") or {}
            src = (loc.get("source") or {}) or {}
            venue = (src.get("display_name") or "").strip()
            if lang not in ("zh",) and not CJK.search(venue):
                continue
            oid = (w.get("id") or "").rsplit("/", 1)[-1]
            if oid in seen:
                continue
            seen.add(oid)
            auths = [((a.get("author") or {}).get("display_name") or "").strip()
                     for a in (w.get("authorships") or [])[:10]]
            oa = w.get("open_access") or {}
            best = oa.get("best_oa_location") or {}
            rows.append({
                "openalex_id": oid, "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "title": title, "authors": [a for a in auths if a],
                "year": w.get("publication_year"), "date": w.get("publication_date"),
                "venue": venue, "language": lang,
                "abstract": inv(w.get("abstract_inverted_index")),
                "is_oa": bool(oa.get("is_oa")), "oa_status": oa.get("oa_status"),
                "pdf_url": best.get("pdf_url"),
                "url": w.get("doi") or (loc.get("landing_page_url") or ""),
                "cited_by": w.get("cited_by_count"), "theme": theme,
            })
            new += 1
        log.append({"query": q, "theme": theme, "returned": len(res), "new": new})
        time.sleep(0.6)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("cn openalex rows:", len(rows), "queries:", len(QUERIES),
          "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
