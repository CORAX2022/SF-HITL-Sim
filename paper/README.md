# 论文工作区（Paper Workspace）

> 本目录是论文的**唯一写作入口**。正文按章拆分为 Markdown 文件，由
> [`paper/manuscript.md`](manuscript.md) 统一导航，用 pandoc 合并导出；
> 修订历史由 git 承担，流程规范见
> [`docs/writing/写作工作流.md`](../docs/writing/写作工作流.md)。

---

## 1. 论文题目

**中文**：存量—流量空间建模驱动的参与式交互仿真：面向公共空间人员流动治理的人机协同实验平台

**英文**：Participatory Interactive Simulation Driven by Stock–Flow Spatial Modelling:
A Human–Machine Collaborative Experimental Platform for Public-Space Pedestrian-Flow Governance

- **短标题**（用于页眉、图表题注）：存量—流量空间建模驱动的参与式交互仿真
- **工作区版本**：v0.1.0（版本规则见 §5）
- **当前阶段**：写作脚手架已就位；摘要、引言、文献综述有可读草稿，其余章节为
  结构化提纲 + 证据锚点。**平台已完成离线验证，真人实验尚未开展。**

> 题目中的"存量—流量"使用全角破折号连接，与英文 Stock–Flow 的短横线（en dash）
> 对应；术语一致性要求见
> [`docs/writing/术语表.md`](../docs/writing/术语表.md)。

---

## 2. 目标期刊 / 会议备选

以下为**备选**，仅记录选题适配性判断；**尚无任何投稿决定，也未向任何刊物投稿**。
最终去向取决于 [`06-结果与验证.md`](sections/06-结果与验证.md) 能否补齐真人实验
（当前仅完成内核与外部模型的离线验证）。

| 备选 | 类型 | 选择理由 | 主要风险 / 待补 |
| --- | --- | --- | --- |
| 《城市规划学刊》 | 中文 · 规划学科综合 | 参与式规划与规划支持系统是本刊长期议题；本文"规划参与 + 人员流动治理"的问题意识与中文语境贴合，且采用中文写作可降低术语转换损耗 | 需强化中文规划实践文献支撑（当前文献池以英文为主）；需把方法贡献表述为规划学科可用的工具而非纯软件工程 |
| Computers, Environment and Urban Systems（CEUS） | 英文 · 空间建模与规划支持系统 | 期刊关注城市系统的计算模型、仿真与决策支持；本文"低成本空间建模 + 误差量化 + 可复现平台"的主线与其范围一致 | 需补齐聚合模型与个体模型的定量对照（假设 H4）；平台复现材料、数据与代码可得性需达到期刊要求 |
| ACM CHI / CSCW | 英文 · 人机交互 | 真人 + 合成智能体同场、"人在回路"实验平台与人机一致性是该社区的方法论议题；本文的统一决策协议与受控替换实验设计有对话空间 | 对真人被试实验、伦理审查与统计效力要求高；须先完成伦理审批与预注册式实验设计 |

> 三条备选互斥地对应三种贡献叙事（规划工具 / 空间模型 / 人机交互方法）。
> **写作时必须先定叙事主线，再决定投哪里**；混写会导致三边都不够深。

---

## 3. 章节文件索引

| 章 | 文件 | 内容一句话 | 状态 |
| --- | --- | --- | --- |
| 00 | [`sections/00-摘要与关键词.md`](sections/00-摘要与关键词.md) | 中英文摘要、关键词 | 初稿 |
| 01 | [`sections/01-引言.md`](sections/01-引言.md) | 问题、缺口、贡献、全文组织 | 初稿 |
| 02 | [`sections/02-文献综述与研究缺口.md`](sections/02-文献综述与研究缺口.md) | 四条脉络、G1–G3、H1–H5 | 初稿 |
| 03 | [`sections/03-研究框架与模型.md`](sections/03-研究框架与模型.md) | 闭环框架与存量—流量形式化 | 待写 |
| 04 | [`sections/04-平台设计与实现.md`](sections/04-平台设计与实现.md) | 分层架构、统一决策协议、内核实现 | 待写 |
| 05 | [`sections/05-实验设计与数据采集.md`](sections/05-实验设计与数据采集.md) | 被试流程、变量、量表、分析计划 | 待写 |
| 06 | [`sections/06-结果与验证.md`](sections/06-结果与验证.md) | 已有实证：单测、守恒、闭环、外部复现 | 初稿 |
| 07 | [`sections/07-讨论与局限.md`](sections/07-讨论与局限.md) | 贡献边界、效度威胁、伦理 | 待写 |
| 08 | [`sections/08-结论与展望.md`](sections/08-结论与展望.md) | 结论与后续工作 | 待写 |

