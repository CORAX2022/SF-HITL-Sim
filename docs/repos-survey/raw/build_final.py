# -*- coding: utf-8 -*-
"""Lane R: build final curated repos.json from verified API metadata only."""
import json, os, glob, datetime, collections

RAW = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(RAW)                      # docs/repos-survey
CUT = datetime.datetime(2023, 10, 14, tzinfo=datetime.timezone.utc)

pool = {}
for f in glob.glob(os.path.join(RAW, "*.json")):
    if os.path.basename(f).startswith("_"):
        continue
    try:
        j = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for it in (j.get("items") or []):
        if it.get("full_name"):
            cur = pool.get(it["full_name"])
            if cur is None or it["stargazers_count"] > cur["stargazers_count"]:
                pool[it["full_name"]] = it
for f in glob.glob(os.path.join(RAW, "core", "*.json")):
    try:
        j = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    if j.get("full_name"):
        cur = pool.get(j["full_name"])
        if cur is None or j["stargazers_count"] > cur["stargazers_count"]:
            pool[j["full_name"]] = j

W = {}
def add(cat, *names):
    for n in names:
        W[n] = cat

add(1,
 "mesa/mesa","mesa/mesa-geo","mesa/mesa-examples","NetLogo/NetLogo","NetLogo/models",
 "JuliaDynamics/Agents.jl","JuliaDynamics/ConcurrentSim.jl","jofmi/agentpy",
 "backspaces/agentscript","krABMaga/krABMaga","evoplex/evoplex","FLAMEGPU/FLAMEGPU2",
 "AgentTorch/AgentTorch","gama-platform/gama","Repast/repast.simphony","eclab/mason",
 "sarl/sarl","noncomputable/AgentMaps","abmgis/abmgis","scottfr/simulation",
 "BioDynaMo/biodynamo","MathCancer/PhysiCell","IBM/AMLSim","starsimhub/covasim",
 "EpiModel/EpiModel","BDI-pathogens/OpenABM-Covid19","maxencefaldor/cax",
 "assume-framework/assume","bancaditalia/BeforeIT.jl","uwol/computational-economy",
 "douthwja01/OpenMAS","pathsim/pathsim","amesoudi/cultural_evolution_ABM_tutorial")
add(2,
 "MengeCrowdSim/Menge","snape/RVO2","snape/RVO2-3D","svenkreiss/socialforce",
 "aillieo/RVO2-Unity","paraboul/mapchecking","sweriko/Horde",
 "sepsamavi/safe-interactive-crowdnav","nathanrooy/rpi-urban-mobility-tracker",
 "jiachenli94/Awesome-Interaction-Aware-Trajectory-Prediction","akphi/PedestrianCounter")
add(3,
 "eclipse-sumo/sumo","matsim-org/matsim-libs","matsim-org/matsim-example-project",
 "cityflow-project/CityFlow","a-b-street/abstreet","a-b-street/osm2streets",
 "flow-project/flow","LibCity/Bigscity-LibCity","LucasAlegre/sumo-rl",
 "bstabler/TransportationNetworks","ucla-mobility/OpenCDA","scikit-mobility/scikit-mobility",
 "motis-project/motis","MobilityData/gbfs","openmobilityfoundation/mobility-data-specification",
 "conveyal/transitive.js","conveyal/r5","opentripplanner/OpenTripPlanner",
 "Project-OSRM/osrm-backend","valhalla/valhalla","graphhopper/graphhopper",
 "MobilityData/gtfs-validator","ActivitySim/activitysim","LBNL-UCB-STI/beam",
 "ropensci/stplanr","BilHim/trafficSimulator","sommer/veins","lcodeca/LuSTScenario",
 "eclipse-mosaic/mosaic","UCF-SST-Lab/UCF-SST-CitySim1-Dataset","metadriverse/urban-sim",
 "mkturkcan/valdrada","Zhangweihui666/silver-tourism-digital-twin",
 "team-watchdog/colombo-skylines","UDST/urbansim","UDST/urbanaccess","streetmix/streetmix",
 "minhe51805/UrbanReflex","Esri/public-transit-tools","ibi-group/datatools-ui",
 "NVlabs/catk","CurryChen77/RIFT","yifanlu0227/ChatSim",
 "OpenDriveLab/End-to-end-Autonomous-Driving")
