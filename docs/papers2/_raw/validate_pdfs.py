# -*- coding: utf-8 -*-
"""Validate every PDF in docs/papers2/pdf -> valid_pdfs.json
Criteria (per lead's guidance): size > 20 KB, fitz pages > 0, text chars > 1000."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDFDIR = os.path.join(os.path.dirname(BASE), "pdf")
OUT = os.path.join(BASE, "valid_pdfs.json")


def ident(p):
    if p.get("arxiv_id"):
        return "ax_" + p["arxiv_id"].replace("/", "_").replace(".", "-")
    d = (p.get("doi") or "").replace("https://doi.org/", "").replace("/", "_").replace(".", "-")
    return "oa_" + d[:60]


def validate(path):
    try:
        size = os.path.getsize(path)
    except OSError:
        return False, {"reason": "missing"}
    if size <= 20480:
        return False, {"reason": "size_lt_20kb", "size": size}
    try:
        import fitz
        doc = fitz.open(path)
        pages = doc.page_count
        chars = 0
        for i in range(min(pages, 50)):
            chars += len((doc[i].get_text() or "").strip())
        title = ""
        if pages:
            lines = [l.strip() for l in (doc[0].get_text() or "").splitlines() if l.strip()]
            title = " ".join(lines[:4])[:160]
        doc.close()
    except Exception as exc:  # noqa: BLE001
        return False, {"reason": "fitz_error:" + repr(exc)[:70], "size": size}
    if pages <= 0:
        return False, {"reason": "zero_pages", "size": size}
    if chars <= 1000:
        return False, {"reason": "chars_le_1000", "size": size, "pages": pages, "chars": chars}
    return True, {"size": size, "pages": pages, "chars": chars, "first_page": title}


def main():
    res = {}
    for fn in sorted(os.listdir(PDFDIR)):
        if not fn.lower().endswith(".pdf"):
            continue
        pid = fn[:-4]
        ok, info = validate(os.path.join(PDFDIR, fn))
        res[pid] = {"ok": ok, "info": info, "file": fn}
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = [k for k, v in res.items() if v["ok"]]
    print("valid:", len(ok), "/", len(res))
    for k in sorted(res):
        if not res[k]["ok"]:
            print("  FAIL", k, res[k]["info"].get("reason"))


if __name__ == "__main__":
    main()