配套目录：

- [`references.bib`](references.bib) — 参考文献库（BibTeX，40 条核心条目）
- [`figures/README.md`](figures/README.md) — 图表来源与命名规范
- [`tables/README.md`](tables/README.md) — 表格来源与命名规范

---

## 4. 如何把 sections 合并成稿

### 4.1 章节文件的固定结构

每个章节文件由**两段**构成：

1. **写作脚手架**（文件开头到 `<!-- ===== 正文区 ===== -->` 之前）：
   `## 本章目标`、`## 已有素材与证据锚点`、`## 待写作要点`、`## 状态` 四节。
   只服务于写作协作，**不进入导出稿**。
2. **正文区**（`<!-- BODY-START -->` 与 `<!-- BODY-END -->` 之间）：
   真正进入论文的文字。

**约定**：任何新章节文件必须沿用同一组标记，否则导出脚本会漏取正文。

### 4.2 合并与导出（PowerShell，可直接复制）

```powershell
# 0) 准备输出目录（build/ 不入库，见 .gitignore 约定）
New-Item -ItemType Directory -Force build | Out-Null

# 1) 按文件名排序抽取各章正文区
$body = foreach ($f in (Get-ChildItem paper/sections/*.md | Sort-Object Name)) {
    $lines = Get-Content -LiteralPath $f.FullName -Encoding utf8
    $start = [array]::IndexOf($lines, '<!-- BODY-START -->')
    $end   = [array]::IndexOf($lines, '<!-- BODY-END -->')
    if ($start -lt 0 -or $end -lt 0) { throw "缺少 BODY 标记：$($f.Name)" }
    $lines[($start + 1)..($end - 1)]
}
$body | Set-Content -LiteralPath build/manuscript-body.md -Encoding utf8

# 2) 合并为 DOCX（含参考文献解析与自动编号）
pandoc build/manuscript-body.md `
  -o build/manuscript.docx `
  --citeproc --bibliography=paper/references.bib `
  --resource-path=paper `
  --number-sections --toc --toc-depth=2
```

```powershell
# 3) 生成 PDF（需要 MiKTeX / TeX Live + xelatex，中文须指定字体）
pandoc build/manuscript-body.md `
  -o build/manuscript.pdf `
  --pdf-engine=xelatex `
  -V CJKmainfont="Microsoft YaHei" -V mainfont="Times New Roman" `
  --citeproc --bibliography=paper/references.bib `
  --resource-path=paper `
  --number-sections --toc
```

**依赖与前置检查**：

```powershell
pandoc --version      # 需 >= 2.11（--citeproc 自 2.11 起内置）
xelatex --version     # 仅 PDF 需要
```

**说明**：

- DOCX 路线无 LaTeX 依赖，是当前默认交付格式；PDF 路线在装有 TeX 的机器上执行。
- 若需统一字体与页边距，追加 `--reference-doc=paper/templates/reference.docx`
  （该模板**尚未创建**，属后续任务，不得在文中假定其存在）。
- 参考文献样式：默认使用 pandoc 内置样式；投中文刊时改为
  `--csl=paper/templates/gb-t-7714-2015-numeric.csl`（该 CSL 文件**尚未入库**，
  获取与放置方式见
  [`docs/writing/参考文献规范.md`](../docs/writing/参考文献规范.md)）。

### 4.3 单章预览（不导出全文）

```powershell
pandoc paper/sections/01-引言.md -o build/ch01-preview.docx --citeproc --bibliography=paper/references.bib
```

> 单章预览会把该章的写作脚手架一并导出，属预期行为；正式交付稿只走 §4.2 的正文区抽取。

---

## 5. 版本与状态约定

