# 实验启动指令（给执行 agent：自动起草 → 你只审批）

> **起手式（你只说这一句）**：「读 `templates/experiment_kickoff.md` 并照做：目标 = ___；材料 = ___；其余你自己完成，做完把草稿给我审。」
> 效果：agent 自动把 `templates/experiment.md` §0–§5 填满并交草稿；你只审批，确认后才跑。红线见根 `AGENTS.md`。

---

你是本仓库的执行 agent。按以下步骤**严格顺序**执行；**未获确认前不许运行、不许动 GPU。**

1. **读**：`AGENTS.md`、项目 README、实际底座档案、`docs/02_实验设计与筛选.md`、`templates/experiment.md`，以及用户给的目标与材料。候选实验必须有完整底座；底座复现可用草稿，边界见 `templates/base_paper_kickoff.md`。
2. **自动起草**：用 `templates/experiment.md` 格式把 §0–§5 逐条填满——能推出的直接填；确实推不出的（实例 GPU、权重路径、evaluator 版本）列成「待确认 + 默认建议」，**不臆造、不留空**。
3. **只交草稿**：一页说清「填了什么 / 哪些待确认 / 能回答什么、不能回答什么」，**停下等确认**。
4. **确认后**才按冻结记录执行（判据不改；遇 blocker 先停并报）。
5. **跑完**按 §6–§8 补结果与判断，并做 §9 收尾。记录落盘到项目 `experiments/<实验名>/experiment.md`，产同目录 `delivery/`（规格见 `docs/04_协作与Agent.md`）；项目 README 链接协议与交付位置。底座复现另回填底座档案；**执行者不 commit/push**。
