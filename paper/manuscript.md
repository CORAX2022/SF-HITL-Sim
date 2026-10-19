# 总稿导航与写作看板

**中文标题**：存量—流量空间建模驱动的参与式交互仿真：面向公共空间人员流动治理的人机协同实验平台

**English Title**：Participatory Interactive Simulation Driven by Stock–Flow Spatial Modelling:
A Human–Machine Collaborative Experimental Platform for Public-Space Pedestrian-Flow Governance

| 项目 | 内容 |
| --- | --- |
| 作者 | 待补 |
| 单位 | 待补 |
| 通讯作者 | 待补 |
| 稿件版本 | **v0.1.0** |
| 目标刊/会 | 备选三选一（《城市规划学刊》/ CEUS / CHI·CSCW），未定，见 [`README.md`](README.md) §2 |
| 当前阶段 | 写作脚手架 + 摘要/引言/综述草稿；平台离线验证完成，真人实验未开展 |

> 本文件**只做导航与状态看板**，不承载正文。正文一律写在
> [`sections/`](sections/) 下的章节文件中；导出方式见 §4。

---

## 1. 章节状态表

状态取值仅四种：**待写 / 初稿 / 修订中 / 定稿**（定义见 [`README.md`](README.md) §5.1）。
字数目标为**中文字符数**（摘要含英文另计）；"素材来源"列只列主证据，
完整清单见 [`README.md`](README.md) §8。

| 章节 | 文件 | 状态 | 字数目标 | 素材来源 |
| --- | --- | --- | --- | --- |
| 00 摘要与关键词 | [`sections/00-摘要与关键词.md`](sections/00-摘要与关键词.md) | 初稿 | 400（另英文约 300 词） | 全文定稿后回写；当前依据 `docs/research/`、`docs/model/`、`data/demo/` |
| 01 引言 | [`sections/01-引言.md`](sections/01-引言.md) | 初稿 | 1500 | `docs/research/研究缺口与选题论证.md`、`docs/literature/文献综述.md` |
| 02 文献综述与研究缺口 | [`sections/02-文献综述与研究缺口.md`](sections/02-文献综述与研究缺口.md) | 初稿 | 2500 | `docs/literature/文献综述.md`、两份 `index.json`、`references.bib` |
| 03 研究框架与模型 | [`sections/03-研究框架与模型.md`](sections/03-研究框架与模型.md) | 初稿 | 3000 | `docs/model/存量-流量模型规范.md` |
| 04 平台设计与实现 | [`sections/04-平台设计与实现.md`](sections/04-平台设计与实现.md) | 初稿 | 2500 | `docs/architecture/系统架构.md`、`src/core/`、`src/actors.py` |
| 05 实验设计与数据采集 | [`sections/05-实验设计与数据采集.md`](sections/05-实验设计与数据采集.md) | 待写 | 2000 | `docs/model/` §6、`docs/architecture/` §4、`docs/research/` §5 |
| 06 结果与验证 | [`sections/06-结果与验证.md`](sections/06-结果与验证.md) | 初稿 | 1800 | `tests/test_core.py`、`examples/run_loop.py`、`data/demo/`、`docs/nlogo/` |
| 07 讨论与局限 | [`sections/07-讨论与局限.md`](sections/07-讨论与局限.md) | 初稿 | 1500 | `docs/model/` §8、`docs/architecture/` §7、`docs/research/` §7 |
| 08 结论与展望 | [`sections/08-结论与展望.md`](sections/08-结论与展望.md) | 待写 | 800 | 全文章节汇总 |

**合计目标**：约 15,000 中文字符 + 英文摘要约 300 词。

> **字数目标 = 定稿目标**，不是当前字数。现有初稿中 01、02 两章已超出目标
> （01 约 1800 汉字 vs 目标 1500；02 约 3000 汉字 vs 目标 2500），
> 这是"先写实、再压缩"的刻意选择；进入"修订中"状态时按目标压缩，
> 而不是删除证据。

### 1.1 可写性判据

| 章节 | 是否可写 | 依据 |
| --- | --- | --- |
| 00–02 | ✅ 可写 | 研究定位、模型与文献证据齐全 |
| 03–04 | ✅ 可写 | 规范文档与代码均已落地（内核可运行） |
| 05 | ⚠️ 可写"设计"，不可写"结果" | 实验尚未实施；只能写计划、变量、分析方案 |
| 06 | ✅ 部分可写 | 有单测、守恒、闭环、外部模型复现；**无真人实验** |
| 07 | ✅ 可写 | 局限已在 `docs/model/` §8 与 `docs/architecture/` §7 明确列出 |
| 08 | ⚠️ 需等 05/06 定稿 | 结论不能超过已验证范围 |

