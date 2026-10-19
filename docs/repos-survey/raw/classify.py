# -*- coding: utf-8 -*-
"""Lane R: classify candidate repos into 7 categories, filter to relevant ones."""
import json, re, os, sys, collections

RAW = os.path.dirname(os.path.abspath(__file__))
cands = json.load(open(os.path.join(RAW, "_candidates.json"), encoding="utf-8"))

# ---- curated overrides (name -> category). Verified against API metadata. ----
CUR = {
    "mesa/mesa": 1, "projectmesa/mesa": 1, "JuliaDynamics/Agents.jl": 1,
    "NetLogo/NetLogo": 1, "RepastHPC/repast_hpc": 1, "repast/repast4py": 1,
    "FIRST-robotics/..." : 1, "jofmi/agentpy": 1, "backspaces/agentscript": 1,
    "krABMaga/krABMaga": 1, "evoplex/evoplex": 1, "FLAMEGPU/FLAMEGPU2": 1,
    "noncomputable/AgentMaps": 1, "abmgis/abmgis": 1, "mesa/mesa-geo": 1,
    "BDI-pathogens/OpenABM-Covid19": 1, "tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation": 1,
    "AgentTorch/AgentTorch": 1, "google-deepmind/concordia": 4,
    "camel-ai/oasis": 4, "camel-ai/sotopia": 4, "joonspk-research/generative_agents": 4,
    "a16z-infra/ai-town": 4, "tsinghua-fib-lab/AgentSociety": 4,
    "microsoft/autogen": 4, "joaomdmoura/crewAI": 4, "geekan/MetaGPT": 4,
    "OpenBMB/ChatDev": 4, "princeton-nlp/SWE-agent": None,
    "eclipse-sumo/sumo": 3, "DLR-TS/sumo": 3, "matsim-org/matsim": 3,
    "matsim-org/matsim-libs": 3, "cityflow-project/CityFlow": 3,
    "UCMerced-...": None, "hydrosquall/...": None,
    "a-b-street/abstreet": 3, "a-b-street/ab-street": 3,
    "carla-simulator/carla": 3, "flow-project/flow": 3,
    "oTree-org/oTree": 5, "jspsych/jsPsych": 5, "psychopy/psychopy": 5,
    "empirica/empirica": 5, "nodeGame/nodegame": 5, "labjs/lab.js": 5,
    "sdwfrost/...": None,
    "SDXorg/pysd": 6, "SDXorg/PySD": 6, "thoughtworks/bptk-py": 6,
    "gboeing/osmnx": 7, "keplergl/kepler.gl": 7, "visgl/deck.gl": 7,
    "movingpandas/movingpandas": 7, "UDST/pandana": 7, "geopandas/geopandas": 7,
    "python-visualization/folium": 7, "flowmapblue/flowmapblue": 7,
    "FlowmapBlue/flowmap.blue": 7, "visgl/flowmap.gl": 7,
}

def text_of(r):
    parts = [r.get("full_name") or "", r.get("description") or ""]
    parts += list(r.get("topics") or [])
    return " ".join(parts).lower()