add(4,
 "joonspk-research/generative_agents","google-deepmind/concordia","camel-ai/oasis",
 "sotopia-lab/sotopia","a16z-infra/ai-town","tsinghua-fib-lab/AgentSociety",
 "tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation","OpenBMB/AgentVerse",
 "Farama-Foundation/ChatArena","microsoft/autogen","camel-ai/camel",
 "FoundationAgents/MetaGPT","crewAIInc/crewAI","OpenBMB/ChatDev",
 "facebookresearch/meta-agents-research-environments","HumanoidAgents/HumanoidAgents",
 "agiresearch/WarAgent","ZJU-LLMs/Agent-Kernel","ZJU-LLMs/OpenStory","LehengTHU/Agent4Rec",
 "Ahren09/AgentReview","FreedomIntelligence/TwinMarket","sethkarten/LLM-Economist",
 "mkturkcan/generative-agents","x-glacier/GenerativeAgentsCN","hello-diana/MASCOT",
 "mluogh/eastworld","AIR-DISCOVER/FreeAskWorld","apromisedland/trustworthy-agent-simulation",
 "JouJouoo/agent-campus","marcopatzelt/brunnfeld-agentic-world",
 "microsoft/AnthropomorphicIntelligence","Purewhiter/mobilegym","nikmcfly/MiroFish-Offline",
 "tt-a1i/MiroFish-local","taichengguo/LLM_MultiAgents_Survey_Papers")
add(5,
 "oTree-org/oTree","jspsych/jsPsych","psychopy/psychopy","psychopy/psychojs",
 "nodeGame/nodegame","Scifabric/pybossa","Toloka/crowd-kit","surveyjs/survey-library",
 "LimeSurvey/LimeSurvey","formr/formr","breadboard-ai/breadboard","kobotoolbox/kpi",
 "getodk/central","open-cogsci/OpenSesame","Psychtoolbox-3/Psychtoolbox-3",
 "didi/xiaoju-survey","huggingface/gym-hil")
add(6,
 "SDXorg/pysd","Fault-lang/Fault","pathsim/pathsim","scottfr/simulation",
 "OpenModelica/OpenModelica","py-why/causal-learn","py-why/dowhy")
add(7,
 "keplergl/kepler.gl","visgl/deck.gl","visgl/flowmap.gl","FlowmapBlue/FlowmapBlue",
 "gboeing/osmnx","gboeing/osmnx-examples","geopandas/geopandas",
 "movingpandas/movingpandas","movingpandas/movingpandas-examples","UDST/pandana",
 "python-visualization/folium","uber/h3","uber/h3-js","uber/h3-py","Turfjs/turf",
 "mbloch/mapshaper","antvis/L7","opengeos/leafmap","rstudio/leaflet","pysal/momepy",
 "pysal/libpysal","benchmark-urbanism/cityseer-api","varoudis/depthmapX",
 "luukvdmeer/sfnetworks","c2g-dev/city2graph","tudelft3d/City4CFD","kunifujiwara/VoxCity",
 "tudelft3d/3dfier","xarray-contrib/xarray-spatial","pyproj4/pyproj","locationtech/jts",
 "postgis/postgis","mapnik/mapnik","placemark/placemark","CesiumGS/cesium",
 "CesiumGS/3d-tiles","cyang-kth/fmm","felixpalmer/a5","r-barnes/dggridR",
 "eurostat/gridviz","tsinghua-fib-lab/DRL-urban-planning","osmlab/atlas",
 "gboeing/ppde642","google/s2geometry","mapbox/mapbox-gl-js","dfsnow/opentimes",
 "wmgeolab/geoBoundaries","mattijn/topojson","fitodic/centerline")

CATLABEL = {1:"①ABM 框架",2:"②人群/行人仿真",3:"③交通/城市/数字孪生",
            4:"④LLM 合成智能体/社会仿真",5:"⑤行为实验/HITL 平台",
            6:"⑥系统动力学/因果回路",7:"⑦空间数据与 OD 可视化"}

