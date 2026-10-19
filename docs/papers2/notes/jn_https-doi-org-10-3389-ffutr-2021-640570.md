# Assignment Matrix Free Algorithms for On-line Estimation of Dynamic Origin-Destination Matrices

- 作者/年份/来源: Marisdea Castiglione, Guido Cantelmo, Moeid Qurashi, Marialisa Nigro, Constantinos Antoniou / 2021 / Frontiers in Future Transportation, 2:640570
- 主题: D — 交通与行人流仿真、动态OD需求在线估计建模

## 研究问题
DTA在线标定中，动态OD需求估计有三重困难：变量多于观测、关系非线性、需求有结构，且依赖难获取的分配矩阵。

## 方法
提出PCA-LETKF：用主成分分析降维并捕捉空间相关性，结合局部集合变换卡尔曼滤波；无需分配矩阵，分配由仿真器承担，可融合多源数据。

## 数据
先以合成实验作基准，再在西班牙Vitoria路网(2,884节点、5,799路段)用Aimsun仿真测试畅通与拥堵情形，种子OD矩阵含不同误差。

## 主要结论
5个集合成员即优于EnKF与LETKF且对规模不敏感；摘要称数据复现改善最高64%，变量由3,249降至195个主成分，维度降低17倍；OD流改善不稳。

## 对本课题的可借鉴点
可借其降维与免分配矩阵思路：用主成分把单元存量与流量压为低维状态，分配交由仿真器，真人与LLM智能体观测进入滤波更新。

## 局限
未说明对行人流的适用性；分配矩阵隐含于仿真器，偏差未讨论；转移方程用多项式插值，最优形式待定。
