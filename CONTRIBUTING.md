# 贡献指南（CONTRIBUTING）

本仓库是「存量—流量空间建模驱动的参与式交互仿真：面向公共空间人员流动治理的人机协同实验平台」
（仓库代号 `SF-HITL-Sim`，<https://github.com/CORAX2022/SF-HITL-Sim>，私有）。
它同时是**研究平台**与**写作平台**：代码与论文共享同一套 git 历史，
写作过程以分支与提交留痕，评审即合并，里程碑即标签。

这份指南说明协作方式。写作格式细节见 `docs/writing/`，版本变更见 `CHANGELOG.md`，
研究路线见 `ROADMAP.md`，引用信息见 `CITATION.cff`。

---

## 1. 仓库定位

- **仿真平台**：以空间单元存量与跨单元流量刻画人流，真人与 LLM 合成智能体经统一决策协议接入同一世界。
- **写作平台**：论文逐章 Markdown 化，小步提交、逐段评审，可回溯到每一次论证与每一个数字。
- **证据仓**：文献索引与笔记、上游溯源清单、复现图表与验证报告均入库，结论可核验。

---

## 2. 目录职责

| 路径 | 职责 | 变更注意 |
| --- | --- | --- |
| `src/core/` | 存量-流量内核（空间图、流量、守恒推进） | 改内核必须同步补测试 |
| `src/actors.py` | 决策者：人类 / LLM 合成体 / 规则背景体 | 统一决策协议不得单方面改动 |
| `tests/` | 单元测试（当前 24 项） | 新增能力必须有对应用例 |
| `examples/` | 闭环演示与守恒性验证 | 演示结果变化需写入 CHANGELOG |
| `configs/scenarios/` | 场景定义：单元、邻接、容量、吸引力 | 结构变更需版本化说明 |
| `data/` | 实验运行期输出（如 `data/demo/`） | 只入库小体积演示数据 |
| `scripts/` | 获取、转换、索引、复现、审计脚本 | 脚本需幂等、可重复执行 |
| `docs/model/` | 存量-流量数学模型规范 | 与 `src/core/` 实现保持同源 |
| `docs/architecture/` | 软件架构与统一决策协议 | 接口变更先改文档再改代码 |
| `docs/research/` | 研究缺口、可证伪假设 H1–H5 | 假设改动需补充证据 |
| `docs/literature/` | 文献综述 | 引用必须可溯源 |
| `docs/papers/`、`docs/papers2/` | 文献索引、逐篇笔记（PDF 不入库） | 索引由脚本生成，不手工改 |
| `docs/verify/` | 上游项目部署与运行验证报告 | 如实记录失败与环境限制 |
| `docs/repos-survey/` | 上游仓库调研与原始清单 | `raw/` 为采集原始数据 |
| `docs/writing/` | 写作规范（工作流 / 风格 / 术语 / 参考文献） | 规范变化影响所有写作提交 |
| `paper/` | 论文写作工作区（总稿、逐章、参考文献） | 一章一次提交，见 §5 |
| `results/repro/` | 复现图表与播放器 | 图表必须可由脚本重建 |
| `_nlogo_run/` | NetLogo 复现运行产物 | 第三方模型目录本身不入库 |
| `deploy/repos/manifest.jsonl` | 上游溯源清单 | 源码不入库，清单必须入库 |

不入库内容由 `.gitignore` 定义：虚拟环境、上游源码、文献 PDF、第三方 NetLogo 模型与临时文件。

---

## 3. 分支模型

```text
main                 稳定主干：可运行、可复现、写作稿可导出
├─ writing/<主题>    写作分支：一章或一个论证单元
└─ review/<主题>     评审快照：提交评审时从 writing/* 拉出，评审通过后合回 main
```

- `main` 始终保持可运行（内核测试通过）与可读（论文各章状态一致）。
- 写作在 `writing/*` 上小步推进，一次提交只改一个论证单元或一章的一节。
- 需要他人评审时，从写作分支拉 `review/<主题>` 并在议题中贴出 diff 范围；
  评审意见落在议题评论，修改回到 `writing/*`，通过后 `git merge --no-ff` 合回 `main`。
- 标签：软件版本从 `v0.1.0` 起用语义化版本；写作阶段稿用 `draft-YYYYMMDD-<主题>`。

示例：

```powershell
git switch -c writing/paper-intro
# …修改 paper/sections/01-引言.md…
git add paper/sections/01-引言.md
git commit                      # 按 .gitmessage 模板填写
git tag draft-20261019-intro
git switch main
git merge --no-ff writing/paper-intro
```

---

## 4. 提交规范

提交信息模板是仓库根目录的 `.gitmessage`，首次使用请启用：

```powershell
git config commit.template .gitmessage
```

首行格式：`<type>(<scope>): <中文祈使摘要，≤50 字>`，例如
`docs(paper): 补写引言与文献综述初稿`。

