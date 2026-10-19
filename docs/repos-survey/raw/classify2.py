# -*- coding: utf-8 -*-
"""Lane R stage 2: strict relevance filter + category assignment."""
import json, re, os, collections

RAW = os.path.dirname(os.path.abspath(__file__))
cands = json.load(open(os.path.join(RAW, "_candidates.json"), encoding="utf-8"))

# curated category overrides for well-known projects (metadata still from API)
CUR = {
    "mesa/mesa": 1, "mesa/mesa-geo": 1, "mesa/mesa-examples": 1,
    "JuliaDynamics/Agents.jl": 1, "NetLogo/NetLogo": 1, "NetLogo/models": 1,
    "jofmi/agentpy": 1, "backspaces/agentscript": 1, "krABMaga/krABMaga": 1,
    "evoplex/evoplex": 1, "FLAMEGPU/FLAMEGPU2": 1, "AgentTorch/AgentTorch": 1,
    "IBM/AMLSim": 1, "gama-platform/gama": 1, "Repast/repast.simphony": 1,
    "eclab/mason": 1, "BioDynaMo/biodynamo": 1, "MathCancer/PhysiCell": 1,
    "noncomputable/AgentMaps": 1, "abmgis/abmgis": 1, "scottfr/simulation": 1,
    "sarl/sarl": 1, "starsimhub/covasim": 1, "EpiModel/EpiModel": 1,
    "BDI-pathogens/OpenABM-Covid19": 1, "ActivitySim/activitysim": 3,
    "LBNL-UCB-STI/beam": 3, "assume-framework/assume": 1,
    "bancaditalia/BeforeIT.jl": 1, "maxencefaldor/cax": 1,
    # crowd
    "MengeCrowdSim/Menge": 2, "svenkreiss/socialforce": 2,
    "paraboul/mapchecking": 2, "sweriko/Horde": 2,
    "sepsamavi/safe-interactive-crowdnav": 2,
    "nathanrooy/rpi-urban-mobility-tracker": 2,
    "aillieo/RVO2-Unity": 2, "jiachenli94/Awesome-Interaction-Aware-Trajectory-Prediction": 2,
    # traffic / urban
    "eclipse-sumo/sumo": 3, "matsim-org/matsim-libs": 3, "matsim-org/matsim": 3,
    "cityflow-project/CityFlow": 3, "a-b-street/abstreet": 3,
    "flow-project/flow": 3, "LibCity/Bigscity-LibCity": 3,
    "LucasAlegre/sumo-rl": 3, "bstabler/TransportationNetworks": 3,
    "ucla-mobility/OpenCDA": 3, "carla-simulator/carla": 3,
    "scikit-mobility/scikit-mobility": 3, "motis-project/motis": 3,
    "MobilityData/gbfs": 3, "openmobilityfoundation/mobility-data-specification": 3,
    "conveyal/transitive.js": 3, "TUDelft-CNS-ATM/bluesky": 3,
    "gboeing/ppde642": 3,
    # LLM / social sim
    "joonspk-research/generative_agents": 4, "google-deepmind/concordia": 4,
    "camel-ai/oasis": 4, "camel-ai/sotopia": 4, "a16z-infra/ai-town": 4,
    "tsinghua-fib-lab/AgentSociety": 4,
    "tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation": 4,
    "microsoft/autogen": 4, "geekan/MetaGPT": 4, "camel-ai/camel": 4,
    "OpenBMB/ChatDev": 4, "joaomdmoura/crewAI": 4,
    # experiments
    "oTree-org/oTree": 5, "jspsych/jsPsych": 5, "psychopy/psychopy": 5,
    "empirica/empirica": 5, "nodeGame/nodegame": 5, "Scifabric/pybossa": 5,
    "Toloka/crowd-kit": 5,
    # system dynamics
    "SDXorg/pysd": 6, "thoughtworks/bptk-py": 6,
    # spatial
    "gboeing/osmnx": 7, "gboeing/osmnx-examples": 7, "keplergl/kepler.gl": 7,
    "visgl/deck.gl": 7, "movingpandas/movingpandas": 7, "UDST/pandana": 7,
    "geopandas/geopandas": 7, "python-visualization/folium": 7,
    "FlowmapBlue/flowmap.blue": 7, "visgl/flowmap.gl": 7,
    "varoudis/depthmapX": 7,
}

