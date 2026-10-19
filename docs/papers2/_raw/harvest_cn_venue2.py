# -*- coding: utf-8 -*-
"""Resolve Chinese journal source ids on OpenAlex, then filter works by source id.
-> cn_venue_raw.json"""
import json, os, re, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cn_venue_raw.json")
MAIL = "research@example.org"
CJK = re.compile(r"[\u3400-\u9fff]")

VENUES = [
    "城市规划", "城市规划学刊", "国际城市规划", "城市发展研究", "现代城市研究", "规划师",
    "地理学报", "地理研究", "地理科学", "地理科学进展", "经济地理", "人文地理",
    "地球信息科学学报", "测绘学报", "交通运输系统工程与信息", "中国公路学报", "城市交通",
    "系统工程理论与实践", "系统工程学报", "管理科学学报", "中国管理科学",
    "自动化学报", "软件学报", "计算机学报", "计算机研究与发展", "智能系统学报",
    "自然资源学报", "生态学报", "建筑学报", "风景园林", "中国人口·资源与环境",
]
QUERIES = [
    ("A", "系统动力学 仿真 城市"), ("A", "存量 更新 空间 模型"), ("A", "要素流动 空间 格局"),
    ("A", "因果 反馈 系统 模型"),
    ("B", "参与式 规划 公众参与"), ("B", "情景模拟 规划支持"), ("B", "仿真实验 决策 平台"),
    ("C", "大语言模型 智能体"), ("C", "生成式人工智能 规划"), ("C", "多智能体 仿真 社会"),
    ("D", "行人流 元胞自动机"), ("D", "人群 疏散 仿真"), ("D", "客流 预测 轨道"),
    ("D", "手机信令 出行"), ("D", "城市 数字孪生 交通"), ("D", "起讫点 OD 估计"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def resolve_sources():
    ids = {}
    for v in VENUES:
        try:
            d = get("https://api.openalex.org/sources?search=" + urllib.parse.quote(v)
                    + "&per-page=3&mailto=" + MAIL)
            for s in d.get("results") or []:
                name = s.get("display_name") or ""
                if CJK.search(name):
                    ids[name] = (s.get("id") or "").rsplit("/", 1)[-1]
                    break
        except Exception:  # noqa: BLE001
            continue
        time.sleep(0.25)
    return ids


def inv(d):
    if not d:
        return ""
    return " ".join(w for _, w in sorted((i, w) for w, idxs in d.items() for i in idxs))


def main():
    sid = resolve_sources()
    json.dump(sid, open(os.path.join(BASE, "cn_source_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("resolved sources:", len(sid))
    sids = list(sid.values())
    rows, seen, log = [], set(), []
    for theme, q in QUERIES:
        for i in range(0, len(sids), 8):
            chunk = sids[i:i + 8]
            url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
                   + "&filter=from_publication_date:2021-10-01,primary_location.source.id:"
                   + "|".join(chunk) + "&per-page=50&mailto=" + MAIL)
            try:
                d = get(url)
                res = d.get("results") or []
            except Exception as exc:  # noqa: BLE001
                log.append({"q": q, "chunk": i, "error": repr(exc)[:120]})
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
            log.append({"q": q, "chunk": i, "returned": len(res), "new": new})
            time.sleep(0.3)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("cn venue rows:", len(rows), "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
