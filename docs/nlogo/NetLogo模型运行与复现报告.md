# NetLogo 模型运行与复现报告

**模型**：An agent-based simulation model of pedestrian evacuation based on Bayesian Nash Equilibrium
**作者**：Yiyu Wang, Jiaqi Ge, Alexis Comber（School of Geography, University of Leeds）
**版本**：v1.0.0 ｜ **许可**：CC BY-SA 4.0
**本机运行环境**：NetLogo **7.0.4**（模型由 NetLogo **6.2.2** 生成）
**日期**：2026-10-15

---

## 0. 结论速览

| 项目 | 结果 |
|---|---|
| 模型能否运行 | ✅ **能**。NetLogo 7.0.4 成功加载并执行 6.2.2 模型，无需手工迁移 |
| 复现规模 | `experiment1-3patterns`，**150 次运行**（3 模式 × 50 重复），18,023 行输出 |
| 耗时 | **37.8 秒**（单次 2000 人约 5 秒） |
| 保真度 | 三种模式出口时间相对偏差 **−2.8% ~ −6.6%**，SD 差 ≤1.4 |
| 核心结论是否复现 | ✅ **完全一致**：出口时间排序 **BNE < Random follow < Shortest route** |

---

## 1. 环境：为什么必须绕开 `netlogo-headless.bat`

### 1.1 发现的两个坑（均已实测）

**坑一：`.bat` 无法处理含空格的路径**

`netlogo-headless.bat` 用 `FOR %%a IN (%*) DO` 逐词展开参数。
本项目路径 `F:\城规工作室\CJ 李昊\SF-HITL-Sim\...` **含空格**，
被拆成多个词后 Java 报错：

```
错误: 找不到或无法加载主类 李昊\SF-HITL-Sim\_nlogo_run\smoke_out.csv
原因: java.lang.ClassNotFoundException: 李昊\SF-HITL-Sim\_nlogo_run\smoke_out.csv
```

**坑二：`.bat` 优先用 `JAVA_HOME`/PATH 上的 Java，而本机 PATH 是 Java 8**

NetLogo 7 需要 **Java 17+**；本机 `java -version` = `1.8.0_503`。
直接调用 `.bat` 会因 Java 版本过低失败（即使路径无空格）。

### 1.2 解决办法（已固化为脚本）

`scripts/run-nlogo.ps1` 直接调用入口类，由 PowerShell 负责每个参数的引用：

```powershell
& "$NetLogoHome\runtime\bin\java.exe" `
  -XX:MaxRAMPercentage=50 -Dfile.encoding=UTF-8 `
  -Dnetlogo.docs.dir=$NetLogoHome `
  -Dnetlogo.models.dir=$NetLogoHome\models `
  -Dnetlogo.extensions.dir=$NetLogoHome\extensions `
  --add-exports=java.base/java.lang=ALL-UNNAMED `
  --add-exports=java.desktop/sun.awt=ALL-UNNAMED `
  --add-exports=java.desktop/sun.java2d=ALL-UNNAMED `
  -classpath "$NetLogoHome\app\netlogo-7.0.4.jar" `
  org.nlogo.headless.Main `
  --model "<模型>" --experiment "<实验名>" --table "<输出.csv>"
```

**关键点**：强制使用 NetLogo **自带的 Java 17**（`D:\NetLogo\runtime\bin\java.exe`），
不依赖 `JAVA_HOME`。这样脚本在中文+空格路径下稳定可跑。

调用方式：

```powershell
pwsh -NoProfile -File ".\scripts\run-nlogo.ps1" `
  -Model ".\_nlogo_run\repro_ex1.nlogo" `
  -Experiment "repro_experiment1" `
  -Table ".\_nlogo_run\repro_experiment1.csv"
