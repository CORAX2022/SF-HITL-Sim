# -*- coding: utf-8 -*-
"""Join validated PDFs with metadata -> notes_input.json (records for all downloaded papers)."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDFDIR = os.path.join(os.path.dirname(BASE), "pdf")


def load(fn):
    return json.load(open(os.path.join(BASE, fn), encoding="utf-8"))


def jn_id(doi):
    return "jn_" + re.sub(r"[^a-zA-Z0-9]+", "-", doi or "")[:58]


def main():
    valid = load("valid_pdfs.json")
    ax = load("curated2.json")["selected"]
    pool = load("pool.json")["pool"]
    jc = load("journal_cand.json")
    dlj = load("download_oa.json") if os.path.exists(os.path.join(BASE, "download_oa.json")) else {}

    byid = {}
    for p in ax:
        pid = "ax_" + p["arxiv_id"].replace("/", "_").replace(".", "-")
        byid[pid] = {
            "id": pid, "title": p["title"], "authors": p.get("authors") or [],
            "year": p.get("year"), "venue": p.get("venue") or "arXiv preprint",
            "source_id": p["arxiv_id"], "url": p["url"], "theme": p["theme"],
            "abstract": (p.get("abstract") or "")[:1400], "open_access": True,
            "journal_ref": p.get("journal_ref") or "", "arxiv_id": p["arxiv_id"],
        }
    for p in pool:
        if p.get("src") != "openalex":
            continue
        d = p.get("doi") or ""
        for pid in (jn_id(d), "oa_" + d.replace("/", "_").replace(".", "-")[:60]):
            if pid in valid and pid not in byid:
                byid[pid] = {
                    "id": pid, "title": p["title"], "authors": p.get("authors") or [],
                    "year": p.get("year"), "venue": p.get("venue") or "",
                    "source_id": d, "url": p.get("url") or ("https://doi.org/" + d),
                    "theme": p["theme"], "abstract": (p.get("abstract") or "")[:1400],
                    "open_access": bool(p.get("is_oa") or p.get("oa")), "arxiv_id": None,
                }
    for c in jc:
        pid = jn_id(c["doi"])
        if pid in valid:
            byid[pid] = {
                "id": pid, "title": c["title"], "authors": c.get("authors") or [],
                "year": c.get("year"), "venue": c.get("venue") or "",
                "source_id": c["doi"], "url": c.get("url") or ("https://doi.org/" + c["doi"]),
                "theme": c["theme"], "abstract": (c.get("abstract") or "")[:1400],
                "open_access": bool(c.get("is_oa")), "arxiv_id": None,
            }

    out, missing = [], []
    rawax = {}
    for fn in ("arxiv_raw.json", "arxiv_raw2.json"):
        for r in load(fn)["rows"]:
            rawax[r["arxiv_id"].split("v")[0]] = r
    for pid, v in sorted(valid.items()):
        if not v.get("ok"):
            continue
        rec = byid.get(pid)
        if not rec and pid.startswith("ax_"):
            key = pid[3:].replace("-", ".")
            key = re.sub(r"v\d+$", "", key)
            r = rawax.get(key)
            if r:
                pub = (r.get("published") or "")[:10]
                rec = {"id": pid, "title": " ".join(r["title"].split()),
                       "authors": r.get("authors") or [],
                       "year": int(pub[:4]) if pub else None,
                       "venue": "arXiv preprint" if not r.get("journal_ref") else r["journal_ref"],
                       "source_id": r["arxiv_id"], "url": r["url"], "theme": r["theme"],
                       "abstract": (r.get("abstract") or "")[:1400], "open_access": True,
                       "arxiv_id": r["arxiv_id"], "journal_ref": r.get("journal_ref") or ""}
        if not rec:
            missing.append(pid)
            continue
        rec = dict(rec)
        rec["pdf_path"] = "docs/papers2/pdf/" + v["file"]
        rec["pages"] = v["info"].get("pages")
        rec["first_page_text"] = (v["info"].get("first_page") or "")[:300]
        out.append(rec)
    json.dump(out, open(os.path.join(BASE, "notes_input.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("records:", len(out), "valid pdfs:", sum(1 for v in valid.values() if v["ok"]),
          "unmatched:", len(missing))
    print("unmatched ids:", missing)
    print("by theme:", {t: sum(1 for r in out if r["theme"] == t) for t in "ABCD"})


if __name__ == "__main__":
    main()
