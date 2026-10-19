# -*- coding: utf-8 -*-
"""Targeted arXiv harvest pass 2 -> arxiv_raw2.json (high-precision queries)."""
import json, os, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
OUT2 = os.path.join(BASE, "arxiv_raw2.json")
NS = {"a": "http://www.w3.org/2005/Atom"}

QUERIES = [
    ("C", 'ti:"generative agents"'),
    ("C", 'ti:"LLM" AND ti:"simulation"'),
    ("C", 'ti:"agent" AND ti:"society" AND abs:"large language model"'),
    ("C", 'abs:"digital twin" AND abs:"large language model" AND abs:"urban"'),
    ("C", 'abs:"synthetic participants" OR abs:"synthetic users" OR abs:"simulated respondents"'),
    ("C", 'abs:"human-AI" AND abs:"collective" AND abs:"decision"'),
    ("C", 'abs:"urban planning" AND abs:"large language model"'),
    ("C", 'abs:"traffic" AND abs:"large language model" AND abs:"agent"'),
    ("B", 'ti:"human-in-the-loop" AND abs:"optimization" AND abs:"design"'),
    ("B", 'abs:"participatory" AND abs:"digital twin"'),
    ("B", 'abs:"human-in-the-loop" AND abs:"agent-based"'),
    ("B", 'abs:"urban planning" AND abs:"participatory" AND abs:"simulation"'),
    ("B", 'ti:"serious game" AND abs:"planning"'),
    ("B", 'abs:"interactive" AND abs:"simulation platform" AND abs:"stakeholders"'),
    ("A", 'abs:"system dynamics" AND abs:"city"'),
    ("A", 'abs:"stock-flow" AND abs:"model"'),
    ("A", 'abs:"urban" AND abs:"flows" AND abs:"network" AND abs:"model"'),
    ("A", 'abs:"mobility" AND abs:"flow" AND abs:"spatial" AND abs:"model"'),
    ("A", 'abs:"land use" AND abs:"system dynamics"'),
    ("A", 'abs:"urban metabolism"'),
    ("D", 'ti:"crowd simulation"'),
    ("D", 'ti:"pedestrian"'),
    ("D", 'ti:"digital twin" AND abs:"city"'),
    ("D", 'abs:"crowd" AND abs:"flow" AND abs:"model"'),
    ("D", 'abs:"origin-destination" AND abs:"estimation"'),
    ("D", 'abs:"pedestrian" AND abs:"macroscopic"'),
    ("D", 'abs:"evacuation" AND abs:"simulation" AND abs:"building"'),
    ("D", 'abs:"cellular automata" AND abs:"traffic"'),
]


def fetch(q, n=40):
    url = ("https://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q, safe="")
           + "&start=0&max_results=%d&sortBy=relevance" % n)
    req = urllib.request.Request(url, headers={"User-Agent": "lit-review/1.0 (research@example.org)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main():
    rows, seen, log = [], set(), []
    for theme, q in QUERIES:
        try:
            root = ET.fromstring(fetch(q))
        except Exception as exc:  # noqa: BLE001
            log.append({"q": q, "error": repr(exc)[:150]})
            time.sleep(2.5)
            continue
        new = 0
        for e in root.findall("a:entry", NS):
            sid = (e.findtext("a:id", "", NS) or "").rsplit("/", 1)[-1]
            if not sid:
                continue
            key = sid.split("v")[0]
            if key in seen:
                continue
            seen.add(key)
            pub = (e.findtext("a:published", "", NS) or "")[:10]
            rows.append({
                "arxiv_id": sid,
                "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
                "authors": [(" ".join((a.findtext("a:name", "", NS) or "").split()))
                            for a in e.findall("a:author", NS)],
                "published": pub,
                "abstract": " ".join((e.findtext("a:summary", "", NS) or "").split()),
                "primary_category": (e.find("a:primary_category", NS).get("term")
                                     if e.find("a:primary_category", NS) is not None else ""),
                "journal_ref": (e.findtext("a:journal_ref", "", NS) or "").strip(),
                "doi": (e.findtext("a:doi", "", NS) or "").strip(),
                "theme": theme, "url": "https://arxiv.org/abs/" + sid,
                "pdf_url": "https://arxiv.org/pdf/" + sid,
            })
            new += 1
        log.append({"q": q, "theme": theme, "new": new})
        time.sleep(2.4)
    json.dump({"log": log, "count": len(rows), "rows": rows},
              open(OUT2, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("arxiv2 rows:", len(rows), "queries:", len(QUERIES),
          "errors:", sum(1 for x in log if "error" in x))


if __name__ == "__main__":
    main()
