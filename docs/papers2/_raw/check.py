# -*- coding: utf-8 -*-
"""Acceptance checks for docs/papers2 deliverables."""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = {"id", "title", "authors", "year", "venue", "source_id", "url", "pdf_path",
       "downloaded", "open_access", "themes", "abstract_zh", "contribution_zh",
       "verified", "notes"}
fail = []

idx = json.load(open(os.path.join(ROOT, "index.json"), encoding="utf-8"))
ex = json.load(open(os.path.join(ROOT, "_raw", "extras.json"), encoding="utf-8"))
APPENDIX = set(json.load(open(os.path.join(ROOT, "_raw", "appendix_ids.json"), encoding="utf-8"))) | \
           {e["id"] for e in ex.get("excluded_out_of_window", [])} | \
           {p["id"] for p in ex.get("pending_window", [])}
print("entries:", len(idx))
print("appendix-legit ids:", sorted(APPENDIX))

for e in idx:
    if set(e) != REQ:
        fail.append((e.get("id"), "fields", sorted(set(e) ^ REQ)))
    if not e["url"] and not e["source_id"]:
        fail.append((e["id"], "no url/source_id"))
    if not e["abstract_zh"]:
        fail.append((e["id"], "empty abstract_zh"))
    if not e["contribution_zh"]:
        fail.append((e["id"], "empty contribution_zh"))
    if e["downloaded"]:
        p = os.path.join(os.path.dirname(ROOT.rstrip("\\/")), e["pdf_path"].replace("/", os.sep)) \
            if not os.path.isabs(e["pdf_path"]) else e["pdf_path"]
        p = e["pdf_path"].replace("docs/papers2/", "docs/papers2/").replace("/", os.sep)
        if not os.path.exists(p):
            fail.append((e["id"], "pdf_path missing", p))
        if os.path.getsize(p) < 20480:
            fail.append((e["id"], "pdf too small"))
    else:
        if e["pdf_path"] is not None:
            fail.append((e["id"], "not downloaded but pdf_path set"))

# ids unique
ids = [e["id"] for e in idx]
if len(ids) != len(set(ids)):
    fail.append(("GLOBAL", "duplicate ids"))

# notes for every downloaded pdf
notes_dir = os.path.join(ROOT, "notes")
have_notes = {f[:-3] for f in os.listdir(notes_dir) if f.endswith(".md")}
missing_notes = [e["id"] for e in idx if e["downloaded"] and e["id"] not in have_notes]
extra_notes = sorted(have_notes - {e["id"] for e in idx} - APPENDIX)

# markdown id coverage: every index id mentioned somewhere in the two md files
md = ""
for fn in ("文献清单.md", "中文文献.md"):
    md += open(os.path.join(ROOT, fn), encoding="utf-8").read()
md_ids = set(re.findall(r"`([A-Za-z0-9_\-\.]+)`", md))
missing_in_md = [e["id"] for e in idx if e["id"] not in md]

# PDFs on disk vs index
pdf_dir = os.path.join(ROOT, "pdf")
on_disk = {f[:-4] for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")}
print("pdfs on disk:", len(on_disk), "| downloaded in index:", sum(1 for e in idx if e["downloaded"]))
print("notes files:", len(have_notes), "| missing notes:", missing_notes, "| orphan notes:", extra_notes)
print("pdfs not in index (appendix allowed):",
      sorted(on_disk - {e["id"] for e in idx if e["downloaded"]} - APPENDIX))
ala = [len(e["abstract_zh"]) for e in idx]
print("abstract_zh chars: min %d max %d avg %d" % (min(ala), max(ala), sum(ala) // len(ala)))
print("out-of-range(40-200):", sum(1 for x in ala if x < 40 or x > 200))
print("FAILURES:", len(fail))
for f in fail[:25]:
    print("  ", f)
