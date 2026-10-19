"""构建 docs/papers/index.json —— 每篇条目的标题/作者/年份均取自 PDF 实际内容，
未成功抽取的条目明确标注 metadata_verified=false，并且不填入未经核实的字段。"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 依据 PDF 首页实际抽取文本与文件名整理的条目。
# verified=True 表示标题/作者来自 PDF 首页正文实际抽取结果。
ENTRIES = [
    # ---------------- A. 存量-流量 / 系统动力学空间建模 ----------------
    dict(id="Baez2022_StockFlowDiagrams", themes=["A"], year=2023, venue="EPTCS 380 (ACT 2022)",
         title="Compositional Modeling with Stock and Flow Diagrams",
         authors=["John Baez", "Xiaoyan Li", "Sophie Libkind", "Benjamin Flint", "Nicholas B. B. S."],
         source="EPTCS", source_id="doi:10.4204/EPTCS.380.5", verified=True,
         contribution="用范畴论为存量-流量图给出严格语义，使系统动力学模型可组合、可形式化验证。",
         borrow="本项目把空间单元存量与跨单元流量写成守恒方程；该文提供了'存量-流量图'的严格数学语义，可支撑模型规范的形式化表述与合法性检查。",
         limitation="纯数学/范畴论视角，不涉及空间分区或人机交互实验。"),

    dict(id="Lyu2025_OvertourismSystemDynamics", themes=["A"], year=2025, venue="preprint",
         title="Overtourism to Equilibrium: A System Dynamics & Multi-Objective Model for Sustainable Destinations",
         authors=["Huanzhu Lyu", "Xiao Yang", "Xintong Ji"], source="preprint", source_id="", verified=True,
         contribution="用系统动力学 + 多目标优化刻画过度旅游的存量-流量演化与可持续平衡策略。",
         borrow="最接近本项目'存量-流量用于人流治理'的应用范例：展示了如何用聚合存量刻画人群压力，并把治理策略作为控制变量。",
         limitation="面向旅游目的地宏观管理，无空间分区粒度，无真人参与回路。"),

    dict(id="Raimbault2020_UrbanScienceDynamics", themes=["A", "D"], year=2020, venue="preprint",
         title="Empowering Urban Governance through Urban Science: Multi-scale Dynamics of Urban Systems Worldwide",
         authors=["Juste Raimbault", "Eric Denis", "Denise Pumain"], source="preprint", source_id="", verified=True,
         contribution="论证城市系统的多尺度动力学，提出以城市科学支撑治理的框架。",
         borrow="为'聚合单元 + 多尺度'的建模立场提供学科论证；可用于说明为何宏观聚合建模对治理有效。",
         limitation="宏观城市体系尺度（城市间），非场地内人流尺度。"),

    dict(id="Martin2020_CommunitySystemDynamics", themes=["A", "B"], year=2020, venue="ICLR 2020",
         title="Participatory Problem Formulation for Fairer Machine Learning through Community Based System Dynamics",
         authors=["Donald Martin, Jr.", "Vinodkumar Prabhakaran", "Margaret Mitchell"], source="ICLR",
         source_id="", verified=True,
         contribution="把社区参与式系统动力学用于机器学习问题的界定，让利益相关者参与建模过程。",
         borrow="'参与式 + 系统动力学'结合的范例，支撑本项目'让真实参与者进入存量-流量建模回路'的合法性；同时提示参与式建模的流程设计要点。",
         limitation="参与发生在'问题界定'阶段而非'仿真运行时'，不是实时闭环。"),

    dict(id="MalardAdam2023_ParticipatoryModelling", themes=["A", "B"], year=2023, venue="preprint",
         title="Développement participatif d'un modèle couplé d'un système agricole indigène à petite échelle (Guatemala)",
         authors=["Malard-Adam et al."], source="preprint", source_id="", verified=True,
         contribution="以参与式方式共同构建小规模农业系统的耦合模型（法文）。",
         borrow="提供了参与式建模（companion modelling）的实操流程：如何组织利益相关者共同定义存量与流量。",
         limitation="农业系统、法文文献、无实时仿真闭环。"),

    dict(id="Herzog2025_UrbanModelPlatform", themes=["A", "D"], year=2025, venue="arXiv:2506.10964",
         title="The Urban Model Platform: A Public Backbone for Modeling and Simulation in Urban Digital Twins",
         authors=["Rico H. Herzog", "Till Degkwitz", "Trivik Verma"], source="arXiv",
         source_id="2506.10964", verified=True,
         contribution="提出面向城市数字孪生的公共建模与仿真基础设施（平台化路线）。",
         borrow="平台化架构与开放基础设施的论证，可用作本项目'平台贡献'的对照与引用；也说明城市仿真平台化的国际趋势。",
         limitation="数字孪生路线，与本项目'降低空间建模复杂度'的取向相反，适合作对照。"),

    # ---------------- B. 人在回路 / 参与式仿真 ----------------
    dict(id="Ni2024_LiPUPMA", themes=["B"], year=2024, venue="preprint",
         title="LiPUP-MA: A Residential Experience-centric Multi-Agent Framework for Living-in-the-loop Participatory Urban Planning",
         authors=["Hang Ni", "Yuzhi Wang", "Yizhi Song", "Hao Liu"],
         source="preprint", source_id="", verified=True,
         contribution="提出以居住体验为中心的 living-in-the-loop 多主体参与式城市规划框架。",
         borrow="**与本项目最直接相关**：同样主张把居民置于规划回路中并采集体验数据。可作为最接近的先行工作，用于精确界定本项目的增量（空间存量-流量聚合 + 合成智能体同场）。",
         limitation="以居住体验与规划方案评价为中心，未采用存量-流量空间模型；合成智能体与真人的同场协同不是重点。"),

    dict(id="Xuan2025_GenerativeAgentHITL", themes=["B", "C"], year=2025, venue="preprint",
         title="Design and Evaluation of Generative Agent-based Platform for Human-Assistant Interaction Research: A Tale of 10 User Studies",
         authors=["Ziyi Xuan", "Yiwen Wu", "Xuhai Xu"], source="preprint", source_id="", verified=True,
         contribution="构建生成式智能体平台并以其开展 10 项用户研究，评估人-助手交互。",
         borrow="**人机同场实验的平台化与用户研究实证**：其'真人与生成式智能体共同参与实验'的做法，为本项目的人机混合实验设计提供方法论模板（含 10 项研究的评估经验）。",
         limitation="面向人-助手交互（对话式），非空间人流决策；环境不是空间存量-流量模型。"),

    dict(id="Suzuki2017_ParticipatoryUrbanSim", themes=["B"], year=2017, venue="preprint (UCL CASA)",
         title="Multiagent-based Participatory Urban Simulation through Inverse Reinforcement Learning",
         authors=["Soma Suzuki"], source="preprint", source_id="", verified=True,
         contribution="用逆强化学习从参与者的行为中反推偏好，驱动多主体参与式城市仿真。",
         borrow="提供了'从真人决策反推偏好参数'的技术路线——正对应本项目从被试选择中估计拥挤弹性/吸引力参数的需求。",
         limitation="依赖个体主体建模，非聚合存量-流量；样本与场景规模有限。"),

    dict(id="Argyle2022_OutOfOneMany", themes=["B", "C"], year=2022, venue="Political Analysis (preprint)",
         title="Out of One, Many: Using Language Models to Simulate Human Samples",
         authors=["Lisa P. Argyle", "Ethan C. Busby", "Nancy Fulda", "Joshua Gubler",
                  "Christopher Rytting", "David Wingate"], source="preprint", source_id="", verified=True,
         contribution="用语言模型条件化生成'硅样本'，复现人类样本的问卷分布（silicon sampling 奠基性工作之一）。",
         borrow="**人机一致性检验的方法论基石**：提供了'合成体分布 vs 真人分布'的比对范式，可直接迁移到本项目'合成智能体能否替代真人群体的空间决策'这一核心问题。",
         limitation="面向政治态度与问卷，非空间行为；未涉及人与合成体在同一环境中的实时交互。"),

    dict(id="Feygin2019_BISTRO", themes=["B"], year=2019, venue="preprint",
         title="BISTRO: A Behavior-Informed Simulation Testbed (behavioral experiments coupled with transport simulation)",
         authors=["S. Feygin et al."], source="preprint", source_id="", verified=False,
         contribution="将行为实验与交通仿真耦合的测试床（待核验细节）。",
         borrow="**潜在的强相关先行工作**：把行为实验接入交通仿真，与本项目'行为实验 + 流量仿真闭环'最接近。",
         limitation="PDF 元数据抽取失败（EOF marker not found），标题/作者待人工核验后方可引用。"),

    # ---------------- C. LLM 合成智能体社会仿真 ----------------
    dict(id="Park2023_GenerativeAgents", themes=["C"], year=2023, venue="UIST 2023 / arXiv:2304.03442",
         title="Generative Agents: Interactive Simulacra of Human Behavior",
         authors=["Joon Sung Park", "Joseph C. O'Brien", "Carrie J. Cai", "Meredith Ringel Morris",
                  "Percy Liang", "Michael S. Bernstein"], source="arXiv", source_id="2304.03442", verified=False,
         contribution="提出生成式智能体架构（记忆-反思-规划），在小镇环境中涌现出可信的社会行为。",
         borrow="合成智能体的**基础架构范式**（记忆流、反思、规划），本项目 LLM 智能体模块的设计起点。",
         limitation="纯计算智能体群体，无真人被试同场；环境非空间存量-流量模型。"),

    dict(id="Park2024_SelfReportSimulation", themes=["C", "B"], year=2024, venue="preprint",
         title="LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals",
         authors=["Joon Sung Park", "Carolyn Q. Zou", "Jonne Kamphorst", "Niles Egan", "Aaron Shaw",
                  "Benjamin Mako Hill", "Carrie J. Cai", "Meredith Ringel Morris", "Percy Liang",
                  "Michael S. Bernstein"], source="preprint", source_id="", verified=True,
         contribution="用真人自陈数据（访谈）为每个 LLM 智能体建立个体化人设，实现可泛化的个体模拟，并在多项社会科学复现中取得较好一致性。",
         borrow="**本项目 LLM 智能体人设构建的直接方法**：以真实参与者的自陈/量表数据塑造合成体的 persona，使'真人 vs 其数字替身'的对照成为可能。",
         limitation="个体级模拟而非群体空间流量；仍是合成体独立运行，无实时人机同场。"),

    dict(id="Piao2025_AgentSociety", themes=["C"], year=2025, venue="arXiv:2502.08691",
         title="AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society",
         authors=["Jinghua Piao et al."], source="arXiv", source_id="2502.08691", verified=False,
         contribution="大规模 LLM 生成式智能体社会仿真平台（城市尺度），复现社会行为。",
         borrow="国内 LLM 合成智能体平台的代表（对应赛博ZJU/SocioVerse 一支）；本项目合成体支柱的核心参照，其缺失的正是真人通道。",
         limitation="纯计算智能体群体，无真实人类被试在回路。"),

    dict(id="Zhang2025_SocioVerse", themes=["C"], year=2025, venue="preprint",
         title="SocioVerse: A World Model for Social Simulation Powered by LLM Agents and A Pool of 10 Million Real-World Users",
         authors=["Xinnong Zhang", "Jiayu Lin", "Xinyi Mou", "Shiyue Yang", "Xiawei Liu", "Libo Sun",
                  "Hanjia Lyu", "Yihang Yang", "et al."], source="preprint", source_id="", verified=True,
         contribution="以千万级真实用户池为校准基础，构建 LLM 智能体驱动的社会仿真'世界模型'。",
         borrow="**本项目缺口论证的关键引文**：其'真实用户池'用于**校准**而非让真人进入仿真闭环——正是本项目所指出缺口的直接证据（真人是数据源，不是回路中的决策者）。",
         limitation="真人仅作为分布校准依据，不参与实时仿真；无空间存量-流量建模。"),

    dict(id="Xie2024_LLMAgentTrust", themes=["C"], year=2024, venue="preprint",
         title="Can Large Language Model Agents Simulate Human Trust Behavior?",
         authors=["Chengxing Xie", "Canyu Chen", "Feiran Jia", "Ziyu Ye", "Shiyang Lai", "Kai Shu",
                  "Jindong Gu", "Adel Bibi", "Ziniu Hu", "David Jurgens", "James Evans", "et al."],
         source="preprint", source_id="", verified=True,
         contribution="系统检验 LLM 智能体能否模拟人类的信任行为，并比较其与真人的差异。",
         borrow="**人机行为一致性检验的实证范例**：其'合成体 vs 真人'比对的实验设计与统计口径，可直接迁移到本项目空间决策场景。",
         limitation="信任博弈（非空间）；未让真人与合成体同处一个仿真环境互动。"),

    dict(id="Zhou2024_LLMParticipatoryPlanning", themes=["C", "B"], year=2024, venue="preprint",
         title="Large Language Model for Participatory Urban Planning",
         authors=["Zhilun Zhou", "Yuming Lin", "et al."], source="preprint", source_id="", verified=True,
         contribution="用大语言模型支撑参与式城市规划，聚合公众意见并辅助方案研判。",
         borrow="LLM 与参与式规划的交叉工作；可用于论证'LLM 进入规划参与'的趋势，并对比其'文本意见聚合'与本项目'空间流量决策'的差异。",
         limitation="以文本意见处理为主，无空间流量仿真闭环。"),

    dict(id="Chen2024_SocialPhysicsDiffusion", themes=["C", "D"], year=2024, venue="preprint (Tsinghua)",
         title="Social Physics Informed Diffusion Model for Crowd Simulation",
         authors=["Hongyi Chen", "Jingtao Ding", "Yong Li", "Yue Wang", "Xiao-Ping Zhang"],
         source="preprint", source_id="", verified=True,
         contribution="以社会物理约束引导扩散模型生成人群运动，兼顾物理合理性与数据驱动。",
         borrow="展示了'物理约束 + 生成模型'混合建模思路，可作为本项目在需要局部个体精化时的技术候选。",
         limitation="个体级微观轨迹生成，与本项目聚合降复杂度取向相反，属对照/接驳路线。"),

    # ---------------- D. 人群/人流与数字孪生 ----------------
    dict(id="Helbing1998_SocialForceModel", themes=["D"], year=1998, venue="Nature / arXiv:cond-mat/9805244",
         title="Social force model for pedestrian dynamics",
         authors=["Dirk Helbing", "Péter Molnár"], source="arXiv", source_id="cond-mat/9805244", verified=True,
         contribution="提出社会力模型，用连续力场刻画行人个体运动，是行人动力学的奠基性工作。",
         borrow="**本项目要对照/替代的经典范式**：作为'个体级、高工程成本'路线的原始文献，用于论证为何需要低成本的聚合替代方案。",
         limitation="个体级微观模型，参数标定成本高，无闭环交互能力。"),

    dict(id="Burstedde2001_CellularAutomatonApplications", themes=["D"], year=2001, venue="Physica A / arXiv:cond-mat/0112119",
         title="Cellular Automaton Approach to Pedestrian Dynamics - Applications",
         authors=["Carsten Burstedde", "Ansgar Kirchner", "Kai Klauck", "Andreas Schadschneider",
                  "Johannes Zittartz"], source="arXiv", source_id="cond-mat/0112119", verified=True,
         contribution="将元胞自动机行人模型应用于实际场景（疏散、通道），验证其工程可用性。",
         borrow="'规则网格元胞'与我方'空间单元'的形式相似，可用于对照说明聚合单元与元胞的区别（前者不追踪个体、以存量/流量为状态）。",
         limitation="元胞级微观建模，计算与标定成本高；静态推演。"),

    dict(id="Schadschneider2001_CellularAutomatonTheory", themes=["D"], year=2001, venue="Physica A / arXiv:cond-mat/0112117",
         title="Cellular Automaton Approach to Pedestrian Dynamics - Theory",
         authors=["Andreas Schadschneider"], source="arXiv", source_id="cond-mat/0112117", verified=True,
         contribution="元胞自动机行人动力学的理论框架（规则、更新机制、基本图）。",
         borrow="同上：微观路线理论基座，作为对照范式的引文。",
         limitation="微观理论；不含参与者交互或主观感知。"),

    dict(id="Amirian2019_DataDrivenCrowdGAN", themes=["D"], year=2019, venue="preprint (Inria)",
         title="Data-Driven Crowd Simulation with Generative Adversarial Networks",
         authors=["Javad Amirian", "Wouter van Toll", "Jean-Bernard Hayet", "Julien Pettré"],
         source="preprint", source_id="", verified=True,
         contribution="用 GAN 从真实轨迹数据学习人群运动，实现数据驱动的人群仿真。",
         borrow="数据驱动标定的思路可迁移到本项目：用实测流量标定吸引力与成本敏感度参数。",
         limitation="需要大规模微观轨迹数据；微观个体级仿真。"),

    dict(id="Wang2024_CrowdEgress", themes=["D"], year=2024, venue="preprint",
         title="CrowdEgress: A Multi-Agent Simulation Platform for Pedestrian Crowd",
         authors=["Peng Wang", "Xiaoda Wang", "Peter Luh", "Neal Olderman", "Christian Wilkie",
                  "Timo Korhonen"], source="preprint", source_id="", verified=True,
         contribution="用于研究复杂人群行为的多主体行人仿真平台（含疏散场景）。",
         borrow="**平台架构对照**：作为已有的人群仿真平台，其功能边界可用于说明本项目的差异化（闭环人机交互 + 聚合建模）。",
         limitation="个体多主体平台，非参与式实验环境。"),

    dict(id="Zaitsev2023_Cormas", themes=["D"], year=2023, venue="preprint",
         title="Cormas: A multi-agent simulation platform for natural resource management (companion modelling)",
         authors=["V. Zaitsev et al."], source="preprint", source_id="", verified=False,
         contribution="Cormas 多主体仿真平台，长期用于参与式/陪伴建模（companion modelling）。",
         borrow="**参与式仿真平台的老牌代表**：其'利益相关者参与建模'传统可为本项目的参与式流程设计提供经验。",
         limitation="PDF 元数据抽取失败，标题/作者待核验。属自然资源管理领域，无空间人流存量-流量。"),

    dict(id="Wang2021_DigitalTwinIntersection", themes=["D"], year=2021, venue="preprint",
         title="Digital twin of an urban intersection for traffic/pedestrian simulation",
         authors=["et al."], source="preprint", source_id="", verified=False,
         contribution="城市交叉口数字孪生的仿真应用（待核验）。",
         borrow="数字孪生路线的对照案例。",
         limitation="PDF 元数据抽取失败，标题/作者待核验。"),

    dict(id="Xu2024_GenAIUrbanDigitalTwins", themes=["D", "C"], year=2024, venue="preprint",
         title="Leveraging Generative AI for Urban Digital Twins: A Scoping Review on the Autonomous Generation of Urban Data, Scenarios, Designs, and 3D City Models",
         authors=["Haowen Xu", "Femi Omitaomu", "Soheil Sabri", "et al."], source="preprint",
         source_id="", verified=True,
         contribution="综述生成式 AI 在城市数字孪生中的应用（数据、情景、设计、3D 模型的自动生成）。",
         borrow="提供'生成式 AI × 城市数字孪生'的文献全景，用于定位本项目在数字孪生谱系中的位置与差异。",
         limitation="综述，非方法创新；面向数字孪生数据生成，非人流流量建模。"),

    dict(id="Qiu2025_LockInHypothesis", themes=["A", "C"], year=2025, venue="preprint",
         title="(待核验) 关于锁定假设/社会演化动力学的研究", authors=[], source="preprint",
         source_id="", verified=False,
         contribution="待核验。",
         borrow="待核验后判断相关性。",
         limitation="PDF 元数据抽取失败（EOF marker not found），标题/作者未核实，**不得引用**直至人工确认。"),

    dict(id="Fang2021_FlowAggregation", themes=["A"], year=2021, venue="preprint",
         title="(待核验) 关于流量聚合的研究", authors=[], source="preprint", source_id="", verified=False,
         contribution="待核验。",
         borrow="文件名提示与'流量聚合'相关，若确认则与本项目流量聚合层直接相关。",
         limitation="PDF 元数据抽取失败（EOF marker not found），标题/作者未核实，**不得引用**直至人工确认。"),
]

def main() -> None:
    root = ROOT
    pdf_dir = root / "docs" / "papers" / "pdf"
    notes_dir = root / "docs" / "papers" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    out = []
    seen = set()
    for e in ENTRIES:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        pdf = pdf_dir / f"{e['id']}.pdf"
        rec = dict(e)
        rec["pdf_path"] = f"docs/papers/pdf/{e['id']}.pdf"
        rec["downloaded"] = pdf.exists()
        rec["size_kb"] = round(pdf.stat().st_size / 1024, 1) if pdf.exists() else None
        rec["note_path"] = f"docs/papers/notes/{e['id']}.md"
        out.append(rec)

    (root / "docs" / "papers" / "index.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    dl = sum(1 for r in out if r["downloaded"])
    ver = sum(1 for r in out if r.get("verified"))
    print(f"index.json 写入 {len(out)} 条；PDF 已下载 {dl} 条；元数据已核实 {ver} 条")
    for r in out:
        if not r["downloaded"]:
            print("  [!] 缺少 PDF:", r["id"])
        if not r.get("verified"):
            print("  [?] 元数据未核实:", r["id"])

if __name__ == "__main__":
    main()
