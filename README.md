# 存量—流量空间建模驱动的参与式交互仿真

**面向公共空间人员流动治理的人机协同实验平台**

> Participatory Interactive Simulation Driven by Stock–Flow Spatial Modelling:
> A Human–Machine Collaborative Experimental Platform for Public-Space Pedestrian-Flow Governance
>
> 仓库代号：`SF-HITL-Sim`（Stock–Flow Human-in-the-Loop Simulation）｜当前版本：v0.1.0｜仓库：
> https://github.com/CORAX2022/SF-HITL-Sim （私有）

---

## 这是什么

一个**人在回路（human-in-the-loop）参与式仿真实验平台**，同时也是一个**用 git 管理与沉淀研究写作的
写作平台**。

它不追踪个体行人的物理运动，而是用**空间单元的存量**与**跨单元的流量**
刻画人流动态——这是系统动力学中经典的存量-流量范式。在此基础上，平台把
**真实人类被试**与**大语言模型驱动的合成智能体**放进**同一个仿真世界**，
通过同一套决策接口做轮回推演，并在闭环中同步采集被试的
**客观时序空间选择**与**主观感知偏好**。

目标用途：公共空间营建的**情景推演工具** + 行为科学的**实证数据采集装置**。

---

## 核心思路（三句话）

1. **人的空间选择本身就是流量。** 所以把真人接进存量-流量模型不需要改造模型结构，
   只需在流量合成处加一项：`f_ij = f_ij^bg + f_ij^human + f_ij^llm`。
   这让"低成本空间建模"与"引入真实决策"两个目标不再冲突。
2. **单一世界 + 同构接口。** 真人与合成智能体必须通过同一协议接入同一世界，
   否则无法干净地回答"合成体能否替代真人"。
3. **闭环产生双重产出。** 平台既推演情景，也生产可证伪的行为科学证据
   （拥挤弹性、人机一致性、揭示偏好 vs 陈述偏好）。

---

## 闭环时序

```
   ① 呈现状态 x(t)  ──►  ② 决策窗口（真人提交 / 合成体生成）
          ▲                              │
          │                              ▼
   ⑤ 采集数据  ◄──  ④ 守恒更新 x(t+1)  ◄──  ③ 聚合为流量 + 约束投影
```

---

## 写作平台（本项目的一半用途）

研究写作与代码开发共用同一套 git 历史：**写作即提交，评审即合并，里程碑即标签**。

### 论文工作区

论文正文在 [`paper/`](paper/) 内以逐章 Markdown 组织，便于小步提交、逐段评审与多人协作：

| 入口                                                     | 用途                                             |
| ------------------------------------------------------ | ---------------------------------------------- |
| [`paper/manuscript.md`](paper/manuscript.md)           | 总稿导航与章节看板（状态、字数目标、素材来源）                        |
| [`paper/sections/`](paper/sections/)                   | 00 摘要 → 08 结论，逐章文件，一章一次提交                      |
| [`paper/references.bib`](paper/references.bib)         | 真实文献条目（来源：`docs/papers/index.json`、`docs/papers2/index.json`） |
| [`paper/README.md`](paper/README.md)                   | 写作约定、导出方式（pandoc → docx/pdf）                   |

### 写作规范

| 文档                                                     | 内容                                        |
| ------------------------------------------------------ | ----------------------------------------- |
| [`docs/writing/写作工作流.md`](docs/writing/写作工作流.md)     | 分支模型、提交粒度、评审循环、图表与数据快照版本化、AI 辅助写作声明       |
| [`docs/writing/风格指南.md`](docs/writing/风格指南.md)       | 中文科技写作规范：术语、标点、数字单位、图表题注、反例→正例             |
| [`docs/writing/术语表.md`](docs/writing/术语表.md)         | 中英术语对照与本文用法（存量、流量、人在回路、人机协同……）             |
| [`docs/writing/参考文献规范.md`](docs/writing/参考文献规范.md)   | GB/T 7714—2015 格式、BibTeX 映射、文献真实性核验流程      |

### git 写作约定（最小可用版）

```powershell
# 1) 启用中文提交模板（一次性）
git config commit.template .gitmessage

# 2) 写作走分支：main 稳定，writing/* 写稿，review/* 评审快照
git switch -c writing/paper-intro
# …编辑 paper/sections/01-引言.md…
git add paper/sections/01-引言.md
git commit            # 按模板填写：docs(paper): 补写引言与文献综述初稿

# 3) 阶段稿打快照标签（写作版本 ≠ 软件版本）
git tag draft-20261019-intro
# 4) 评审通过后合回主干
git switch main
git merge --no-ff writing/paper-intro

# 5) 里程碑发布
git tag -a v0.1.0 -m "初始版本：内核、闭环、文献、写作平台"
```

