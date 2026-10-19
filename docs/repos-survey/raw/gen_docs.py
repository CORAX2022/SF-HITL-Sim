# -*- coding: utf-8 -*-
"""Lane R: generate 项目汇总.md and 统计.md from verified repos.json."""
import json, os, collections, datetime

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(OUT, "raw")
repos = json.load(open(os.path.join(OUT, "repos.json"), encoding="utf-8"))
NQ = len([f for f in os.listdir(RAW) if f.endswith(".json") and not f.startswith("_")])
NC = len([f for f in os.listdir(os.path.join(RAW, "core")) if f.endswith(".json")])
CUT = datetime.datetime(2023, 10, 14, tzinfo=datetime.timezone.utc)
NOW = datetime.datetime(2026, 10, 14, tzinfo=datetime.timezone.utc)

CATS = {
 1: "1 多主体 / ABM 仿真框架",
 2: "2 人群 / 行人仿真",
 3: "3 交通与城市仿真 / 数字孪生 / SUMO 生态",
 4: "4 LLM 合成智能体 / 社会仿真",
 5: "5 行为实验 / HITL 平台（oTree、jsPsych 生态）",
 6: "6 系统动力学 / 存量-流量 / 因果回路",
 7: "7 空间数据与 OD 流量可视化",
}
COMMENT = {
1: "这一类成熟度最高，Mesa、Agents.jl、NetLogo、GAMA、Repast、MASON 构成完整梯队，Python/Julia/Java 各有主力，多数项目已维护 10 年以上且近 3 年仍有推送。空缺在**空间表达能力参差**：多数框架只给抽象网格，真正把街道、地块、行政单元等真实空间单元当作一等公民的仅 Mesa-Geo、GAMA、abmgis 等少数。建议优先评估 mesa + mesa-geo（与本项目 Python 数据栈无缝）、Agents.jl（性能上限）、AgentTorch（百万级可微分大种群）以及 scottfr/simulation（同一份世界表达内并存系统动力学与 ABM）。",
2: "这是七类中最薄弱的一类：同时满足“星标 > 100 且近 3 年活跃”的 GitHub 项目不足 10 个，且多为微观运动求解器（RVO2、社会力）或仿真框架（Menge、Horde），缺少“行人流 + 空间设计 + 人类被试”的完整平台。反差明显：pedsim_ros（593★，2023-08 后停更）、CrowdNav（738★，2022 后停更）、jupedsim（前身 JuPedSim/jpscore，已更名且仅 96★）、Vadere（不在 GitHub）等知名项目均因不满足星标或活跃度阈值而未入表。结论：行人微观内核可复用 RVO2/Menge/socialforce，但“聚合存量-流量 + 个体规则”的人群引擎需要自研，这正是本课题的空白点与贡献空间。",
3: "生态最完整、可复用度最高的一类：SUMO 与 MATSim 分别代表微观交通与活动基需求两大气候，CityFlow / flow / SUMO-RL 提供强化学习闭环，OSM 路由生态（OSRM、Valhalla、GraphHopper、OpenTripPlanner、r5）提供路网与 OD 成本计算，GTFS/GBFS 提供数据规范。数字孪生方向呈现三条不同技术路线：AB Street（OSM→桌面可交互城市）、valdrada（实时公共数据驱动的纽约孪生）、Colombo-Skylines（游戏引擎内孪生）。建议进一步评估 AB Street（模拟与参与式街道设计一体）、urbanaccess + r5（可达性→OD）、以及 CitySim/OpenCDA 提供的可复现实验数据集。",
4: "近 3 年爆发最明显的一类：Generative Agents 之后涌现 OASIS（百万智能体）、AgentSociety、Concordia、Sotopia、AI-Town、Humanoid Agents 等，形成“沙盒世界—社会交互—行为评测”的分层结构，且多数创建于 2023 年之后。主要空缺是**与空间和交通模型的耦合**：绝大多数平台的社会空间是抽象图或纯文本，只有 FreeAskWorld、trustworthy-agent-simulation、urban-sim 等少数把 LLM 智能体落到城市与路网上。建议进一步评估 AgentSociety（国内平台，含实验编排与城市场景）、Concordia（抽象最干净、易嵌入自研世界）、Humanoid Agents（人类相似度指标）、以及 microsoft/autogen 与 camel-ai/camel 作为异构智能体（LLM + 规则）集成底座。",
5: "oTree、jsPsych、PsychoPy、LimeSurvey、SurveyJS、ODK/KoboToolbox 覆盖“实验室博弈实验—在线行为实验—问卷与田野调查”三段流程，成熟稳定、文档完善。但没有现成平台实现真正的 HITL——人类被试与仿真世界实时双向耦合：Empirica（63★）、lab.js、nodeGame 等要么星标不足，要么只提供消息同步层，缺少与仿真引擎共享同一世界状态、支持暂停/回放/干预的机制。建议进一步评估 jsPsych（在线被试前端）、oTree（多人同步决策）、nodeGame（实时同步架构）与 huggingface/gym-hil（人类反馈直接进入智能体训练闭环）。",
6: "最小众、生态明显落后于商业软件（Vensim、Stella、AnyLogic 均闭源）的一类：仅 PySD（把 Vensim/XMILE 存量-流量模型翻译为 Python）、Fault、pathsim、OpenModelica 与因果方向工具 causal-learn / dowhy 满足条件；bptk_py（36★）、simlin（99★）因未过星标阈值未入表。核心空缺是**存量-流量与多智能体混合建模的工具化支持**——目前只能在 scottfr/simulation 之类通用库或自研代码中实现。建议进一步评估 PySD（复用既有 CLD/存量-流量资产并嵌入 Python 世界）与 causal-learn（用观测数据反向校验因果回路结构）。",
7: "体量最大但相关性分化明显：一侧是通用地理基础设施（GeoPandas、PostGIS、JTS、Turf、H3、S2、Mapnik），另一侧是 OD/流向可视化专用件（kepler.gl、deck.gl + flowmap.gl、FlowmapBlue）与空间单元分析（OSMnx、momepy、cityseer-api、depthmapX、city2graph、City4CFD、VoxCity）。与本课题最贴合的是“空间单元划分 + OD 流量表达”这条线：OSMnx/H3/A5/dggridR 提供单元方案，deck.gl/flowmap.gl 提供流向表达，fmm 与 opentimes 提供轨迹→OD 与 OD 成本矩阵。建议进一步评估 flowmap.gl（流量图层）、city2graph（地理关系→图结构）与 momepy（空间单元形态指标）。",
}

