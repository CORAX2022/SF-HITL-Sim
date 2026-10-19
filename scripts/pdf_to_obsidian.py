#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF -> token-efficient Markdown -> Obsidian project vault.

Follows the existing conventions of the sibling project
``Research/wargaming-library`` (see its ``_system/schema.md``):

* stable ID   = SHA-256 of the source file bytes
* note name   = truncated title + "--" + first 16 hex chars of the ID
* page heading= ``## PDF页 N``  (``## 正文`` when page splitting is impossible)
* frontmatter = id / type / title / extraction_status / semantic_verified
* registry    = ``| ID | 来源笔记 | 状态 |`` with a vault-absolute wikilink

Token-efficiency: the PDF body is never printed to the console; only counts
are emitted.  Long notes are split by page heading so they can be searched
on demand instead of being loaded whole.

Idempotent: an existing note whose frontmatter ``id`` equals the current
source SHA-256 is skipped unless ``--force`` is given.

Usage:
    py -3.13 scripts/pdf_to_obsidian.py \
        --pdf-dir  docs/papers/pdf \
        --index    docs/papers/index.json \
        --vault-project "C:/Users/22181/Documents/Obsidian Vault/Research/sf-hitl-sim" \
        [--force] [--report docs/obsidian/转换报告.md]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import traceback
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    sys.stderr.write("PyMuPDF (fitz) is required but not importable.\n")
    raise

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------

NOTE_DIR_REL = Path("Sources") / "Papers"
REGISTRY_REL = Path("_system") / "registry.md"

HEADER_NOTE = (
    "> 自动文字提取，未作事实核验、翻译或内容概括。"
    "PDF页码为文件物理页码；表格、公式与图示须查看原件。"
)

LOW_PAGE_CHARS = 80        # a page below this is "low text"
NOTE_MIN_CHARS = 400       # whole note below this is needs_review
LOW_PAGE_RATIO = 0.5       # or when at least half the pages are low text

HARD_CASES = {
    "Feygin2019_BISTRO",
    "Park2023_GenerativeAgents",
    "Piao2025_AgentSociety",
    "Zaitsev2023_Cormas",
    "Wang2021_DigitalTwinIntersection",
    "Qiu2025_LockInHypothesis",
    "Fang2021_FlowAggregation",
}

ILLEGAL = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
MULTISPACE = re.compile(r"[ \t\u00a0]{2,}")
PAGENUM_ONLY = re.compile(r"^\s*(?:[-–—]\s*)?\d{1,4}\s*$")
DIGITS = re.compile(r"\d+")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def note_stem(title: str, max_len: int = 60) -> str:
    """Truncated, filesystem-safe title stem used in the note filename."""
    stem = ILLEGAL.sub("_", (title or "").strip())
    stem = re.sub(r"\s+", "_", stem).strip("._- ")
    if len(stem) > max_len:
        stem = stem[:max_len].rstrip("._- ")
    return stem or "note"