分支、标签、评审清单的完整约定见 [`docs/writing/写作工作流.md`](docs/writing/写作工作流.md)，
协作与提交要求见 [`CONTRIBUTING.md`](CONTRIBUTING.md)，版本变更见
[`CHANGELOG.md`](CHANGELOG.md)，研究路线见 [`ROADMAP.md`](ROADMAP.md)。

---

## 文档地图

| 文档                                                         | 内容                                              |
| ---------------------------------------------------------- | ----------------------------------------------- |
| [`docs/model/存量-流量模型规范.md`](docs/model/存量-流量模型规范.md)       | **数学模型**：空间划分、守恒方程、三类流量驱动、容量与投影、数据字段、局限         |
| [`docs/architecture/系统架构.md`](docs/architecture/系统架构.md)   | **软件架构**：分层设计、统一决策协议、轮次生命周期、技术选型、工程风险、MVP 路径    |
| [`docs/research/研究缺口与选题论证.md`](docs/research/研究缺口与选题论证.md) | **研究定位**：四条既有脉络、三个子缺口 G1/G2/G3、预期贡献、可证伪假设 H1–H5 |
| [`docs/literature/文献综述.md`](docs/literature/文献综述.md)       | 文献综述与缺口证据                                       |
| [`docs/papers/index.json`](docs/papers/index.json)         | 文献索引 + PDF 本地路径（PDF 不入库，见下）                      |
| [`docs/papers2/index.json`](docs/papers2/index.json)       | 扩展文献池索引（含中文摘要与贡献注记）                             |
| [`docs/verify/`](docs/verify/)                             | 上游项目的部署与可运行性验证报告                                |
| [`deploy/repos/manifest.jsonl`](deploy/repos/manifest.jsonl) | 已下载的上游仓库溯源清单（stars / license / 分支 / sha256）      |
| [`paper/`](paper/)                                         | **论文写作工作区**（总稿、逐章、参考文献）                         |
| [`docs/writing/`](docs/writing/)                           | **写作规范**（工作流、风格、术语、参考文献）                        |

> **仓库体积策略**：虚拟环境（`.venv-*`）、第三方上游源码（`deploy/repos/` 下除
> `manifest.jsonl` 外）、第三方 NetLogo 模型目录与文献 PDF 均**不入库**，仅保留
> 索引、笔记与获取脚本；忽略规则见 [`.gitignore`](.gitignore)。当前提交体积约 27 MB。

---

## 上游项目（star > 100）

本项目**不重复造轮子**，而是在成熟组件之上补齐"真人 + 空间存量流量 + 合成体同场"
这一缺失组合。已纳入的上游项目：

