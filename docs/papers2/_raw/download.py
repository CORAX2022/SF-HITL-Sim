# -*- coding: utf-8 -*-
"""Download candidate PDFs into docs/papers2/pdf/ with immediate validation.
Validation: size > 20 KB, fitz pages > 0, total text chars > 1000.
Writes docs/papers2/_raw/download_report.json  (no stdout dumps)."""
import json, os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
PDFDIR = os.path.join(os.path.dirname(BASE), "pdf")
os.makedirs(PDFDIR, exist_ok=True)

CUR = json.load(open(os.path.join(BASE, "curated.json"), encoding="utf-8"))["selected"]
REPORT = os.path.join(BASE, "download_report.json")


def slug(p):
    t = p["title"].lower()
    keep = []
    for ch in t:
        if ch.isalnum():
            keep.append(ch)
        elif ch in " -_" and (not keep or keep[-1] != "_"):
            keep.append("_")
    s = "".join(keep).strip("_")
    return (s[:56] or "paper").strip("_")


def ident(p):
    if p["arxiv_id"]:
        return "ax_" + p["arxiv_id"].replace("/", "_").replace(".", "-")
    d = (p["doi"] or "").replace("https://doi.org/", "").replace("/", "_").replace(".", "-")
    return "oa_" + (d or slug(p))[:60]


def validate(path):
    """return (ok, info)"""
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
        for i in range(min(pages, 40)):
            chars += len((doc[i].get_text() or "").strip())
        doc.close()
    except Exception as exc:  # noqa: BLE001
        return False, {"reason": "fitz_error:" + repr(exc)[:80], "size": size}
    if pages <= 0:
        return False, {"reason": "zero_pages", "size": size}
    if chars <= 1000:
        return False, {"reason": "chars_le_1000", "size": size, "pages": pages, "chars": chars}
    return True, {"size": size, "pages": pages, "chars": chars}


def dl(url, path, maxtime=120):
    cmd = ["curl.exe", "-sL", "--max-time", str(maxtime), "-A",
           "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
           "-o", path, url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=maxtime + 40)
        return r.returncode
    except Exception:  # noqa: BLE001
        return -1


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    shard = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    nshard = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    results = {}
    if os.path.exists(REPORT):
        try:
            results = json.load(open(REPORT, encoding="utf-8")).get("items", {})
        except Exception:  # noqa: BLE001
            results = {}
    jobs = [p for p in CUR if p["pdf_url"]]
    jobs.sort(key=lambda p: (0 if p["src"] == "arxiv" else 1, -p["score"]))
    if only == "arxiv":
        jobs = [p for p in jobs if p["src"] == "arxiv"]
    elif only == "oa":
        jobs = [p for p in jobs if p["src"] != "arxiv"]
    jobs = [p for i, p in enumerate(jobs) if i % nshard == shard]

    for i, p in enumerate(jobs, 1):
        pid = ident(p)
        path = os.path.join(PDFDIR, pid + ".pdf")
        if results.get(pid, {}).get("ok"):
            continue
        ok, info = (False, {})
        if os.path.exists(path):
            ok, info = validate(path)
        if not ok:
            for attempt, mt in ((1, 120), (2, 240)):
                dl(p["pdf_url"], path, mt)
                ok, info = validate(path)
                if ok:
                    break
        if not ok and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        results[pid] = {"ok": ok, "info": info, "src": p["src"], "theme": p["theme"],
                        "title": p["title"], "pdf_url": p["pdf_url"],
                        "arxiv_id": p["arxiv_id"], "doi": p["doi"]}
        json.dump({"items": results}, open(REPORT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("[%d/%d] %s %s %s" % (i, len(jobs), pid, "OK" if ok else "FAIL",
                                    info.get("reason", "")), flush=True)

    good = sum(1 for v in results.values() if v["ok"])
    print("TOTAL ok:", good, "/", len(results))


if __name__ == "__main__":
    main()
