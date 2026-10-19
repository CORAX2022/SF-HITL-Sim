# -*- coding: utf-8 -*-
"""OpenAlex harvester -> docs/papers2/_raw/openalex_raw.json"""
import json, os, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "openalex_raw.json")
MAIL = "research@example.org"

QUERIES = [
    ("A", "stock and flow model urban spatial"),
    ("A", "system dynamics urban land use simulation"),
    ("A", "causal loop diagram urban planning"),
    ("A", "urban flow aggregate modelling"),
    ("A", "spatial system dynamics city model"),
    ("A", "urban metabolism stock flow"),
    ("A", "system dynamics pedestrian flow"),
    ("B", "human-in-the-loop simulation urban planning"),
    ("B", "participatory simulation planning support system"),
    ("B", "companion modelling agent-based participatory"),
    ("B", "planning support system collaboration"),
    ("B", "interactive simulation experiment stakeholders"),
    ("B", "living lab urban experimentation"),
    ("B", "serious game participatory urban planning"),
    ("B", "digital twin participatory planning"),
    ("C", "large language model agents social simulation"),
    ("C", "generative agents human behavior simulation"),
    ("C", "silicon sampling LLM survey"),
    ("C", "LLM synthetic respondents opinion"),
    ("C", "human-AI hybrid experiment agent"),
    ("C", "LLM agent urban simulation"),
    ("C", "foundation model agent-based modelling"),
    ("D", "crowd simulation pedestrian dynamics"),
    ("D", "urban digital twin traffic simulation"),
    ("D", "cellular automata pedestrian evacuation"),
    ("D", "origin destination matrix estimation urban"),
    ("D", "traffic assignment model urban network"),
    ("D", "pedestrian flow cellular automaton"),
]


def fetch(q, per=40, page=1):
    url = ("https://api.openalex.org/works?search=" + urllib.parse.quote(q)
           + "&filter=from_publication_date:2021-01-01,type:article"
           + "&per-page=%d&page=%d&mailto=%s" % (per, page, MAIL))
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def inv_to_text(inv):
    if not inv:
        return ""
    pos = []
    for w, idxs in inv.items():
        for i in idxs:
            pos.append((i, w))
    pos.sort()
    return " ".join(w for _, w in pos)


def norm(w, theme):
    if not w:
        return None
    title = (w.get("title") or w.get("display_name") or "").strip()
    if not title:
        return None
    doi = (w.get("doi") or "").strip()
    auths = []
    for a in (w.get("authorships") or [])[:12]:
        n = ((a.get("author") or {}).get("display_name") or "").strip()
        if n:
            auths.append(n)
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {}) or {}
    venue = (src.get("display_name") or "").strip()
    yr = w.get("publication_year")
    oa = w.get("open_access") or {}
    best = oa.get("best_oa_location") or {}
    pdf = (best.get("pdf_url") or loc.get("pdf_url") or "").strip() or None
    landing = (best.get("landing_page_url") or loc.get("landing_page_url") or "").strip()
    return {
        "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1],
        "doi": doi, "title": title, "authors": auths, "year": yr,
        "venue": venue, "type": w.get("type"),
        "cited_by": w.get("cited_by_count"),
        "publication_date": w.get("publication_date"),
        "abstract": inv_to_text(w.get("abstract_inverted_index")),
        "is_oa": bool(oa.get("is_oa")), "oa_status": oa.get("oa_status"),
        "pdf_url": pdf, "landing": landing or doi or "",
        "theme": theme,
        "url": doi or (loc.get("landing_page_url") or ""),
    }


def main():
    rows, seen, log = [], set(), []
    for theme, q in QUERIES:
        for page in (1, 2):
            try:
                d = fetch(q, per=40, page=page)
                res = d.get("results") or []
            except Exception as exc:  # noqa: BLE001
                log.append({"query": q, "page": page, "error": repr(exc)[:200]})
                time.sleep(1.5)
                continue
            new = 0
            for w in res:
                n = norm(w, theme)
                if not n:
                    continue
                key = n["openalex_id"] or n["doi"] or n["title"].lower()
                if key in seen:
                    continue
                seen.add(key)
                rows.append(n)
                new += 1
            log.append({"query": q, "theme": theme, "page": page,
                        "returned": len(res), "new": new})
            time.sleep(0.7)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"log": log, "count": len(rows), "rows": rows}, f,
                  ensure_ascii=False, indent=1)
    print("openalex rows:", len(rows), "queries:", len(QUERIES),
          "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
