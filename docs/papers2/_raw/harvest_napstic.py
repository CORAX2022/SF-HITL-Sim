# -*- coding: utf-8 -*-
"""Harvest Chinese journal articles from NAPSTIC (国家科技期刊平台) search API.
-> cn_napstic_raw.json ; then curate to cn_final.json"""
import json, os, re, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "cn_napstic_raw.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

QUERIES = [
    "系统动力学 城市", "存量 流量 城市 空间", "因果回路图", "城市代谢", "土地 存量 更新 模拟",
    "空间 相互作用 模型 城市", "要素流动 城市网络", "客流 预测 模型",
    "参与式 规划", "公众参与 城市规划", "规划支持系统", "情景 模拟 规划",
    "交互 仿真 实验 平台", "人在回路", "协同设计 城市",
    "大语言模型 城市", "大语言模型 智能体", "生成式人工智能 规划", "人工智能 规划 决策",
    "多智能体 仿真 社会", "智能体 仿真 城市",
    "行人流 元胞自动机", "人群 仿真 疏散", "行人 仿真 模型", "城市 数字孪生",
    "手机信令 出行 行为", "交通 出行 分布 模型", "起讫点 OD 反推",
]
TOP_JOURNALS = ["城市规划", "城市规划学刊", "国际城市规划", "城市发展研究", "现代城市研究",
                "规划师", "地理学报", "地理研究", "地理科学", "地理科学进展", "经济地理",
                "人文地理", "地球信息科学", "测绘学报", "交通运输系统工程与信息",
                "中国公路学报", "城市交通", "系统工程理论与实践", "系统工程学报",
                "管理科学学报", "中国管理科学", "自动化学报", "软件学报", "计算机学报",
                "计算机研究与发展", "智能系统学报", "自然资源学报", "生态学报", "建筑学报",
                "风景园林", "中国人口·资源与环境", "武汉大学学报", "同济大学学报",
                "东南大学学报", "清华大学学报", "浙江大学学报", "华南理工大学学报",
                "长安大学学报", "北京工业大学学报", "上海城市规划", "城乡规划", "西部人居环境学刊"]
THEME_KW = {
    "A": ["系统动力学", "存量", "流量", "因果", "回路", "城市代谢", "物质流", "流空间",
          "要素流动", "空间相互作用", "反馈", "承载力", "供需", "集聚", "扩散"],
    "B": ["参与式", "公众参与", "规划支持", "人在回路", "交互仿真", "仿真实验", "利益相关",
          "协同设计", "共同设计", "决策支持", "工作坊", "情景模拟", "实验平台", "众包"],
    "C": ["大语言模型", "大模型", "语言模型", "智能体", "生成式", "人机协同", "人工智能",
          "社会仿真", "多智能体", "深度强化学习", "数字人"],
    "D": ["人群", "行人", "人流", "元胞自动机", "数字孪生", "交通流", "出行", "疏散",
          "起讫点", "轨迹", "客流", "步行", "手机信令", "移动性", "仿真", "预测"],
}


def fetch(q, page=1, size=20):
    url = ("https://opaj.napstic.cn/search/literature?q=" + urllib.parse.quote(q)
           + "&page=%d&size=%d" % (page, size))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def main():
    rows, seen, log = [], set(), []
    for q in QUERIES:
        for page in (1, 2, 3, 4, 5, 6, 7, 8):
            try:
                d = fetch(q, page, 20)
                lst = (((d.get("result") or {}).get("searchResult") or {}).get("list")) or []
            except Exception as exc:  # noqa: BLE001
                log.append({"q": q, "page": page, "error": repr(exc)[:120]})
                time.sleep(1.0)
                continue
            new = 0
            for it in lst:
                title = ((it.get("title") or {}).get("zh") or "").strip()
                if not title:
                    continue
                key = re.sub(r"\s+", "", title)[:60]
                if key in seen:
                    continue
                pub = it.get("publication") or {}
                yr = pub.get("year")
                jn = ((pub.get("name") or {}).get("zh") or "").strip()
                if not yr or int(yr) < 2021:
                    continue
                seen.add(key)
                rows.append({
                    "title": title, "journal": jn, "year": int(yr),
                    "volume": pub.get("volume"), "issue": pub.get("issue"),
                    "pages": pub.get("page"), "issn": pub.get("issn"),
                    "authors": [((c.get("name") or "").strip()) for c in (it.get("creators") or [])],
                    "affil": [((c.get("organization") or "").strip()) for c in (it.get("creators") or [])][:1],
                    "keywords": [k.get("name") for k in
                                 ((it.get("keywords") or {}).get("keyWordsCN") or [])],
                    "abstract": ((it.get("abstract") or {}).get("zh") or "").strip(),
                    "language": it.get("language"),
                    "is_oa": pub.get("isOA"),
                    "origin_id": (it.get("identifier") or {}).get("originId"),
                    "data_id": (it.get("identifier") or {}).get("dataId"),
                    "data_origin": pub.get("dataOrigin"),
                    "query": q,
                })
                new += 1
            log.append({"q": q, "page": page, "returned": len(lst), "new": new})
            time.sleep(0.4)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("napstic rows:", len(rows), "errors:", sum(1 for x in log if "error" in x))

    # curate
    acc, seen2 = [], set()
    for r in rows:
        jn = r["journal"]
        body = (r["title"] + " "
                + " ".join(k for k in r["keywords"] if k)
                + " " + (r["abstract"] or "")[:400])
        themes, sc = [], 0
        for th, kws in THEME_KW.items():
            th_hit = sum(1 for k in kws if k in r["title"])
            b_hit = sum(1 for k in kws if k in body)
            if th_hit or b_hit:
                themes.append(th)
                sc += 4 * th_hit + b_hit
        if any(t in jn for t in TOP_JOURNALS):
            sc += 6
        if not themes or sc < 6:
            continue
        key = re.sub(r"\s+", "", r["title"])[:50]
        if key in seen2:
            continue
        seen2.add(key)
        r = dict(r)
        r["themes"] = themes
        r["score"] = sc
        r["top_journal"] = any(t in jn for t in TOP_JOURNALS)
        acc.append(r)
    acc.sort(key=lambda x: (-x["score"], -x["year"]))
    json.dump(acc, open(os.path.join(BASE, "cn_final.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("cn curated:", len(acc), "top-journal:", sum(1 for r in acc if r["top_journal"]))
    for r in acc[:14]:
        print("%s|%s|%s|%s|%s" % (r["year"], "".join(r["themes"]), r["journal"][:14],
                                  r["title"][:34], (r["authors"][0] if r["authors"] else "?")))


if __name__ == "__main__":
    main()
