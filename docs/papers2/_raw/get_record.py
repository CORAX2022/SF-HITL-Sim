# -*- coding: utf-8 -*-
"""Print one record's grounding fields for a note writer.
Usage: py -3.13 get_record.py <id> [--full]
"""
import json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
recs = json.load(open(os.path.join(BASE, "notes_input.json"), encoding="utf-8"))
pid = sys.argv[1]
full = "--full" in sys.argv
r = next((x for x in recs if x["id"] == pid), None)
if not r:
    print("NOT_FOUND", pid)
    sys.exit(1)
print("ID:", r["id"])
print("TITLE:", r["title"])
print("AUTHORS:", ", ".join(r.get("authors") or [])[:300])
print("YEAR:", r.get("year"), "| VENUE:", r.get("venue"), "| THEME:", r.get("theme"))
print("SOURCE_ID:", r.get("source_id"), "| URL:", r.get("url"))
print("PDF_PATH:", r.get("pdf_path"), "| PAGES:", r.get("pages"))
print("ABSTRACT:", (r.get("abstract") or "")[: (6000 if full else 1500)])