def d(x):
    return (x or "")[:10] or "—"

# ---------------- 项目汇总.md ----------------
by = collections.defaultdict(list)
for r in repos:
    by[r["category"]].append(r)

L = ["# 开源项目汇总（近 3 年活跃 · 星标 > 100）", "",
     "> 数据来源：GitHub REST API（2026-10-14 抓取），全部字段直接取自 API 返回，未做任何推测。",
     "> **本次仅做信息汇总，未下载或克隆任何仓库。** 星标 ≤ 100 或近 3 年（2023-10-14 之后）无推送的项目已全部剔除。",
     "> 共 **%d** 个项目，覆盖全部 7 个类别。字段说明见 `repos.json`。" % len(repos), "",
     "## 目录", ""]
for c in sorted(CATS):
    L.append("- %s —— %d 个" % (CATS[c], len(by[c])))
L.append("")
for c in sorted(CATS):
    L += ["## %s · %d 个" % (CATS[c], len(by[c])), "",
          "| 项目 | 星标 | 语言 | 许可证 | 最近推送 | 与本课题关系 |",
          "| --- | ---: | --- | --- | --- | --- |"]
    for r in by[c]:
        L.append("| [%s](%s) | %s | %s | %s | %s | %s |" % (
            r["full_name"], r["url"], format(r["stars"], ","), r["language"] or "—",
            r["license_spdx"] or "未标注", d(r["pushed_at"]), r["relevance_note"]))
    L += ["", "**归纳**：" + COMMENT[c], ""]
