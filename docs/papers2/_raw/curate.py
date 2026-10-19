# -*- coding: utf-8 -*-
"""Score + select candidates from the two raw harvests -> curated.json (top-N per theme)."""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
CUT = "2021-10-01"

KW = {
    "A": ["stock and flow", "stock-flow", "system dynamics", "causal loop", "urban metabolism",
          "aggregate model", "urban flow", "flow model", "spatial dynamics", "land use model",
          "feedback loop", "flow network", "material flow"],
    "B": ["human-in-the-loop", "human in the loop", "participatory", "companion model",
          "planning support", "interactive simulation", "living lab", "serious game",
          "stakeholder", "co-design", "co-creation", "citizen science", "human input",
          "interactive experiment", "workshop", "decision support"],
    "C": ["large language model", "llm", "generative agent", "silicon sampl", "synthetic",
          "language model agent", "foundation model", "gpt", "chatgpt", "digital human",
          "human-ai", "hybrid intelligence", "social simulation", "agent society",
          "synthetic data", "persona", "role-play"],
    "D": ["crowd simulation", "pedestrian", "cellular automat", "digital twin", "origin-destination",
          "origin destination", "od matrix", "traffic assignment", "evacuation", "social force",
          "walking behavior", "footfall", "flow estimation", "trajectory", "urban mobility",
          "mesoscopic", "macroscopic", "taz", "traffic flow"],
}
# titles that signal a different field entirely -> strong penalty
BAD = ["protein", "cancer", "covid", "sars-cov", "molecul", "quantum", "galax", "genome",
       "semiconductor", "battery", "drug", "clinical", "neural network compression",
       "recommendation system", "image classification", "speech recognition", "llm benchmark",
       "code generation", "mathematical", "physics", "chemistry", "robot arm", "wireless",
       "6g", "blockchain", "cybersecurity", "malware", "compiler", "database query"]
GOODT = ["urban", "city", "cities", "pedestrian", "crowd", "planning", "spatial", "simulation",
         "agent", "stock", "flow", "mobility", "traffic", "land use", "neighbourhood",
         "neighborhood", "street", "public space", "participat", "human", "llm", "language model"]


def score(text, title, theme):
    t = (title or "").lower()
    b = (text or "").lower()
    s = 0.0
    for k in KW[theme]:
        if k in t:
            s += 6
        elif k in b:
            s += 2
    for k in GOODT:
        if k in t:
            s += 1.0
    for k in BAD:
        if k in t:
            s -= 8
        elif k in b:
            s -= 1
    return s


def clean(t):
    return re.sub(r"\s+", " ", (t or "")).strip().strip(".")


def main():
    ax = json.load(open(os.path.join(BASE, "arxiv_raw.json"), encoding="utf-8"))["rows"]
    oa = json.load(open(os.path.join(BASE, "openalex_raw.json"), encoding="utf-8"))["rows"]

    seen_titles = set()
    pool = []
    for r in ax:
        pub = (r.get("published") or "")[:10]
        if pub and pub < CUT:
            continue
        s = score(r.get("abstract", ""), r.get("title", ""), r["theme"])
        if s < 6:
            continue
        pool.append({"kind": "arxiv", "theme": r["theme"], "score": s, "title": clean(r["title"]),
                     "authors": r["authors"], "year": int(pub[:4]) if pub else None,
                     "date": pub, "venue": "arXiv preprint", "abstract": r["abstract"],
                     "doi": r.get("doi") or "", "arxiv_id": r["arxiv_id"],
                     "url": r["url"], "pdf_url": r["pdf_url"], "oa": True,
                     "src": "arxiv", "cited_by": None})
    for r in oa:
        d = r.get("publication_date") or ""
        if d and d < CUT:
            continue
        s = score(r.get("abstract", ""), r.get("title", ""), r["theme"])
        if s < 6:
            continue
        if not (r.get("doi") or r.get("url")):
            continue
        pool.append({"kind": "openalex", "theme": r["theme"], "score": s + (2 if r.get("is_oa") else 0),
                     "title": clean(r["title"]), "authors": r["authors"], "year": r.get("year"),
                     "date": d, "venue": r.get("venue") or "journal article",
                     "abstract": r.get("abstract", ""), "doi": r.get("doi") or "",
                     "arxiv_id": None, "url": r.get("url") or r.get("landing"),
                     "pdf_url": r.get("pdf_url"), "oa": bool(r.get("is_oa")),
                     "src": "openalex", "cited_by": r.get("cited_by")})

    # dedup by normalized title and by doi
    out, seen_doi = [], set()
    for p in sorted(pool, key=lambda x: -x["score"]):
        key = re.sub(r"[^a-z0-9]+", "", p["title"].lower())[:90]
        if not key or key in seen_titles:
            continue
        dkey = (p["doi"] or "").lower().replace("https://doi.org/", "")
        if dkey and dkey in seen_doi:
            continue
        seen_titles.add(key)
        if dkey:
            seen_doi.add(dkey)
        out.append(p)

    by_theme = {}
    for p in out:
        by_theme.setdefault(p["theme"], []).append(p)

    sel = []
    for th in "ABCD":
        rows = by_theme.get(th, [])
        # prefer entries with a real PDF url, then score
        rows.sort(key=lambda x: (0 if x["pdf_url"] else 1, -x["score"]))
        arrive = [r for r in rows if r["src"] == "arxiv"][:18]
        journal = [r for r in rows if r["src"] == "openalex"][:14]
        sel.extend(arrive)
        sel.extend(journal)

    with open(os.path.join(BASE, "curated.json"), "w", encoding="utf-8") as f:
        json.dump({"pool": len(out), "selected": sel}, f, ensure_ascii=False, indent=1)
    counts = {}
    for p in sel:
        counts[(p["theme"], p["src"])] = counts.get((p["theme"], p["src"]), 0) + 1
    print("pool:", len(out), "selected:", len(sel))
    print("per theme/src:", sorted(counts.items()))
    print("with pdf_url:", sum(1 for p in sel if p["pdf_url"]))


if __name__ == "__main__":
    main()
