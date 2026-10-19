# -*- coding: utf-8 -*-
"""Crossref harvest for Chinese-language journal records -> crossref_raw.json
Only keeps items whose title or journal name contains CJK characters."""
import json, os, re, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "crossref_raw.json")
MAIL = "research@example.org"
CJK = re.compile(r"[\u3400-\u9fff]")

QUERIES = [
    "系统动力学 城市",
    "存量 流量 城市 空间",
    "因果回路图",
    "人在回路 仿真",
    "参与式 规划 仿真",
    "规划支持系统",
    "大语言模型 智能体 仿真",
    "生成式智能体 社会仿真",
    "人群仿真 行人流",
    "元胞自动机 行人",
    "城市数字孪生",
    "交通 出行 分布 模型",
    "人流 治理",
    "城市仿真 平台",
    "联合规划 实验 主体",
]


def fetch(q, rows=40):
    url = ("https://api.crossref.org/works?query.bibliographic="
           + urllib.parse.quote(q)
           + "&filter=from-pub-date:2021-10-01,type:journal-article&rows=%d" % rows)
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (mailto:%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    rows, seen, log = [], set(), []
    for q in QUERIES:
        try:
            d = fetch(q)
            items = (d.get("message") or {}).get("items") or []
        except Exception as exc:  # noqa: BLE001
            log.append({"query": q, "error": repr(exc)[:200]})
            time.sleep(1.5)
            continue
        new = 0
        for it in items:
            title = " ".join((it.get("title") or [""])[0].split())
            venue = " ".join((it.get("container-title") or [""])[0].split())
            if not title:
                continue
            if not (CJK.search(title) or CJK.search(venue)):
                continue
            doi = (it.get("DOI") or "").strip()
            if not doi or doi in seen:
                continue
            seen.add(doi)
            auths = []
            for a in (it.get("author") or [])[:10]:
                n = " ".join(filter(None, [a.get("given"), a.get("family")]))
                n = n or (a.get("name") or "")
                if n:
                    auths.append(n.strip())
            yr = None
            dp = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
            if dp and dp[0]:
                yr = int(dp[0])
            rows.append({
                "doi": doi, "title": title, "authors": auths, "year": yr,
                "venue": venue, "abstract": re.sub(r"<[^>]+>", " ", it.get("abstract") or ""),
                "url": it.get("URL") or ("https://doi.org/" + doi),
                "cited_by": it.get("is-referenced-by-count"), "query": q,
                "language": it.get("language") or "",
            })
            new += 1
        log.append({"query": q, "returned": len(items), "new_cjk": new})
        time.sleep(1.2)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("crossref cjk rows:", len(rows), "queries:", len(QUERIES),
          "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
