# -*- coding: utf-8 -*-
"""Assemble non-arXiv journal candidates (real OA journals) + multi-route PDF download
(OpenAlex pdf_url -> Unpaywall -> landing page scrape). -> journal_cand.json / download_oa.json"""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
PDFDIR = os.path.join(os.path.dirname(BASE), "pdf")
MAIL = "research@example.org"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

STRONG = {
    "A": ["system dynamics", "stock and flow", "stock-flow", "causal loop", "urban metabolism",
          "mobility flow", "mobility flows", "flow generation", "urban flow", "land use change",
          "land-use", "spatial interaction", "aggregate model", "flow model", "material flow"],
    "B": ["human-in-the-loop", "participatory", "companion model", "planning support",
          "interactive simulation", "living lab", "serious game", "co-design", "co-creation",
          "public participation", "collaborative planning", "stakeholder", "citizen science"],
    "C": ["large language model", "generative agent", "silicon sampl", "synthetic",
          "llm agent", "human-ai", "social simulation", "agent society", "gpt-4", "chatgpt"],
    "D": ["crowd simulation", "pedestrian", "cellular automat", "digital twin",
          "origin-destination", "od matrix", "traffic assignment", "evacuation", "social force",
          "footfall", "traffic flow", "macro", "mesoscopic"],
}
GOOD_VEN = ["sustainability", "cities", "urban", "transport", "geograph", "planning", "land",
            "environment", "ecology", "complexity", "systems", "simulation", "computers",
            "applied sciences", "smart", "mobility", "physics", "safety", "buildings",
            "journal of", "proceedings", "frontiers", "plos", "nature", "springer", "ieee access",
            "transactions", "review"]
BAD = ["plastics", "protein", "cancer", "covid", "river ecosystem", "flood", "nursing",
       "teaching", "education", "student", "medical", "tourism", "e-commerce", "soil",
       "wastewater", "battery", "crop", "forest fire", "landslide", "earthquake", "energy demand of"]


def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip().strip(".")


def valid(path):
    try:
        if os.path.getsize(path) <= 20480:
            return False
        import fitz
        doc = fitz.open(path)
        pages = doc.page_count
        chars = sum(len((doc[i].get_text() or "").strip()) for i in range(min(pages, 40)))
        doc.close()
        return pages > 0 and chars > 1000
    except Exception:  # noqa: BLE001
        return False


def curl(url, out, mt=90):
    try:
        r = subprocess.run(["curl.exe", "-sL", "--max-time", str(mt), "-A", UA, "-o", out, url],
                           capture_output=True, timeout=mt + 30)
        return r.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def unpaywall(doi):
    try:
        u = "https://api.unpaywall.org/v2/%s?email=%s" % (urllib.parse.quote(doi), MAIL)
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        locs = ([d.get("best_oa_location")] if d.get("best_oa_location") else []) + (d.get("oa_locations") or [])
        urls = []
        for l in locs:
            if not l:
                continue
            for k in ("url_for_pdf", "url"):
                v = l.get(k)
                if v and v not in urls:
                    urls.append(v)
        return urls
    except Exception:  # noqa: BLE001
        return []


def scrape_pdf_links(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            html = r.read(400000).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return []
    hits = re.findall(r'href="([^"]+\.pdf[^"]*)"', html, flags=re.I)
    out = []
    for h in hits[:6]:
        if h.startswith("//"):
            h = "https:" + h
        elif h.startswith("/"):
            p = urllib.parse.urlparse(url)
            h = "%s://%s%s" % (p.scheme, p.netloc, h)
        if h.startswith("http") and h not in out:
            out.append(h)
    return out


def main():
    oa = json.load(open(os.path.join(BASE, "openalex_raw.json"), encoding="utf-8"))["rows"]
    cand, per = [], {"A": 0, "B": 0, "C": 0, "D": 0}
    for r in oa:
        t = clean(r.get("title", ""))
        ab = (r.get("abstract") or "").lower()
        tl = t.lower()
        v = (r.get("venue") or "").lower()
        if len(t) < 18 or not r.get("doi"):
            continue
        if any(b in tl for b in BAD):
            continue
        hits = [k for k in STRONG[r["theme"]] if k in tl or k in ab]
        if not hits:
            continue
        if not any(g in v for g in GOOD_VEN):
            continue
        cand.append({"src": "openalex", "theme": r["theme"], "title": t,
                     "authors": r.get("authors") or [], "year": r.get("year"),
                     "date": r.get("date") or "", "venue": r.get("venue") or "",
                     "abstract": r.get("abstract") or "", "doi": r.get("doi"),
                     "url": r.get("url") or "", "pdf_url": r.get("pdf_url"),
                     "is_oa": bool(r.get("is_oa")), "oa_status": r.get("oa_status"),
                     "cited_by": r.get("cited_by"), "hits": hits})
    # dedup and take a balanced, quality-first slice
    seen, out = set(), []
    for c in sorted(cand, key=lambda x: (-(len(x["hits"])), -(x["cited_by"] or 0))):
        k = re.sub(r"[^a-z0-9]+", "", c["title"].lower())[:70]
        if k in seen:
            continue
        seen.add(k)
        if per[c["theme"]] >= 14:
            continue
        per[c["theme"]] += 1
        out.append(c)
    json.dump(out, open(os.path.join(BASE, "journal_cand.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("journal candidates:", len(out), per)

    # download attempts
    res_path = os.path.join(BASE, "download_oa.json")
    res = {}
    if os.path.exists(res_path):
        try:
            res = json.load(open(res_path, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            res = {}
    for i, c in enumerate(out, 1):
        pid = "jn_" + re.sub(r"[^a-zA-Z0-9]+", "-", c["doi"])[:58]
        if res.get(pid, {}).get("ok"):
            continue
        path = os.path.join(PDFDIR, pid + ".pdf")
        routes = []
        if c.get("pdf_url"):
            routes.append(c["pdf_url"])
        if c.get("doi"):
            routes += unpaywall(c["doi"])
            routes.append("https://doi.org/" + c["doi"])
        seenr = set()
        ok = False
        used = ""
        for u in routes:
            if not u or u in seenr:
                continue
            seenr.add(u)
            if u.lower().endswith(".pdf") or "/pdf" in u.lower():
                curl(u, path, 90)
                if valid(path):
                    ok, used = True, u
                    break
            for link in scrape_pdf_links(u)[:3]:
                curl(link, path, 90)
                if valid(path):
                    ok, used = True, link
                    break
            if ok:
                break
        if not ok and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
        res[pid] = {"ok": ok, "route": used, "doi": c["doi"], "title": c["title"],
                    "theme": c["theme"], "venue": c["venue"]}
        json.dump(res, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[%d/%d] %s %s" % (i, len(out), pid, "OK" if ok else "FAIL"), flush=True)
    print("OA journal PDFs ok:", sum(1 for v in res.values() if v["ok"]), "/", len(res))


if __name__ == "__main__":
    main()
