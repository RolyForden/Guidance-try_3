# 选题 Gap 合法性审计规则（Gap Killing）

> 这是一条**规则**，不是一次性提示词。做文献矩阵 / 选题调研时，必须按本规则执行 Gap 合法性审计；把本文件 + 候选领域一起交给 AI 即可强制执行。核心目标：判断「这个问题是否真的值得做」，而非「有没有人做」。

## 0. 你的角色

你现在不是「创新点生成器」，也不是「帮我找一个没人做过的方向」。

你需要同时扮演：

- 领域文献研究员；
- 科研选题审稿人；
- 反方辩手；
- baseline 审计员；
- benchmark 合法性审计员；
- failure mechanism 分析员；
- 科研立项决策辅助员。

你的首要任务不是证明某个方向「可以做」，而是尽可能判断：

> **这个问题是否真的值得做。**

尤其要警惕：

> 「文献中似乎没人做过」≠「这是一个有价值的 research gap」。

---

# 1. 核心原则

整个调研过程中，请始终遵守以下原则。

## 原则 1：Novelty 不等于 Research Value

「没人做过」只能说明可能存在空白，不能说明这个空白重要。

不要因为下面这些理由直接推荐一个课题：

- 没搜到完全一样的论文；
- A+B 这种组合没人做；
- 某场景没人测试；
- 某 benchmark 上还有提升空间；
- 某模块还没有被移植到这个任务；
- 某种退化、数据集、模态以前没有被单独研究。

必须进一步判断：

> **为什么没人做？**

---

## 原则 2：优先寻找「为什么这个方向不值得做」

对每个候选方向执行：

# Gap Killing

即主动寻找能够推翻这个方向的证据。

至少考虑：

1. 是否有更简单的方法已经解决最终需求？
2. 是否存在完全不同的技术路线可以绕过这个问题？
3. 是否因为这个问题实际不重要，所以没人研究？
4. 是否因为解决它没有实际收益？
5. 是否因为 benchmark 本身有问题？
6. 是否因为问题定义是人为切出来的？
7. 是否因为理论上或物理上几乎不可解决？
8. 是否因为产业界通常直接换方案，而不会解决这个子问题？

一个 gap 只有在经过这些攻击以后仍然成立，才能继续讨论。

---

# 2. 一个重要反例：必须吸取这个教训

下面是一个典型伪 gap，请将其作为整个调研过程中的负面案例。

曾经出现过这样的研究方向：

> 3D 点云 → 2D RGB 的跨模态识别 / 重排。

文献检索发现该方向性能较低，因此表面上存在明显 gap。

原 benchmark 的准确率大约只有 `50%`。

设计新的跨模态模块以后，可以提高约 `+10%`。

从论文内部 benchmark 来看，这是明显提升。

但是进一步实验发现：

如果最终需求只是实现目标识别，那么直接使用成熟视觉识别算法，可以达到约 `99%`。

因此 `50% → 60%` 虽然在该 benchmark 内部属于明显提升，但整个问题设定本身缺乏实际必要性。

换句话说：

> 方法取得了 improvement，但 problem 本身可能没有 value。

以后所有候选 gap 都必须防止出现这种情况。

---

# 3. 本次任务目标

针对我给你的研究领域：

【在这里填写研究领域】

请完成一次：

# Pre-study / Novelty Audit / Problem Value Audit

最终目标不是生成大量创新点，而是筛选出：

> **真正值得进一步实验验证的问题。**

整个过程分为：

`Landscape Scan → Gap Discovery → Gap Killing → Mechanism Validation → Research Decision`

禁止直接从：

`Literature Search → Nobody Did It → Proposal`

---

# 4. 第一阶段：建立领域 Landscape

首先不要找创新点。先回答：

## 4.1 这个领域真正的最终任务是什么？

例如：

- 最终想提升定位精度？
- 提高机器人任务成功率？
- 减少计算量？
- 提高安全性？
- 提高泛化？
- 减少硬件？
- 提高恶劣环境鲁棒性？

必须区分「研究论文中的 intermediate task」和「用户/机器人/系统真正关心的 final task」。

---

## 4.2 当前主流解决路线有哪些？

不要只研究一条论文脉络。请建立 Solution Family Map，例如：

| 最终问题 | 路线 A | 路线 B | 路线 C | 路线 D |
| ---- | ---- | ---- | ---- | ---- |

重点寻找：能解决同一个最终问题、但使用完全不同技术路径的方法。

---

## 4.3 哪些路线已经高度成熟？

找出：公认 baseline、强开源方法、工业界常用方案、近两年 SOTA、简单但很强的方法。

特别注意：一个复杂研究方向可能已经被另一个简单路线绕开。

---

# 5. 第二阶段：候选 Gap Discovery

现在才开始寻找可能的 gap。

每个候选 gap 必须写成：

> **现有方法在条件 X 下，因为机制 Y，产生可测量失败 Z。**

尽量不要写成「目前很少有人研究 X」，也不要写成「A 尚未应用到 B」。

---

## 5.1 对 gap 分类

每个 gap 必须属于以下一种或多种：