| 项目                                                                                | Stars | 定位            | 本项目如何使用            |
| --------------------------------------------------------------------------------- | ----- | ------------- | ------------------ |
| [mesa/mesa](https://github.com/mesa/mesa)                                         | 3881  | Python ABM 框架 | 仿真内核骨架（调度、空间、数据采集） |
| [jspsych/jsPsych](https://github.com/jspsych/jsPsych)                             | 1226  | 浏览器行为实验       | 被试端空间选择与量表呈现、精确计时  |
| [oTree-org/oTree](https://github.com/oTree-org/oTree)                             | 530   | 多人/问卷实验框架     | 房间与多轮同步、被试支付与问卷范式  |
| [JuliaDynamics/Agents.jl](https://github.com/JuliaDynamics/Agents.jl)             | 919   | Julia ABM 框架  | 备选高性能内核 / 空间建模参考   |
| [tsinghua-fib-lab/AgentSociety](https://github.com/tsinghua-fib-lab/AgentSociety) | 1338  | LLM 社会仿真平台    | 合成智能体的记忆与 LLM 编排参考 |
| [eclipse-sumo/sumo](https://github.com/eclipse-sumo/sumo)                         | 4221  | 交通/行人仿真       | 场景数据格式与标定参考；多尺度接驳  |
| [cityflow-project/CityFlow](https://github.com/cityflow-project/CityFlow)         | 1029  | 城市交通 RL 环境    | 对照组：精细 vs 聚合的误差量化  |
| [a-b-street/abstreet](https://github.com/a-b-street/abstreet)                     | 8188  | 城市交通规划仿真      | 规划情景概念与可视化参考       |
| [open-cogsci/OpenSesame](https://github.com/open-cogsci/OpenSesame)               | 281   | 图形化实验构建器      | 主观感知量表实验设计参考       |

> **重要**：SUMO / CityFlow / AB Street 是**对照与接驳**对象，**不是**本平台的运行内核——
> 它们正是本范式要"以聚合建模降低复杂度替代"的精细仿真路线。

### 🎉 已发现本机自带 SUMO 1.27.0（可直接使用）

验证过程中发现**本机已安装 SUMO 1.27.0 预编译二进制**（`F:\SUMO\`），
且构建特性包含 **JuPedSim（行人动力学）**——这对"人流"研究尤为关键。

已完成**完整端到端验证**：建网 → 仿真 → 统计输出 + `sumolib` 读取路网。详见
[`docs/verify/lane-d-sumo-cityflow-abstreet.md`](docs/verify/lane-d-sumo-cityflow-abstreet.md)。

配套交付了**路网转换器**，把 SUMO 路网直接转为本项目的空间单元场景：

```powershell
pip install sumolib
py -3.13 scripts\sumo_to_units.py <net.xml> -o configs\scenarios\from_sumo.json
```

映射关系（已实测打通 转换 → 内核加载 → 仿真运行）：

| SUMO 概念                 | 本项目概念                    |
| ----------------------- | ------------------------ |
| `edge`                  | 空间单元 `u_i`               |
| `edge from/to`          | 有向邻接 `(i,j) ∈ E`         |
| `edge.length` / `speed` | 通行成本 `c_ij`              |
| `edge.numLanes`         | 容量 `C_i` 的物理代理           |
| **`taz`（交通分析小区）**       | **空间单元**（语义直接对应）         |
| 网络边界节点                  | 自动判定 `entry` / `exit` 单元 |

> ⚠️ **许可证**：SUMO 为 **EPL-2.0（弱 copyleft）**，是几个上游项目中唯一对
> 成果转化构成实质约束的依赖。建议**仅作对照/标定用途**，不嵌入交付物。

---

## 目录结构

```
SF-HITL-Sim/
├─ README.md
├─ CHANGELOG.md  ROADMAP.md  CONTRIBUTING.md  CITATION.cff
├─ .gitignore  .gitattributes  .editorconfig  .gitmessage
├─ paper/                     论文写作工作区
│  ├─ README.md               写作约定与导出方式
│  ├─ manuscript.md           总稿导航与章节看板
│  ├─ sections/               00 摘要 → 08 结论（逐章文件）
│  ├─ references.bib          真实文献条目
│  ├─ figures/  tables/       图表说明与命名规范
├─ docs/
│  ├─ writing/                写作工作流 / 风格指南 / 术语表 / 参考文献规范
│  ├─ model/                  数学模型规范
│  ├─ architecture/           软件架构设计
│  ├─ research/               研究缺口与选题论证
│  ├─ literature/             文献综述
│  ├─ papers/  papers2/       文献索引、逐篇笔记（PDF 不入库）
│  ├─ verify/                 上游项目部署验证报告
│  ├─ repos-survey/           上游仓库调研（含采集原始清单）
│  ├─ tooling/                可用项目、快速启动清单、许可证风险
│  ├─ nlogo/                  外部 NetLogo 模型复现报告
│  └─ obsidian/               文献→笔记转换报告
├─ deploy/repos/manifest.jsonl  上游仓库溯源清单（源码不入库）
├─ src/
│  ├─ core/                   存量-流量内核（空间图 / 流量 / 守恒推进）
│  └─ actors.py               决策者：人类 / LLM 合成体 / 规则背景体
├─ examples/run_loop.py       闭环演示 + 守恒性验证（可运行）
├─ tests/test_core.py         24 项单元测试（全部通过）
├─ configs/scenarios/         场景定义：单元、邻接、容量、吸引力
├─ data/demo/                 闭环演示输出
├─ results/repro/             NetLogo 复现图表与播放器
├─ _nlogo_run/                NetLogo 复现运行产物（模型副本与统计表）
└─ scripts/                   获取、转换、索引、复现与审计脚本
```

---

## 环境与网络说明（重要）

本机环境的两个约束已诊断清楚，后续开发者**不必重复试错**：

### 1. GitHub 可达性：依赖本机加速器

`github.com` / `api.github.com` 在 hosts 中被解析到 `127.0.0.1`，由本机的
**Steam++（Watt Toolkit）加速器**在 `127.0.0.1:443` 做本地转发与证书代签。
**加速器运行时**，`git clone/https`、`gh api` 与 REST API 均可正常使用
（本仓库即通过该通道创建并推送）。

- ✅ 保持 Steam++ 运行即可直连 GitHub（当前实测状态）
- 🔁 若关闭加速器：改用 `https://gh-proxy.com` 通道（本仓库已固化代理凭据）
  或恢复系统 DNS
- 🧰 现成工具：[`scripts/gh-fetch.ps1`](scripts/gh-fetch.ps1)（仓库存在性校验 → 归档下载
  → zip 完整性校验 → 解压 → 追加 `manifest.jsonl`，幂等可重复执行）

```powershell
# 下载仓库默认分支源码到 deploy/repos/<name>（加速器不可用时使用）
pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "mesa/mesa" -DestDir ".\deploy\repos"
```

已固化的本地 git 配置（本仓库已设置）：`core.quotepath=false`（中文路径不转义显示）、
`core.longpaths=true`、`i18n.commitEncoding=utf-8`、`i18n.logOutputEncoding=utf-8`。

### 2. 工具链现状

| 工具                | 状态                  | 说明                                              |
| ----------------- | ------------------- | ----------------------------------------------- |
| Python            | ✅ `py -3.13` / `uv` | 裸 `python` 是 WindowsApps 占位存根，**不可用**           |
| Node.js           | ✅ v24.15.0 + pnpm   |                                                 |
| PyPI              | ✅                   | 建议 `-i https://mirrors.aliyun.com/pypi/simple/` |
| npm               | ✅                   | 建议 `--registry=https://registry.npmmirror.com`  |
| arXiv             | ✅ 直连                | 文献下载主通道                                         |
| **C/C++ 编译器**     | ❌ 无                 | 无 MSVC / gcc / clang                            |
| **cmake / ninja** | ❌ 无                 |                                                 |
| **Rust (cargo)**  | ❌ 无                 |                                                 |
| **Julia**         | ❌ 无                 | Agents.jl 运行验证受限                                |
| **conda**         | ❌ 无                 |                                                 |
| Docker            | ❓ 未确认               | 影响 AgentSociety 等重型依赖                           |
| 磁盘                | ⚠️ F: 空间紧张          | 注意上游大仓库（如 abstreet）                             |

**直接后果**：需要编译的引擎（SUMO 源码、CityFlow、AB Street）在本机**无法构建**，
只能做静态分析 + 库层面验证。各 Lane 的验证报告如实记录了这一点，
并给出在有编译环境的机器上完成构建的确切命令。

其他不可达的服务（已确认连接失败，勿依赖）：
`api.semanticscholar.org`、`api.crossref.org`、`api.openalex.org`、`cloudflare-dns.com`。
文献检索请用 arXiv + `web_search` / `web_fetch`。

---

## 当前进度

### 已完成并经过实证验证

| 阶段                 | 状态             | 证据                                                                                             |
| ------------------ | -------------- | ---------------------------------------------------------------------------------------------- |
| 仓库初始化与写作平台         | ✅ 完成           | 本仓库（git 语义化提交历史 + `paper/` + `docs/writing/`）                                              |
| 数学模型规范             | ✅ 完成           | [`docs/model/存量-流量模型规范.md`](docs/model/存量-流量模型规范.md)                                           |
| 软件架构设计             | ✅ 完成           | [`docs/architecture/系统架构.md`](docs/architecture/系统架构.md)                                       |
| 研究缺口论证             | ✅ 完成           | [`docs/research/研究缺口与选题论证.md`](docs/research/研究缺口与选题论证.md)                                     |
| **存量-流量仿真内核**      | ✅ **实现并测试通过**  | [`src/core/`](src/core/) — **24/24 单元测试通过**                                                    |
| **闭环演示（含人类决策注入）**  | ✅ **运行通过**     | `py -3.13 examples/run_loop.py` — 三条件守恒检验全部 PASS                                               |
| 文献下载与索引            | ✅ 完成           | **28 篇 PDF** + `docs/papers/index.json`（21 篇元数据经 PDF 正文核实）                                     |
| 扩展文献池              | ✅ 完成           | `docs/papers2/`（索引 + 逐篇笔记 + 中文摘要）                                                              |
| 文献综述与缺口证据          | ✅ 完成           | [`docs/literature/文献综述.md`](docs/literature/文献综述.md)                                           |
| Mesa 仿真内核验证        | ✅ 运行验证通过       | [`docs/verify/lane-b-mesa-agentsjl.md`](docs/verify/lane-b-mesa-agentsjl.md)                   |
| oTree 实验平台验证       | ✅ 端到端验证通过      | [`docs/verify/lane-a-otree-jspsych.md`](docs/verify/lane-a-otree-jspsych.md)                   |
| jsPsych 验证         | ✅ 构建 + 测试通过    | 同上（59/59 构建、740 测试通过）                                                                          |
| **SUMO 1.27.0 验证** | ✅ **完整仿真跑通**   | [`docs/verify/lane-d-sumo-cityflow-abstreet.md`](docs/verify/lane-d-sumo-cityflow-abstreet.md) |
| **SUMO → 本项目场景转换** | ✅ **全链路打通**    | [`scripts/sumo_to_units.py`](scripts/sumo_to_units.py)                                         |
| AgentSociety 评估    | ✅ 安装 + 源码级缺口核查 | [`docs/verify/lane-c-agentsociety.md`](docs/verify/lane-c-agentsociety.md)                     |
| 上游仓库下载             | ✅ 8 个仓库落盘      | `deploy/repos/` + `manifest.jsonl`                                                             |
| 论文写作脚手架            | ✅ 完成           | [`paper/manuscript.md`](paper/manuscript.md) + 9 个章节文件                                          |

### 关键实证结果（可复现）

**内核守恒性**（`examples/run_loop.py`，200 轮 × 3 种条件）：

```
[A-pure-background] 守恒检验 PASS | 最大总量漂移=9.734e-13 | 最小存量=0.000e+00
[B-human-injected]  守恒检验 PASS | 最大总量漂移=1.233e-12 | 最小存量=0.000e+00
[C-mixed]           守恒检验 PASS | 最大总量漂移=8.740e-13 | 最小存量=0.000e+00
=== 总体判定: ALL PASS ===
```

**闭环有效性**（注入 20 名"人类被试"后相对无人条件的存量变化）：

| 单元            | 无人     | 有人     | 变化率        |
| ------------- | ------ | ------ | ---------- |
| fountain（喷泉）  | 124.88 | 228.23 | **+82.8%** |
| corr_ne（东北通道） | 36.00  | 94.10  | +161.4%    |
| exit_e（出口）    | 172.40 | 83.36  | −51.6%     |

→ 人的空间选择作为外生流量输入**确实改变了系统演化**，闭环成立。

### 待完成

| 阶段                        | 状态                                                                 |
| ------------------------- | ------------------------------------------------------------------ |
| 论文正文写作                    | ⏳ 脚手架就绪；`paper/sections/` 仅引言与综述为初稿，其余为提纲                              |
| 阶段 2：LLM 合成智能体接入          | ⬜ 待启动（实现 `LLMAgent`，接入统一决策协议）                                     |
| 阶段 3：真人被试实验              | ⬜ 待启动（jsPsych 前端 + oTree 式轮次骨架）                                   |
| 阶段 4：混合实验与人机一致性          | ⬜ 待启动                                                              |
| AgentSociety 全量源码（362 MB） | ⏳ 已获取元数据 + 核心文件 + 完成 PyPI 安装；全量源码树受体积与镜像带宽限制未落盘                    |
| CityFlow 源码构建             | ⏳ 源码已落盘；**本机无 MSVC/CMake 无法编译**，无 PyPI wheel；已给出具编译环境时的确切命令        |
| AB Street                 | ⏳ 仅元数据（仓库过大）；**本机无 cargo 无法编译**；已确认 Apache-2.0 与 Rust workspace 结构 |
| SUMO pip wheel（150 MB）    | ✅ **不需要**——本机已有 SUMO 1.27.0，仅装 `sumolib`+`traci`（各 ~140 KB）即可      |
| 真人实验与伦理审查                 | ⬜ 待启动                                                              |
| 中文文献（CNKI/Wanfang）补检      | ⏳ 已有中文文献池；系统性补检仍待启动                                                |

详见 [`docs/verify/`](docs/verify/) 各 Lane 验证报告。

### 下一步（按架构文档 §8 的最短路径）

1. **阶段 2｜接入合成智能体**：实现 `LLMAgent`，按统一决策协议产出选择
   （可直接复用 AgentSociety / Park2024 的 persona 构造方法）。
2. **阶段 3｜接入真人被试**：以 jsPsych 前端 + oTree 式轮次骨架接
   [`src/core/kernel.py`](src/core/kernel.py) 的 `state_snapshot()` 与 `step()`。
3. **阶段 4｜混合实验**：混合比例扫描 + 人机一致性分析。
4. **阶段 5｜情景推演**：多方案对比，输出决策支撑报告。

### 快速上手（已验证可运行）

```powershell
# 运行单元测试（24 项）
py -3.13 tests\test_core.py

# 运行闭环演示（200 轮 × 3 条件，含守恒性验证）
py -3.13 examples\run_loop.py

# 重新生成文献索引与笔记
py -3.13 scripts\build_paper_index.py
py -3.13 scripts\build_paper_notes.py

# 提交前启用中文提交模板
git config commit.template .gitmessage
```

---

## 附：NetLogo 外部模型运行与复现

本目录纳入了第三方模型
`an-agent-based-simulation-model-of-pedestrian-evacuation-based-on-bayesian-nash-equilibrium_v1.0.0`
（University of Leeds，CC BY-SA 4.0）——**基于贝叶斯纳什均衡的隧道行人疏散 ABM**。
该第三方模型目录（约 62 MB）与原始结果 **不入库**，按下方复现流程单独获取；
本仓库仅保留复现产物（`_nlogo_run/`、`results/repro/`）。

| 项目 | 结果 |
| --- | --- |
| 运行环境 | NetLogo **7.0.4**（模型由 6.2.2 生成，7.0.4 可直接加载） |
| 复现规模 | `experiment1-3patterns`，150 次运行（3 模式 × 50 重复），18,023 行 |
| 耗时 | 37.8 秒（单次 2000 人约 5 秒） |
| 保真度 | 出口时间相对偏差 −2.9% ~ −6.6%，SD 差 ≤1.4 |

**核心结论已复现**：出口时间 **BNE < Random follow < Shortest route**
（作者 58 / 129 / 192 步；复现 56 / 122 / 179 步），且 BNE 峰值密度最低。

| 产物 | 路径 |
| --- | --- |
| 运行脚本 | [`scripts/run-nlogo.ps1`](scripts/run-nlogo.ps1) |
| 完整报告 | [`docs/nlogo/NetLogo模型运行与复现报告.md`](docs/nlogo/NetLogo模型运行与复现报告.md) |
| 统计对比 | [`scripts/compare_nlogo_repro.py`](scripts/compare_nlogo_repro.py) |
| 绘图脚本 | [`scripts/plot_nlogo_repro.py`](scripts/plot_nlogo_repro.py) |
| 对比图 | `results/repro/fig1..fig4*.png` |

```powershell
# 完整复现（150 runs，约 38 秒）
pwsh -NoProfile -File ".\scripts\run-nlogo.ps1" `
  -Model ".\_nlogo_run\repro_ex1.nlogo" -Experiment "repro_experiment1" `
  -Table ".\_nlogo_run\repro_experiment1.csv"
py -3.13 scripts\compare_nlogo_repro.py
py -3.13 scripts\plot_nlogo_repro.py
```

> ⚠️ **两个已实测的环境坑**（详见报告 §1）：
>
> 1. `netlogo-headless.bat` 用 `FOR %%a IN (%*)` 逐词展开参数，
>    遇到含空格的路径（本工程路径含空格）会拆词并报
>    `ClassNotFoundException`；
> 2. 该 `.bat` 优先用 `JAVA_HOME`/PATH 上的 Java，而本机 PATH 上是 **Java 8**，
>    而 NetLogo 7 需要 **Java 17+**。
>
> **解决**：直接调用入口类 `org.nlogo.headless.Main`，并强制使用 NetLogo
> **自带的** `runtime\bin\java.exe`（Java 17），见 `scripts/run-nlogo.ps1`。

---

## 伦理与合规

- 涉及**真人被试**，实验前须完成**伦理审查**与**知情同意**。
- 数据采集遵循匿名化原则：仅存匿名 ID 与聚合量，不存可识别个人信息。
- 上游项目许可证需逐仓库核对（见 `docs/verify/` 各报告），
  避免 AGPL 等传染性许可证影响成果转化。
- 本项目**暂未声明开源许可证**；文献 PDF 与第三方源码/模型按各自许可证单独管理，不入库。

---

## 引用

引用元数据见 [`CITATION.cff`](CITATION.cff)。论文发表前请引用本仓库；论文发表后请引用论文。

本项目立场：**在既有成熟组件之上，补齐"真人 + 存量-流量空间 + 合成智能体同场"
这一缺失组合**，而不是从零重写仿真框架。
