# -*- coding: utf-8 -*-
"""Select theme-relevant Chinese-language records from crossref_raw.json
-> cn_curated.json ; prints one compact line per accepted record."""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u3400-\u9fff]")

KW = {
    "A": ["系统动力学", "存量", "流量", "因果", "回路", "城市代谢", "物质流", "空间流", "动力模型"],
    "B": ["人在回路", "参与式", "参与", "规划支持", "交互仿真", "实验平台", "利益相关", "协同设计",
          "众包", "公众参与", "决策支持", "联合规划"],
    "C": ["大语言模型", "大模型", "语言模型", "智能体", "生成式", "人工智能生成", "人机", "混合智能",
          "社会仿真", "数字人", "GPT", "仿真智能"],
    "D": ["人群", "行人", "人流", "元胞自动机", "数字孪生", "交通流", "出行", "疏散",
          "OD", "起讫点", "轨迹", "客流", "步行"],
}


def main():
    d = json.load(open(os.path.join(BASE, "crossref_raw.json"), encoding="utf-8"))
    rows = d["rows"]
    acc, seen = [], set()
    for r in rows:
        t = r["title"]
        if len(CJK.findall(t)) < 4:
            continue
        body = t + " " + (r.get("abstract") or "") + " " + (r.get("venue") or "")
        themes, sc = [], 0
        for th, kws in KW.items():
            hit = sum(1 for k in kws if k in body)
            titlehit = sum(1 for k in kws if k in t)
            if hit:
                themes.append(th)
                sc += hit + 2 * titlehit
        if not themes or sc < 3:
            continue
        key = re.sub(r"[^\w\u3400-\u9fff]+", "", t)[:60]
        if key in seen:
            continue
        seen.add(key)
        r = dict(r)
        r["themes"] = themes
        r["score"] = sc
        r["has_abstract"] = bool((r.get("abstract") or "").strip())
        acc.append(r)
    acc.sort(key=lambda x: (-x["score"], -(x["year"] or 0)))
    json.dump(acc, open(os.path.join(BASE, "cn_curated.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("cn accepted:", len(acc))
    for r in acc[:45]:
        print("|".join([str(r.get("year")), "".join(r["themes"]), ("ABS" if r["has_abstract"] else "noabs"),
                        r["title"][:44], (r["authors"][0] if r["authors"] else "?"),
                        (r["venue"] or "")[:22], r["doi"]]))


if __name__ == "__main__":
    main()
