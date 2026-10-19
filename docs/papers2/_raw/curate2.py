# -*- coding: utf-8 -*-
"""Final curation: merge arXiv pass1+pass2, pick per-theme sets for index + PDF pool.
-> curated2.json  (fields ready for download.py and build_index.py)"""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
CUT = "2021-10-01"

KW = {
    "A": [("stock and flow", 5), ("stock-flow", 5), ("system dynamics", 6), ("causal loop", 6),
          ("urban metabolism", 6), ("aggregate model", 4), ("urban flow", 5), ("flows", 2),
          ("spatial model", 3), ("land use model", 3), ("feedback", 2), ("material flow", 4),
          ("flow network", 3), ("mobility flow", 3), ("mesoscopic", 3), ("macroscopic", 3)],
    "B": [("human-in-the-loop", 7), ("human in the loop", 7), ("participatory", 6),
          ("companion model", 6), ("planning support", 6), ("interactive simulation", 5),
          ("living lab", 5), ("serious game", 5), ("stakeholder", 3), ("co-design", 4),
          ("co-creation", 4), ("citizen science", 4), ("workshop", 2), ("decision support", 3),
          ("human feedback", 3), ("expert-in-the-loop", 5), ("interactive experiment", 4)],
    "C": [("large language model", 7), ("llm", 5), ("generative agent", 8), ("silicon sampl", 8),
          ("synthetic participant", 6), ("synthetic user", 5), ("language model agent", 6),
          ("foundation model", 4), ("gpt", 3), ("chatgpt", 3), ("human-ai", 5),
          ("hybrid intelligence", 5), ("social simulation", 6), ("agent society", 6),
          ("persona", 3), ("role-play", 3), ("multi-agent", 3), ("digital twin", 2)],
    "D": [("crowd simulation", 8), ("pedestrian", 6), ("cellular automat", 6), ("digital twin", 6),
          ("origin-destination", 7), ("origin destination", 6), ("od matrix", 6),
          ("traffic assignment", 6), ("evacuation", 5), ("social force", 6), ("footfall", 5),
          ("flow estimation", 4), ("trajectory", 2), ("urban mobility", 4), ("taz", 3),
          ("traffic flow", 5), ("crowd", 4), ("walking", 3), ("simulation", 1)],
}
BAD = ["protein", "cancer", "sars-cov", "covid", "molecul", "quantum comput", "galax", "genome",
       "semiconductor", "battery", "clinical trial", "image classification", "speech recognition",
       "benchmark", "code generation", "wireless", "6g", "blockchain", "malware", "compiler",
       "neural radiance", "diffusion model", "recommender", "federated learning", "slam",
       "autonomous driving perception", "robot manipulat", "drug", "gene", "particle physics",
       "reward model", "jailbreak", "prompt injection"]
GOODT = ["urban", "city", "cities", "pedestrian", "crowd", "planning", "spatial", "simulation",
         "agent", "stock", "flow", "mobility", "traffic", "land use", "street", "public space",
         "participat", "human", "llm", "language model", "neighbourhood", "neighborhood",
         "evacuation", "digital twin", "policy"]


def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip().strip(".")


def score(title, abstract, theme):
    t = title.lower()
    b = abstract.lower()
    s = 0.0
    for k, w in KW[theme]:
        if k in t:
            s += 2.0 * w
        elif k in b:
            s += w
    for k in GOODT:
        if k in t:
            s += 1.5
    for k in BAD:
        if k in t:
            s -= 14
        elif k in b:
            s -= 2
    return s


def main():
    rows = []
    for fn in ("arxiv_raw.json", "arxiv_raw2.json"):
        rows += json.load(open(os.path.join(BASE, fn), encoding="utf-8"))["rows"]
    pool, seen_t, seen_b = [], set(), set()
    for r in rows:
        pub = (r.get("published") or "")[:10]
        if not pub or pub < CUT:
            continue
        ttl = clean(r["title"])
        if not ttl or len(ttl) < 12:
            continue
        th = r["theme"]
        s = score(ttl, r.get("abstract", ""), th)
        if s < 8:
            continue
        kt = re.sub(r"[^a-z0-9]+", "", ttl.lower())[:80]
        if kt in seen_t:
            continue
        seen_t.add(kt)
        authors = r.get("authors") or []
        ka = (authors[0].lower() if authors else "") + "|" + str(r.get("published", ""))[:4]
        if ka in seen_b and len(authors) < 3:
            continue
        seen_b.add(ka)
        pool.append({
            "src": "arxiv", "theme": th, "score": s, "title": ttl, "authors": authors,
            "year": int(pub[:4]), "date": pub, "venue": "arXiv preprint",
            "abstract": r.get("abstract", ""), "doi": r.get("doi") or "",
            "arxiv_id": r["arxiv_id"], "url": r["url"], "pdf_url": r["pdf_url"],
            "oa": True, "journal_ref": r.get("journal_ref") or "", "cats": r.get("primary_category") or "",
        })

    by = {}
    for p in pool:
        by.setdefault(p["theme"], []).append(p)
    sel = []
    for th in "ABCD":
        lst = sorted(by.get(th, []), key=lambda x: -x["score"])
        sel += lst[:16]
    json.dump({"selected": sel}, open(os.path.join(BASE, "curated2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("pool:", len(pool), "selected:", len(sel))
    for th in "ABCD":
        n = sum(1 for p in sel if p["theme"] == th)
        print(th, n, "|", " ; ".join(p["title"][:38] + " (" + str(p["year"]) + ")"
                                     for p in sel if p["theme"] == th)[:300])


if __name__ == "__main__":
    main()