### 5.1 稿件状态取值

**只允许**以下四种状态，禁止自造（如"进行中""基本完成"）：

| 状态 | 含义 | 进入条件 | 退出条件 |
| --- | --- | --- | --- |
| 待写 | 仅有提纲与证据锚点，无成段正文 | 章节文件建立 | 写完第一版可通读的正文 |
| 初稿 | 有完整正文，事实与引用已核验 | 自查清单通过 → 提交 | 收到实质修改意见并开始改写 |
| 修订中 | 正在按评审意见改写 | 进入评审循环 | 意见全部处理并通过交叉评审 |
| 定稿 | 不再改动，可进入导出与投稿包 | 交叉评审通过 + Lead 确认 | 仅可因事实错误回退 |

状态记录在两处，**必须同步**：各章 `## 状态` 节、本文 §3 索引表与
[`manuscript.md`](manuscript.md) 看板。

### 5.2 版本号

- 遵循语义化版本 `vMAJOR.MINOR.PATCH`：
  - `MAJOR`：投稿/返修等对外节点；
  - `MINOR`：新增章节或结构性改写；
  - `PATCH`：文字修订、引用订正、图表更新。
- 里程碑用 git 标签 `vX.Y.Z`；写作快照用 `draft-YYYYMMDD` 标签。
  打标签的时机、命名与命令见
  [`docs/writing/写作工作流.md`](../docs/writing/写作工作流.md)。
- 当前版本：**v0.1.0**（脚手架建立）。

### 5.3 变更记录

- 稿件层面的变更以 **git 提交信息**为准（Conventional Commits 中文规范），
  **不另建**手工变更日志，避免两处不一致。
- 需要对外说明的版本变化，写入投稿信或 `CHANGELOG`（若仓库后续引入）。

---

## 6. 引用规则

1. 正文引用统一用 pandoc 语法 `[@bibkey]`，多篇写作 `[@key1; @key2]`。
2. bib key 规则：`第一作者姓年份_短标题`（如 `Baez2022_StockFlowDiagrams`），
   与 `docs/papers/index.json` 的 `id` 一致，便于机器回溯。
3. **先有证据，再写引用**：每个 `[@key]` 必须在
   [`references.bib`](references.bib) 中存在，且该条目在文献索引中有对应记录。
4. 元数据未核验的条目在 bib 文件里带 `% TODO: 待核实` 注释；**带 TODO 的条目
   可以出现在综述草稿中，但定稿前必须核实或删除**。
5. 引文格式（GB/T 7714—2015）与字段映射见
   [`docs/writing/参考文献规范.md`](../docs/writing/参考文献规范.md)。

---

## 7. references.bib 的来源与补全方式

### 7.1 当前状态

- 共 **40 条**核心条目，由两份索引去重生成：
  - `docs/papers/index.json`（28 篇，21 篇经 PDF 正文核验）；
  - `docs/papers2/index.json`（74 条，含 `abstract_zh` / `contribution_zh`）。
- 两库重复条目（CrowdEgress、Cormas、SocioVerse）取 papers2 的核验后作者表与
  预印本编号，避免 bib 内出现两个 key。
- 每条条目上方注明来源（哪份索引、是否 `verified`）与不确定字段。

### 7.2 为什么只收 40 条而不是全部 102 条

- `docs/papers2/index.json` 中大量条目是背景性检索结果，与本课题核心论证距离较远；
  先把"论证链上必须出现的文献"钉死，再按需扩展，避免 bib 成为剪贴板。
- 部分条目**元数据不足以构成可引用条目**，已排除（见 §7.4）。

### 7.3 如何补条目

```powershell
# 1) 在两份索引中定位候选条目（示例：按主题 C、2024 年之后）
py -3.13 -c "import json;[print(x['id'],x['year'],x['title']) for x in json.load(open('docs/papers2/index.json',encoding='utf-8')) if 'C' in x.get('themes',[])]"

# 2) 用脚本把索引条目转换为 BibTeX 草稿（脚本尚未提供，属后续任务）
#    转换时必须保留 source_id 与 verified 字段到 note/注释，便于复核。

# 3) 人工核验：打开 PDF（若有）核对标题、作者、年份、卷期页码，再补齐字段。
```