INC = {
 1: [r"agent[- ]based", r"\babm\b", r"\bnetlogo\b", r"\brepast\b", r"mason multiagent",
     r"gama platform", r"flamegpu", r"agentpy", r"agentscript", r"agenttorch",
     r"krabmaga", r"evoplex", r"agents\.jl", r"individual[- ]based model",
     r"multi[- ]agent (based )?simulat", r"agent[- ]based model", r"agent[- ]based simulat",
     r"large population model", r"cellular automata accelerator",
     r"agent[- ]oriented programming", r"simulation toolkit"],
 2: [r"crowd (simulation|dynamic|behavio|navigation|counter|flow)",
     r"\bpedestrian", r"evacuation", r"social force", r"jupedsim", r"\bvadere\b",
     r"\bmenge\b", r"collision avoidance", r"walkability", r"crowd\b.*simulat",
     r"simulat.*crowd", r"crowd counting", r"footfall", r"trajectory predict"],
 3: [r"\bsumo\b", r"\bmatsim\b", r"cityflow", r"ab[- ]?street", r"traffic (simulation|flow|signal|micro|model|dynamics)",
     r"traffic signal control", r"transport(ation)? (simulation|model|planning|network|research)",
     r"(multi[- ]agent )?transport simulation", r"urban (simulation|mobility|data|computing|planning|analytics)",
     r"digital twin", r"smart city", r"street network", r"road network", r"driving simulator",
     r"autonomous driving", r"travel demand", r"activity[- ]based travel", r"car[- ]following",
     r"vehicular (network|traffic|simulat)", r"transit (data|network|viz|visuali)",
     r"bikeshare", r"mobility (data|analysis|simulation|specification)", r"public transport",
     r"traffic control", r"trajectory data mining", r"urban spatio"],
 4: [r"generative agent", r"social simulation", r"agent society", r"agent[- ]based social",
     r"llm[- ]?(based )?(social|society|simulat)", r"social (simulat|agent)",
     r"silicon sample", r"digital human", r"opinion dynamic", r"simulacra",
     r"ai[- ]town", r"\bsotopia\b", r"\bconcordia\b", r"\boasis\b",
     r"human(oid)? agents", r"multi[- ]agent.*(llm|language model|gpt)",
     r"(llm|language model|gpt).*(simulat|society|social|behavio|economic)",
     r"agent[- ]based model(ing)? and simulation with llm", r"generative (multi[- ])?agent"],
 5: [r"\botree\b", r"jspsych", r"psychopy", r"empirica", r"online experiment",
     r"behaviou?ral experiment", r"human[- ]in[- ]the[- ]loop", r"\bhitl\b",
     r"experiment (platform|framework)", r"experimental economics", r"economic experiment",
     r"survey (platform|framework|tool|js)", r"questionnaire", r"limesurvey",
     r"crowdsourc(ing|ed) (framework|platform|experiment|data)", r"\bmturk\b",
     r"mechanical turk", r"participant (recruitment|pool)", r"psychology experiment",
     r"cognitive (science|experiment)", r"web[- ]based experiment",
     r"nodegame", r"\bformr\b", r"reaction time", r"breadboard", r"jspsych",
     r"human subject", r"behavioral (research|study)", r"data collection.*(survey|participant)"],
 6: [r"system dynamic", r"causal loop", r"stock[- ]and[- ]flow", r"stocks and flows",
     r"\bvensim\b", r"\bpysd\b", r"\bstella\b", r"feedback loop", r"causal (diagram|map|graph)",
     r"insightmaker", r"bptk", r"loop diagram", r"system[s]? thinking"],
 7: [r"\bosmnx\b", r"\bosm\b.*(network|data|graph|map)", r"geospatial (visual|data|analysis|tool)",
     r"\bgis\b", r"od matrix", r"origin[- ]destination", r"flow ?map", r"flowmap",
     r"\bkepler\b", r"deck\.gl", r"choropleth", r"movingpandas", r"pandana", r"geopandas",
     r"folium", r"spatial (network|analysis|data|interaction|unit)", r"cartograph",
     r"space syntax", r"urban (form|morphology|network)", r"land[- ]use",
     r"network (flow )?visuali", r"transit (data )?visuali", r"flow visuali",
     r"\bh3\b", r"hexagonal (grid|binning)", r"grid (cell|unit)", r"map visuali",
     r"geovisuali", r"gravity model", r"trip distribution", r"od[- ]flow", r"\bflow data\b"],
}

