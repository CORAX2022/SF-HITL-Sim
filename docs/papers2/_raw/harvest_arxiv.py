# -*- coding: utf-8 -*-
"""arXiv harvester -> docs/papers2/_raw/arxiv_raw.json (no stdout dumps)."""
import json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "arxiv_raw.json")
NS = {"a": "http://www.w3.org/2005/Atom"}

QUERIES = [
    ("C", 'all:"generative agents" AND all:"large language model"'),
    ("C", 'abs:"LLM agents" AND abs:"social simulation"'),
    ("C", 'abs:"silicon sampling" OR abs:"silicon subjects"'),
    ("C", 'abs:"human-AI" AND abs:"experiment" AND abs:"agent"'),
    ("C", 'abs:"large language model" AND abs:"agent-based model"'),
    ("C", 'abs:"LLM" AND abs:"city" AND abs:"simulation"'),
    ("C", 'abs:"generative agent" AND abs:"urban"'),
    ("B", 'abs:"human-in-the-loop" AND abs:"simulation" AND abs:"planning"'),
    ("B", 'abs:"participatory simulation"'),
    ("B", 'abs:"companion modelling" OR abs:"companion modeling"'),
    ("B", 'abs:"planning support system"'),
    ("B", 'abs:"interactive simulation" AND abs:"participants"'),
    ("B", 'abs:"human-in-the-loop" AND abs:"reinforcement learning" AND abs:"urban"'),
    ("B", 'abs:"living lab" AND abs:"urban"'),
    ("B", 'abs:"serious game" AND abs:"urban planning"'),
    ("A", 'abs:"system dynamics" AND abs:"urban"'),
    ("A", 'abs:"causal loop diagram" AND abs:"urban"'),
    ("A", 'abs:"stock and flow" AND abs:"model" AND abs:"city"'),
    ("A", 'abs:"urban metabolism" AND abs:"flow"'),
    ("A", 'abs:"spatial" AND abs:"system dynamics" AND abs:"land use"'),
    ("A", 'abs:"aggregate model" AND abs:"pedestrian"'),
    ("D", 'abs:"pedestrian dynamics"'),
    ("D", 'abs:"crowd simulation"'),
    ("D", 'abs:"urban digital twin"'),
    ("D", 'abs:"cellular automata" AND abs:"pedestrian"'),
    ("D", 'abs:"origin-destination" AND abs:"flow" AND abs:"estimation"'),
    ("D", 'abs:"traffic assignment" AND abs:"urban"'),
    ("D", 'abs:"social force model"'),
    ("D", 'abs:"agent-based" AND abs:"pedestrian" AND abs:"evacuation"'),
]


def fetch(q, n=60):
    url = ("https://export.arxiv.org/api/query?search_query="
           + urllib.parse.quote(q, safe="")
           + "&start=0&max_results=%d&sortBy=submittedDate&sortOrder=descending" % n)
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (research@example.org)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def parse(xml_bytes, theme):
    root = ET.fromstring(xml_bytes)
    rows = []
    for e in root.findall("a:entry", NS):
        eid = (e.findtext("a:id", "", NS) or "").strip()
        short = eid.rsplit("/", 1)[-1]
        title = " ".join((e.findtext("a:title", "", NS) or "").split())
        summ = " ".join((e.findtext("a:summary", "", NS) or "").split())
        pub = (e.findtext("a:published", "", NS) or "").strip()
        upd = (e.findtext("a:updated", "", NS) or "").strip()
        authors = [(" ".join((a.findtext("a:name", "", NS) or "").split()))
                   for a in e.findall("a:author", NS)]
        cats = [c.get("term") for c in e.findall("a:category", NS)]
        prim = e.find("a:primary_category", NS)
        jr = e.findtext("a:journal_ref", "", NS)
        doi = e.findtext("a:doi", "", NS)
        if not short or not title:
            continue
        rows.append({
            "arxiv_id": short, "title": title, "authors": authors,
            "published": pub, "updated": upd, "abstract": summ,
            "categories": cats, "primary_category": prim.get("term") if prim is not None else "",
            "journal_ref": (jr or "").strip(), "doi": (doi or "").strip(),
            "theme": theme,
            "url": "https://arxiv.org/abs/" + short,
            "pdf_url": "https://arxiv.org/pdf/" + short,
        })
    return rows


def main():
    allrows = []
    seen = set()
    log = []
    for i, (theme, q) in enumerate(QUERIES, 1):
        try:
            xmlb = fetch(q)
            rows = parse(xmlb, theme)
        except Exception as exc:  # noqa: BLE001
            log.append({"query": q, "error": repr(exc)[:200]})
            time.sleep(2.5)
            continue
        new = 0
        for r in rows:
            key = r["arxiv_id"].split("v")[0]
            if key in seen:
                continue
            seen.add(key)
            allrows.append(r)
            new += 1
        log.append({"query": q, "theme": theme, "returned": len(rows), "new": new})
        time.sleep(2.2)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"log": log, "count": len(allrows), "rows": allrows}, f,
                  ensure_ascii=False, indent=1)
    print("arxiv rows:", len(allrows), "queries:", len(QUERIES), "errors:",
          sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