补条目硬性要求：

- **不得凭记忆填 DOI、卷期、页码**；索引里没有的信息，一律留空 + `% TODO: 待核实`。
- 新条目 key 不得与既有 key 冲突；同一文献在两库出现时**只保留一条**。
- 定稿前执行一次全库检查：`biber`/`pandoc --citeproc` 不报 warning，
  正文引用的每个 key 都能在 bib 里找到。

### 7.4 已排除、不可引用的条目

以下条目在 `docs/papers/index.json` 中 `verified: false` 且元数据残缺，
**当前不进入 references.bib，也不得在正文引用**：

| 索引 id | 问题 |
| --- | --- |
| `Qiu2025_LockInHypothesis` | 标题记为"(待核验)"，无作者；先在索引中补全再考虑引用 |
| `Fang2021_FlowAggregation` | 标题记为"(待核验)"，无作者 |
| `Wang2021_DigitalTwinIntersection` | 作者记为"et al."，无标题、无标识符 |

另有三条 **metadata_verified: false 但元数据基本完整**的条目
（`Feygin2019_BISTRO`、`Park2023_GenerativeAgents`、`Piao2025_AgentSociety`）
已收入 bib，但条目上方有 `% TODO: 待核实` 注释；**引用前必须打开 PDF 首页复核**。

---

## 8. 素材来源总表（写作时先去这里拿证据）

| 素材 | 路径 | 能用做什么 |
| --- | --- | --- |
| 数学模型 | [`docs/model/存量-流量模型规范.md`](../docs/model/存量-流量模型规范.md) | 形式化定义、守恒方程、三类流量驱动、约束投影、模型局限 |
| 软件架构 | [`docs/architecture/系统架构.md`](../docs/architecture/系统架构.md) | 分层、统一决策协议、轮次生命周期、技术选型、MVP 路径 |
| 研究缺口 | [`docs/research/研究缺口与选题论证.md`](../docs/research/研究缺口与选题论证.md) | G1/G2/G3、贡献论证、H1–H5 |
| 文献综述 | [`docs/literature/文献综述.md`](../docs/literature/文献综述.md) | 四线综述、能力矩阵、先行工作增量表、语料局限声明 |
| 文献索引 | [`docs/papers/index.json`](../docs/papers/index.json)、[`docs/papers2/index.json`](../docs/papers2/index.json) | 引用的机器可读来源 |
| 内核实现 | [`src/core/`](../src/core/)、[`src/actors.py`](../src/actors.py) | 实现细节、接口、同构性论证 |
| 单元测试 | [`tests/test_core.py`](../tests/test_core.py) | 24 项测试，守恒/投影/阻挡/闭环 |
| 闭环演示 | [`examples/run_loop.py`](../examples/run_loop.py) | A/B/C 三条件、守恒检验、人类注入效应 |
| 演示输出 | `data/demo/loop_demo_summary.json`、`data/demo/stock_trajectories.csv` | 结果章的一切数值来源 |
| 外部模型复现 | [`docs/nlogo/NetLogo模型运行与复现报告.md`](../docs/nlogo/NetLogo模型运行与复现报告.md) | 150 runs、出口时间对照、保真度与复现边界 |
| 复现图 | `results/repro/fig1..fig4*.png`、`results/repro/nlogo_播放器.html` | 结果章图件（用法见 `figures/README.md`） |
| 上游验证 | [`docs/verify/`](../docs/verify/) | 依赖可行性、许可证与构建限制 |

> **铁律**：正文出现的任何数字，都必须能在这张表里指到文件；
> 文件里没有的数字，一律不写。

---

## 9. 当前不写的内容（避免虚构）

- 真人被试实验数据：**尚未开展**（伦理审查未完成），任何"被试表现""显著性"
  表述都属虚构。
- LLM 合成智能体实验结果：`src/actors.py` 目前的 `llm` 通道是 `ScriptedActor`
  占位，**不是真实 LLM**；只能写"接口已同构、实现待接入"。
- 与 SUMO/CityFlow/AB Street 的定量对照：仅完成场景转换链路与静态分析，
  **没有**误差量化结果。
- 投稿状态、审稿意见、录用信息：不存在。