NOTES = {
 "mesa/mesa":"本课题核心候选：纯 Python ABM，支持空间网格与 GIS，最贴合“存量-流量 + 智能体”混合建模。",
 "mesa/mesa-geo":"Mesa 的 GIS 扩展，把 ABM 智能体绑定到真实空间单元，是本课题空间单元划分的直接桥梁。",
 "NetLogo/NetLogo":"教学与快速原型事实标准，行为空间/系统动力学并存，适合向人类被试展示的可视化模型。",
 "JuliaDynamics/Agents.jl":"性能最高的开源 ABM 之一，适合大规模人群智能体的算力验证。",
 "AgentTorch/AgentTorch":"面向百万级“大种群模型”的可微分 ABM，可用于宏观存量-流量与微观智能体的耦合。",
 "gama-platform/gama":"GIS 原生 ABM 平台，内置空间单元与道路网络，适合城市尺度人群仿真。",
 "Repast/repast.simphony":"经典 ABM 平台（Java），工程成熟度高，可作对照实现。",
 "eclab/mason":"MASON 多智能体仿真工具包，Java 高性能离散事件内核。",
 "jofmi/agentpy":"轻量 Python ABM + 参数扫描，工程可读性好。",
 "FLAMEGPU/FLAMEGPU2":"GPU 加速 ABM，用于大规模人群/交通智能体的性能上限评估。",
 "noncomputable/AgentMaps":"把 ABM 智能体放到真实地图上，交互式社会仿真，界面范式可借鉴。",
 "scottfr/simulation":"同时支持系统动力学与 ABM 的 JS 仿真库，同一份世界表达两种范式。",
 "starsimhub/covasim":"大规模流行病 ABM，展示了干预策略与人群异质性的工程化做法。",
 "IBM/AMLSim":"多智能体金融交易仿真，可作为“规则智能体 + 聚合流量”工程样板。",
 "abmgis/abmgis":"ABM 与 GIS 集成专著配套代码，空间单元与智能体耦合的参考实现。",
 "MengeCrowdSim/Menge":"经典开源人群仿真框架，含社会力/ORCA 等底层模型，可直接做行人流内核。",
 "snape/RVO2":"ORCA 互惠避碰参考实现，行人微观运动的工业级基线。",
 "svenkreiss/socialforce":"可微分社会力模型（JAX/PyTorch），可与数据同化/参数校准结合。",
 "paraboul/mapchecking":"按地图区域估算人群密度与容量，人-空间承载力校核的现成工具。",
 "nathanrooy/rpi-urban-mobility-tracker":"边缘设备行人/自行车计数，为仿真提供真实到达率标定数据。",
 "jiachenli94/Awesome-Interaction-Aware-Trajectory-Prediction":"行人轨迹预测文献清单，支撑真实人群运动参数化。",
 "eclipse-sumo/sumo":"微观交通仿真事实标准，含行人（步行）模型与人流-车流耦合接口。",
 "matsim-org/matsim-libs":"基于活动的交通需求仿真，最接近“人的活动决策 + 网络流量”的工程范式。",
 "cityflow-project/CityFlow":"大规模城市交通强化学习环境，可用于信号/流量的在线学习闭环。",
 "a-b-street/abstreet":"从 OSM 生成城市并做交通仿真与规划可视化，数字孪生+交互式参与式界面范例。",
 "flow-project/flow":"RL 交通控制框架，把 SUMO 封装为 Gym 环境，HITL 实验可复用其闭环。",
 "LibCity/Bigscity-LibCity":"城市时空数据挖掘统一库，含 OD 预测任务，为模型提供数据管线。",
 "metadriverse/urban-sim":"城市微观移动性仿真平台，支持大规模智能体。",
 "UDST/urbansim":"城市土地/区位选择微观模拟，存量-流量与区位决策的经典实现。",
 "UDST/urbanaccess":"基于 GTFS 的可达性计算，用于空间单元可达性指标。",
 "streetmix/streetmix":"街道横断面协同设计，人类被试参与空间方案的界面参考。",
 "Project-OSRM/osrm-backend":"开源路径规划引擎，OD 流量分配与最短路的工程底座。",
 "valhalla/valhalla":"多模式路径规划，可算 OD 出行时间矩阵。",
 "graphhopper/graphhopper":"Java 路径规划库，轻量嵌入易用。",
 "opentripplanner/OpenTripPlanner":"多模式公交路径规划，用于公共交通 OD 可达性。",
 "conveyal/r5":"交通情景规划的快速路径算法，区域尺度可达性分析。",
 "motis-project/motis":"多模式路由/地理编码一体化服务。",
 "MobilityData/gtfs-validator":"公共交通数据质量校验，仿真输入数据的质量保障。",
 "joonspk-research/generative_agents":"LLM 生成式智能体里程碑，人类行为可信度评审范式可迁移到 HITL 实验。",
 "google-deepmind/concordia":"DeepMind 生成式社会仿真库，提供“智能体+环境+社会”标准抽象。",
 "camel-ai/oasis":"百万级 LLM 智能体社会交互仿真，规模上限参考。",
 "sotopia-lab/sotopia":"社交智能体交互与社会智能评测，可直接产出人类-智能体对话行为数据。",
 "a16z-infra/ai-town":"可自托管的多智能体小镇，工程上最接近“可玩的社会仿真世界”。",
 "tsinghua-fib-lab/AgentSociety":"国内 LLM 社会仿真平台，含城市/社会场景与实验编排，本课题最直接对标。",
 "tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation":"LLM 与 ABM 融合的综述与代码，理论接口参考。",
 "facebookresearch/meta-agents-research-environments":"Meta 的智能体研究环境平台，可复现实验编排。",
 "microsoft/autogen":"通用多智能体编排框架，可作为异构智能体（LLM+规则）集成底座。",
 "camel-ai/camel":"角色扮演式多智能体框架，便于构造合成被试。",
 "FoundationAgents/MetaGPT":"软件公司式多智能体协作，组织结构建模参考。",
 "crewAIInc/crewAI":"生产级多智能体编排，工程集成成本低。",
 "HumanoidAgents/HumanoidAgents":"让生成式智能体更像人（基本需求/情绪/关系），人类行为可信度提升方案。",
 "agiresearch/WarAgent":"LLM 多智能体历史仿真，验证 LLM 群体行为涌现。",
 "sethkarten/LLM-Economist":"LLM 大种群经济模拟，接近“聚合存量-流量 + LLM 个体”混合路线。",
 "AIR-DISCOVER/FreeAskWorld":"交互式仿真框架，含人类参与接口。",
 "apromisedland/trustworthy-agent-simulation":"可审计的 LLM 多智能体城市仿真（AgentScope+Mesa），与本课题技术栈最接近的组合。",
 "microsoft/AnthropomorphicIntelligence":"拟人化 AI 研究项目，人类相似度评价指标可借鉴。",
 "oTree-org/oTree":"多人交互决策实验标准平台，人类被试实验（公共品/博弈/流选择）首选。",
 "jspsych/jsPsych":"浏览器行为实验框架，适合做空间选择/路径选择的在线被试实验。",
 "psychopy/psychopy":"心理学实验构建与运行，精细刺激呈现与反应时采集。",
 "psychopy/psychojs":"PsychoPy 的在线版，便于远程被试。",
 "nodeGame/nodegame":"实时多人同步实验平台，适合小组协同/网络化实验。",
 "Scifabric/pybossa":"众包微任务平台，可发布大规模人类标注/判断任务。",
 "Toloka/crowd-kit":"众包数据质量与聚合工具，人类判断数据的清洗与一致性评估。",
 "surveyjs/survey-library":"开源问卷引擎，可承载空间偏好/出行选择问卷与量表。",
 "LimeSurvey/LimeSurvey":"成熟问卷系统，适合纵向/分层抽样调查。",
 "formr/formr":"面向纵向追踪与经验采样（ESM）的实验/问卷框架。",
 "breadboard-ai/breadboard":"可视化编排 LLM 与人类节点的图结构，HITL 流程原型工具。",
 "kobotoolbox/kpi":"移动数据采集/问卷平台，野外调查与空间标注。",
 "getodk/central":"ODK 数据采集服务端，标准化表单与地理点位采集。",
 "open-cogsci/OpenSesame":"图形化实验构建器，非程序员也能搭建人类被试实验。",
 "Psychtoolbox-3/Psychtoolbox-3":"MATLAB 实验工具箱，反应时与视觉呈现的金标准。",
 "didi/xiaoju-survey":"企业级问卷/表单平台，适合国内大规模线上调查部署。",
 "huggingface/gym-hil":"人在回路强化学习环境，把人类反馈直接纳入智能体训练闭环。",
 "SDXorg/pysd":"把 Vensim/XMILE 存量-流量模型翻译为 Python，可直接嵌入仿真世界。",
 "Fault-lang/Fault":"面向系统动力学建模的语言，CLD/存量-流量表达简洁。",
 "pathsim/pathsim":"基于框图范式的动态系统仿真，贴近存量-流量与反馈回路表达。",
 "OpenModelica/OpenModelica":"方程型系统建模语言实现，可表达连续存量-流量与多域耦合。",
 "py-why/causal-learn":"因果结构学习，可对观测数据自动推断因果图，与 CLD 互证。",
 "py-why/dowhy":"因果推断工具箱，用于实验/仿真结果的因果效应估计。",
 "keplergl/kepler.gl":"大规模地理数据可视化，OD 弧线/流向图的现成方案。",
 "visgl/deck.gl":"WebGL 地理可视化底层，FlowmapLayer/ArcLayer 可做大规模 OD 流。",
 "visgl/flowmap.gl":"专为流向图设计的 deck.gl 图层，OD 流量可视化首选。",
 "FlowmapBlue/FlowmapBlue":"零代码流向地图工具，报告与参与式展示友好。",
 "gboeing/osmnx":"从 OSM 构建街道网络与空间单元，本课题空间基底构建的核心工具。",
 "geopandas/geopandas":"矢量空间数据处理的 Python 基础库。",
 "movingpandas/movingpandas":"移动轨迹数据探索与分析，用于从轨迹提取 OD 流。",
 "UDST/pandana":"快速可达性与最短路计算，城市单元可达性指标。",
 "python-visualization/folium":"轻量交互地图，快速出图与检查空间单元。",
 "uber/h3":"六边形层级空间索引，替代不规则行政单元做统计与聚合。",
 "pysal/momepy":"城市形态量化工具包，为空间单元提供形态学特征。",
 "pysal/libpysal":"空间分析算法库，空间权重矩阵与空间自相关。",
 "benchmark-urbanism/cityseer-api":"街道网络中心性与城市分析，空间单元指标生成。",
 "varoudis/depthmapX":"空间句法分析软件，街道网络与空间构形经典工具。",
 "c2g-dev/city2graph":"把地理关系转成图结构，直接支撑“空间单元 → 网络/流量图”的建模。",
 "tudelft3d/City4CFD":"从 3D 城市模型重建建筑用于城市流场仿真，风/人流环境耦合参考。",
 "kunifujiwara/VoxCity":"地理数据+3D 城市建模+城市分析框架，空间单元与三维环境耦合。",
 "cyang-kth/fmm":"快速地图匹配，把 GPS 轨迹转成路网 OD 流。",
 "felixpalmer/a5":"五边形层级地理索引，空间单元划分方案备选。",
 "r-barnes/dggridR":"离散全球网格系统，跨尺度空间单元划分。",
 "eurostat/gridviz":"规则网格数据可视化，网格化空间单元展示。",
 "tsinghua-fib-lab/DRL-urban-planning":"深度强化学习做城市空间布局，空间单元生成/优化参考。",
 "dfsnow/opentimes":"美国普查地理单元间的免费通行时间矩阵，OD 成本矩阵现成数据源。",
 "wmgeolab/geoBoundaries":"全球行政边界数据集，空间单元划分基准。",
 "mattijn/topojson":"地图拓扑编码，相邻空间单元拓扑关系构建。",
 "CesiumGS/cesium":"三维地球可视化平台，数字孪生城市场景渲染。",
}