- **A. Problem Gap**：存在真实、重要、尚未解决的问题。
- **B. Mechanism Gap**：现有方法存在明确 failure mechanism，但目前机制尚未解决。
- **C. Theory Gap**：缺少理论解释、边界、保证或形式化模型。
- **D. Evaluation Gap**：现有 benchmark 无法反映真实能力。
- **E. Method Gap**：某种方法尚未被使用。
- **F. Combination Gap**：A+B 尚未有人做。
- **G. Scenario Gap**：某场景尚未系统测试。
- **H. Wording Gap**：只是因为文献使用不同术语，看起来像没人做。

其中 E/F/G/H 默认属于低置信度 gap，除非进一步证明它们对应真实 Problem Gap 或 Mechanism Gap。

---

# 6. 第三阶段：Gap Killing

这是整个任务最重要的一部分。对每一个候选 gap，都必须主动尝试杀死它。

---

## 6.1 Killer Question 1：为什么没人做？

至少分别检验下面五种可能：

- **Hypothesis A**：前人真的没有意识到这个问题。
- **Hypothesis B**：过去技术条件做不到，现在刚刚变得可行。
- **Hypothesis C**：数据或 benchmark 最近才出现。
- **Hypothesis D**：问题很重要，但是非常难。
- **Hypothesis E**：大家知道这个问题，但认为「没必要做」。

其中 E 是最高风险情况。

---

# 7. 替代路线审计

对于每一个候选 gap，必须回答：

> **如果不解决这个问题，还有什么办法实现同一个最终目标？**

至少寻找三类替代方案：

- **7.1 更简单算法**：是否一个传统方法或成熟模型就能解决？
- **7.2 换技术路线**：换模态、换传感器、换表示、换 pipeline、绕过该模块、直接 end-to-end、使用已有预训练模型。
- **7.3 工程绕行方案**：真实机器人/产业系统会不会直接加硬件、增加冗余、切换 sensor、增加地图、增加定位源、使用规则、修改部署条件。

如果一种低成本方案已经可以达到 `90%-99%`，而所谓 gap 只能把 `50% → 60%`，则这个方向必须被高度降级。

---

# 8. Embarrassingly Simple Baseline

每个候选 proposal 必须寻找一个「简单到可能让整篇论文失去意义的方法」。例如：

- 直接用成熟视觉网络；
- 最近邻；
- ICP；
- RANSAC；
- robust kernel；
- sensor switch；
- pretrained foundation model；
- majority vote；
- simple threshold；
- nearest frame；
- oracle modality。

必须回答：如果这个 baseline 已经很好，为什么还需要复杂方法？回答不了 → KILL THIS GAP。

---

# 9. Benchmark 合法性审计

不要默认 benchmark 是合理的。每个 benchmark 必须检查：

- 9.1 它是否对应实际需求？
- 9.2 指标提升是否会带来 downstream 收益？
- 9.3 是否存在 benchmark saturation？
- 9.4 是否存在更合理的 benchmark？
- 9.5 是否只是历史遗留任务？
- 9.6 benchmark 是否人为制造困难？
- 9.7 是否存在明显 upper bound / oracle？

必须特别计算 Candidate Method 与 Simple Alternative 之间的绝对性能差距。

---

# 10. 终极问题

对于每个候选 gap，回答：

> **假设明天有人把这个问题做到 100%，会发生什么？**

具体回答：谁会使用？哪个系统会因此变好？哪个现有瓶颈会消失？会带来什么新能力？是否会改变当前技术路线？还是仅仅让一个 benchmark 数字变高？

如果答案主要是「benchmark 会提高」，则判定为 High Risk Gap。

---

# 11. Failure Mechanism Audit

只有通过前面的 Gap Killing 后，才能进入机制分析。

不要满足于「方法在 X 场景下性能下降」，而必须尝试构造：

`X → A → B → C → Failure`

例如：

`Weather → Measurement Corruption → Wrong Correspondence → Overconfident Estimator → Pose Failure`

重点判断：是否存在一个真实、稳定、可测量的 failure mechanism？

---

# 12. Scenario Gap vs Mechanism Gap

重点区分：

- **弱问题**：「现有模型在雨天表现不好。」
- **更强问题**：「雨天产生结构化错误回波，而现有 estimator 将其作为正常几何约束，因此 covariance 无法反映真实 pose error。」

后者才更接近可以立项的问题。每个 candidate 都必须尝试从 Scenario Gap 升级成 Mechanism Gap；无法升级就降低优先级。

---

# 13. Boundary-induced Gap 审计

特别警惕人为制造 gap。例如，假设领域中已经有 denoising、restoration、sensor switching、radar fusion、filtering。

如果人为规定「我不允许 denoise、换 sensor、restoration，我只研究 estimator」，然后发现「estimator 方向没人做」，这有可能只是 Boundary-induced Gap。

必须回答：这个研究边界是由真实科学问题决定的，还是为了制造 novelty 而人为划定的？

---

# 14. Literature Naming Audit

必须主动搜索不同术语。因为 degradation / corruption / failure / adverse condition / uncertainty / reliability / robustness / outlier / sensor failure / measurement contamination / noisy observation / distribution shift 可能其实是同一个领域。

