# -*- coding: utf-8 -*-
"""Curate Chinese-language OpenAlex records -> cn2_curated.json; compact readable listing."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
CJK = re.compile(r"[\u3400-\u9fff]")

KW = {
    "A": ["系统动力学", "存量", "流量", "因果", "回路", "城市代谢", "物质流", "空间流",
          "动力学模型", "流空间", "要素流动", "供需", "承载力"],
    "B": ["参与式", "公众参与", "规划支持", "人在回路", "交互仿真", "仿真实验", "利益相关",
          "协同设计", "共同设计", "决策支持", "众包", "开放实验", "情景模拟", "工作坊"],
    "C": ["大语言模型", "大模型", "语言模型", "智能体", "生成式", "人机协同", "混合智能",
          "社会仿真", "数字人", "人工智能生成", "多智能体", "GPT", "仿真"],
    "D": ["人群", "行人", "人流", "元胞自动机", "数字孪生", "交通流", "出行", "疏散",
          "起讫点", "轨迹", "客流", "步行", "移动性", "手机信令", "时空行为"],
}
GOOD_VENUE = ["城市规划", "地理学报", "地理研究", "地理科学", "城市规划学刊", "国际城市规划",
              "城市发展研究", "人文地理", "经济地理", "交通运输系统工程与信息", "中国公路学报",
              "系统工程理论与实践", "管理科学", "建筑学报", "风景园林", "地球信息科学",
              "武汉大学学报", "清华大学学报", "同济大学学报", "东南大学学报", "测绘学报",
              "自然资源学报", "生态学报", "中国人口", "现代城市研究", "规划师", "城乡规划",
              "城市交通", "交通运输工程", "智能系统学报", "计算机科学", "软件学报", "自动化学报"]


def main():
    rows = json.load(open(os.path.join(BASE, "cn_openalex_raw.json"), encoding="utf-8"))["rows"]
    acc, seen = [], set()
    for r in rows:
        t = r["title"]
        if len(CJK.findall(t)) < 5:
            continue
        body = t + " " + (r.get("abstract") or "")
        themes, sc = [], 0
        for th, kws in KW.items():
            th_hit = sum(1 for k in kws if k in t)
            b_hit = sum(1 for k in kws if k in body)
            if th_hit or b_hit:
                themes.append(th)
                sc += 3 * th_hit + b_hit
        v = r.get("venue") or ""
        vs = 4 if any(g in v for g in GOOD_VENUE) else 0
        ab = 2 if (r.get("abstract") or "").strip() else 0
        sc += vs + ab
        if not themes or sc < 6:
            continue
        key = re.sub(r"[^\w\u3400-\u9fff]+", "", t)[:50]
        if key in seen:
            continue
        seen.add(key)
        r = dict(r)
        r["themes"] = themes
        r["score"] = sc
        r["has_abstract"] = bool(ab)
        r["good_venue"] = bool(vs)
        acc.append(r)
    acc.sort(key=lambda x: (-x["score"], -(x["year"] or 0)))
    json.dump(acc, open(os.path.join(BASE, "cn2_curated.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("cn2 accepted:", len(acc))
    for r in acc[:40]:
        print("%s|%s|%s|%s|%s|%s|%s" % (r.get("year"), "".join(r["themes"]),
              "ABS" if r["has_abstract"] else "-", r["title"][:40],
              (r["authors"][0] if r["authors"] else "?"), (r.get("venue") or "")[:20],
              r.get("doi") or r["openalex_id"]))


if __name__ == "__main__":
    main()
