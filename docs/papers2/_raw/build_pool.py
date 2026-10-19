# -*- coding: utf-8 -*-
"""Build the final candidate pool: arXiv (curated2) + top OpenAlex papers (non-arXiv),
attempting OA PDFs for OpenAlex items. -> pool.json, then download via download_pool.py"""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

KW = {
    "A": [("system dynamics", 6), ("stock and flow", 6), ("stock-flow", 6), ("causal loop", 6),
          ("urban metabolism", 5), ("urban flow", 5), ("aggregate model", 4), ("spatial model", 3),
          ("land use", 4), ("material flow", 4), ("mobility", 3), ("flow", 2), ("feedback", 3),
          ("mesoscopic", 3), ("macroscopic", 3), ("network", 2), ("supply", 2)],
    "B": [("human-in-the-loop", 7), ("human in the loop", 7), ("participatory", 6),
          ("companion model", 6), ("planning support", 7), ("interactive simulation", 5),
          ("living lab", 5), ("serious game", 5), ("stakeholder", 4), ("co-design", 4),
          ("co-creation", 4), ("citizen science", 4), ("decision support", 4), ("workshop", 3),
          ("human feedback", 4), ("collaborative planning", 5), ("public participation", 6)],
    "C": [("large language model", 7), ("llm", 5), ("generative agent", 8), ("silicon sampl", 8),
          ("synthetic", 4), ("language model agent", 6), ("foundation model", 4), ("gpt", 3),
          ("chatgpt", 3), ("human-ai", 5), ("hybrid", 3), ("social simulation", 6),
          ("agent society", 6), ("digital human", 4), ("persona", 3), ("multi-agent", 3),
          ("agent-based", 3), ("simulation", 1)],
    "D": [("crowd simulation", 8), ("pedestrian", 7), ("cellular automat", 6), ("digital twin", 7),
          ("origin-destination", 7), ("od matrix", 6), ("traffic assignment", 6), ("evacuation", 5),
          ("social force", 6), ("footfall", 5), ("trajectory", 3), ("mobility", 4),
          ("traffic flow", 5), ("crowd", 5), ("walking", 3), ("taz", 3), ("flow estimation", 4)],
}
BAD = ["protein", "cancer", "sars-cov", "covid-19", "molecul", "quantum comput", "galax", "genome",
       "semiconductor", "clinical", "image classification", "speech recognition", "code generation",
       "wireless", "6g", "blockchain", "malware", "compiler", "radiance field", "federated learning",
       "jailbreak", "prompt injection", "recommender", "robot manipulat", "drug delivery",
       "teaching", "education", "curriculum", "student", "classroom", "nursing", "medical",
       "tourism management", "e-commerce", "supply chain finance"]
GOODT = ["urban", "city", "cities", "pedestrian", "crowd", "planning", "spatial", "simulation",
         "agent", "stock", "flow", "mobility", "traffic", "land use", "street", "public space",
         "participat", "human", "llm", "language model", "evacuation", "digital twin", "policy",
         "neighbourhood", "neighborhood", "resilience"]


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
            s -= 16
        elif k in b:
            s -= 2
    return s


def main():
    arx = json.load(open(os.path.join(BASE, "curated2.json"), encoding="utf-8"))["selected"]
    oa = json.load(open(os.path.join(BASE, "openalex_raw.json"), encoding="utf-8"))["rows"]

    pool, seen_t, seen_d = [], set(), set()
    for p in arx:
        kt = re.sub(r"[^a-z0-9]+", "", p["title"].lower())[:80]
        seen_t.add(kt)
        if p.get("doi"):
            seen_d.add(p["doi"].lower().replace("https://doi.org/", ""))
        pool.append(p)

    cand = []
    for r in oa:
        t = clean(r.get("title", ""))
        if not t or len(t) < 14:
            continue
        kt = re.sub(r"[^a-z0-9]+", "", t.lower())[:80]
        if kt in seen_t:
            continue
        dk = (r.get("doi") or "").lower().replace("https://doi.org/", "")
        if dk and dk in seen_d:
            continue
        s = score(t, r.get("abstract", ""), r["theme"])
        if s < 12:
            continue
        seen_t.add(kt)
        if dk:
            seen_d.add(dk)
        cand.append({
            "src": "openalex", "theme": r["theme"], "score": s, "title": t,
            "authors": r.get("authors") or [], "year": r.get("year"), "date": r.get("date") or "",
            "venue": r.get("venue") or "", "abstract": r.get("abstract") or "",
            "doi": r.get("doi") or "", "arxiv_id": None,
            "url": r.get("url") or "", "pdf_url": r.get("pdf_url"),
            "oa": bool(r.get("is_oa")), "is_oa": bool(r.get("is_oa")),
            "cited_by": r.get("cited_by"), "openalex_id": r.get("openalex_id"),
            "journal_ref": "", "cats": "",
        })
    cand.sort(key=lambda x: -x["score"])
    pool += cand[:110]
    json.dump({"pool": pool, "n_arxiv": len(arx), "n_openalex": min(110, len(cand))},
              open(os.path.join(BASE, "pool.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("pool:", len(pool), "arxiv:", len(arx), "openalex:", min(110, len(cand)))
    print("openalex with pdf_url:", sum(1 for p in pool if p["src"] == "openalex" and p.get("pdf_url")))
    for th in "ABCD":
        n = sum(1 for p in pool if p["theme"] == th and p["src"] == "openalex")
        print(" oa", th, n)


if __name__ == "__main__":
    main()
