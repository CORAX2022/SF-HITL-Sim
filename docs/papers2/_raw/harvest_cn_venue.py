# -*- coding: utf-8 -*-
"""Second-pass Chinese harvest: OpenAlex search filtered to known Chinese venues.
-> cn_venue_raw.json"""
import json, os, re, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cn_venue_raw.json")
MAIL = "research@example.org"
CJK = re.compile(r"[\u3400-\u9fff]")

VENUES = [
    "城市规划", "城市规划学刊", "国际城市规划", "城市发展研究", "现代城市研究", "规划师",
    "地理学报", "地理研究", "地理科学", "地理科学进展", "经济地理", "人文地理",
    "地球信息科学学报", "测绘学报", "武汉大学学报(信息科学版)",
    "交通运输系统工程与信息", "中国公路学报", "城市交通", "交通运输工程与信息学报",
    "系统工程理论与实践", "系统工程学报", "管理科学学报", "中国管理科学",
    "自动化学报", "软件学报", "计算机学报", "计算机研究与发展", "智能系统学报",
    "自然资源学报", "生态学报", "建筑学报", "风景园林", "中国人口·资源与环境",
]

QUERIES = [
    ("A", "系统动力学 仿真 城市"),
    ("A", "存量 更新 空间 模型 城市"),
    ("A", "城市流 网络 空间 关联"),
    ("A", "因果回路 系统 反馈"),
    ("A", "要素流动 空间 格局"),
    ("B", "参与式 规划 公众参与 决策"),
    ("B", "情景 模拟 规划 支持 系统"),
    ("B", "仿真 实验 平台 人 决策"),
    ("B", "数字孪生 规划 参与"),
    ("C", "大语言模型 智能体 仿真"),
    ("C", "生成式人工智能 城市 规划"),
    ("C", "多智能体 仿真 社会"),
    ("C", "人工智能 规划 决策 大模型"),
    ("D", "行人流 元胞自动机 仿真"),
    ("D", "人群 疏散 仿真 模型"),
    ("D", "客流 预测 轨道 交通"),
    ("D", "手机信令 出行 空间 行为"),
    ("D", "数字孪生 城市 交通"),
    ("D", "起讫点 OD 估计"),
]


def fetch(q, venue, per=50):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
           + "&filter=from_publication_date:2021-10-01,primary_location.source.display_name.search:"
           + urllib.parse.quote(venue)
           + "&per-page=%d&mailto=%s" % (per, MAIL))
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def inv(d):
    if not d:
        return ""
    return " ".join(w for _, w in sorted((i, w) for w, idxs in d.items() for i in idxs))


def main():
    rows, seen, log = [], set(), []
    VEN = VENUES[:14]  # journal-side focus
    for theme, q in QUERIES:
        for venue in VEN:
            try:
                d = fetch(q, venue)
                res = d.get("results") or []
            except Exception as exc:  # noqa: BLE001
                log.append({"q": q, "venue": venue, "error": repr(exc)[:120]})
                time.sleep(0.5)
                continue
            new = 0
            for w in res:
                title = (w.get("title") or "").strip()
                if not title or len(CJK.findall(title)) < 4:
                    continue
                oid = (w.get("id") or "").rsplit("/", 1)[-1]
                if oid in seen:
                    continue
                seen.add(oid)
                loc = w.get("primary_location") or {}
                oa = w.get("open_access") or {}
                best = oa.get("best_oa_location") or {}
                rows.append({
                    "openalex_id": oid,
                    "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                    "title": title,
                    "authors": [((a.get("author") or {}).get("display_name") or "").strip()
                                for a in (w.get("authorships") or [])[:10]],
                    "year": w.get("publication_year"), "date": w.get("publication_date"),
                    "venue": ((loc.get("source") or {}) or {}).get("display_name") or "",
                    "language": w.get("language") or "",
                    "abstract": inv(w.get("abstract_inverted_index")),
                    "is_oa": bool(oa.get("is_oa")), "oa_status": oa.get("oa_status"),
                    "pdf_url": best.get("pdf_url"),
                    "url": w.get("doi") or (loc.get("landing_page_url") or ""),
                    "cited_by": w.get("cited_by_count"), "theme": theme, "query": q,
                })
                new += 1
            log.append({"q": q, "venue": venue, "returned": len(res), "new": new})
            time.sleep(0.35)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("cn venue rows:", len(rows), "calls:", len(QUERIES) * len(VEN),
          "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
