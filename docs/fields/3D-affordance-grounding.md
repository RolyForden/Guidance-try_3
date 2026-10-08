# Frontier Map: Language-Guided 3D Affordance Grounding

> **历史示例，冻结于 2026-09，不是当前领域结论或新选题推荐。** 仅示范 Frontier Map 的结构，下面的“唯一入口”“基本关闭”、候选失败与文献细节均保留为当时记录，不能据此淘汰新方向。
> 原来源为 Guidance-try_1 的 CAGE 机制报告（旧目录记录）；本次未在当前工作树及 HEAD 找到该报告，因此来源未恢复，本文不能承担已核实文献矩阵的作用。后续任务应重新核正文、官方代码与实际证据，不补造原报告链接。
> 相关停止决定可追溯至 Guidance-try_1 [复盘固定版本](https://github.com/RolyForden/Guidance-try_1/blob/534d2983ed97b086b0cdb267b8023e0f18cc61d7/projects/20260902-CCFC%E9%80%89%E9%A2%98/%E5%A4%8D%E7%9B%98.md)。这不是原文献报告的替代证据；访问需原仓库权限。

## 1. 领域定义

- 任务：给定物体点云 + 任务文字（如「握持」「切割」），预测每个三维点与当前功能的相关程度（逐点热图 / mask）。
- 输入 / 输出：点云 P + 文字 q → 逐点 affordance mask。
- 为什么重要（一句话）：机器人要「看清」同一件工具的哪个部位能完成当前任务，是操作的前提。

## 2. 时间线（研究脉络）

- 起点：LASO / PointRefer（CVPR 2024）——语言引导 3D affordance 分割 + 公开数据。
- 扩张：GEAL（CVPR 2025）——多粒度融合 + 2D-3D 一致性；GLANCE（ICCV 2025）——中间层 cross-modal connector + 几何先验。
- 现状：CMAT / LAS（CVPR 2026）——2D 语义关系迁移；2D/VLM 侧 GroundBench（2026）——反事实 affordance 失败定位。

**所处阶段**：快速扩张 → 早期同质化（机制方法开始重复，但「行为诊断」刚有人碰）。

## 3. 已解决的问题

- 多尺度 / 多粒度 fusion：GEAL 等。
- 2D → 3D 语义迁移：GEAL、CMAT。
- 中间层 cross-modal 连接 + 几何先验：GLANCE。
- 未见类别泛化：GLANCE、CMAT。

## 4. 尚存的可测失败（frontier）

- 失败 1：**query-insensitive mask switching**——同一几何、不同有效 affordance 指令下，模型可能不切换 mask。谁能测：PointRefer / GEAL 官方权重 + 受控 pair；怎么测：valid swap + paraphrase control；为什么重要：选错功能区域 = 操作事故。**状态：未证实（D 级），需 D0/D1 诊断。**
- 失败 2：**global semantic vs local spatial precision 的结构性矛盾**——小功能区域在固定多视图下被平滑。**状态：未证实，导师提出的候选 gap。**

## 5. 关键工作（Top-10 最近邻）

| 工作 | 年份 | 核心机制 | 相似度 | 威胁 |
|---|---|---|---|---|
| LASO / PointRefer | CVPR 2024 | 语言注入 + question-conditioned decoder | 高（被解释对象） | 高 |
| GEAL | CVPR 2025 | 多粒度融合 + 2D-3D 一致性 | 高 | 高 |
| GLANCE | ICCV 2025 | 中间层 connector + 几何 query | 高 | 高 |
| CMAT / LAS | CVPR 2026 | 2D 语义关系迁移 + co-attention | 高 | 高 |
| GroundBench | arXiv 2026 | 反事实 affordance 失败定位（2D/VLM） | 极高 | 极高 |
| Same Task, Different Circuits | NeurIPS 2025 | circuit localization + back-patching | 极高 | 极高 |
| Vision-Default, Prior-Override | arXiv 2026 | activation patching（routing vs writing） | 极高 | 极高 |

## 6. 公开资产

- 数据：LASO（19,751 点云-问题对）、PIAD（7,012 实例）、SceneFun3D（场景级）。
- 代码 / 权重：LASO/PointRefer、GEAL、GLANCE、CMAT 官方代码。
- 评测协议：aIoU / AUC / SIM / MAE。

## 7. 进入成本

- 单卡可行性：24GB 级 GPU 可复现 GEAL。
- 复现难度：中（官方代码 + 权重在）。
- 周期：感知方法已在快速同质化，「行为诊断」是唯一相对空的入口。

## 8. 当前判断

- 机制方法（局部/融合/迁移/蒸馏）已拥挤，谁做都可能被「只是换 backbone / 只是 3D 迁移」否掉。
- 唯一相对空的是「同几何多有效 mask 的反事实诊断」，但 GroundBench 已占 2D/VLM 版，3D dense 版是否成立**必须查重 + D0/D1 实证**，不能想当然。
- 一句话：感知方法线基本关闭；若要投，只能投「行为诊断 / 因果定位」这个窄口，且先证明现象存在。
