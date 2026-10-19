"""从 docs/papers/index.json 生成逐篇笔记 docs/papers/notes/<id>.md。

每篇笔记包含：书目信息、本语料中的核实状态、一句话核心贡献、
对本研究的可借鉴点、局限。内容来源为 index.json 中经 PDF 首页实际抽取核验的记录，
并附该 PDF 首页的原文片段（证据），便于人工复核。
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "papers" / "index.json"
NOTES = ROOT / "docs" / "papers" / "notes"
HEADS = ROOT / ".scratch" / "pdf_heads.json"

THEME_NAME = {
    "A": "存量-流量 / 系统动力学空间建模",
    "B": "人在回路 / 参与式仿真",
    "C": "LLM 合成智能体与社会仿真",
    "D": "人群/人流仿真与数字孪生",
}


def main() -> None:
    NOTES.mkdir(parents=True, exist_ok=True)
    entries = json.loads(INDEX.read_text(encoding="utf-8"))

    heads = {}
    if HEADS.exists():
        for rec in json.loads(HEADS.read_text(encoding="utf-8")):
            name = Path(rec["file"]).stem
            heads[name] = rec

    written = 0
    for e in entries:
        eid = e["id"]
        h = heads.get(eid, {})
        verified = e.get("verified", False)
        themes = "、".join(f"{t}（{THEME_NAME[t]}）" for t in e["themes"])
        authors = "、".join(e["authors"]) if e["authors"] else "（待核验）"

        lines = [
            f"# {e.get('title') or '（标题待核验）'}",
            "",
            f"- **条目 id**：`{eid}`",
            f"- **作者**：{authors}",
            f"- **年份**：{e['year']}",
            f"- **来源**：{e.get('venue') or '—'}"
            + (f"（`{e['source_id']}`）" if e.get("source_id") else ""),
            f"- **主题线索**：{themes}",
            f"- **PDF**：`{e['pdf_path']}`"
            + (f"（{e['size_kb']} KB，{h.get('pages', '?')} 页）" if e.get("downloaded") else " ⚠️ 未下载"),
            f"- **元数据核实**：{'✅ 已由 PDF 首页正文抽取核验' if verified else '⚠️ **未核实**——标题/作者取自文件名，引用前必须人工确认'}",
            "",
            "## 核心贡献",
            "",
            e["contribution"] or "—",
            "",
            "## 对本研究的可借鉴点",
            "",
            e["borrow"] or "—",
            "",
            "## 局限",
            "",
            e["limitation"] or "—",
        ]

        if h.get("head"):
            head = re.sub(r"\s+", " ", h["head"]).strip()
            lines += [
                "",
                "## 证据：PDF 首页原文片段",
                "",
                "> " + head[:500].replace("|", "\\|"),
                "",
                f"*（自动抽取自 `{e['pdf_path']}` 第 1 页，用于人工复核条目信息。）*",
            ]
        else:
            lines += [
                "",
                "## 证据",
                "",
                "> ⚠️ 本 PDF 的文本层抽取失败（`EOF marker not found` 或文本为图像），"
                "无法自动核验条目信息。**引用前须人工打开 PDF 确认。**",
            ]

        (NOTES / f"{eid}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        written += 1

    print(f"写入 {written} 篇笔记 -> {NOTES}")


if __name__ == "__main__":
    main()