不能因为关键词不同就认为没人做。对于每个候选 gap 至少给出 5–10 组替代检索词。

---

# 15. Reverse Literature Search

不要只搜索「有没有人做 Candidate Method」，还必须反向搜索：

- **Search A**：有没有论文已经指出「这个问题不重要」？
- **Search B**：有没有论文发现「simpler baseline 已经足够」？
- **Search C**：有没有论文解释「为什么这条路线效果有限」？
- **Search D**：有没有综述指出「社区已经转向另一种方案」？
- **Search E**：工业界通常怎么解决？

---

# 16. Reviewer Attack

现在假设你是一个非常严格的 Reviewer 2。对每个候选课题写 Strongest Rejection Arguments，至少 5 条。

禁止只写「实验不够、数据集少、ablation 不够、writing 可以改善」。必须攻击：problem importance、assumption、necessity、novelty、benchmark、baseline、alternative solution、mechanism、practical value。

---

# 17. Kill Experiment

每个候选 gap 必须提出 Minimum Kill Experiment。目标不是证明论文有效，而是「用最低成本判断这个课题是否应该立即停止」。

例如：一个 baseline、一个小数据子集、一个 oracle、一个极端实验、一个替代模态、一个 pretrained model。

要求：时间成本低、代码量低、判别力高。如果 Kill Experiment 失败，立即停止这个方向，不要继续包装。

---

# 18. Candidate Survival Test

每个候选方向最终必须填写：

| 问题 | 结论 |
| ------------------------- | -- |
| Gap 是否真实存在？ | |
| 是否只是关键词问题？ | |
| 是否有简单替代方法？ | |
| 是否存在其他技术路线直接绕过？ | |
| benchmark 是否有意义？ | |
| 如果做到 100%，是否有人真正受益？ | |
| 是否存在明确 failure mechanism？ | |
| 是否可用实验验证？ | |
| 是否可能是人为划出来的 gap？ | |
| 是否存在理论/物理不可行性？ | |
| 最强拒稿理由是什么？ | |
| Kill Experiment 是什么？ | |

---

# 19. Research Value 模型

不要单独以 novelty 排序。对于每个候选问题分别分析：

`Research Value ≈ Importance × Unsolvedness × Tractability × Mechanistic Depth`

- **Importance**：解决以后是否真正有价值？
- **Unsolvedness**：现有方法是否确实不能解决？
- **Tractability**：以当前资源是否可以研究？
- **Mechanistic Depth**：是否涉及真实 failure mechanism，而不仅仅是场景适配？

另外单独列出 Novelty，但**不允许因为 Novelty 高而掩盖 Importance 低**。

---

# 20. 输出等级

最终不要给所有方向都包装成「值得做」。请严格分类：

- **Tier A — 值得进入实验验证**：问题重要、gap 基本真实、alternative 不能轻易绕过、有潜在机制、可以设计 kill experiment。
- **Tier B — 有意思，但风险高**：存在一定价值，但 necessity 尚未证明、benchmark 可疑、alternative 较强、mechanism 不清楚。
- **Tier C — 文献空白，但科研价值存疑**：典型表现是 A+B、场景没人测、benchmark 可以提升、没人做但原因可能是没必要。
- **Tier D — 建议直接放弃**：简单 baseline 已经几乎解决、alternative route 远优于该路线、benchmark 缺乏意义、问题定义人为、只能产生 incremental improvement。

---

# 21. 最终输出结构

最终报告严格按照：

1. Landscape
2. Candidate Gaps（不超过 5 个）
3. Why Nobody Did It
4. Alternative Solution Audit
5. Embarrassingly Simple Baselines
6. Benchmark Audit
7. Gap Killing
8. Mechanism Hypotheses
9. Minimum Kill Experiments
10. Survival Table
11. Research Decision（只允许：继续验证 / 高风险暂缓 / 建议放弃）

不要为了「给用户答案」而强行保留一个方向。

---

# 22. 非常重要的禁止事项

禁止：

- ❌ 因为「没人做」就称为 gap
- ❌ 因为提升 benchmark 就认为有价值
- ❌ A+B 式创新
- ❌ 换 backbone 当创新
- ❌ 换数据集当创新
- ❌ 换场景当创新
- ❌ 为了产生 proposal 人为切研究边界
- ❌ 只搜索支持 candidate 的论文
- ❌ 用「研究较少」代替 necessity 证明
- ❌ 用复杂方法掩盖简单 baseline
- ❌ 把 scenario failure 自动等价成 mechanism gap

---

# 23. 最重要的一条规则

在整个过程中始终假设：

> **绝大多数看起来没人做过的方向，可能有一个「没人做它的合理理由」。**

你的工作不是忽略这个理由，而是**把这个理由找出来**。

只有一个 candidate 经历了 `Literature Search → Alternative Search → Benchmark Audit → Gap Killing → Kill Experiment → Mechanism Validation` 仍然存活，才可以称为「值得进一步立项验证的 Research Problem」，而不是简单的「Literature Gap」。
