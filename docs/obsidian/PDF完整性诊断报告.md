# PDF 完整性诊断报告

> 记录一次**真实的失败与修复**，以及由此得到的校验方法修正。
> 目的是避免后续重复踩坑。

---

## 1. 结论先行

首批 28 篇文献 PDF 中，经**逐文件独立进程复测**：
**23 篇可正常提取文字，5 篇确为损坏**（打开后 0 页）。

**两条关键教训**（均由实测证伪得出）：

1. **不能用「文件尾部是否含 `%%EOF`」判断完整性。**
   该判据在**两个方向上都错了**：既把 3 个完全可用的文件误判为损坏
   （`Piao2025_AgentSociety`、`Park2024_SelfReportSimulation`、`Zaitsev2023_Cormas`），
   也漏掉了若干真正截断的文件（它们根本没有 trailer）。
2. **本机的 PDF 下载通道会损坏大文件。**
   同一 URL 多次下载得到的**字节数与大小互相矛盾**
   （声明 `/L 3563209` 却只收到 2,160,948 字节；
   某次声明 1,750,890 字节却收到 5,009,894 字节）。
   说明链路上存在**中间设备改写**，而非简单的下载中断。

**唯一可信的判据**：用 PyMuPDF 打开并统计可提取字符数（见 §3）。

---

## 2. 三个被证伪的假设（按发现顺序）

### 假设一：「文件尾部有 `%%EOF` 才算完整」 —— **双向错误**

初判：28 篇中 8 篇缺失 `%%EOF`，判定为截断。
该判断随后被证明**在两个方向上都不成立**：

| 文件 | `%%EOF` | 实际可读性 | 说明 |
|---|---|---|---|
| `Piao2025_AgentSociety` | 缺失 | ✅ 49 页 / 178,975 字符 | **假阳性**：被判损坏，实为可用 |
| `Park2024_SelfReportSimulation` | 缺失 | ✅ 86 页 / 224,998 字符 | **假阳性** |
| `Zaitsev2023_Cormas` | 缺失 | ✅ 10 页 / 24,428 字符 | **假阳性** |
| `Feygin2019_BISTRO` | 缺失 | ❌ 0 页 | 真损坏 |
| `Qiu2025_LockInHypothesis` | 缺失 | ❌ 0 页 | 真损坏 |

同时，部分**真正截断**的文件（如 `Fang2021`）**根本没有 trailer**，
因此该判据**也无法可靠地发现损坏**——即假阴性同样存在。

**修正**：废弃该判据。

### 假设二：「pypdf 抽取失败 = PDF 损坏」

`pypdf` 对多个文件报 `EOF marker not found`。

**证伪**：同样文件用 **PyMuPDF 成功抽取**——
`Piao2025_AgentSociety` 用 pypdf 失败，用 PyMuPDF 得到 **17.9 万字符**。

**修正**：PyMuPDF (fitz 1.27.2.3) 的容错能力显著强于 pypdf，**应作为首选抽取器**。

### 假设三：「HTTP 200 + 文件够大 = 下载成功」

`curl` 返回 200 且文件 1–6 MB，但其中 5 个打不开。

**修正**：下载后必须做**内容级校验**（PyMuPDF 能否打开），不能只看状态码与体积。

### 补充发现：`/L`（linearization 声明长度）是有用的**辅证**

带线性化头的 PDF 会在头部声明完整文件长度 `/L <n>`。
`实际字节数 < 声明 /L` 是**廉价且强**的截断证据：

```
Fang2021_FlowAggregation.pdf      actual 2,414,720  declared /L 2,820,395  -> TRUNCATED
Park2024_SelfReportSimulation.pdf actual 2,160,948  declared /L 3,563,209  -> TRUNCATED
```

**但**：28 篇中只有 2 篇带 `/L`，**覆盖率太低**，不能作为主判据，
只能作为"命中即高度可疑"的辅助信号。**主判据仍是 PyMuPDF 可读性。**

### 补充发现：下载通道存在**内容改写**

同一 URL 多次下载，声明大小与实际收到大小**互相矛盾**：

```
www.arxiv.org/pdf/2304.03442v2  ->  声明 1,750,890 B  /  实收 5,009,894 B
arxiv.org/pdf/2304.03442v2      ->  实收 5,059,046 B（同样 0 页）
```

不同路径拿到**不同字节数、且都不可用**。这是中间设备改写内容的典型特征。
**结论**：本机环境下，**大体积 PDF 的下载结果不可信任**，必须逐文件内容级校验。

---

## 3. 权威校验方法（已固化为流程）