NOTES.update({
 "EpiModel/EpiModel":"R 语言传染病 ABM 建模框架，展示网络接触结构与干预情景的工程化抽象。",
 "maxencefaldor/cax":"JAX 加速的元胞自动机库，可作为空间离散存量演化的高性能底座。",
 "mesa/mesa-examples":"Mesa 官方模型库，含人群与交通类示例，可作二次开发起点。",
 "krABMaga/krABMaga":"Rust 高性能 ABM 框架，适合对大规模智能体做性能对照。",
 "MathCancer/PhysiCell":"生物多细胞 ABM 平台，展示大规模个体规则与连续场的耦合实现。",
 "JuliaDynamics/ConcurrentSim.jl":"Julia 离散事件仿真框架，适合构建服务台/排队式人流设施模型。",
 "sarl/sarl":"面向智能体的编程语言（JVM），可把智能体行为与空间规则形式化。",
 "douthwja01/OpenMAS":"MATLAB 多智能体仿真器，便于与控制/工程侧方法互操作。",
 "uwol/computational-economy":"微观主体加总出宏观均衡的 ABM，与存量-流量加总逻辑同源。",
 "BioDynaMo/biodynamo":"高性能模块化 ABM 平台，架构分层清晰，可借鉴其扩展机制。",
 "BDI-pathogens/OpenABM-Covid19":"英国政府使用的 ABM 疫情模型，含人口分层与干预参数化范本。",
 "NetLogo/models":"NetLogo 官方模型库，可直接改造为社会/空间互动的教学与预实验原型。",
 "bancaditalia/BeforeIT.jl":"央行级宏观 ABM，展示存量-流量一致性与大规模校准流程。",
 "backspaces/agentscript":"浏览器端 ABM，便于把仿真世界嵌入网页实验界面交给被试操作。",
 "assume-framework/assume":"电力市场 ABM 框架，含智能体学习与市场出清，可迁移到资源配置仿真。",
 "amesoudi/cultural_evolution_ABM_tutorial":"文化演化 ABM 教学代码，含参数扫描与统计汇总范式。",
 "snape/RVO2-3D":"三维 ORCA 实现，适用于多层空间与立体通道的人群流动。",
 "aillieo/RVO2-Unity":"Unity 中的 ORCA 实现，可快速搭建可视化人群仿真场景。",
 "sepsamavi/safe-interactive-crowdnav":"机器人在人群中安全导航的论文代码，含人群交互与避让约束。",
 "sweriko/Horde":"Three.js 大规模人群渲染与仿真，用于结果可视化呈现。",
 "OpenDriveLab/End-to-end-Autonomous-Driving":"端到端自动驾驶综述与基准，车辆轨迹生成与评测口径参考。",
 "ucla-mobility/OpenCDA":"协同驾驶自动化原型框架，含 SUMO 与 CARLA 联合仿真。",
 "LucasAlegre/sumo-rl":"SUMO 强化学习环境集合，HITL 中智能体在线学习可复用。",
 "bstabler/TransportationNetworks":"交通研究标准路网与需求数据，OD 分配的基准输入。",
 "MobilityData/gbfs":"共享单车数据规范，微出行 OD 与供给数据源。",
 "scikit-mobility/scikit-mobility":"移动性数据分析库，含 OD 矩阵构建与轨迹统计。",
 "openmobilityfoundation/mobility-data-specification":"城市微出行数据规范，含出行起讫与地理围栏定义。",
 "conveyal/transitive.js":"公交路径与换乘可视化组件，用于结果呈现。",
 "ropensci/stplanr":"R 交通规划工具，含 OD 分配与可达性计算。",
 "yifanlu0227/ChatSim":"用自然语言编辑驾驶场景的仿真，展示语言模型控制世界状态。",
 "UCF-SST-Lab/UCF-SST-CitySim1-Dataset":"城市交通仿真轨迹数据集，可用于校准与评测。",
 "BilHim/trafficSimulator":"Python 微观交通仿真器，代码量适中，便于改造为行人-车辆耦合模型。",
 "sommer/veins":"车联网仿真框架（OMNeT++ 与 SUMO），通信与交通联合仿真。",
 "team-watchdog/colombo-skylines":"游戏引擎内城市数字孪生，参与式城市设计的交互范式参考。",
 "ActivitySim/activitysim":"活动基出行需求平台，个体日程决策与聚合流量衔接的范本。",
 "Zhangweihui666/silver-tourism-digital-twin":"语义数字孪生加 500 智能体养老旅游实验室，与本课题场景最接近。",
 "NVlabs/catk":"交通模型闭环微调工具包，含轨迹级评测。",
 "Esri/public-transit-tools":"ArcGIS 公交 GTFS 工具链，空间单元上的公交可达性处理。",
 "matsim-org/matsim-example-project":"MATSim 官方入门工程，评估其集成成本的最短路径。",
 "mkturkcan/valdrada":"公共数据驱动的纽约实时数字孪生，展示实时数据接入与三维呈现。",
 "a-b-street/osm2streets":"把 OSM 车道级路网转换为核心街道模型，空间单元与路网的桥接件。",
 "LBNL-UCB-STI/beam":"行为-能源-自主性-出行仿真框架，含出行者决策代理。",
 "ibi-group/datatools-ui":"公交数据工具前端，GTFS 编辑与校验的工程参考。",
 "CurryChen77/RIFT":"交通仿真轨迹的可控生成与微调，提升智能体行为真实性。",
 "minhe51805/UrbanReflex":"开源智慧城市平台，路侧感知数据与城市指标管理。",
 "lcodeca/LuSTScenario":"卢森堡 SUMO 标准场景，可直接用于交通仿真基准测试。",
 "eclipse-mosaic/mosaic":"多域多尺度交通仿真框架，支持 SUMO 与通信/环境联合仿真。",
 "OpenBMB/ChatDev":"多智能体协作开发范式，可借鉴其角色分工与记忆机制。",
 "OpenBMB/AgentVerse":"多 LLM 智能体部署框架，含任务求解与社会行为两类环境。",
 "nikmcfly/MiroFish-Offline":"离线多智能体社会仿真与预测引擎，可离线复现实验结果。",
 "Farama-Foundation/ChatArena":"多智能体语言博弈环境，适合设计人类-LLM 混合博弈实验。",
 "taichengguo/LLM_MultiAgents_Survey_Papers":"LLM 多智能体综述清单，用于快速定位方法谱系。",
 "mkturkcan/generative-agents":"本地低成本生成式智能体复现，实验成本可控。",
 "Purewhiter/mobilegym":"可验证并行仿真平台，强调可复现的智能体评测。",
 "hello-diana/MASCOT":"多智能体社会协作评测论文代码，提供社交能力指标。",
 "Ahren09/AgentReview":"用 LLM 智能体模拟同行评审，展示群体决策过程的仿真。",
 "ZJU-LLMs/Agent-Kernel":"微内核多智能体社会仿真框架，架构上易嵌入自研世界模型。",
 "x-glacier/GenerativeAgentsCN":"生成式智能体中文重构版，便于中文被试与中文场景实验。",
 "LehengTHU/Agent4Rec":"生成式智能体做推荐仿真，含用户行为可信度评测方法。",
 "ZJU-LLMs/OpenStory":"LLM 多智能体叙事与社会演化框架。",
 "mluogh/eastworld":"游戏场景中的生成式智能体框架，可做低成本虚拟世界原型。",
 "FreedomIntelligence/TwinMarket":"多智能体金融市场仿真，含异质主体行为校准。",
 "tt-a1i/MiroFish-local":"MiroFish 本地可运行版本，便于离线实验与复现。",
 "marcopatzelt/brunnfeld-agentic-world":"中世纪村落经济仿真，最多 1000 个 LLM 智能体，规模与成本参考。",
 "JouJouoo/agent-campus":"LangGraph 构建的校园社会仿真，含记忆与社交关系，场景贴近本课题。",
 "mapbox/mapbox-gl-js":"主流 Web 地图渲染库，交互式地图与流向图层的底座。",
 "Turfjs/turf":"前端空间分析函数库，用于空间单元几何运算。",
 "mbloch/mapshaper":"Shapefile 与 GeoJSON 编辑简化，空间单元数据预处理。",
 "antvis/L7":"大规模 WebGL 地理可视化引擎，国内生态可用。",
 "mapnik/mapnik":"地图渲染工具箱，静态出图与瓦片生产。",
 "opengeos/leafmap":"Python 交互式地图与地理分析，快速探索空间单元。",
 "google/s2geometry":"球面层级网格索引，空间单元划分与聚合的备选方案。",
 "CesiumGS/3d-tiles":"三维瓦片流式规范，数字孪生城市数据分发标准。",
 "postgis/postgis":"空间数据库扩展，空间单元与 OD 流的海量存储与查询。",
 "locationtech/jts":"Java 拓扑套件，几何运算与空间关系判断基础库。",
 "gboeing/osmnx-examples":"OSMnx 官方示例集，街道网络与空间单元构建的速查手册。",
 "placemark/placemark":"浏览器端地理数据编辑与转换工具，人工核查空间单元方便。",
 "gboeing/ppde642":"城市数据科学课程（含 OSMnx 与网络分析），方法与代码模板。",
 "pyproj4/pyproj":"坐标投影转换，空间单元对齐与投影选择必用。",
 "uber/h3-js":"H3 六边形索引的 JS 实现，前端空间聚合。",
 "uber/h3-py":"H3 六边形索引的 Python 实现，便于与仿真数据管线集成。",
 "xarray-contrib/xarray-spatial":"栅格空间分析算法（含视线与密度），网格化空间单元分析。",
 "rstudio/leaflet":"R 交互地图，统计分析与出图一体化。",
 "tudelft3d/3dfier":"从二维数据重建三维城市模型，用于三维空间单元与环境耦合。",
 "luukvdmeer/sfnetworks":"R 空间网络整洁数据结构，路网与 OD 流的图分析。",
 "fitodic/centerline":"多边形中心线提取，把街区或地块转成线性空间单元。",
 "osmlab/atlas":"OSM 数据内存对象模型，便于按空间单元做拓扑查询。",
 "movingpandas/movingpandas-examples":"移动数据分析示例集，轨迹转 OD 的方法可直接套用。",
})