EXC = [
 r"network traffic", r"packet", r"pcap", r"\btcp\b", r"netflow", r"sniff", r"proxy",
 r"ddos", r"cdn\b", r"nginx", r"kubernetes", r"websocket", r"packet captur",
 r"traffic (monitor|replay|receiver|accounting|analy|generat|light)", r"relay", r"tunnel",
 r"aviation", r"aircraft", r"air traffic", r"\bads-?b\b", r"tower defense", r"archetype-based entity",
 r"entity component system", r"argocd", r"whatsapp", r"philosoph", r"thinking map",
 r"rmm\b", r"tax (and|benefit|calculator)", r"microsimulation model of", r"tokenspice",
 r"solidity", r"evm ", r"blockchain", r"cryptocurrenc",
 r"navigation mesh", r"navmesh", r"recast", r"detour", r"game engine", r"unreal engine",
 r"godot", r"unity", r"oculus", r"vr ", r"video game", r"life sim", r"mars simulation",
 r"tokamak", r"bioinformatic", r"protein", r"genom", r"molecul", r"chemistry",
 r"cybersecurity", r"forensic", r"dataset (collection|curated)", r"awesome[- ]list",
 r"curated list", r"awesome\b",
]

def text_of(r):
    return " ".join([r.get("full_name") or "", r.get("description") or ""] + list(r.get("topics") or [])).lower()

GINC = {k: [re.compile(p) for p in v] for k, v in INC.items()}
GEXC = [re.compile(p) for p in EXC]

def manual_cat(r):
    fn = r["full_name"]
    if fn in CUR:
        return CUR[fn]
    return None

rows = []
for r in cands:
    if r.get("archived"):
        continue
    t = text_of(r)
    mc = manual_cat(r)
    if mc is None:
        if any(p.search(t) for p in GEXC):
            continue
        scores = {c: sum(1 for p in ps if p.search(t)) for c, ps in GINC.items()}
        scores = {c: s for c, s in scores.items() if s > 0}
        if not scores:
            continue
        prio = {2: 0, 6: 1, 5: 2, 4: 3, 3: 4, 1: 5, 7: 6}
        best = sorted(scores.items(), key=lambda kv: (-kv[1], prio[kv[0]]))[0][0]
        r["_cat"] = best
        r["_scores"] = scores
    else:
        r["_cat"] = mc
        r["_scores"] = {mc: 9}
    rows.append(r)

cnt = collections.Counter(r["_cat"] for r in rows)
print("filtered total:", len(rows))
for c in sorted(cnt):
    print("  cat%d: %d" % (c, cnt[c]))

rows.sort(key=lambda r: (-r["_cat"], -r["stars"]))
json.dump(rows, open(os.path.join(RAW, "_classified.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
with open(os.path.join(RAW, "_review.txt"), "w", encoding="utf-8") as f:
    for c in sorted(cnt):
        f.write("=== cat%d (%d) ===\n" % (c, cnt[c]))
        for r in [x for x in rows if x["_cat"] == c]:
            f.write("%-58s %6d %-12s %s\n" % (r["full_name"][:58], r["stars"],
                    (r["language"] or "")[:12], (r["description"] or "")[:74]))
print("wrote _classified.json / _review.txt")