```python
import fitz

def pdf_status(path) -> tuple[int, int]:
    """返回 (页数, 可提取字符数)。"""
    doc = fitz.open(str(path))
    chars = sum(len((page.get_text() or "").strip()) for page in doc)
    pages = len(doc)
    doc.close()
    return pages, chars

# 判据（唯一权威）：
#   pages > 0 且 chars > 1000   -> extracted（可用）
#   pages == 0 或 chars <= 1000 -> failed / needs_review（损坏或无文字层）
```

**流程纪律**：
1. 先下载到**临时路径**；
2. 用上述函数校验；
3. **校验通过才原子替换**目标文件；
4. **绝不先删除再下载**（本报告 §5 的事故即由违反此条造成）。

---

## 4. 已实测的 28 篇状态（逐文件独立进程复测）

### 4.1 可用（23 篇，`extracted`）

21 篇首批即可用，另有 **2 篇经修复恢复**：

| 恢复的文件 | 修复动作 | 修复后 |
|---|---|---|
| `Park2024_SelfReportSimulation` | 重新下载（根因：**我误将完好文件覆盖为截断文件**） | 86 页 / 224,998 字符 |
| `Zaitsev2023_Cormas` | 经 arXiv 检索确认来源为 **2310.12534** 后重下 | 10 页 / 24,428 字符 |

### 4.2 损坏、需重下（5 篇，`failed`）

**均为：打开后 0 页 / 0 字符。**

| 文件 | 体积 | 来源可追溯性 |
|---|---|---|
| `Fang2021_FlowAggregation.pdf` | 2.4 MB | ❌ 无 source_id；`/L` 证明截断。需人工定位来源 |
| `Feygin2019_BISTRO.pdf` | 2.5 MB | ⚠️ arXiv 检索到疑似 `1908.03821`（Berkeley Integrated System for Transportation Optimization），**待人工确认是否同一篇** |
| `Park2023_GenerativeAgents.pdf` | 2.8 MB | ✅ 书目已由 **arXiv API 确认**：2304.03442，Generative Agents: Interactive Simulacra of Human Behavior，作者 Joon Sung Park 等 6 人。**但 PDF 多路径重下均损坏**（含 `www.arxiv.org` 与直连），属通道改写导致，非来源问题 |
| `Qiu2025_LockInHypothesis.pdf` | 6.3 MB | ❌ 无 source_id（元数据显示为 macOS Keynote 导出） |
| `Wang2021_DigitalTwinIntersection.pdf` | 969 KB | ❌ 无 source_id |

**处置原则**：
- 这 5 篇**不得在论文中引用为已读文献**，除非取得可用全文；
- 其中 `Park2023_GenerativeAgents` 的**书目信息已核实可用**
  （arXiv API 原文返回），可作为"仅元数据、全文待补"的条目，
  但**不能声称已阅读全文**；
- `Feygin2019_BISTRO`、`Qiu2025`、`Wang2021`、`Fang2021` 连来源都未确认，
  **必须人工核实后才能进入文献表**。

### 4.3 可用的替代方案（针对 Park2023）

`ar5iv` 提供该文的 HTML 渲染版且可取：

```
https://ar5iv.labs.arxiv.org/html/2304.03442   -> HTTP 200, 259,872 B
```

可作为"正文可读"的**替代来源**（非原始 PDF）。
若采用，须在笔记中**明确标注为 ar5iv HTML 转换文本**，与 PDF 原件区分。

---

## 5. 需要记录的流程事故（诚实记录）

在修复过程中，我基于**已被证伪的 `%%EOF` 判据**执行了删除动作，
导致 `Park2023_GenerativeAgents`、`Piao2025_AgentSociety`、
`Park2024_SelfReportSimulation` 三个文件一度从 `docs/papers/pdf/` 消失。

- **影响**：并行的 Lane O（Obsidian 导入）检测到目录变动并报告阻塞；
  目录文件数一度由 28 降至 25。
- **恢复**：三个文件均从临时副本恢复，**目录已回到 28 个文件，与 index.json 完全一致**。
- **教训**：
  1. 未经**内容级验证**不要删除源文件——先把新文件校验通过再替换；
  2. 多人并行时，写目录前应先在共享任务板登记，避免对同一目录并发写；
  3. 校验方法出错时，错误会沿流程**放大**（误判 → 误删 → 他人阻塞）。

---

## 6. 给后续工作的建议

1. **抽取器**：一律用 PyMuPDF；不要因为 pypdf 报错就判定文件损坏。
2. **下载校验**：写成一个函数，落盘前调用；失败时**重试一次**再标记失败。
3. **替换策略**：下载到临时路径 → 校验通过 → 原子替换；**绝不先删后下**。
4. **状态语义**：`extracted` / `needs_review` / `failed` 三态要如实标注，
   `semantic_verified` 在人工核验前**恒为 false**。
5. **引用纪律**：无 `source_id` 且未核实的条目，不得进入论文引用。
