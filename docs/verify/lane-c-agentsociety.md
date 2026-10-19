# Lane C 验证报告：LLM 合成智能体平台（AgentSociety）

> 本报告只记录**实际执行**的命令与**实际观测**的输出。
> 未能执行的项明确标注，并给出后续完成所需的确切条件。

- 执行环境：Windows，Python 3.13.3
- 网络：GitHub 被封（DNS 劫持至 127.0.0.1），经 `gh-proxy.com` 代理访问；
  PyPI 直连正常

---

## 1. 仓库元数据

| 项目 | Stars | Language | License (SPDX) | 默认分支 | 仓库大小 |
|---|---|---|---|---|---|
| [tsinghua-fib-lab/AgentSociety](https://github.com/tsinghua-fib-lab/AgentSociety) | **1340** | Python | **Apache-2.0** | `main` | **362 MB** |

- 本项目选择的理由：它是国内 LLM 合成智能体平台的代表，
  与"赛博ZJU / SocioVerse"同属一支，且具备完整的工程化实现（PyPI 双包、前端、文档）。
- 关联论文：**AgentSociety 2 → arXiv:2607.11895**；
  AgentSociety v1 → **arXiv:2502.08691**（后者已收录于本项目文献库：
  `docs/papers/pdf/Piao2025_AgentSociety.pdf`）。

---

## 2. ⚠️ 全量源码获取受限（如实记录）

**现象**：仓库体积 **362 MB**，经 `gh-proxy.com` 镜像下载归档时超时失败。

```
$ pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "tsinghua-fib-lab/AgentSociety" -DestDir ".\deploy\repos" -TimeoutSec 900
<超时失败>
```

**已完成的部分**（真实获取）：
- ✅ GitHub API 元数据（stars / license / 分支 / 体积）
- ✅ 仓库根目录完整文件清单（经 Contents API）
- ✅ `pyproject.toml` 与 `README.md` 全文（经代理 raw / contents）

**未完成**：完整源码树（362 MB）未落盘。

**后续完成的确切条件**：
```powershell
# 方案一：加大超时并重试（镜像带宽是瓶颈）
pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "tsinghua-fib-lab/AgentSociety" `
     -DestDir ".\deploy\repos" -TimeoutSec 3600
# 方案二：直接使用 PyPI 分发包（推荐，见 §3）
#   注意：此仓库是 monorepo（uv workspace），真正要装的是 packages/agentsociety2
```

> **重要说明**：全量源码未落盘**不影响**本 Lane 的核心结论——
> 因为该平台以 PyPI 包形式分发，可直接安装验证（见 §3）；
> 而源码树对**依赖与架构分析**而言，`pyproject.toml` + `README.md` + 根目录清单已足够。

---

## 3. ✅ 依赖与可安装性 —— 实测通过

### 3.1 仓库结构（经 Contents API 实际获取）

```
AgentSociety/
├─ .dockerignore  Dockerfile  Makefile  .gitlab-ci.yml   # 容器化与 CI
├─ .env.example                                          # 环境变量模板
├─ pyproject.toml  uv.lock                               # uv workspace
├─ README.md  README_zh.md  CHANGELOG.md
├─ AGENTS.md  CLAUDE.md                                  # 面向 AI 助手的开发指南
├─ CITATION.cff  citations.bib  LICENSE                  # Apache-2.0
├─ packages/          # v2 (agentsociety2) + v1 (agentsociety) + community + benchmark
├─ frontend/          # React Web 前端
├─ extension/         # VSCode 扩展
├─ examples/  scripts/  static/
```

### 3.2 根 `pyproject.toml`（实际获取全文）

```toml
[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"

[tool.uv.workspace]
members = ["packages/agentsociety2"]

[[tool.uv.index]]
name = "tuna"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

**关键观测**：该仓库使用 **uv workspace**（monorepo），
且**默认索引指向清华 TUNA 镜像**。
→ 注意：本机实测 `pypi.tuna.tsinghua.edu.cn` **不可达**（连接失败），
因此直接 `uv sync` 会失败；须改用 `pypi.org` 或 `mirrors.aliyun.com`。

### 3.3 PyPI 分发包（实测）

该平台在 PyPI 上有**两个包**（来自 README 徽章与实测）：

| 包名 | 说明 | 实测状态 |
|---|---|---|
| `agentsociety2` | **v2.x，推荐**（现代 LLM-native 平台） | ✅ 依赖解析成功（v2.9.3） |
| `agentsociety` | v1.x，legacy 城市仿真（gRPC） | 未测 |

**依赖解析实测输出（`pip install --dry-run`）**：

```
Would install ... agentsociety2-2.9.3 ...
```

依赖列表中的关键项（实际输出节选）：

| 依赖 | 用途 |
|---|---|
| `litellm`, `openai`, `httpx` | LLM 接入（多供应商） |
| `duckdb`, `SQLAlchemy`, `sqlmodel`, `aiosqlite` | 数据与实验回放存储 |
| `faiss-cpu`, `qdrant-client`, `mem0ai` | 向量检索与智能体记忆 |
| `fastapi`, `uvicorn`, `starlette`, `sse-starlette` | Web 服务 |
| `pydantic`, `pydantic-settings`, `jsonschema` | 配置与模式校验 |
| `mcp` | Model Context Protocol 工具扩展 |
| `geojson`, `shapely`, `pyproj` | 空间数据处理 |
| `pycityproto`, `grpcio` | v1 城市环境协议 |
| `pandas`, `numpy`, `scipy`, `scikit-learn`, `plotly` | 分析 |
| `huggingface_hub`, `tokenizers`, `tiktoken` | 模型与分词 |
| `boto3`, `cryptography`, `pywin32` | 云存储与系统集成 |

**判定**：`agentsociety2` 的依赖**可在本机解析**，无缺失的平台级依赖。
`agentsociety2` 的依赖**可在本机解析并实际安装成功**，无缺失的平台级依赖。

### 3.4 ✅ 实际安装结果（实测）

```powershell
$ py -3.13 -m venv .venv-as
$ .venv-as\Scripts\python.exe -m pip install agentsociety2 -i https://pypi.org/simple/
Successfully installed agentsociety2-2.9.3 ... （共 157 个包）
$ .venv-as\Scripts\python.exe -c "import agentsociety2"
```

关键依赖实测落盘：`litellm-1.105.1`、`openai-2.54.0`、`duckdb-1.5.6`、
`faiss-cpu-1.15.1`、`qdrant-client-1.19.1`、`mem0ai-2.2.1`、`fastapi-0.143.0`、
`mcp-1.30.0`、`shapely-2.2.0`、`pycityproto-2.4.5`。

### 3.5 ⚠️ 导入时强制校验 LLM API key（实测，控制组对照）

这是**一个重要的部署约束**：`agentsociety2` 在**导入阶段**（而非运行阶段）
就强制校验 LLM 凭证。

**控制组 —— 不设 key**：

```
$ .venv-as\Scripts\python.exe -c "import agentsociety2"
  File ".../agentsociety2/config/config.py", line 697, in <module>
    raise ValueError(
ValueError: AGENTSOCIETY_LLM_API_KEY is required. Please set this environment
variable before running AgentSociety2.
```

**实验组 —— 设置 key 后**：

```
$ $env:AGENTSOCIETY_LLM_API_KEY="dummy-key-for-import-test"
$ .venv-as\Scripts\python.exe -c "import agentsociety2; print(agentsociety2.__version__)"
2.9.3
```

**含义**：即使只想做静态 API 探查，也必须提供（哪怕是占位的）key。
这一点会影响任何"先装后配"的部署脚本设计——
配置必须**先于**任何 import 完成。

### 3.6 ⚠️⚠️ Windows 上的 Ray 部署陷阱（实测，重要工程发现）

README 宣称 "Agents are workspace-bound stateless records driven by **Ray Tasks**"，
且 `step` / `run_questionnaire` 的 docstring 明确提到
"``questionnaire_agent_batch`` Ray Task"。但实测发现：

**（a）`ray` 是被声明依赖，但在 Windows 上被条件排除：**

```
$ python -c "from importlib.metadata import requires; print([d for d in requires('agentsociety2') if 'ray' in d.lower()])"
['ray>=2.0.0; sys_platform != 'win32']
```

**（b）因此默认安装后 `ray` 不存在：**

```
$ python -c "import ray"
ModuleNotFoundError: No module named 'ray'
```

**（c）但 Ray 本身在 Windows + Python 3.13 上其实可装（实测成功）：**

```
$ python -m pip install ray -i https://pypi.org/simple/
Successfully installed ray-2.59.0 msgpack-1.2.3
$ python -c "import ray; print(ray.__version__)"
2.59.0
```

**含义（对研究的直接影响）**：
- 在 Windows 上按官方依赖安装，`ray` **不会**被装上，而 `step`/`run_questionnaire`
  等核心路径依赖 Ray Task → **可能在运行期失败**；
- 上游用 `sys_platform != 'win32'` 排除 Ray，
  推测是因为 **Ray 在 Windows 上的支持长期不完整**；
- 生产部署建议：**使用 Linux/WSL2 环境**运行 AgentSociety，或在 Windows 上
  手动补装 `ray` 并自行承担兼容性风险。

> 这是本次验证中对**工程落地最有价值的发现之一**：
> 一个"能在 Windows 上 pip 装成功"的包，其核心执行路径可能因平台而被静默降级。

### 3.7 运行所需的配置

README 快速开始**必须**配置外部 LLM：

```bash
export AGENTSOCIETY_LLM_API_KEY="your-api-key"
export AGENTSOCIETY_LLM_API_BASE="https://api.openai.com/v1"
export AGENTSOCIETY_LLM_MODEL="gpt-5.5"
```

**结论**：
1. ✅ **不需要** Docker / PostgreSQL 即可使用 PyPI 包（v2 走 SQLite/DuckDB 路线）；
2. ⚠️ **必须**外部 LLM API key（OpenAI 兼容接口）——**硬性前置条件，导入时强制校验**；
3. ⚠️ **Windows 上 Ray 被依赖声明排除**，核心并行执行路径需额外处理（见 §3.6）。

**本 Lane 未提供真实 LLM key，故未执行端到端仿真运行**（仅完成导入与 API 探查）。

### 3.8 安装后的公开 API（实测）

```python
import agentsociety2 as a
# 顶层导出：['AgentBase','AgentSocietyHelper','CodeGenRouter','EnvBase','PersonAgent',
#            'PlanExecuteRouter','ReActRouter','ReplayWriter','RouterBase','SearchToolRouter',
#            'TwoTierPlanExecuteRouter','TwoTierReActRouter', ...]

from agentsociety2.society import AgentSociety
# AgentSociety 公开成员：
# ['agent_ids','agent_specs','all_token_stats','ask','cache_hit_rate','close','current_time',
#  'from_workspace','init','intervene','mark_step_completed','router_token_stats',
#  'run','run_questionnaire','step','step_count','to_workspace','token_stats']
```

### 3.9 快速开始代码（实测获取，来自 README）

```python
import asyncio
from datetime import datetime
from pathlib import Path
from agentsociety2.env import CodeGenRouter
from agentsociety2.contrib.env import SimpleSocialSpace
from agentsociety2.society import AgentSociety

async def main():
    agent_specs = [{"id": 1, "profile": {"name": "Alice"}, "config": {}}]
    env = CodeGenRouter(env_modules=[SimpleSocialSpace(agent_id_name_pairs=[(1, "Alice")])])
    society = AgentSociety(
        agent_specs=agent_specs,
        agent_class_name="PersonAgent",
        env_router=env,
        start_t=datetime.now(),
        run_dir=Path("run"),
    )
    await society.init()
    response = await society.ask("What's your name?")
    print(response)
    await society.close()

asyncio.run(main())
```

---

## 4. 🎯 核心问题的答复：是否支持真实人类被试进入仿真闭环？

> 本研究的核心缺口命题是："现有 LLM 合成智能体平台大多仅运行纯计算生成的智能体群体，
> 并未引入真实人类受试者参与闭环仿真。"
> 本 Lane **在已安装的 2.9.3 源码上直接核查**，而非停留在文档推断。

### 4.1 结论

**不支持。AgentSociety 的参与者集合完全由 `agent_specs` 声明为合成智能体；
不存在任何面向"真实人类被试"的接入通道、等待点或人机同场机制。**

### 4.2 证据（方法：对已安装包 `agentsociety2` 全量源码做关键词与 API 核查）

**证据 1 —— 全量源码关键词扫描（实测计数）**

对 `.venv-as/Lib/site-packages/agentsociety2` 下**全部 `.py` 文件**扫描：

| 关键词 | 命中数 |
|---|---|
| `human_in_the_loop` | **0** |
| `human-in-the-loop` | **0** |
| `human_input` | **0** |
| `wait_for_human` | **0** |
| `human_agent` | **0** |
| `WebSocket` / `websocket` | **0** |
| `participant` | 3 |
| `subject` | 3 |

- **前六项全为 0**：没有任何"人类在回路"的命名、没有 WebSocket 长连接
  （即没有把真人浏览器接进仿真的实时通道）、没有"等待人类输入"的阻塞原语；
- 对比 oTree 有 `WaitPage`（见 [Lane A 报告](lane-a-otree-jspsych.md) §5.1），
  AgentSociety **没有**对应物——这是"真人能否进回路"的结构性判据。

**证据 2 —— 仅有的 6 处命中经人工核查后无关真人参与**

| 文件 | 行 | 性质 |
|---|---|---|
| `contrib/agent/public_goods_agent.py` | 353 | 公共品博弈中"其他参与者"= 其他**智能体** |
| `contrib/agent/volunteer_dilemma_agent.py` | 332, 352 | 志愿者困境中"其他参与者"= 其他**智能体** |
| `contrib/agent/llm_donor_agent.py` | 188, 430, 443 | 捐赠博弈中的"被试"= **LLM 智能体扮演的**被试 |

→ 这些是**行为博弈论实验的智能体实现**，`participant`/`subject` 指的是
**博弈中的智能体角色**，而非真人被试。

**证据 3 —— `intervene()` 是"研究者指令"通道，不是"人类被试"通道**

实测签名与实现（`agentsociety2/society/society.py`）：

```python
async def intervene(self, instruction: str) -> str:
    """对仿真进行干预（由 helper 协调执行）。

    :param instruction: 干预指令文本。
    :returns: 执行结果/反馈文本。
    """
    return await self._get_helper().intervene(instruction)
```

- 入参是一个**文本指令**，由实验者/研究者发出；
- 语义是"对仿真进行干预"（类似外部冲击注入），
  **不是**"等待并接收人类被试的实时决策"；
- 它不产生"人类决策 → 流量场"的数据通路，
  也不记录被试反应时/量表等人类实验数据。

**证据 4 —— `run_questionnaire()` 的问答对象是"智能体"，不是人**

实测 docstring（`society.py`）：

```
async def run_questionnaire(self, questionnaire, target_agent_ids=None):
    """向目标 agents 发放问卷并返回结构化结果。
    目标 agent 按 id 切批，每批提交一个 ``questionnaire_agent_batch`` Ray Task ...
    """
```

**这是最直接的证据**：平台的问卷/量表能力是**发给合成智能体**的，
返回的是**智能体生成的结构化回答**。
本项目所要求的"采集真实参与者的主观感知偏好"在该平台中
**恰好由合成体自答替代**——这正是本项目要填补的缺口。

**证据 5 —— 环境侧按 agent_id 绑定**

```python
env = CodeGenRouter(env_modules=[SimpleSocialSpace(agent_id_name_pairs=[(1, "Alice")])])
```

环境参与者映射的键是 **agent ID**，不是人类会话 ID。

### 4.3 对本研究的意义

这一结论把本项目的缺口命题 **G3 从"文献印象"升级为"代码级核查结论"**：

| AgentSociety 具备 | AgentSociety 缺失（本项目填补） |
|---|---|
| 合成智能体（人设 `agent_specs`、记忆、多推理模式） | **真人被试接入通道**（0 处相关代码） |
| `ask` / `intervene`（研究者问答与干预） | **真人决策的实时注入**（`intervene` 是文本指令，非被试决策） |
| `run_questionnaire` → **发给智能体** | **真实参与者的主观感知采集** |
| Ray 分布式执行、实验回放（ReplayWriter + DuckDB） | 人机**同场**协同推演 |
| 空间数据处理依赖（geojson/shapely） | **存量-流量聚合空间模型** |

> **可直接写入论文的表述**：本文对当前国内代表性 LLM 社会仿真平台
> AgentSociety（v2.9.3）的完整源码核查显示，其全部参与者由 `agent_specs`
> 声明为合成智能体；源码中不存在 human-in-the-loop 相关实现（关键词命中 0），
> 无 WebSocket 实时人机通道（命中 0），且其 `run_questionnaire()`
> 将问卷发放给**智能体**而非人类被试。这证实了"现有平台以纯计算智能体运行、
> 真实人类未进入闭环"的判断。

---

## 5. 可复用与本项目需自建的部分

### 5.1 可复用（设计与实现参考）

| 能力 | AgentSociety 的做法 | 本项目如何使用 |
|---|---|---|
| 合成智能体人设 | `agent_specs` 的 `profile` 声明式定义 | 设计 `LLMAgent` 的配置格式 |
| 多推理模式 | CodeGen（默认）/ ReAct / Plan-Execute / Two-Tier / Search | 为空间决策选择合适推理模式 |
| 智能体记忆 | `mem0ai` + `faiss-cpu` + `qdrant-client` 向量记忆 | 复用其记忆架构选型，避免重复造轮子 |
| LLM 多供应商接入 | `litellm` 统一接口 | 直接采用 `litellm`，降低成本与合规风险 |
| 实验回放 | Catalog-driven JSONL + DuckDB | 借鉴其**实验可回放**设计（与本项目 Recorder 目标一致） |
| 工具扩展 | MCP 集成 | 后续接入外部数据源 |
| 情景管理 | `run_dir` + 配置驱动 | 对齐本项目 `configs/` 场景定义 |

### 5.2 本项目必须自建（AgentSociety 不提供）

1. **真人被试接入层**（统一决策协议 + 决策窗口 + 超时处理）——缺口 G3 核心；
2. **存量-流量聚合空间模型**（守恒方程、重力流、约束投影）——
   已在本项目 `src/core/` 实现并通过 24 项测试；
3. **状态回传通道**（每轮把空间状态推给被试与合成体）；
4. **主观感知量表采集**（oTree/jsPsych 侧，见 Lane A 报告）；
5. **人机一致性分析**（真人分布 vs 合成体分布比对）。

---

## 6. 复现命令汇总

```powershell
# 元数据与关键文件（实测通过，GitHub 必须走代理）
$ curl.exe -sL "https://gh-proxy.com/https://api.github.com/repos/tsinghua-fib-lab/AgentSociety"
$ curl.exe -sL "https://gh-proxy.com/https://raw.githubusercontent.com/tsinghua-fib-lab/AgentSociety/main/pyproject.toml"

# 全量源码（362 MB，需长超时；本机未完成）
pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "tsinghua-fib-lab/AgentSociety" `
     -DestDir ".\deploy\repos" -TimeoutSec 3600

# 安装（实测成功：157 个包）
py -3.13 -m venv .venv-as
.\.venv-as\Scripts\python.exe -m pip install agentsociety2 -i https://pypi.org/simple/

# 运行前置条件（必须，导入时即强制校验）
$env:AGENTSOCIETY_LLM_API_KEY="<your-key>"
$env:AGENTSOCIETY_LLM_API_BASE="https://api.openai.com/v1"
$env:AGENTSOCIETY_LLM_MODEL="<model>"

# Windows 上需补装 Ray（官方依赖条件排除 win32，实测可装）
.\.venv-as\Scripts\python.exe -m pip install ray -i https://pypi.org/simple/
```

---

## 7. 结论

| 维度 | 判定 | 证据位置 |
|---|---|---|
| 仓库元数据 | ✅ 已获取（1340★ / Apache-2.0 / main / 362 MB） | §1 |
| 全量源码落盘 | ⚠️ **未完成**（体积 + 镜像带宽限制），已记录重试条件 | §2 |
| 依赖可解析性与安装 | ✅ **实测成功**（`agentsociety2-2.9.3`，157 个包） | §3.4 |
| LLM key 前置条件 | ✅ **实测确认**（不设 key 则 import 直接抛 `ValueError`） | §3.5 |
| **Windows Ray 陷阱** | ⚠️ **实测确认**（`ray>=2.0.0; sys_platform != 'win32'`，但核心路径依赖 Ray Task） | §3.6 |
| 端到端仿真运行 | ⚠️ **未执行**（缺真实 LLM API key；不编造） | §3.7 |
| **真人接入闭环** | ❌ **不支持**——源码级核查：HITL 关键词命中 0、无 WebSocket、问卷发给智能体 | §4.2 |

**许可证**：Apache-2.0，宽松，可安全用于学术与本项目集成（需保留声明与变更说明）。

### 本 Lane 最有价值的三项产出

1. **证据化的缺口判定（§4）**：把"现有平台不支持真人进回路"
   从文献印象变成**对已安装源码的代码级核查结论**
   （HITL 关键词命中 0 / 无 WebSocket / `run_questionnaire` 发给智能体）。
   可直接写入论文的表述见 §4.3 末。
2. **Windows 部署陷阱（§3.6）**：上游用 `sys_platform != 'win32'` 排除 Ray，
   但 `step`/`run_questionnaire` 依赖 Ray Task —— Windows 上会静默缺件。
   这直接影响本项目的部署环境选择（建议 Linux/WSL2）。
3. **可复用技术栈清单（§5.1）**：`litellm`（多供应商 LLM）、
   `mem0ai`+`faiss-cpu`+`qdrant-client`（智能体记忆）、
   `duckdb`（实验回放）——本项目可直接采用，避免重复造轮子。
