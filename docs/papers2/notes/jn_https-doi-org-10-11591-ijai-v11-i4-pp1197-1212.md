# Simulation of pedestrian movements using a fine grid cellular automata model

- 作者/年份/来源: Siamak Sarmady, Fazilah Haron, Abdullah Zawawi Talib / 2022 / IAES International Journal of Artificial Intelligence (IJ-AI), Vol. 11, No. 4, pp. 1197-1212
- 主题: D（基于元胞自动机的行人流微观仿真建模方法）

## 研究问题
常规元胞自动机模型以行人身体大小划分单元格，每人只占一格，移动如棋盘棋子般不连续，且所有人尺寸与速度相同，无法刻画异质行人。

## 方法
提出细网格元胞自动机模型，用小单元格并允许行人身体占据多个单元，支持不同体型、形状与速度的行人，并模拟其朝特定目标点的移动。

## 数据
该文摘要未说明具体数据，仅以典型通道场景测试并与经验速度—密度曲线对比。

## 主要结论
细粒度离散使行人移动更平滑，仿真结果与经验速度—密度图吻合良好。

## 对本课题的可借鉴点
细网格与"一人占多格"实现了空间单元与主体粒度解耦：本课题以空间单元为存量、单元间移动为流量，可借细网格降低离散化带来的流量分配误差，并让真人被试与 LLM 合成主体共享同一格网与异质参数。

## 局限
该文摘要未说明；验证仅限典型通道场景。