rows, missing, dropped = [], [], []
for name, cat in W.items():
    it = pool.get(name)
    if it is None:
        missing.append("%s (cat%d)" % (name, cat)); continue
    stars = it.get("stargazers_count") or 0
    pushed = it.get("pushed_at")
    pushed_dt = None
    if pushed:
        try:
            pushed_dt = datetime.datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        except Exception:
            pushed_dt = None
    active = bool(pushed_dt and pushed_dt >= CUT)
    if stars <= 100:
        dropped.append("%s stars=%d" % (name, stars)); continue
    if not active:
        dropped.append("%s inactive pushed=%s" % (name, pushed)); continue
    desc = (it.get("description") or "").strip()
    note = NOTES.get(name)
    if not note:
        short = (desc[:58] + "…") if len(desc) > 58 else desc
        note = "%s；%s" % (CATLABEL[cat], short) if short else CATLABEL[cat]
    lic = (it.get("license") or {}).get("spdx_id") if it.get("license") else None
    if lic in ("NOASSERTION", "NONE"):
        lic = None
    rows.append({
        "host": "github",
        "full_name": it["full_name"],
        "url": it.get("html_url") or ("https://github.com/" + it["full_name"]),
        "stars": stars,
        "language": it.get("language"),
        "license_spdx": lic,
        "default_branch": it.get("default_branch"),
        "created_at": it.get("created_at"),
        "pushed_at": pushed,
        "topics": list(it.get("topics") or []),
        "description": desc or None,
        "category": cat,
        "near_3y_active": active,
        "relevance_note": note,
    })

rows.sort(key=lambda r: (r["category"], -r["stars"]))
seen, uniq = set(), []
for r in rows:
    if r["full_name"] in seen:
        continue
    seen.add(r["full_name"]); uniq.append(r)
json.dump(uniq, open(os.path.join(OUT, "repos.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
cnt = collections.Counter(r["category"] for r in uniq)
print("FINAL entries:", len(uniq))
for c in sorted(cnt): print("  cat%d: %d" % (c, cnt[c]))
print("MISSING metadata (%d):" % len(missing))
for m in missing: print("   ", m)
print("DROPPED by rules (%d):" % len(dropped))
for d in dropped: print("   ", d)