PATS = {
 1: [r"agent[- ]based", r"\babm\b", r"\bnetlogo\b", r"\brepast\b", r"\bmason\b",
     r"gama platform", r"flamegpu", r"agentpy", r"agentscript", r"agenttorch",
     r"krabmaga", r"evoplex", r"agents\.jl", r"individual[- ]based model",
     r"multi[- ]agent simulation", r"multiagent simulation", r"agent simulation framework",
     r"simulation framework", r"cellular automat", r"agent[- ]based model",
     r"microsimulation", r"agent[- ]based modeling"],
 2: [r"\bcrowd\b", r"pedestrian", r"evacuation", r"social force", r"jupedsim",
     r"\bvadere\b", r"crowd dynamic", r"walking behavi", r"pedsim",
     r"crowd simulation", r"footfall", r"pedflow"],
 3: [r"\btraffic\b", r"\bsumo\b", r"\bmatsim\b", r"cityflow", r"ab[- ]?street",
     r"urban simulation", r"digital twin", r"urban mobility", r"transport(ation)? simulation",
     r"transport(ation)? model", r"\btransit\b", r"road network", r"traffic signal",
     r"vehicular", r"car[- ]following", r"autonomous driving", r"smart city",
     r"urban planning", r"street network", r"city simulation", r"driving simulator",
     r"travel demand", r"traffic flow", r"urban data", r"urban analytics",
     r"public transport", r"\bmobility\b", r"intelligent transport", r"urban computing"],
 4: [r"\bllm\b", r"large language model", r"generative agent", r"social simulation",
     r"agent society", r"concordia", r"\boasis\b", r"sotopia", r"ai[- ]town",
     r"simulacra", r"multi[- ]agent llm", r"llm[- ]agent", r"llm agent",
     r"language model agent", r"opinion dynamic", r"\bgpt\b", r"agentic simulation",
     r"silicon sample", r"digital human", r"social agent"],
 5: [r"\botree\b", r"jspsych", r"psychopy", r"empirica", r"survey platform",
     r"questionnaire", r"behaviou?ral experiment", r"online experiment",
     r"human[- ]in[- ]the[- ]loop", r"\bhitl\b", r"experiment platform",
     r"cognitive experiment", r"nodegame", r"lab\.js", r"\bformr\b",
     r"experimental economics", r"participant recruitment", r"surveyjs",
     r"limesurvey", r"lime survey", r"\bmturk\b", r"mechanical turk",
     r"participatory", r"economic experiment", r"psychology experiment",
     r"reaction time experiment", r"web experiment", r"crowdsourc.*experiment"],
 6: [r"system dynamic", r"causal loop", r"stock[- ]and[- ]flow", r"stocks and flows",
     r"\bvensim\b", r"\bpysd\b", r"\bstella\b", r"feedback loop", r"causal diagram",
     r"insightmaker", r"bptk", r"causal map", r"system[s]? thinking",
     r"loop diagram", r"system dynamics model"],
 7: [r"\bosm\b", r"osmnx", r"geospatial", r"\bgis\b", r"od matrix", r"origin[- ]destination",
     r"flow map", r"flowmap", r"kepler", r"deck\.gl", r"choropleth",
     r"movingpandas", r"pandana", r"geopandas", r"folium", r"spatial analysis",
     r"cartograph", r"\bh3\b", r"geovisual", r"network visualization", r"map visuali",
     r"spatial data", r"land use", r"leaflet", r"mapbox", r"flow visualization",
     r"geospatial visualization", r"urban form", r"space syntax", r"spatial network",
     r"spatial interaction", r"gravity model", r"od[- ]flow", r"routing"],
}
COMP = {k: [re.compile(p) for p in v] for k, v in PATS.items()}

rows = []
for r in cands:
    if r.get("archived"):
        continue
    if r["full_name"] in CUR and CUR[r["full_name"]] is None:
        continue
    t = text_of(r)
    scores = {}
    for c, ps in COMP.items():
        s = sum(1 for p in ps if p.search(t))
        if s:
            scores[c] = s
    if r["full_name"] in CUR and CUR[r["full_name"]]:
        scores = {CUR[r["full_name"]]: max(scores.get(CUR[r["full_name"]], 0), 3)}
    if not scores:
        continue
    # priority tie-break: more specific/domain categories first
    prio = {2: 0, 5: 1, 6: 2, 4: 3, 1: 4, 3: 5, 7: 6}
    best = sorted(scores.items(), key=lambda kv: (-kv[1], prio[kv[0]]))[0][0]
    r["_cat"] = best
    r["_scores"] = scores
    r["_n"] = len(scores)
    rows.append(r)

rows.sort(key=lambda r: (-r["_cat"], -r["stars"]))
json.dump(rows, open(os.path.join(RAW, "_classified.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

cnt = collections.Counter(r["_cat"] for r in rows)
print("classified total:", len(rows))
for c in sorted(cnt):
    print("  cat%d: %d" % (c, cnt[c]))
# compact listing per category (top 70 by stars) to a review file
with open(os.path.join(RAW, "_review.txt"), "w", encoding="utf-8") as f:
    for c in sorted(cnt):
        f.write("=== cat%d (%d) ===\n" % (c, cnt[c]))
        for r in [x for x in rows if x["_cat"] == c][:90]:
            f.write("%-58s %6d %-12s %s\n" % (r["full_name"][:58], r["stars"],
                    (r["language"] or "")[:12], (r["description"] or "")[:78]))
print("wrote _classified.json / _review.txt")
