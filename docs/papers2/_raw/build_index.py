# -*- coding: utf-8 -*-
"""Assemble docs/papers2/index.json + 文献清单.md + 中文文献.md
Sources: notes_input.json (55 validated PDFs) + _raw/zh/*.json + _raw/extras.json."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # docs/papers2
RAW = os.path.join(ROOT, "_raw")
PDFREL = "docs/papers2/pdf/"

THEME_NAME = {
    "A": "存量-流量 / 系统动力学空间建模",
    "B": "人在回路与参与式仿真",
    "C": "LLM 合成智能体与社会仿真",
    "D": "人群/人流空间仿真与数字孪生",
}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def norm_title(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    recs = load(os.path.join(RAW, "notes_input.json"))
    zh = {}
    zdir = os.path.join(RAW, "zh")
    for f in os.listdir(zdir):
        if f.endswith(".json"):
            d = load(os.path.join(zdir, f))
            zh[d["id"]] = d
    ex = load(os.path.join(RAW, "extras.json"))
    extras = ex["entries"]

    # entries whose verified publication date / issue falls outside the 2021-10+ window
    # (OpenAlex publication_date confirmed, or Chinese 2021 issue month unverifiable)
    WINDOW_OUT = {
        "jn_https-doi-org-10-3389-frsc-2021-690458":
            "Frontiers in Sustainable Cities，OpenAlex publication_date 2021-08-06，早于 2021-10 时间窗",
        "jn_https-doi-org-10-3389-ffutr-2021-640570":
            "Frontiers in Future Transportation，OpenAlex publication_date 2021-03-18，早于 2021-10 时间窗",
    }
    pending = {p["id"]: p["reason"] for p in ex.get("pending_window", [])}
    out_ids = {e["id"]: e["reason"] for e in ex.get("excluded_out_of_window", [])}

    entries, appendix = [], []
    for r in recs:
        pid = r["id"]
        z = zh.get(pid, {})
        src = r.get("source_id") or ""
        if src.startswith("10."):
            source_id = src
            url = r.get("url") or ("https://doi.org/" + src)
        else:
            source_id = src
            url = r.get("url") or ("https://arxiv.org/abs/" + src)
        rec = {
            "id": pid,
            "title": norm_title(r["title"]),
            "authors": r.get("authors") or [],
            "year": r.get("year"),
            "venue": r.get("venue") or "",
            "source_id": source_id,
            "url": url,
            "pdf_path": r.get("pdf_path"),
            "downloaded": True,
            "open_access": bool(r.get("open_access", True)),
            "themes": [r.get("theme")] if r.get("theme") else [],
            "abstract_zh": z.get("abstract_zh", "").strip(),
            "contribution_zh": z.get("contribution_zh", "").strip(),
            "verified": True,
            "notes": "PDF 已下载并经 PyMuPDF 校验（页数 %s，正文可读）；标题/作者/摘要取自 arXiv 或出版方 API 实际返回。" % r.get("pages"),
        }
        if pid in WINDOW_OUT:
            appendix.append(dict(rec, window=WINDOW_OUT[pid]))
            continue
        entries.append(rec)
    for e in extras:
        rec = {
            "id": e["id"], "title": norm_title(e["title"]), "authors": e["authors"],
            "year": e["year"], "venue": e["venue"], "source_id": e["source_id"],
            "url": e["url"], "pdf_path": None, "downloaded": False,
            "open_access": bool(e.get("open_access")), "themes": e["themes"],
            "abstract_zh": e["abstract_zh"], "contribution_zh": e["contribution_zh"],
            "verified": True, "notes": e["notes"],
        }
        if e["id"] in out_ids:
            appendix.append(dict(rec, window=out_ids[e["id"]]))
            continue
        if e["id"] in pending:
            rec["notes"] = "【时间窗待核，未计入主表】" + pending[e["id"]] + "；" + rec["notes"]
            appendix.append(dict(rec, window=pending[e["id"]]))
            continue
        entries.append(rec)

    # order: by theme A->D, downloaded first, then year desc
    entries.sort(key=lambda x: (min(x["themes"]) if x["themes"] else "Z",
                                0 if x["downloaded"] else 1,
                                -(x["year"] or 0), x["title"]))
    with open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    json.dump([e["id"] for e in appendix],
              open(os.path.join(RAW, "appendix_ids.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    dl = [e for e in entries if e["downloaded"]]
    print("index entries:", len(entries), "downloaded:", len(dl),
          "not-downloaded:", len(entries) - len(dl))
    print("per theme:", {t: sum(1 for e in entries if t in e["themes"]) for t in "ABCD"})
    print("downloaded per theme:", {t: sum(1 for e in dl if t in e["themes"]) for t in "ABCD"})

    # ---------- 文献清单.md ----------
    L = ["# 近五年文献清单（2021-10 至 2026-10）", "",
         "> 生成说明：条目来自 arXiv API、OpenAlex API、NAPSTIC（国家科技期刊平台）检索 API 的实际返回；",
         "> `downloaded=是` 表示 PDF 已下载到 `docs/papers2/pdf/` 并通过 PyMuPDF 校验（页数 > 0 且正文可提取 > 1000 字符，文件 > 20 KB）。",
         "> 结构：按 A/B/C/D 四个主题分节。完整字段见 `index.json`。", "",
         "统计：主表条目 **%d** 条（全部为 2021-10 之后发表/预印），其中已下载 PDF **%d** 篇，未获 PDF **%d** 篇（均给出可核验链接与摘要）；"
         "另有 **%d** 条时间窗外/待核条目单列于文末附录，不计入主表。"
         % (len(entries), len(dl), len(entries) - len(dl), len(appendix)), ""]
    for t in "ABCD":
        rows = [e for e in entries if t in e["themes"]]
        L.append("## 主题 %s — %s（%d 条，其中已下载 %d 篇）" % (t, THEME_NAME[t], len(rows),
                                                              sum(1 for e in rows if e["downloaded"])))
        L.append("")
        L.append("| # | 年份 | 标题 | 作者 | 来源 | 已下 PDF | 链接 |")
        L.append("|---|---|---|---|---|---|---|")
        for i, e in enumerate(rows, 1):
            au = ", ".join(e["authors"][:3]) + (" 等" if len(e["authors"]) > 3 else "")
            ttl = e["title"].replace("|", "\\|")
            L.append("| %d | %s | %s | %s | %s | %s | [%s](%s) |" % (
                i, e["year"], ttl, au, e["venue"].replace("|", "\\|") or "-",
                "是" if e["downloaded"] else "否",
                ("原文页" if e["downloaded"] else "链接"), e["url"]))
        L.append("")
        L.append("**本主题可借鉴点摘要**")
        L.append("")
        for e in rows:
            L.append("- `%s` %s" % (e["id"], e["contribution_zh"]))
        L.append("")
    L += ["## 附：时间窗外 / 时间窗待核条目（不计入主表，仅备查）", "",
          "主表严格限定 2021-10 之后发表或预印。以下条目经核验其发表时间早于该窗口，或仅能确认年份、月份无法核验，",
          "因此不计入主表 A/B/C/D 统计，单独列出以保持完整性（其中 2 篇 PDF 已下载，保留在 `pdf/` 与 `notes/` 中）。",
          "另：Su et al. (2021) *Spatial Interaction Spillover Effects…*（DOI 10.3390/ijerph18168535，OpenAlex 发表日 2021-08-12）",
          "同样早于时间窗，检索中已遇到但未纳入候选清单。", "",
          "| id | 年份 | 标题 | 作者 | 来源 | PDF | 链接 | 排除原因 |",
          "|---|---|---|---|---|---|---|---|"]
    for e in appendix:
        L.append("| `%s` | %s | %s | %s | %s | %s | [链接](%s) | %s |" % (
            e["id"], e["year"], e["title"].replace("|", "\\|"),
            ", ".join(e["authors"][:3]), e["venue"].replace("|", "\\|"),
            "已下载" if e["downloaded"] else "未获得", e["url"],
            e.get("window", "").replace("|", "\\|")))
    L.append("")
    L += ["## 背景经典（不计入主表，均早于 2021-10）", "",
          "本次检索聚焦 2021-10 之后的文献，未单独收录早于该时间窗的奠基性文献；",
          "相关经典（如 Forrester 系统动力学、Meadows 存量-流量、Batty 城市建模、Helbing 社会力模型）",
          "建议作为背景另行补录，避免与主表时间窗混淆。", ""]
    with open(os.path.join(ROOT, "文献清单.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 中文文献.md ----------
    cn = [e for e in entries if re.search(r"[\u3400-\u9fff]", e["title"])]
    cn_pending = [e for e in appendix if re.search(r"[\u3400-\u9fff]", e["title"])]
    C = ["# 中文文献题录", "",
         "## 检索与核验说明", "",
         "- 知网（CNKI）、万方均无公开 API，无法批量抓取；本次中文题录取自 **NAPSTIC 国家科技期刊平台**",
         "  公开检索接口（`https://opaj.napstic.cn/search/literature`）的实际返回 JSON，",
         "  字段包括题名、作者、期刊、年卷期页、关键词与摘要，均已逐条核验。",
         "- 上述平台不提供稳定的文章详情页 URL（详情页为 500/404），因此 `url` 字段给出的是",
         "  **平台检索页链接**（可按标题复现检索），并在 `notes` 中记录 NAPSTIC 记录号（origin_id）与卷期页。",
         "- **全部中文条目均未获得 PDF**：这些期刊为订阅制，全文需机构账号或付费下载，",
         "  公开渠道（DOAJ/Unpaywall/OpenAlex OA location）均无合法开放全文。原因逐条列在表中。", "",
         "共 %d 条中文题录（其中 %d 条已计入主表；%d 条因 2021 年月份无法核验列入时间窗待核附录）。"
         % (len(cn) + len(cn_pending), len(cn), len(cn_pending)), ""]
    C.append("| # | 年份 | 标题 | 作者 | 期刊 | 主题 | PDF | 未获原因 / 核对信息 |")
    C.append("|---|---|---|---|---|---|---|---|")
    for i, e in enumerate(cn, 1):
        C.append("| %d | %s | %s | %s | %s | %s | 未获得 | %s |" % (
            i, e["year"], e["title"].replace("|", "\\|"),
            "、".join(e["authors"][:3]), e["venue"].replace("|", "\\|"),
            "/".join(e["themes"]), "订阅期刊，无公开 OA 全文；" + e["notes"].replace("|", "\\|")))
    C.append("")
    if cn_pending:
        C.append("### 时间窗待核条目（2021 年，月份无法核验，未计入主表）")
        C.append("")
        for e in cn_pending:
            C.append("- **%s**（%s，%s）｜作者：%s｜主题：%s｜[平台检索链接](%s)｜**未获得 PDF**：%s" % (
                e["title"], e["year"], e["venue"], "、".join(e["authors"]),
                "/".join(e["themes"]), e["url"], e.get("window", "")))
        C.append("")
    C.append("## 各条摘要（来自平台返回，非翻译生成）")
    C.append("")
    for e in cn:
        C.append("### %s（%s，%s）" % (e["title"], e["year"], e["venue"]))
        C.append("")
        C.append("- 作者：%s" % "、".join(e["authors"]))
        C.append("- 主题：%s｜可核验来源：%s" % ("/".join(e["themes"]), e["url"]))
        C.append("- 摘要（平台原文，节选）：%s" % e["abstract_zh"])
        C.append("- 核心贡献：%s" % e["contribution_zh"])
        C.append("- 本次状态：**未获得 PDF** — %s" % e["notes"])
        C.append("")
    with open(os.path.join(ROOT, "中文文献.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(C))

    print("wrote index.json / 文献清单.md / 中文文献.md ; cn entries:", len(cn))


if __name__ == "__main__":
    main()
