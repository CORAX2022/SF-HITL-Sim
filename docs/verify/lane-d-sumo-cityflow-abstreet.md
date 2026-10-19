# Lane D 验证报告：人流/交通/城市仿真参考实现

> 本报告只记录**实际执行**的命令与**实际观测**的输出。
> 未能执行的项明确标注，并给出后续完成所需的确切条件。

- 执行环境：Windows，Python 3.13.3
- 网络：GitHub 被封（DNS 劫持至 127.0.0.1），经 `gh-proxy.com` 代理；
  PyPI 直连正常
- 本机工具链：**无 C/C++ 编译器、无 cmake、无 cargo/Rust、无 conda**

---

## 1. 元数据总览

| 项目 | Stars | Language | License (SPDX) | 默认分支 | 获取状态 |
|---|---|---|---|---|---|
| [eclipse-sumo/sumo](https://github.com/eclipse-sumo/sumo) | 4221 | Python/C++ | **EPL-2.0** | `main` | ⚠️ 源码归档不完整；**但本机已装 SUMO 1.27.0 并完整验证** |
| [cityflow-project/CityFlow](https://github.com/cityflow-project/CityFlow) | 1029 | C++ | Apache-2.0 | `master` | ✅ 源码已落盘（70 文件） |
| [a-b-street/abstreet](https://github.com/a-b-street/abstreet) | 8188 | Rust | Apache-2.0 | `main` | ⚠️ 仅元数据（仓库过大） |

> 许可证说明：SUMO 的 EPL-2.0 与 Apache-2.0 **不同**，属弱 copyleft，
> 分发衍生作品时有额外义务。**成果转化前必须单独评估**（见 §5 许可证风险）。

---

## 2. 🎉 SUMO —— 完整端到端验证通过（本 Lane 最大成果）

### 2.1 关键发现：本机**已安装** SUMO 1.27.0

最初判断"本机无编译器故 SUMO 不可用"是**不完整**的。实测发现
**SUMO 已以预编译二进制形式安装在本机**：

```
$ .venv-sumo2\Scripts\python.exe -c "import sumolib; print(sumolib.checkBinary('sumo'))"
F:\SUMO\bin\sumo.exe
```

```
$ F:\SUMO\bin\sumo.exe --version
Eclipse SUMO sumo 1.27.0
 Build features: Windows-10.0.17763 AMD64 MSVC 19.29.30133.0 Release SumoUtilsLibrary
                 FMI Proj GUI FMT Intl SWIG Parquet Eigen GDAL FFmpeg OSG GL2PS
                 JuPedSim
 Copyright (C) 2001-2026 German Aerospace Center (DLR) and others
 ...made available under the terms of the Eclipse Public License v2.0
```

**重要**：构建特性中包含 **`JuPedSim`** —— 即 SUMO 自带**行人动力学**支持。
这对本项目研究"人流"极为关键，不可忽略。

安装布局：

```
F:\SUMO\
├─ bin\     # sumo.exe, netconvert.exe, duarouter.exe, sumo-gui.exe, polyconvert.exe, ...
├─ data\  doc\  include\  share\  tools\
```

### 2.2 Python 侧工具链（实测安装通过）

```powershell
$ py -3.13 -m venv .venv-sumo2
$ .venv-sumo2\Scripts\python.exe -m pip install sumolib traci -i https://pypi.org/simple/
Successfully installed sumolib-1.28.0 traci-1.28.0
```

实测导入：

```
sumolib 1.28.0
traci 1.28.0
```

全部 SUMO 工具可被 `sumolib.checkBinary` 定位：

```
  sumo         -> F:\SUMO\bin\sumo.exe
  netconvert   -> F:\SUMO\bin\netconvert.exe
  duarouter    -> F:\SUMO\bin\duarouter.exe
  sumo-gui     -> F:\SUMO\bin\sumo-gui.exe
  polyconvert  -> F:\SUMO\bin\polyconvert.exe
```

> 注：`eclipse-sumo` 的 pip wheel 达 **150 MB**，经镜像下载**极慢**
> （实测 ~4.7 MB/min，最终取消）。由于本机已有 SUMO 二进制，
> **安装该 wheel 是冗余的**——只需 `sumolib` + `traci` 即可驱动本地 SUMO。

### 2.3 完整仿真运行（实测，从零创建路网）

**步骤 1：编写节点/边/连接/需求文件**（最小 3 节点 2 边路网，600 veh/h）

**步骤 2：`netconvert` 生成路网**

```
$ F:\SUMO\bin\netconvert.exe -n demo.nod.xml -e demo.edg.xml -x demo.con.xml -o demo.net.xml
Success.
```

**步骤 3：`sumo` 执行仿真（原始输出）**

```
$ F:\SUMO\bin\sumo.exe -c demo.sumocfg --no-step-log --duration-log.statistics
Simulation version 1.27.0 started with time: 0.00.
Simulation ended at time: 200.00.
Reason: The final simulation step has been reached.
Performance:
 Duration: 0.01s
 Real time factor: 25000
 UPS: 33125.000000
Vehicles:
 Inserted: 17
 Running: 0
 Waiting: 0
Statistics (avg of 17):
 RouteLength: 195.00
 Speed: 12.62
 Duration: 15.59
 WaitingTime: 0.00
 TimeLoss: 0.80
 DepartDelay: 0.00
```

**判定：SUMO 的建网 → 仿真 → 统计输出全链路在本机真实跑通。**

### 2.4 `sumolib` 读取路网（实测）—— 对"空间单元映射"直接有用

```python
import sumolib
net = sumolib.net.readNet("demo.net.xml")
```

实际输出：

```
network read OK
  edges: ['AB', 'BC']
  nodes: ['A', 'B', 'C']
  edge AB: from=A to=B len=100.0m lanes=2 speed=13.89
  edge BC: from=B to=C len=100.0m lanes=2 speed=13.89
```

**这正是把 SUMO 路网映射为本项目"空间单元 + 邻接关系"所需的最小信息集**：
- `edge` → 可作为**空间单元**（或单元之间的连接段）；
- `from/to` → 直接给出**有向邻接**（对应模型规范的 `E`）；
- `length` / `speed` → 可直接换算为**通行成本 `c_ij`**；
- `lanes` → 可作为**容量 `C_i`** 的物理代理量。

---

## 3. CityFlow —— 源码已落盘；**无法编译**（缺 MSVC）

### 3.1 获取状态

✅ 源码已落盘：`deploy/repos/CityFlow`（70 个文件）

```
CityFlow/
├─ src/           # C++ 引擎源码
├─ extern/        # 第三方依赖（git submodule）
├─ frontend/  docs/  examples/  tests/  tools/
├─ CMakeLists.txt  setup.py  Dockerfile  README.rst  LICENSE.txt
```

### 3.2 构建可行性判定

**结论：REQUIRES-COMPILER-NOT-AVAILABLE（本机无法构建）**

理由（实测）：
- 构建系统为 **CMake**（`CMakeLists.txt`、`src/CMakeLists.txt`、`tests/CMakeLists.txt`）；
- 本机 `Get-Command cmake` → **MISSING**；`cl`（MSVC）→ **MISSING**；
  `gcc`/`g++` → **MISSING**；`ninja` → **MISSING**；
- 无 `C:\Program Files\Microsoft Visual Studio`；
- 并且 `extern/` 依赖 **git submodule**，
  而本机 `git clone` 因 GitHub DNS 劫持**不可用**，
  submodule 无法初始化（这是额外的、本项目特有的障碍）。

### 3.3 PyPI 分发：不存在

```
$ py -3.13 -m pip download cityflow --no-deps -i https://pypi.org/simple/
ERROR: No matching distribution found for cityflow
```

```
$ py -3.13 -m pip index versions cityflow
ERROR: No matching distribution found for cityflow
```

**判定：CityFlow 没有官方 PyPI wheel，只能源码编译。**

### 3.4 在具备编译环境的机器上完成构建的确切命令

```powershell
# 前置：Visual Studio 2022 (C++ 工作负载) + CMake >= 3.15
git clone --recursive https://github.com/cityflow-project/CityFlow.git   # 必须 --recursive 取 submodule
cd CityFlow
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
# Python 绑定
pip install .
# 验证
python -c "import cityflow; print(cityflow.__version__)"
```

> ⚠️ 注意：`--recursive` 在**本机不可能完成**（GitHub 被封）。
> 若在受限网络下工作，须改用代理逐一下载 submodule，或改用**有完整网络的机器**。

---

## 4. AB Street —— 仅元数据；**无法构建**（缺 cargo）

### 4.1 获取状态

⚠️ 仅获取到 API 元数据（`deploy/repos/abstreet/api-metadata.json`）。
仓库含大量地图资源，体积过大，经镜像下载失败（已记录原因）。

### 4.2 已确认的信息（经代理 raw 实测获取）

`Cargo.toml`（实测全文片段）证实这是一个 **Rust workspace**：

```toml
[workspace]
resolver = "2"
members = [
  "abstio", "abstutil", "apps/*", "blockfinding", "cli", "collisions",
  "convert_osm", "headless", "importer", "kml", "map_gui", "map_model",
  "piggyback", "popdat", "popgetter", ...
]
```

`LICENSE`（实测获取首行）确认为 **Apache License 2.0**。

### 4.3 构建可行性判定

**结论：REQUIRES-COMPILER-NOT-AVAILABLE（本机无法构建）**

理由：Rust 工具链缺失 —— `Get-Command cargo` → **MISSING**。

完成构建的确切命令（在具备 Rust 环境的机器上）：

```bash
rustup toolchain install stable
git clone https://github.com/a-b-street/abstreet.git
cd abstreet
cargo build --release
# 或 headless 模式（更适合批量情景推演）
cargo run --release --bin headless -- <scenario>
```

### 4.4 分析价值（不依赖构建）

作为**城市交通规划仿真**的参考实现，AB Street 的意义在于：

1. **规划情景的表达方式**：它以"编辑器修改街道 → 立即重跑仿真 → 看指标变化"
   为交互范式，与本研究"空间营建方案对比推演"的诉求一致，
   可作为**主试端交互设计**的参考。
2. **宏观指标口径**：其输出的通行时间、流量、拥挤指标，
   可作为本项目聚合模型**误差量化的对照基线**。
3. **人群规模假设**：其 agent 规模量级可为本项目"聚合 vs 个体"的复杂度对比提供参照。
4. ⚠️ 但其路线是**高保真、个体级**，工程成本高，
   正是本项目在 motivation 中要**对照**的对象，而非运行内核。

---

## 5. 许可证风险提示（对成果转化有直接影响）

| 项目 | License | 性质 | 风险与建议 |
|---|---|---|---|
| **SUMO** | **EPL-2.0** | **弱 copyleft** | ⚠️ **重点风险**。EPL-2.0 要求：分发包含 SUMO 的作品时，对 SUMO 本身的修改须以 EPL-2.0 开源，且须提供源码获取途径。**若本项目仅通过命令行/Python API 调用 SUMO（不改其源码）**，通常属"独立作品"使用，风险较低；但**不得**把 SUMO 源码并入自有闭源产品。**建议：仅作对照/标定用途，不嵌入交付物**；如须嵌入，咨询法务。 |
| CityFlow | Apache-2.0 | 宽松 | ✅ 可用于研究与非嵌入式集成；须保留 NOTICE 与版权声明 |
| AB Street | Apache-2.0 | 宽松 | ✅ 同上；注意其地图数据可能另有许可（需单独核对数据来源） |

> **行动项**：若本项目成果要转化（如申请软著或商业应用），
> 应在交付物中**明确排除 SUMO 源码**，仅以外部依赖方式调用，
> 并在文档中标注 EPL-2.0 依赖关系。

---

## 6. 可复用资产：从精细仿真到存量-流量聚合的映射

即使 CityFlow/AB Street 无法构建，其**数据格式与概念模型**对本项目仍有直接价值。
以下是"精细仿真概念 → 本项目聚合概念"的映射表：

| SUMO / 精细仿真概念 | 本项目聚合概念 | 映射说明 |
|---|---|---|
| `edge`（路段） | **空间单元** `u_i` | 路段即最小的空间聚集单位（实测已可读取） |
| `node`（节点） | 单元边界 / 交叉口 | 可合并入相邻单元 |
| `from`→`to`（边连接） | **邻接边** `(i,j) ∈ E` | 直接给出有向邻接（实测已可读取） |
| `edge.length` | **通行成本** `c_ij` | 或与速度结合得行程时间 |
| `edge.speed` | 通行成本折算 | `c_ij = length / speed` |
| `edge.numLanes` | **容量** `C_i` 的物理代理 | `C_i ∝ lanes × length` |
| `flow` / `route` 需求 | **外部流入** `b_i` / O-D 需求 | SUMO 需求文件可作为 b_i 的标定输入 |
| `taz`（交通分析小区） | **空间单元**（更粗粒度） | **最直接对应**：TAZ 分区天然是聚合单元 |
| 车辆轨迹输出（fcd） | **流量** `f_ij` 的估计源 | 把轨迹在时间上聚合即得流量 |
| 行人模块（JuPedSim） | 个体级对照模型 | 用于多尺度误差量化（模型规范 §7） |

**关键洞察**：SUMO 的 **TAZ（Traffic Analysis Zone）** 概念与本项目的
"空间单元"在**语义上完全对应**——这为本项目提供了一条
**低成本标定路径**：用既有交通模型的分区与需求数据初始化本项目的场景。

**建议的最小工作流**：
```
已有 SUMO 路网/需求（实测可读取）
  → sumolib 抽取 edge/node/adjacency/length/speed/lanes
  → 转换为本项目 configs/scenarios/*.json 的 units + edges
  → 运行聚合内核（src/core，已验证 24/24 测试通过）
  → 与 SUMO 个体仿真结果对比，量化聚合近似误差
```

---

## 7. 结论

| 项目 | 获取 | 构建/运行 | 判定 |
|---|---|---|---|
| **SUMO 1.27.0** | ✅ 本机已安装（含 JuPedSim 行人模块） | ✅ **netconvert + sumo 完整跑通**；sumolib 读取路网成功 | **RUNNABLE** ✅ |
| SUMO 源码归档 | ⚠️ 不完整（体积/带宽） | 无需源码即可运行 | 源码非必需 |
| **CityFlow** | ✅ 源码已落盘（70 文件） | ❌ 缺 MSVC + CMake + 无 PyPI wheel + submodule 不可取 | **REQUIRES-COMPILER-NOT-AVAILABLE** |
| **AB Street** | ⚠️ 仅元数据（仓库过大） | ❌ 缺 cargo | **REQUIRES-COMPILER-NOT-AVAILABLE** |

### 本 Lane 的三项核心产出

1. **纠正了一个错误前提**：原判断"无编译器故 SUMO 不可用"是**错的**——
   本机**已安装 SUMO 1.27.0 预编译二进制**，且带 **JuPedSim 行人动力学**模块。
   已完成从建网到仿真到统计的**完整端到端验证**。
2. **给出了可直接使用的空间映射路径**：`sumolib` 可读取 `edge/from/to/length/speed/lanes`，
   恰好覆盖本项目"空间单元 + 邻接 + 通行成本 + 容量"的全部输入需求，
   并指出 SUMO 的 **TAZ 概念与"空间单元"语义对应**。
3. **明确了许可证风险**：SUMO 为 **EPL-2.0 弱 copyleft**，
   是四个上游项目中**唯一**对成果转化构成实质约束的依赖，
   须在交付物中与自有代码隔离。

### 后续可立即开展的工作

- [ ] 编写 `scripts/sumo_to_units.py`：用 `sumolib` 把 SUMO 路网转为本项目场景 JSON
- [ ] 在演示场景上做"聚合内核 vs SUMO 个体仿真"的误差量化（对应假设 H4）
- [ ] 核对 AB Street 地图数据许可证（与代码许可可能不同）
- [ ] 评估 CityFlow 是否有必要在 Linux CI 上构建（当前判断：非必需，SUMO 已足够）