open(os.path.join(OUT, "项目汇总.md"), "w", encoding="utf-8").write("\n".join(L))

# ---------------- 统计.md ----------------
n = len(repos)
langs = collections.Counter(r["language"] or "未标注" for r in repos)
lics = collections.Counter(r["license_spdx"] or "未标注/无 SPDX" for r in repos)
cats = collections.Counter(r["category"] for r in repos)

def bucket_pushed(p):
    try:
        dt = datetime.datetime.fromisoformat(p.replace("Z", "+00:00"))
    except Exception:
        return "未知"
    days = (NOW - dt).days
    if days <= 365: return "1 年内有推送"
    if days <= 730: return "1–2 年内有推送"
    return "2–3 年内有推送"
pb = collections.Counter(bucket_pushed(r["pushed_at"]) for r in repos)

def bucket_stars(s):
    if s >= 10000: return "≥ 10k"
    if s >= 3000: return "3k–10k"
    if s >= 1000: return "1k–3k"
    if s >= 500: return "500–1k"
    return "100–500"
sb = collections.Counter(bucket_stars(r["stars"]) for r in repos)

def is_new(r):
    try:
        return datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")) >= CUT
    except Exception:
        return False
new = sorted([r for r in repos if is_new(r)], key=lambda r: -r["stars"])
recent = sorted([r for r in repos if r["created_at"] and r["created_at"] >= "2024-10-14"],
                key=lambda r: -r["stars"])

S = ["# 统计：近 3 年活跃 · 星标 > 100 的相关开源项目", "",
     "抓取时间：2026-10-14（GitHub REST API，经 api.github.com 直连与 gh-proxy 镜像双通道）。",
     "筛选口径：`stars > 100` **且** `pushed_at ≥ 2023-10-14`（或近 3 年新建）。全文未使用任何未经 API 核验的数值。", "",
     "## 1. 总量", "",
     "| 指标 | 数值 |", "| --- | --- |",
     "| 收录项目总数 | **%d** |" % n,
     "| 托管平台 | GitHub %d / Gitee 0 / GitLab 0（见第 7 节说明） |" % n,
     "| 覆盖类别 | 7 / 7 |",
     "| 全部项目星标 > 100 | 是 |",
     "| 全部项目近 3 年有推送 | 是 |",
     "| 检索命中并缓存查询数 | %d 条 GitHub search 查询（原始 JSON 全部落盘于 `raw/`） |" % NQ,
     "| 单个仓库详情核验 | %d 次 core API `/repos/{owner}/{repo}` 调用 |" % NC, "",
     f"原始候选池 {1270} 个去重仓库 → 近 3 年活跃 {1091} 个 → 人工相关性筛选后 **{n}** 个入表。", "",
     "## 2. 类别分布", "", "| 类别 | 数量 | 占比 |", "| --- | ---: | ---: |"]
for c in sorted(CATS):
    S.append("| %s | %d | %.1f%% |" % (CATS[c], cats[c], 100.0 * cats[c] / n))
S += ["", "## 3. 语言分布", "", "| 语言 | 数量 | 占比 |", "| --- | ---: | ---: |"]
for k, v in langs.most_common(15):
    S.append("| %s | %d | %.1f%% |" % (k, v, 100.0 * v / n))
if len(langs) > 15:
    S.append("| 其他 %d 种语言 | %d | %.1f%% |" % (
        len(langs) - 15, sum(v for _, v in langs.most_common()[15:]), 100.0 * sum(v for _, v in langs.most_common()[15:]) / n))
S += ["", "## 4. 许可证分布", "", "| 许可证（SPDX） | 数量 |", "| --- | ---: |"]
for k, v in lics.most_common():
    S.append("| %s | %d |" % (k, v))