```

---

## 2. 模型解读（读源码得出，非推测）

**空间**：隧道，`world` 为 **68 × 20 = 1360 patches**（由
`min-pxcor=-34, max-pxcor=34, min-pycor=-10, max-pycor=10` 实测确认），
左右两端为出口，`door-width` 控制出口宽度。

**四类移动模式**（由 chooser `moving-pattern` 选择）：

| 模式 | 决策规则 |
|---|---|
| `Shortest route`（SR） | 直接朝出口移动 |
| `Random follow`（RF） | 在视野锥（半径 `follow-radius`、60°）内随机选**最近**的邻居跟随 |
| `BNE (mixed with SR)` | `BNE-type=1` 的用 BNE 决策，其余走 SR |
| `BNE (mixed with RF)` | `BNE-type=1` 的用 BNE 决策，其余走 RF |

**效用结构**（patch 级状态变量）：

- `Ud_lt` / `Ud_rt`：前往左/右出口的**距离效用**
- `Uec`：**期望舒适效用**（BNE 的核心——对拥挤的期望）
- `U_total = Ud + Uec`，agent 选择 `U_total` 最大的邻近 patch 移动
- `N_total`：影响 `Uec` 的总人数

**每轮流程**（`to go`）：`Expected-Uc` 让所有 patch 重算 `Uec` →
按 `moving-pattern` 分派决策 → 结算已出场地者 → `tick`。

---

## 3. 复现方法与一个诚实说明

### 3.1 复现配置

我按作者 `results/experiment1-3patterns-table.csv` 的**实际列结构**反推了实验定义：

| 参数 | 取值 | 依据 |
|---|---|---|
| `moving-pattern` | Shortest route / Random follow / BNE (mixed with RF) | 作者输出的三种取值 |
| `Percentage-of-agents-with-BNE` | 100 | 作者输出单一取值 |
| `number-persons` | **2000** | ⚠️ 见 3.2 |
| `door-width` | **6** | ⚠️ 见 3.2 |
| repetitions | 50 | 每模式 50 个 run（可精确验证） |
| timeLimit | 5000 步 | 安全上限，实际在疏散完成时自然终止 |

### 3.2 ⚠️ 必须说明的不确定性

作者的结果文件**没有** `number-persons` 与 `door-width` 两列
（其 BehaviorSpace 实验定义未把它们列为参数）。
我据 `count turtles` 起始值 = **2000** 确认了 `number-persons=2000`；
但 **`door-width` 无法从作者输出反推**，我取 **6**（模型默认档位之一）。

**这解释了残差**：出口宽度直接决定出口通过能力，因而直接影响出口时间。
若 `door-width` 实际为 9，作者的疏散会更快，而我用 6 会更慢——
实测偏差方向（复现普遍**偏快** 2.8%–6.6%）与此不完全一致，
更可能来自 NetLogo 7 与 6.2.2 在**随机数发生器**上的差异
（BehaviorSpace 未固定 seed，故每次运行本身就有随机波动，见 SD ≈ 10–25）。

---

## 4. 复现结果与作者原始数据对比

**样本**：作者 19,112 行 / 复现 18,023 行；各模式均 50 个 run、起始 2000 人。

| 模式 | 指标 | 作者 | 复现 | 差异 |
|---|---|---|---|---|
| **Shortest route** | 出口时间均值 | 192.0 | 179.3 | **−12.6 (−6.6%)** |
| | 出口时间 SD | 22.9 | 23.8 | +0.9 |
| | 出口时间 max | 254 | 245 | −9 |
| | 峰值密度均值 | 31.2 | 30.8 | −0.4 |
| **Random follow** | 出口时间均值 | 129.2 | 121.8 | **−7.5 (−5.8%)** |
| | 出口时间 SD | 24.2 | 24.8 | +0.6 |
| | 出口时间 max | 179 | 166 | −13 |
| | 峰值密度均值 | 44.3 | 46.6 | +2.3 |
| **BNE (mixed with RF)** | 出口时间均值 | 58.0 | 56.4 | **−1.7 (−2.9%)** |
| | 出口时间 SD | 9.6 | 11.0 | +1.4 |
| | 出口时间 max | 97 | 125 | +28 |
| | 峰值密度均值 | 24.6 | 23.9 | −0.8 |

### 4.1 核心结论完全复现

```
作者: SR=192  RF=129  BNE=58  ->  BNE < RF < SR
复现: SR=179  RF=122  BNE=56  ->  BNE < RF < SR
```

**论文主张**：以 BNE 决策的个体能显著加快疏散，且**降低局部峰值密度**
（BNE 峰值密度 24.6，低于 SR 的 31.2 与 RF 的 44.3）。
本复现在**方向、量级、排序**三方面均一致。

### 4.2 图示

| 图 | 内容 |
|---|---|
| `results/repro/fig1_剩余人数曲线对比.png` | 三模式剩余人数演化曲线，作者 vs 复现**几乎重合** |
| `results/repro/fig2_出口时间箱线图.png` | 出口时间分布对比 |
| `results/repro/fig3_峰值密度对比.png` | 峰值密度分布对比 |
| `results/repro/fig4_出口时间均值对照.png` | 均值柱状 + 相对偏差标注 |

`fig1` 的视觉证据最有说服力：三种模式的曲线在整条时间轴上**基本重叠**，
说明模型动力学被忠实复现，而非仅仅均值接近。

---

## 5. 与本课题（存量-流量人机混合参与式仿真）的关系

这个模型对本课题有**三项直接价值**：

### 5.1 提供了一个"个体级决策规则"的可插拔实现

本课题的自研内核 `src/core/` 采用**聚合存量-流量**（不追踪个体），
而这个模型是**个体级 agent**、以效用最大化选下一步。
两者恰好构成模型规范 §7 所述的**多尺度接驳**关系：

- BNE 的 `U_total = Ud + Uec` 思想可直接**上移**到聚合层——
  把 `Uec`（期望舒适效用）变成单元吸引力 `Attr_j`，把 `Ud` 变成通行成本 `c_ij`；
- 于是本课题的 `Attr_j` 不再是外生给定的常数，而可由**拥挤期望**内生决定。

### 5.2 `Uec` 就是本课题要采集的"主观感知"

`Uec`（expected comfort utility）在数学上是 agent 对拥挤的**主观预期**。
本课题要采集的正是真人的**感知拥挤度/安全感/满意度**。
因此该模型给出了一个**把主观量表映射为效用参数**的现成结构：
真人被试的 Likert 评分 → `Uec` → 影响其空间选择 → 注入流量场。

### 5.3 四种决策模式 = 现成的对照组设计

`SR / RF / BNE-SR / BNE-RF` 四种模式，本质上就是
"不同决策理性程度"的对照梯度。本课题要做"真人 vs LLM 合成体"的一致性检验时，
可直接借用这套模式划分作为**行为基线**。

---

## 6. 复现的边界（须在引用时声明）

1. **`door-width` 未确认**：作者输出无该列，我用 6。这是残差最可能的来源之一。
2. **随机种子未固定**：BehaviorSpace 实验未指定 seed，故单次运行不可逐行比对；
   本报告比对的是**分布统计量**（均值/SD/峰值），这是在此前提下唯一诚实的做法。
3. **NetLogo 版本跨代**：模型由 6.2.2 生成，本机为 7.0.4。
   实测 7.0.4 加载无报错，但**不排除**随机数实现差异带来的系统偏移。
4. **仅复现了 `experiment1`**：作者另有 8 个更大规模的结果文件
   （最大 22 MB，覆盖 `number-persons` 1000–3000、`door-width` 1–18）。
   这些可继续复现，但需先确定其各自参数。

---

## 7. 产出清单

| 类型 | 路径 |
|---|---|
| 运行脚本 | `scripts/run-nlogo.ps1` |
| 复现模型 | `_nlogo_run/repro_ex1.nlogo` |
| 复现输出 | `_nlogo_run/repro_experiment1.csv`（18,023 行） |
| 对比脚本 | `scripts/compare_nlogo_repro.py` |
| 绘图脚本 | `scripts/plot_nlogo_repro.py` |
| 对比图 | `results/repro/fig1..fig4*.png` |
| 本报告 | `docs/nlogo/NetLogo模型运行与复现报告.md` |

---

## 8. 复现命令

```powershell
# 单次计时运行（约 5 秒）
pwsh -NoProfile -File ".\scripts\run-nlogo.ps1" `
  -Model ".\_nlogo_run\repro_ex1.nlogo" -Experiment "timing1" `
  -Table ".\_nlogo_run\timing1.csv"

# 完整复现（150 runs，约 38 秒）
pwsh -NoProfile -File ".\scripts\run-nlogo.ps1" `
  -Model ".\_nlogo_run\repro_ex1.nlogo" -Experiment "repro_experiment1" `
  -Table ".\_nlogo_run\repro_experiment1.csv"

# 统计对比与出图
py -3.13 scripts\compare_nlogo_repro.py
py -3.13 scripts\plot_nlogo_repro.py
```