- **type**：`feat` / `fix` / `docs` / `refactor` / `test` / `chore` / `style` / `perf` / `build` / `ci`
- **scope**（候选，取最贴近的一层）：`core` / `model` / `arch` / `research` / `literature` /
  `paper` / `writing` / `sumo` / `nlogo` / `repo` / `data`
- 正文说明「为什么改」与「改了什么」；涉及数值时写明证据来源（如「24/24 测试通过」「守恒检验 PASS」）。
- 页脚用 `Refs #12` / `Closes #12` 关联议题；需同步变更记录时写 `CHANGELOG: added` 等。

写作类提交建议在正文补充：本轮改动的章节、使用的数据/图表快照版本、AI 辅助使用情况。

---

## 5. 写作类变更评审清单

评审论文、综述、研究文档时逐条核对，任何一条不满足都不合并：

- [ ] **事实可核验**：机制、数字与结论能在仓库内找到出处（代码、数据、验证报告或文献）。
- [ ] **引用真实**：每条引文都能在 `docs/papers/index.json` / `docs/papers2/index.json` 或
      `paper/references.bib` 中找到，且 DOI / 作者 / 年份与原文一致（见 §8）。
- [ ] **图表可复现**：图中数据来自仓库内脚本与数据快照，题注写明生成命令；无手工改数。
- [ ] **术语一致**：使用 `docs/writing/术语表.md` 的译法与定义，首次出现给中英对照。
- [ ] **边界诚实**：未验证的断言、外部环境限制（无编译器、无 GPU 等）如实标注，不写成结论。
- [ ] **结构一致**：符合 `paper/sections/` 既有章节模板，标题层级与 `paper/manuscript.md` 看板一致。

---

## 6. 代码类变更要求

- **测试通过**：提交前运行

  ```powershell
  py -3.13 tests\test_core.py       # 24 项应全部通过
  py -3.13 examples\run_loop.py     # 闭环三条件守恒检验应 ALL PASS
  ```

  若改动了守恒逻辑，必须同时给出漂移量数值。
- **不新增编译依赖**：本机无 MSVC / CMake / cargo / Julia，新增需编译的依赖会让仓库无法验证；
  新库优先选纯 Python wheel（PyPI 走阿里云镜像），并在验证报告中记录安装与运行结果。
- **向后兼容**：统一决策协议与场景 JSON 结构变更需同步更新文档与示例，并写入 CHANGELOG「变更」。
- **脚本可重复**：`scripts/` 下脚本应幂等、参数显式、失败给出可操作信息。

---

## 7. 数据与图表版本化

- 小体积演示数据（如 `data/demo/`）与复现图表（`results/repro/`）入库；原始大文件不入库。
- 只提交由脚本生成的结果，生成命令写进图表题注或所在文档，例如：

  ```powershell
  py -3.13 scripts\compare_nlogo_repro.py
  py -3.13 scripts\plot_nlogo_repro.py
  ```

- 一次图表更新作为独立提交（`data` 或 `paper` scope），并在正文说明数据快照对应哪次运行。
- 大体积中间产物与临时导出放 `.scratch/`（已被忽略）。

---

## 8. 文献引用纪律

- **不凭记忆补 DOI**：任何 DOI、卷期、页码、作者列表都必须在 PDF 正文或出版方页面核实后写入。
- 新增文献先落入索引（`docs/papers/*`、`docs/papers2/*`，由 `scripts/build_paper_index.py`
  等脚本生成），再写入 `paper/references.bib`；BibTeX key 与索引条目一一对应。
- 引用格式遵循 `docs/writing/参考文献规范.md`（GB/T 7714—2015 与 BibTeX 映射）。
- 元数据无法核实的条目标注「待核实」，不得以确定语气引用，也不得进入正式参考文献表。
- 文献 PDF 不入库（版权归出版方），仓库只保存索引、笔记与原始清单。

---

## 9. AI 辅助写作声明

本项目使用 AI 辅助（检索、提纲、改写、代码与脚本生成），但**责任在人**：

- AI 产出的每一个事实、引文、数字，必须由提交者本人对照原文或运行结果核验后才能提交。
- 不得让 AI 生成不存在的文献、DOI 或实验数据；发现即回滚。
- 写作类提交在正文说明 AI 参与范围（如「提纲由 AI 辅助，论证与引文人工核验」）。
- 评审者有权要求对任何 AI 参与段落提供溯源证据。

---

## 10. 提问与协作

- 用议题（issue）描述问题与复现步骤；数值/结论类问题请附命令与输出。
- 仓库为私有仓库，GitHub 访问依赖本机加速器；不可用时按 README「环境与网络说明」
  使用 `scripts/gh-fetch.ps1` 通道，不要重复试错。
- 评审顺序建议：先看 `README.md` 与 `ROADMAP.md` 确认阶段目标，再看 diff；
  写作稿先看 `paper/manuscript.md` 看板，避免在过期章节上评审。
- 重大方向调整（模型假设、实验设计、数据采集口径）先在议题中讨论并形成结论，再动代码或论文。
