# 变更日志

本项目的所有重要变更都记录在此文件中，便于评审、复盘与复现时回溯。
写作稿的阶段快照另用 `draft-YYYYMMDD-*` 标签标记，不与软件版本号混用（约定见 CONTRIBUTING.md）。

- 格式遵循 [Keep a Changelog 中文版][Keep a Changelog]；
- 版本号遵循[语义化版本 2.0.0][SemVer]；
- 日期使用 ISO 8601（YYYY-MM-DD）。

## [Unreleased]

### 计划中

- **阶段 2｜接入 LLM 合成智能体**：实现 `LLMAgent`，按统一决策协议产出空间选择；
  合成体 persona 与记忆编排可直接复用 AgentSociety / Park2024 的构造方法（见 README「下一步」）。
- **阶段 3｜接入真人被试**：以 jsPsych 前端 + oTree 式轮次骨架对接
  `src/core/kernel.py` 的 `state_snapshot()` 与 `step()`；同步启动伦理审查与知情同意流程。
- **阶段 4｜混合实验与人机一致性**：混合比例扫描、人机选择一致性分析、揭示偏好与陈述偏好对照。
- **阶段 5｜情景推演与决策报告**：多方案对比，输出面向公共空间营建的决策支撑报告。
- **论文正文写作**：`paper/sections/` 从提纲推进到完整初稿（当前仅引言与文献综述为初稿）。
- **文献与构建补检**：中文文献（CNKI/Wanfang）系统性补检；
  CityFlow / AB Street 在有编译环境的机器上完成构建验证（本机无 MSVC/CMake/cargo）。

## [0.1.1] - 2026-10-19

### 变更

- 仓库可见性由私有转为**公开**（<https://github.com/CORAX2022/SF-HITL-Sim>）：
  服务器可匿名克隆，不再需要凭据；私有时期发布的 `v0.1.0` Release 资产保留为历史快照。
- 交付包新增**全量资产版**（`SF-HITL-Sim-full-v0.1.1.zip`）：除 git 仓库外，一并打包
  文献 PDF、第三方上游源码、第三方 NetLogo 模型与本地虚拟环境，供离线服务器一次性搬运；
  常规版（`SF-HITL-Sim-v0.1.1.zip`）仍只含 git 仓库与写作资产。
- README、CONTRIBUTING、CITATION 与交接文档同步更新公开仓库说明与版本号。

## [0.1.0] - 2026-10-19

首个版本：仿真内核、闭环演示、文献与上游验证、写作平台同时就位，仓库可作为长期研究写作平台使用。

### 新增

- **仓库与写作平台初始化**：建立目录骨架、中文提交模板（`.gitmessage`）、忽略与文本属性规则
  （`.gitignore` / `.gitattributes` / `.editorconfig`），以及 `paper/` 论文写作脚手架与
  `docs/writing/` 写作规范（工作流、风格指南、术语表、参考文献规范）。
- **存量-流量仿真内核**：`src/core/` 实现空间单元、跨单元流量合成与守恒推进；
  `tests/test_core.py` 24/24 单元测试通过。
- **闭环演示与守恒性验证**：`examples/run_loop.py` 以 200 轮 × 3 条件
  （纯背景体 / 注入人类决策 / 混合）运行，三条件守恒检验全部 PASS，最大总量漂移 < 1.3e-12。
- **文献索引与笔记**：`docs/papers/`（28 篇 PDF 索引，21 篇元数据经 PDF 正文核实）、
  `docs/papers2/`（扩展文献池索引、逐篇笔记、中文摘要），以及 `docs/literature/文献综述.md`。
- **上游仓库验证**：mesa、oTree、jsPsych、AgentSociety、SUMO、CityFlow、AB Street、Agents.jl
  的部署与可运行性验证报告（`docs/verify/`）；8 个上游仓库落盘并写入
  `deploy/repos/manifest.jsonl` 溯源清单（stars / license / 分支 / sha256）。
- **SUMO 路网转换器**：`scripts/sumo_to_units.py` 把 SUMO 路网转换为空间单元场景，
  打通「转换 → 内核加载 → 仿真运行」全链路；并完成本机 SUMO 1.27.0（含 JuPedSim）端到端验证。
- **NetLogo 外部模型复现**：`experiment1-3patterns` 150 次运行（3 模式 × 50 重复）复现完成，
  出口时间排序与峰值密度结论一致；产物见 `results/repro/`，报告见 `docs/nlogo/`。
- **研究文档**：存量-流量数学模型规范、软件架构设计、研究缺口与选题论证（G1–G3、H1–H5），
  以及工具评估、许可证风险与快速启动清单。

### 变更

- 项目更名为「**存量—流量空间建模驱动的参与式交互仿真：面向公共空间人员流动治理的
  人机协同实验平台**」（原标题：基于存量-流量空间建模的参与式交互仿真：面向人流治理的
  人-AI混合实验平台），研究定位、阶段计划与写作平台定位同步更新到 README 与 ROADMAP。
- 统一容量口径表述：以模型规范 §4.1 的**软容量**定义为准，架构文档阶段 1 验收由
  「容量不越界」改为「容量反馈生效（超软容量触发进入方向拥挤惩罚与硬阻挡）」；
  论文第 6.5 / 7.6 节据此定稿口径。
- 仓库体积策略确立：虚拟环境、第三方上游源码（仅保留 `manifest.jsonl` 溯源清单）、
  第三方 NetLogo 模型与文献 PDF 均不入库，当前提交体积约 27 MB。
- 引用元数据统一以 `CITATION.cff` 为唯一入口；本项目暂未声明开源许可证。

[Keep a Changelog]: https://keepachangelog.com/zh-CN/1.1.0/
[SemVer]: https://semver.org/lang/zh-CN/
[Unreleased]: https://github.com/CORAX2022/SF-HITL-Sim/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/CORAX2022/SF-HITL-Sim/releases/tag/v0.1.1
[0.1.0]: https://github.com/CORAX2022/SF-HITL-Sim/releases/tag/v0.1.0