def yaml_str(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', "'") + '"'


def file_uri(path: Path) -> str:
    return path.resolve().as_uri()


def source_link(entry: dict) -> str:
    sid = (entry.get("source_id") or "").strip()
    if not sid:
        return ""
    if sid.startswith("doi:"):
        return "https://doi.org/" + sid[4:].strip()
    if sid.startswith("http://") or sid.startswith("https://"):
        return sid
    if re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", sid):
        return "https://arxiv.org/abs/" + sid
    if re.fullmatch(r"[a-z-]+(\.[A-Za-z]{2})?/\d{7}(v\d+)?", sid):
        return "https://arxiv.org/abs/" + sid
    return sid


# --------------------------------------------------------------------------
# text cleaning
# --------------------------------------------------------------------------

def clean_lines(raw: str) -> list[str]:
    """Per-line normalisation: squeeze whitespace, drop control chars."""
    out = []
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.replace("\u00ad", "")           # soft hyphen
        line = MULTISPACE.sub(" ", line).strip()
        out.append(line)
    return out


def drop_running_heads(pages: list[list[str]]) -> tuple[list[list[str]], list[str]]:
    """Remove lines that repeat as page headers/footers across the document."""
    if len(pages) < 4:
        return pages, []
    counter: dict[str, int] = {}
    for lines in pages:
        body = [l for l in lines if l]
        cands = body[:2] + body[-2:]
        for cand in set(cands):
            if len(cand) < 3 or len(cand) > 120:
                continue
            counter[cand] = counter.get(cand, 0) + 1
    threshold = max(3, int(len(pages) * 0.5))
    drop = {k for k, v in counter.items() if v >= threshold}
    if not drop:
        return pages, []
    cleaned = []
    for lines in pages:
        body_idx = [i for i, l in enumerate(lines) if l]
        edge = body_idx[:2] + body_idx[-2:]
        removals = {i for i in edge if lines[i] in drop}
        cleaned.append([l for i, l in enumerate(lines) if i not in removals])
    return cleaned, sorted(drop)


def drop_edge_page_numbers(lines: list[str]) -> list[str]:
    body_idx = [i for i, l in enumerate(lines) if l]
    if not body_idx:
        return lines
    keep = set(body_idx)
    for i in (body_idx[0], body_idx[-1]):
        if PAGENUM_ONLY.match(lines[i]):
            keep.discard(i)
    return [l for i, l in enumerate(lines) if i in keep]


def dehyphenate(text: str) -> str:
    # join words broken across lines by a hyphen: "informa-\ntion" -> "information"
    text = re.sub(r"(?<=[A-Za-z])-\n(?=[a-z])", "", text)
    # join a line that ends mid-sentence with a lowercase continuation
    text = re.sub(r"(?<=[A-Za-z,;])\n(?=[a-z])", " ", text)
    return text


def render_page(lines: list[str]) -> str:
    lines = drop_edge_page_numbers(lines)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    text = "\n".join(lines)
    text = dehyphenate(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------
# extraction
# --------------------------------------------------------------------------

def diagnose_damage(pdf: Path) -> str:
    """Cheap structural facts used only to explain a hard failure.

    PyMuPDF readability is the authority; these are supporting details.
    """
    try:
        raw = pdf.read_bytes()
    except OSError as exc:
        return f"无法读取文件：{exc}"
    facts = [f"文件大小 {len(raw)} 字节"]
    m = re.search(rb"/Linearized\s+1.*?/L\s+(\d+)", raw[:2048], re.S)
    if m:
        try:
            declared = int(m.group(1))
            facts.append(f"线性化头声明完整长度 {declared} 字节"
                         + ("（实际偏小，下载被截断）" if declared > len(raw) else ""))
        except ValueError:
            pass
    if b"%%EOF" not in raw[-4096:]:
        facts.append("文件尾部无 %%EOF/xref 尾部结构")
    if b"/Root" not in raw and b"/Catalog" not in raw:
        facts.append("文件中找不到 /Root 或 /Catalog（页面树在截断部分）")
    return "；".join(facts)


def extract_pdf(pdf: Path) -> tuple[list[str], int, str]:
    """Return (rendered page texts, page count, error message)."""
    try:
        doc = fitz.open(str(pdf))
    except Exception as exc:  # damaged / truncated file
        return [], 0, f"{type(exc).__name__}: {exc}"
    try:
        pages_raw: list[list[str]] = []
        try:
            n = doc.page_count
        except Exception as exc:
            return [], 0, f"page_count failed: {type(exc).__name__}: {exc}"
        for i in range(n):
            try:
                raw = doc[i].get_text("text") or ""
            except Exception as exc:      # tolerate a single broken page
                raw = ""
                pages_raw.append([f"[页面 {i+1} 抽取失败: {type(exc).__name__}]"])
                continue
            pages_raw.append(clean_lines(raw))
        pages_clean, _ = drop_running_heads(pages_raw)
        rendered = [render_page(p) for p in pages_clean]
        return rendered, n, ""
    finally:
        try:
            doc.close()
        except Exception:
            pass


# --------------------------------------------------------------------------
# note rendering
# --------------------------------------------------------------------------

def build_note(entry: dict, pdf: Path, digest: str, pages: list[str],
               status: str, hints: list[str]) -> str:
    title = entry.get("title") or entry.get("id") or pdf.stem
    authors = entry.get("authors") or []
    year = entry.get("year") or ""
    venue = (entry.get("venue") or "").strip()
    link = source_link(entry)
    sid = (entry.get("source_id") or "").strip()
    venue_label = venue or entry.get("source") or "（元数据未提供）"
    if sid and sid not in venue_label:
        venue_label = f"{venue_label}（{sid}）"

    fm = [
        "---",
        f"id: {yaml_str(digest)}",
        "type: source",
        f"title: {yaml_str(title)}",
        f"authors: {yaml_str(', '.join(authors) if authors else '（元数据未提供）')}",
        f"year: {yaml_str(year)}",
        f"source: {yaml_str(venue_label)}",
        f"source_link: {yaml_str(link or '（元数据未提供）')}",
        f"local_file: {yaml_str(file_uri(pdf))}",
        f"extraction_status: {status}",
        "semantic_verified: false",
        "---",
        "",
        f"# {title}",
        "",
        HEADER_NOTE,
        "",
        "## 元数据",
        f"- 标题：{title}",
        f"- 作者：{', '.join(authors) if authors else '（元数据未提供）'}",
        f"- 年份：{year or '（元数据未提供）'}",
        f"- 来源：{venue_label}",
        f"- 来源链接：{link or '（元数据未提供）'}",
        f"- 状态：{status}",
        "",
        "## 原件",
        f"- [{pdf.name}]({file_uri(pdf)})",
        "",
    ]

    if hints:
        fm += ["## 提取提示", ""]
        fm += [f"- {h}" for h in hints]
        fm.append("")

    if not pages:
        fm += ["## 正文", ""]
        return "\n".join(fm).rstrip() + "\n"

    for idx, text in enumerate(pages, 1):
        fm.append(f"## PDF页 {idx}")
        fm.append("")
        if text:
            fm.append(text)
            fm.append("")

    body = "\n".join(fm)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.rstrip() + "\n"


# --------------------------------------------------------------------------
# existing note / registry
# --------------------------------------------------------------------------

FM_ID = re.compile(r'^id:\s*"?([0-9a-f]{64})"?\s*$', re.M)
FM_STATUS = re.compile(r'^extraction_status:\s*(\S+)\s*$', re.M)


def existing_id(note: Path) -> str | None:
    try:
        head = note.read_text(encoding="utf-8", errors="replace")[:1200]
    except OSError:
        return None
    m = FM_ID.search(head)
    return m.group(1) if m else None


def prune_orphans(note_dir: Path, expected: set[str], pdf_dir: Path) -> list[str]:
    """Delete stale notes this script owns whose source hash no longer matches.

    Only notes whose frontmatter ``local_file`` points into ``pdf_dir`` are
    considered, so notes written by other lanes are never touched.
    """
    removed = []
    prefix = file_uri(pdf_dir)
    for note in sorted(note_dir.glob("*.md")):
        if note.name in expected:
            continue
        text = note.read_text(encoding="utf-8", errors="replace")
        head = text[:2000]
        if "type: source" not in head:
            continue
        m = re.search(r'^local_file:\s*"?(file://[^"\n]+)"?\s*$', head, re.M)
        if not m or not m.group(1).startswith(prefix):
            continue
        note.unlink()
        removed.append(note.name)
    return removed


def rebuild_registry(project: Path, vault_name: str, project_slug: str) -> int:
    note_dir = project / NOTE_DIR_REL
    rows = []
    for note in sorted(note_dir.glob("*.md")):
        text = note.read_text(encoding="utf-8", errors="replace")
        head = text[:1500]
        m = FM_ID.search(head)
        s = FM_STATUS.search(head)
        if not m:
            continue
        rows.append((m.group(1), note.stem, s.group(1) if s else "unknown"))
    rows.sort(key=lambda r: r[0])

    registry = project / REGISTRY_REL
    registry.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 来源登记表",
        "",
        "| ID | 来源笔记 | 状态 |",
        "|---|---|---|",
    ]
    for rid, stem, status in rows:
        lines.append(
            f"| {rid} | [[Research/{project_slug}/{NOTE_DIR_REL.as_posix()}/{stem}]] | {status} |"
        )
    registry.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(rows)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    # MuPDF prints its repair chatter to stderr; keep the run readable.
    for _fn in ("mupdf_display_errors", "mupdf_display_warnings"):
        try:
            getattr(fitz.TOOLS, _fn)(False)
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="PDF -> Obsidian token-efficient Markdown")
    ap.add_argument("--pdf-dir", required=True, help="directory holding the source PDFs")
    ap.add_argument("--index", required=True, help="papers index.json with metadata")
    ap.add_argument("--vault-project", required=True, help="Obsidian project folder")
    ap.add_argument("--force", action="store_true", help="re-extract even if unchanged")
    ap.add_argument("--report", default=None, help="markdown report path")
    args = ap.parse_args(argv)

    pdf_dir = Path(args.pdf_dir)
    index_path = Path(args.index)
    project = Path(args.vault_project)
    note_dir = project / NOTE_DIR_REL
    note_dir.mkdir(parents=True, exist_ok=True)

    entries = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(entries, dict):
        entries = entries.get("papers") or entries.get("items") or []

    # vault root derived from .../Research/<slug>
    project_slug = project.name
    research = project.parent
    vault_name = research.parent.name if research.parent else ""

    results = []
    by_hash: dict[str, str] = {}

    for entry in entries:
        eid = entry.get("id") or ""
        rec = {
            "id": eid,
            "title": entry.get("title") or eid,
            "authors": entry.get("authors") or [],
            "year": entry.get("year") or "",
            "venue": (entry.get("venue") or "").strip(),
            "stem": note_stem(eid or entry.get("title") or ""),
            "pages": 0,
            "chars": 0,
            "status": "",
            "note": "",
            "hint": "",
            "hard_case": eid in HARD_CASES,
            "low_pages": 0,
            "skipped": False,
        }
        results.append(rec)

        pdf = pdf_dir / f"{eid}.pdf"
        if not pdf.is_file():
            cand = list(pdf_dir.glob(f"{eid}*.pdf"))
            pdf = cand[0] if cand else pdf
        if not pdf.is_file():
            rec.update(status="failed", hint="源 PDF 文件缺失（索引中有记录，磁盘上找不到）")
            results[-1] = rec
            continue

        try:
            digest = sha256_file(pdf)
        except Exception as exc:
            rec.update(status="failed", hint=f"读取源文件失败：{type(exc).__name__}: {exc}")
            continue

        note = note_dir / f"{rec['stem']}--{digest[:16]}.md"
        rec["note"] = note.name

        if note.exists() and not args.force and existing_id(note) == digest:
            head = note.read_text(encoding="utf-8", errors="replace")
            m = FM_STATUS.search(head[:1500])
            prior = m.group(1) if m else "extracted"
            rec["status"] = prior
            rec["skipped"] = True
            rec["hint"] = "哈希未变，跳过重写"
            rec["chars"] = len(head)
            rec["pages"] = head.count("\n## PDF页 ")
            if by_hash.get(digest) is None:
                by_hash[digest] = note.name
            continue

        collapse = by_hash.get(digest)
        if collapse:  # identical content already converted under another entry
            rec.update(status="duplicate", note=collapse,
                       hint=f"与 {collapse} 内容相同（SHA-256 一致），未重复建笔记")
            continue

        try:
            pages, n, err = extract_pdf(pdf)
        except Exception as exc:  # never die on one file
            pages, n, err = [], 0, f"{type(exc).__name__}: {exc}"
            rec["hint_tb"] = traceback.format_exc(limit=2)

        rec["pages"] = n
        total = sum(len(p) for p in pages)
        low = sum(1 for p in pages if len(p) < LOW_PAGE_CHARS)
        rec["chars"] = total
        rec["low_pages"] = low

        hints: list[str] = []
        if err:
            status = "failed"
            hints.append(f"转换异常：{err}")
            hints.append(diagnose_damage(pdf))
        elif not pages:
            status = "failed"
            hints.append(
                "源 PDF 被截断，PyMuPDF 打开后 0 页（无可解析的页面树），无法提取文字；"
                "需重新获取完整原件"
            )
            hints.append(diagnose_damage(pdf))
        else:
            if total < NOTE_MIN_CHARS:
                status = "needs_review"
            elif pages and low / len(pages) >= LOW_PAGE_RATIO:
                status = "needs_review"
            else:
                status = "extracted"
            if status == "needs_review":
                if low == len(pages) and total == 0:
                    hints.append("未提取到文字；需要 OCR 或人工核验")
                else:
                    page_list = ",".join(str(i) for i, p in enumerate(pages, 1)
                                         if len(p) < LOW_PAGE_CHARS)
                    hints.append(
                        f"低文字量页面（可能扫描页、插图或空白页）: {page_list}"
                    )
                    hints.append(
                        f"全文合计 {total} 字符 / {len(pages)} 页，低于可靠阈值；建议人工核验"
                    )
            if rec["hard_case"] and status != "extracted":
                hints.append("本文件此前在其它抽取器中报 “EOF marker not found”，已用 PyMuPDF 逐页重试")

        try:
            note.write_text(
                build_note(entry, pdf, digest, pages, status, hints),
                encoding="utf-8",
            )
        except Exception as exc:
            rec.update(status="failed", hint=f"写入笔记失败：{type(exc).__name__}: {exc}")
            continue

        rec["status"] = status
        rec["hint"] = "；".join(hints)
        by_hash.setdefault(digest, note.name)

    # ---------------- registry ----------------
    expected = {r["note"] for r in results if r["note"]}
    pruned = prune_orphans(note_dir, expected, pdf_dir)
    row_count = rebuild_registry(project, vault_name, project_slug)

    # ---------------- report / console ----------------
    counted = {"extracted": 0, "needs_review": 0, "failed": 0,
               "skipped": 0, "duplicate": 0}
    for r in results:
        base = r["status"].split(" ")[0]
        counted[base] = counted.get(base, 0) + 1
        if r.get("skipped"):
            counted["skipped"] += 1

    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# PDF → Obsidian 转换报告",
        "",
        f"- 运行时间：{now}",
        f"- 源目录：`{pdf_dir}`",
        f"- 索引：`{index_path}`",
        f"- 目标库目录：`{project}`",
        f"- 来源笔记目录：`{note_dir}`",
        f"- 登记表：`{project / REGISTRY_REL}`（{row_count} 行 = 笔记数）",
        f"- 运行模式：{'--force 全量重跑' if args.force else '增量（幂等）'}",
        "",
        "## 总计",
        "",
        "| 状态 | 篇数 |",
        "|---|---|",
        f"| extracted（提取完成） | {counted['extracted']} |",
        f"| needs_review（低文字量/无文字层） | {counted['needs_review']} |",
        f"| failed（转换异常） | {counted['failed']} |",
        f"| skipped（哈希未变，跳过） | {counted['skipped']} |",
        f"| duplicate（内容重复，未重复建笔记） | {counted['duplicate']} |",
        f"| **索引条目合计** | **{len(results)}** |",
        "",
        "## 逐篇明细",
        "",
        "| # | 条目 ID | 页数 | 字符数 | 状态 | 笔记文件 | 备注 |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['id']} | {r['pages']} | {r['chars']} | "
            f"{r['status']}{' (skipped)' if r.get('skipped') else ''} | "
            f"{r['note'] or '—'} | {r['hint'] or ''} |"
        )

    low_list = [r for r in results if r["status"].startswith("needs_review")]
    fail_list = [r for r in results if r["status"] == "failed"]
    lines += ["", "## 低文字量需人工复核清单", ""]
    lines.append("### needs_review（低文字量 / 无文字层）")
    lines.append("")
    if low_list:
        for r in low_list:
            lines.append(
                f"- `{r['id']}` — {r['pages']} 页 / {r['chars']} 字符"
                + (f"（低文字页：{r['low_pages']}）" if r["low_pages"] else "")
                + f" → `{r['note']}`"
            )
    else:
        lines.append("- 无")
    lines += ["", "### failed（0 页，实质无文字，同样需要人工处理）", ""]
    if fail_list:
        for r in fail_list:
            lines.append(f"- `{r['id']}` — 0 页 / 0 字符 → `{r['note'] or '（未生成笔记）'}`")
    else:
        lines.append("- 无")

    lines += ["", "## 失败清单与原因", ""]
    if fail_list:
        for r in fail_list:
            lines.append(f"### `{r['id']}`")
            lines.append("")
            lines.append(f"- 状态：failed")
            for part in (r["hint"] or "未记录原因").split("；"):
                if part.strip():
                    lines.append(f"- {part.strip()}")
            lines.append("")
    else:
        lines.append("- 无")

    lines += [
        "",
        "## 约定对照（wargaming-library schema）",
        "",
        "- 稳定 ID = 源文件内容 SHA-256（写入 frontmatter `id`）。",
        "- 笔记文件名 = 截短标题 + `--` + ID 前 16 位。",
        "- 每页 PDF 使用二级标题 `## PDF页 N`；无法按页切分时使用 `## 正文`。",
        "- `semantic_verified` 始终为 `false`（未经人工核验）。",
        "- 登记表 `| ID | 来源笔记 | 状态 |`，wikilink 指向库内绝对路径。",
        "",
        "## 后续建议",
        "",
        "1. 标为 `failed` 的文件均为**截断下载**：文件尾部缺少 `%%EOF`/`xref`/页面树，",
        "   PyMuPDF 打开后 0 页。请从原始来源重新下载完整原件后，",
        "   重跑本脚本（幂等，会自动补建笔记并刷新登记表）。",
        "2. 判断下载是否完整请用**内容级校验**（PyMuPDF 打开后统计可提取字符数），",
        "   不要只看 HTTP 状态码、文件体积或尾部是否含 `%%EOF`；后者在 arXiv PDF 上会误判。",
        "3. 替换源文件前先下载到临时路径并校验通过，再原子替换，避免出现",
        "   “旧的好文件被新的截断文件覆盖”。",
        "4. 源文件内容变化时，本脚本会删除哈希已失效的旧笔记（仅限 `local_file`",
        "   指向本次 `--pdf-dir` 的笔记），以保持“登记表条目数 = 笔记数”。",
        "",
    ]

    if pruned:
        lines += ["## 已清理的过期笔记（源文件哈希已变化）", ""]
        lines += [f"- `{name}`" for name in pruned]
        lines.append("")

    report_path = Path(args.report) if args.report else Path("docs/obsidian/转换报告.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # ASCII-safe console digest (avoids Windows code-page mangling)
    print("== pdf_to_obsidian ==")
    print(f"index entries : {len(results)}")
    for k in ("extracted", "needs_review", "failed", "skipped", "duplicate"):
        print(f"{k:<14}: {counted.get(k, 0)}")
    print(f"notes on disk : {len(list(note_dir.glob('*.md')))}")
    print(f"registry rows : {row_count}")
    print(f"pruned stale  : {len(pruned)}")
    print(f"report        : {report_path}")
    for r in results:
        print("  - %-42s pages=%-4s chars=%-7s %s" % (
            r["id"][:42], r["pages"], r["chars"], r["status"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
