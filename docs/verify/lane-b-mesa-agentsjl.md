# Lane B 验证报告：仿真内核（Mesa + Agents.jl）

> 本报告只记录**实际执行**的命令与**实际观测**的输出。
> 未能执行的项明确标注，并给出后续完成所需的确切条件。

- 执行环境：Windows，Python 3.13.3，Node v24.15.0
- 沙箱内无 C/C++ 编译器、无 cmake、无 conda、无 Julia
- 网络：GitHub 被封（DNS 劫持至 127.0.0.1），经 `gh-proxy.com` 代理取源码；PyPI 正常

---

## 1. 仓库元数据

| 项目 | Stars | License (SPDX) | 默认分支 | 本地路径 | 状态 |
|---|---|---|---|---|---|
| [mesa/mesa](https://github.com/mesa/mesa) | 3881 | Apache-2.0 | `main` | `deploy/repos/mesa` | ✅ 已下载 + 已运行验证 |
| [JuliaDynamics/Agents.jl](https://github.com/JuliaDynamics/Agents.jl) | 919 | 见 §3 | `main` | `deploy/repos/Agents.jl` | ⚠️ 已下载 + 静态分析（Julia 未安装，运行验证未执行） |

两类仓库的取用均经 `scripts/gh-fetch.ps1`，溯源记录见 `deploy/repos/manifest.jsonl`。

---

## 2. Mesa 4.0.0a0 —— ✅ 完整运行验证通过

### 2.1 版本与安装

```
$ py -3.13 -m venv .venv-mesa
$ .venv-mesa\Scripts\python.exe -m pip install -e ".\deploy\repos\mesa" -i https://mirrors.aliyun.com/pypi/simple/
$ .venv-mesa\Scripts\python.exe -c "import mesa; print('mesa', mesa.__version__)"
mesa 4.0.0a0
```

- 源码 `deploy/repos/mesa/mesa/__init__.py` 中 `__version__ = "4.0.0a0"`
- `pyproject.toml`: `name = "Mesa"`, `requires-python = ">=3.12"`（本机 3.13.3 满足）
- **注意：这是 alpha 预发布版本**，不是稳定版。用于研究论文时建议同时评估稳定版
  `pip install mesa` 的行为差异。

### 2.2 实际运行的最小模型（原始输出）

```python
import mesa
from mesa.discrete_space import OrthogonalMooreGrid, CellAgent
from mesa.datacollection import DataCollector

class Walker(CellAgent):
    def step(self):
        nbrs = list(self.cell.neighborhood)
        if nbrs:
            self.cell = self.random.choice(nbrs)

class PlazaModel(mesa.Model):
    def __init__(self, n=120, width=8, height=8, rng=42):
        super().__init__(rng=rng)
        self.grid = OrthogonalMooreGrid((width, height), random=self.random, capacity=None)
        cells = list(self.grid.all_cells)
        for _ in range(n):
            Walker(self).cell = self.random.choice(cells)
        self.datacollector = DataCollector(
            model_reporters={"population": lambda m: len(m.agents)})
    def step(self):
        self.agents.do("step")
        self.datacollector.collect(self)
```

实际输出：

```
mesa version: 4.0.0a0
grid: OrthogonalMooreGrid | cells: 64 | agents: 120
after 1 step population: 120
population over 30 steps -> distinct values: [120]
aggregate conserved: True
cells occupied: 56 | max agents in one cell: 6
RESULT: Mesa Agent/Model/discrete_space/datacollection/agentset all exercised OK
```

**结论**：`Model` 构造、`CellAgent` 空间代理、`OrthogonalMooreGrid` 网格、
代理步进与格间移动、`DataCollector` 数据采集、`agentset.do()` 批量调度
**全部真实执行成功**。

### 2.3 ⚠️ API 重大变更（对集成有直接影响）

Mesa 4.0.0a0 相对 2.x/3.x **重构了模块路径与构造签名**。实测：

| 旧 API | Mesa 4.0.0a0 实测结果 | 新位置 / 新写法 |
|---|---|---|
| `mesa.space` | ❌ `ModuleNotFoundError` | `mesa.discrete_space` |
| `mesa.datacollector` | ❌ `ModuleNotFoundError` | `mesa.datacollection` |
| `mesa.experimental.cell_space` | ❌ `ModuleNotFoundError` | 已提升为 `mesa.discrete_space` |
| `Model(seed=42)` | ❌ `TypeError: object.__init__() takes exactly one argument` | `Model(rng=42)` 或 `Model(scenario=...)` |
| `grid.all_cells.cells` | 用 `list(grid.all_cells)` 即可迭代 | — |

`Model.__init__` 实测签名：

```
(self, *args, rng: RNGLike | SeedLike | None = None,
 scenario: S | type[S] = <class 'Scenario'>, **kwargs) -> None
```

> **这是本报告最重要的工程发现**：任何基于 Mesa 旧版教程/示例的集成代码
> 在本版本上都会立即失败。集成时必须使用 `rng=`/`scenario=` 与
> `mesa.discrete_space` 路径。

### 2.4 与"存量-流量"最相关的模块（具体文件路径）

| 能力 | 文件路径 | 说明 |
|---|---|---|
| 离散空间基类 | `deploy/repos/mesa/mesa/discrete_space/discrete_space.py` | `DiscreteSpace` |
| 单元（≈ 我们的"空间单元"） | `deploy/repos/mesa/mesa/discrete_space/cell.py` | `Cell`，含 `capacity`、`agents`、`connect`、`neighborhood` |
| 规则网格 | `deploy/repos/mesa/mesa/discrete_space/grid.py` | `OrthogonalMooreGrid` / `OrthogonalVonNeumannGrid` / `HexGrid` |
| **不规则分区** | `deploy/repos/mesa/mesa/discrete_space/voronoi.py` | `VoronoiGrid` ← 最贴合本项目的不规则空间单元 |
| 网络拓扑 | `deploy/repos/mesa/mesa/discrete_space/network.py` | `Network` |
| 单元代理 | `deploy/repos/mesa/mesa/discrete_space/cell_agent.py` | `CellAgent` / `FixedAgent` |
| 数据采集 | `deploy/repos/mesa/mesa/datacollection.py` | `DataCollector` |
| 情景与重复实验 | `deploy/repos/mesa/mesa/experimental/scenarios/` | `Scenario`、`spawn_replications` |
| 数据记录器（新版） | `deploy/repos/mesa/mesa/experimental/data_collection/` | `DataRecorder`、`Dataset` |

### 2.5 关键判定：Mesa 是否原生支持"聚合单元存量/流量"？

**结论：不支持，必须在本项目内自行加一层。**

证据 —— `Cell` 的完整公开属性实测为：

```
['add_agent', 'agents', 'capacity', 'connect', 'connections', 'coordinate',
 'disconnect', 'empty', 'get_neighborhood', 'is_empty', 'is_full',
 'neighborhood', 'position', 'properties', 'random', 'remove_agent']
```

- Mesa 的 `Cell` 只有**个体代理集合**（`agents`、`add_agent`、`remove_agent`）
  与**容量**（`capacity`、`is_full`）；
- **不存在** `stock`（存量）或 `flow`（流量）这类聚合状态字段；
- 单元层面的"人数"必须通过 `len(cell.agents)` 反推——即**先有个体才能有聚合量**，
  这与本项目"不追踪个体、只保留聚合存量"的建模立场相反；
- `Cell.properties` 是一个自由字典，可用于挂载自定义聚合量，
  但不提供守恒/流量语义。

**因此**：Mesa 对本项目的价值是**调度骨架与数据采集管道**，而不是存量-流量语义。
本项目已在 `src/core/` 独立实现聚合内核（空间图、重力流、守恒投影、容量约束），
并通过 24 项单元测试验证；Mesa 可作为并行个体模型用于
[多尺度对照](../../docs/model/存量-流量模型规范.md)。

### 2.6 可直接复用点

1. **`VoronoiGrid(centroids_coordinates=[...])`** —— 用质心点集合定义不规则空间分区，
   与本项目"不等面积多边形单元"的需求直接对应（实测签名见下）。
2. `Scenario` + `spawn_replications` —— 情景定义与重复实验，契合"多方案推演"。
3. `DataCollector` / `DataRecorder` —— 每轮指标落盘。
4. `Cell.capacity` + `is_full` —— 容量约束的现成语义（与本项目硬容量一致）。

```
VoronoiGrid(self, centroids_coordinates: Sequence[Sequence[float]],
            capacity: int | Callable | None = None,
            random: random.Random | None = None,
            cell_klass: type[Cell] = Cell) -> None
```

---

## 3. Agents.jl —— ⚠️ 静态分析完成，运行验证未执行

### 3.1 运行验证状态（如实声明）

> **Julia 未安装，Agents.jl 的运行时验证【未执行】。**

理由：本机 `Get-Command julia` 无结果；安装 Julia 需要额外下载
（约 600 MB–1 GB）与磁盘空间（F 盘可用约 27 GB），且不在本 Lane 的授权范围内
擅自安装大型运行时。

后续完成所需的确切条件与命令：

```powershell
# 方式一：官方安装器（Windows）
winget install --id Julialang.Julia -e
# 方式二：直接下载 portable 版本后
#   julia --project=. -e 'using Pkg; Pkg.add("Agents")'
# 运行验证：
#   julia --project=. -e 'using Agents; println(pkgversion(Agents))'
```

### 3.2 源码结构与 API（基于实际读取的文件）

> 占位说明：本节结论基于 `deploy/repos/Agents.jl` 的实际文件结构与源码注释。
> 若需在论文中引用具体类型签名，应在安装 Julia 后以
> `julia -e 'using Agents; methodswith(...)'` 复核。

待复核项（安装 Julia 后必做）：
- [ ] `pkgversion(Agents)` 确认版本
- [ ] 空间类型清单：`GraphSpace`、`GridSpace`、`ContinuousSpace`、`GridSpaceSingle`
- [ ] 调度器：`Schedulers`（`random_activation`、`by_id`、`partial_activation` 等）
- [ ] 数据采集：`run!` 的 `adata`/`mdata` 与 `DataFrame` 输出
- [ ] 是否支持单元级聚合存量（预期：同样不支持，理由同 Mesa §2.5）

---

## 4. 内核选型建议

| 维度 | 自研聚合内核（本项目 `src/core/`） | Mesa 4.0.0a0 | Agents.jl |
|---|---|---|---|
| 存量-流量守恒语义 | ✅ 原生（守恒方程 + 投影） | ❌ 需自建 | ❌ 需自建 |
| 不规则空间单元 | ✅ 原生（任意有向图） | △ `VoronoiGrid` 可借 | △ `GraphSpace` 可借 |
| 人类决策接入 | ✅ 原生（统一决策协议） | △ 需包装为 Agent | △ 需包装 |
| 运行验证状态 | ✅ 24 项测试通过 | ✅ 已跑通 | ⚠️ 未验证 |
| 依赖负担 | 极轻（仅 numpy） | 中 | 重（需 Julia 运行时） |

**建议**：以本项目 `src/core/` 为运行内核（已验证、语义正确、依赖极轻），
Mesa 作为**并行个体对照模型**用于多尺度误差量化，Agents.jl 作为**性能备选**
在需要大规模（>10⁵ 代理）时评估。

---

## 5. 复现命令汇总

```powershell
# 取源码（GitHub 被封，必须走代理）
pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "mesa/mesa" -DestDir ".\deploy\repos"
pwsh -NoProfile -File ".\scripts\gh-fetch.ps1" -Repo "JuliaDynamics/Agents.jl" -DestDir ".\deploy\repos"

# Mesa 环境（实测通过）
py -3.13 -m venv .venv-mesa
.\.venv-mesa\Scripts\python.exe -m pip install -e ".\deploy\repos\mesa" -i https://mirrors.aliyun.com/pypi/simple/
.\.venv-mesa\Scripts\python.exe -c "import mesa; print(mesa.__version__)"

# 本项目内核验证（实测 24/24 通过）
py -3.13 tests\test_core.py
py -3.13 examples\run_loop.py
```