---

## 2. 写作顺序建议

按"证据确定性"排序，先写能写实的，再写需要实验支撑的：

1. **02 文献综述**（证据最全）→ 反过来校准 01 引言的缺口表述；
2. **01 引言**（依赖 02 的缺口结论）；
3. **03 研究框架与模型**（有形式化规范，改写成本低）；
4. **04 平台设计与实现**（有代码与架构文档）；
5. **06 结果与验证**（有可核验数值，写法最容易失控，必须最后定稿数据口径）；
6. **07 讨论与局限**（依赖 03/04/06 的结论）；
7. **05 实验设计**（真人实验方案，需与伦理审查同步修订）；
8. **08 结论**（等 05/06 定稿后再写）；
9. **00 摘要**（**最后写**，从定稿正文回写）。

> **反例警示**：先写摘要再写正文，会让摘要承诺超出正文能兑现的范围——
> 当前摘要草稿已按"平台已实现、实验未开展"的口径写，必须随正文迭代。

---

## 3. 写作看板（按状态聚合）

| 状态 | 章节 | 下一步动作 |
| --- | --- | --- |
| 初稿 | 00、01、02、03、04、06、07 | 交叉评审 → 修订中 |
| 待写 | 05、08 | 05 待伦理审查与预实验确定参数后成文；08 待 05/06 定稿后成文 |
| 修订中 | — | — |
| 定稿 | — | — |

看板更新规则：

- 章节文件 `## 状态` 节与本节**同时**更新；
- 状态迁移必须伴随一次 git 提交（`docs(paper): 02 综述 初稿→修订中`）；
- 禁止只改看板不改章节文件。

---

## 4. 导出说明

### 4.1 一次性导出（正文区抽取 + pandoc）

```powershell
New-Item -ItemType Directory -Force build | Out-Null

$body = foreach ($f in (Get-ChildItem paper/sections/*.md | Sort-Object Name)) {
    $lines = Get-Content -LiteralPath $f.FullName -Encoding utf8
    $start = [array]::IndexOf($lines, '<!-- BODY-START -->')
    $end   = [array]::IndexOf($lines, '<!-- BODY-END -->')
    if ($start -lt 0 -or $end -lt 0) { throw "缺少 BODY 标记：$($f.Name)" }
    $lines[($start + 1)..($end - 1)]
}
$body | Set-Content -LiteralPath build/manuscript-body.md -Encoding utf8

pandoc build/manuscript-body.md `
  -o build/manuscript.docx `
  --citeproc --bibliography=paper/references.bib `
  --resource-path=paper `
  --number-sections --toc --toc-depth=2
```

### 4.2 导出 PDF（需 xelatex）

```powershell
pandoc build/manuscript-body.md `
  -o build/manuscript.pdf `
  --pdf-engine=xelatex `
  -V CJKmainfont="Microsoft YaHei" -V mainfont="Times New Roman" `
  --citeproc --bibliography=paper/references.bib `
  --resource-path=paper `
  --number-sections --toc
```

### 4.3 环境检查

```powershell
pandoc --version
xelatex --version   # 仅 PDF 需要
```

**约定**：

- `build/` 为临时产物目录，**不入库**；不要在 `paper/` 下堆放导出文件。
- 导出前确认 `pandoc --citeproc` 无未解析引用警告（警告即视为构建失败）。
- 图表引用用相对路径（如 `figures/fig-06-01-....png`），配合
  `--resource-path=paper` 解析。
- 图中文字体、表注格式按
  [`docs/writing/风格指南.md`](../docs/writing/风格指南.md) 执行；
  表格另存为 Markdown 片段时见 [`tables/README.md`](tables/README.md)。

---

## 5. 定稿前的"事实核对"关卡

导出前逐条核对，**任一不通过则不得标记定稿**：

1. 正文中每个数字都能在 `paper/README.md` §8 的素材表里指到文件；
2. `grep -r "TODO" paper/references.bib` 的条目已全部核实或删除；
3. 无旧题名残留（旧题名不在本论文中使用）；
4. 无"已开展真人实验""显著""被试认为"等未发生的表述；
5. 图表编号与 `figures/`、`tables/` 目录中的文件一一对应；
6. 全文术语与 [`docs/writing/术语表.md`](../docs/writing/术语表.md) 一致。