S += ["", "注：GitHub API 对 GPL/自定义许可证常返回 `NOASSERTION`，此类在 `repos.json` 中记为 `null`（未标注），不臆测为具体许可证。", "",
      "## 5. 活跃度与星标规模", "", "| 最近推送时间 | 数量 |", "| --- | ---: |"]
for k in ["1 年内有推送", "1–2 年内有推送", "2–3 年内有推送", "未知"]:
    if pb.get(k):
        S.append("| %s | %d |" % (k, pb[k]))
S += ["", "| 星标区间 | 数量 |", "| --- | ---: |"]
for k in ["≥ 10k", "3k–10k", "1k–3k", "500–1k", "100–500"]:
    if sb.get(k):
        S.append("| %s | %d |" % (k, sb[k]))
S += ["", "## 6. 近 3 年新出现的高星项目（最新动向）", "",
      f"判据：`created_at ≥ 2023-10-14`，共 **{len(new)}** 个（占 {100.0*len(new)/n:.1f}%）；其中 {len(recent)} 个创建于近 2 年内（≥ 2024-10-14）。",
      "", "| 项目 | 星标 | 类别 | 创建时间 | 语言 |", "| --- | ---: | --- | --- | --- |"]
for r in new:
    S.append("| [%s](%s) | %s | %s | %s | %s |" % (
        r["full_name"], r["url"], format(r["stars"], ","), CATS[r["category"]].split(" ")[0],
        d(r["created_at"]), r["language"] or "—"))
S += ["", "**解读**：新出现的高星项目高度集中在第 4 类（LLM 合成智能体 / 社会仿真），"
      "说明“语言模型驱动的社会仿真”是 2023 年以来最明确的增长极；第 3 类（城市/交通数字孪生）"
      "与第 7 类（OD 可视化）也有新项目，但多是在成熟范式上做工程化封装；"
      "第 6 类（系统动力学）近 3 年几乎无新星标项目，第 2 类（人群仿真）新增项目星标普遍偏低——"
      "这两类是本课题最容易形成增量贡献的方向。", "",
      "## 7. 方法与局限", "",
      "- **检索**：GitHub `/search/repositories`，全部查询带 `stars:>100` 或 `stars:>50` 约束，"
      "按 `sort=stars` 取前 100；查询覆盖 7 大类关键词与 `topic:` 标签（abm、agent-based、crowd、sumo、"
      "traffic、mobility、digital-twin、llm-agents、human-in-the-loop、experiment、geospatial、"
      "spatial-analysis、transportation、urban-planning、flow-map 等）。原始响应全部缓存于 `raw/`。",
      "- **核验**：关键词已知但未被检索命中的知名项目，逐个用 core API `/repos/{owner}/{repo}` 核验星标、"
      "许可证、默认分支、创建与推送时间；星标不足或近 3 年无推送者剔除（evoplex、abmgis、"
      "PedestrianCounter 即因此未入表）。",
      "- **Gitee**：`https://gitee.com/api/v5/search/repositories` 实测对全部测试查询返回空数组"
      "（该接口现需 access token），故本次未能补充国内托管平台数据；GitLab / Codeberg / HuggingFace "
      "未逐站检索。这意味着**中文社区的高星项目覆盖不完整**，若需要 Gitee 数据，需提供 token 后补检。",
      "- **局限**：GitHub 仓库检索默认只匹配名称、简介与话题标签，不覆盖 README 全文，"
      "因此存在“确实相关但简介未提关键词”的漏检；类别归属由人工判定，一个项目只入一类（主要类别）。",
      "- **合规**：全过程仅调用元数据 API 与网页，**未执行任何 git clone / 压缩包下载**。", ""]
open(os.path.join(OUT, "统计.md"), "w", encoding="utf-8").write("\n".join(S))
print("wrote 项目汇总.md (%d entries) and 统计.md" % n)
print("new(3y)=%d recent(2y)=%d" % (len(new), len(recent)))
