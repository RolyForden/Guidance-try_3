# Experiment - P1 20% Baseline Training

待审草案v0.2（2026-10-10）：用户已同意从基础初始化重建baseline、训练缺失的对齐模块；此为路线确认，不冒充完整协议审批或工程验收。以下§0–§5由agent预填；实际命令、参数加载与保存恢复验收完成后提交最终冻结版，用户只审批、不填表。本轮未训练。

## 0. 身份
- 类型：20%平台的同步baseline准备；无P1候选模块，不作方法有效性判决。
- run前缀：p1_rebuilt_screen20_s17 / p1_rebuilt_screen20_s29；不得与发布checkpoint诊断混用目录。
- 源码：固定HF f40fa586e28f644d5db19e6d8905f626a6b7fd13及已单列的question-only/生成对齐工程补丁；实际运行快照哈希在启动前固定。
- 初始化：LLaVA-v1.6-vicuna-7b deae57a8c0ccb0da4c2661cc1891cc9d06503d11 + 固定CLIP/SAM2；三片基础权重已独立核对大小/SHA256，不使用全DRSeg微调后的发布PixDLM初始化本训练。路径为/root/autodl-tmp/p1-prep/assets/llava-v1.6-vicuna-7b、deployment/models/clip-vit-large-patch14及deployment/models/sam2_checkpoints/sam2.1_hiera_large.pt。
- baseline身份：PixDLM结构的重建同步baseline，不是完整发布模型、原样官方复现或论文量级复现。发布checkpoint缺对齐权重，来源/键核查见项目EVIDENCE.md；本训练不用它给缺失模块“补权重”。
- 数据：DRSeg 2b143f9a0721b7b5dbba4dd9f0bed9a22ede444d；提议清单[p1_screen20_manifest.json](p1_screen20_manifest.json)，SHA256 5947d8c48b62b5bf776c85654af25e356bd0f3eb19a2a788cba2dfd0db7cd338。尚未改写数据目录。

## 1. 预注册
- 唯一问题：在固定约20%训练子集上，从未见DRSeg监督的基础权重建立训练与question-only评分都可追溯的同步baseline，供后续获批候选公平比较。
- 支持：训练/保存/恢复/无GT输入的评分链路验收通过，两seed达到下述基本收敛判据；独立重算指标一致。
- 否定：输入污染、错配、无解释加载键、丢失样本或保存恢复不一致时，仅否定本次工程链路。分数低或不收敛不等于否定P1方向，不隐藏负结果。
- Prediction/Confidence：训练可运行与P1收益均未证实，不给未经测量的概率或性能目标。
- 主指标：问题-only目标前景gIoU，原图逐mask均值，非空union用intersection/(union+1e-5)、空union设1；次指标cIoU=累计intersection/(累计union+1e-10)及三题型分组。logit>0、ignore255；独立mask_metrics.py的13项合成边界测试及100例官方前景计数/公式对照通过。真实预测/GT解码、坐标及CI入口仍待验收，不能直接用官方回答条件validation数字。
- baseline达标线：工程正确与基本收敛，不预设追平论文13B或发布7B数值。候选涨点/全量门槛不在本协议内。
- 停止：test路径、输入污染、NaN/Inf、坏资产、未解释加载异常、OOM、存储不足或保存恢复失败；记录原失败，不静默换精度、batch、划分或初始化。

## 2. 对照矩阵
| 标签 | 定义/本轮处理 |
|---|---|
| 主基线 | 固定PixDLM结构与监督，从基础初始化重建，显式训练缺失对齐模块，仅使用提议训练子集 |
| 最简对照 | 同一checkpoint的question-only一致性复跑；P1位置提示收益另需真实失败证据后审批 |
| 朴素聚合 | 不适用：本轮未实现候选或多路聚合，不把缺项冒充对照 |
| 候选方法 | 不运行；先得到可靠同步baseline及真实失败证据 |
| 负控制A | 评分入口移除/替换附带answers，tokens/特征/预测必须不变；训练监督使用answers合法且单独记录 |
| 负控制B | 替换离线GT mask，预测不变，仅评分可变化；不改原标签 |
| 参数/预算匹配 | 两seed结构、子集、初始化、优化器/解码配置一致；未来候选需另行冻结匹配条件 |

## 3. 统计协议
- 原训练分母2999图，每图1题。按(time_of_day, location, altitude, camera_angle, sequence_id)采集元数据代理整组抽取，不拆同一代理组；采样seed=20261008，精确定序/编码见清单。
- 提议训练604图/139代理组，占20.140%；题型spatial183、attribute215、scene206。提议内部development302图/61代理组：91/107/104。两集合ID及代理组交集均为0，余下2093原train图不用于本轮。
- 代理组不是经过核实的独立scene：train缺sequence_id 1215图、官方val缺846图。train/val无完全相同的图像文件，但共享576采集元数据组合，不能据此宣称无近重复或跨场景泛化。
- 内部development仅来自原train，用于收敛与checkpoint选择。官方2000图val保留原划分，只在方案/checkpoint冻结后报告，不用于本轮调参；官方test不读、不解包、不评分。
- 训练seed建议17、29，不挑最好seed；逐seed报告。最终固定checkpoint输出做2000次代理组bootstrap，seed=20261008，报告95%CI并披露代理组可能不能消除相关性；不把两seed平均冒充完整论文复现。
- gIoU与cIoU均报告，不事后更换主指标；本轮没有候选配对差或显著收益结论。

## 4. 固定条件
- 保留官方结构/监督默认：三尺度、每尺度3个SEG token、HRD、多路径编码、LoRA r8/alpha16/dropout0.05，q_proj/v_proj；训练可用原answers/GT，所有development/val预测只用RGB+原问题。
- 已确认的协议改动：在官方LoRA/任务头解冻之后，额外解冻model.vision_tower.align_stages与align_stages_latent的全部参数；不替换模块，不删除SAM路径，不改变损失。两类模块保留固定源码自身的初始化（包括latent投影的零初始化），由各训练seed在构造前固定随机状态；不把它们称为预训练模块。沿用相同AdamW参数组默认，不额外搜索对齐学习率。
- 参数边界：保留官方语言LoRA、任务头、embedding/lm_head与mm_projector训练设置；CLIP/SAM骨干保持冻结，仅对齐模块解冻。先输出完整参数名/shape/requires_grad及各来源加载键清单，逐项核验，而非靠名称包含vision_tower整体解冻；任何额外新建/重置/未加载参数都须解释来源，不以strict=False吞掉缺项。
- 初始化审计：LoRA/任务头/对齐模块以及新增token embedding可由固定seed初始化；mm_projector若因LLaVA与PixDLM形状/结构不同需重建，必须列出精确键/shape与初始化规则后纳入最终审批。当前不宣称键兼容，不提供忽略全部mismatch的加载命令。CLIP/SAM应核对对应源权重加载，不在加载后重建模块覆盖已载参数。
- 官方默认优化器：AdamW lr3e-4、betas(0.9,0.95)、weight_decay0；CE/Dice/BCE权重1/0.5/2，梯度裁剪1、WarmupDecayLR warmup100步、ZeRO2；不在本轮私自改成别的算法。
- 默认batch1、accumulation1、bf16、CLIP448中心裁剪、细节图长边1024后标准化/补零；已核1张RTX4080 SUPER（驱动32760MiB）、bf16与小型CUDA运算通过。真实模型显存、前向/反向仍待验收，遇OOM不静默量化或改变batch。
- 评分解码默认建议：seed17、greedy（do_sample=False）、num_beams=1、max_new_tokens=512，沿用固定tokenizer/EOS、缓存生成与question-only特征构造；这些是待冻结条件，不是已跑通的模型配置。无完整SEG组时保留生成文本/状态，记录结构失败率，并按空前景计入所有样本分母，不丢样本、不根据GT补SEG或挑mask；shape/NaN/加载与实现异常仍停报。需在独立评分入口用失败夹具检验此规则，不能把填充的空预测称为原模型mask。
- 训练按官方random-with-replacement采样，不能将日志epoch称为完整遍历。默认建议每604 optimizer更新核一次固定development；初始固定计划30个区间=18120更新，最早在20区间之后判基本收敛。
- 收敛判据建议：最近5个区间development gIoU极差<=0.002且训练总loss区间均值的相对极差<=1%，所有损失/梯度有限。此阈值是待批准的工程判据，不是已有实验结果或文献结论；未满足不称收敛。
- 若30区间仍未收敛，保留结果，明确需要继续及调度审查，不以计划结束宣称方向无效。18120是待冻结的学习率调度长度，不是算力/费用上限。
- checkpoint按内部development gIoU最高选，平分取更早一步，保留last与best、optimizer/scheduler/RNG；正式训练前必须验证保存恢复等价和磁盘够用。原脚本保存两份完整DeepSpeed状态，当前50G盘不能未经实测假定放得下；存储方案待核，不用skip_save绕过验收。
- 存储候选（尚未实现/验收）：安装中取得的DeepSpeed0.15.4源码支持save_checkpoint(exclude_frozen_parameters=True)。可减少固定骨干重复保存，但必须从固定初始化重建、严格核对遗漏键恰为冻结参数并验证冻结状态哈希、恢复预测/optimizer/scheduler/RNG等价后才可采纳；不能仅用load_module_strict=False掩盖缺键，不提前声称省盘或恢复成功。
- 偏离清单：已有question-only生成输入/缓存对齐修复、额外训练对齐模块、子集/internal development及独立评分入口；每项在快照中单列，不称只有两处传递修复。未加入P1候选结构；未来候选必须以这份重建baseline的相同训练协议比较，不能与缺权重的发布部署混比。
- 单样本默认建议：从604图训练清单按稳定ID排序取首个合法非空标注样本，seed17，完成训练监督前向/反向与一次更新、保存恢复/下一步重放；随后同RGB+原问题验证生成入口及GT隔离。初始随机任务头的表现仅作工程检查，不作baseline分数；smoke权重不续作正式seed起点，正式运行重新初始化。许可、GT解码与几何、失败评分、加载和参数梯度审计先完成，不能省略。
- 精确命令待验收：源码/root/autodl-tmp/p1-prep/source/PixDLM-generation-aligned-f40fa58、Python/root/autodl-tmp/p1-prep/env/bin/python、数据/root/autodl-tmp/p1-prep/datasets/DRSeg、清单datasets/proposals/p1_screen20_manifest.json已定位；实际训练入口改动、目录映射、单样本/评分/seed重放和存储未验收。默认输出datasets之外的独立runs/p1_rebuilt_screen20_s17或_s29目录；启动前固定完整argv/配置/源码与参数来源hash，不使用看似可运行的占位命令。

## 5. 上机前自检
- [x] 提议清单回读核对604/302唯一ID、题型计数及整组归属；原数据未改写，test未读。
- [x] 基础初始化版本/预期大小/官方SHA256已固定；与发布PixDLM用途区分。
- [x] 三片初始化权重大小/SHA256验收；固定依赖、SAM2及PixDLM模块CPU导入检查通过（不等于修改后训练入口验收）。
- [x] GPU已恢复，bf16和小型CUDA计算通过。
- [x] 用户确认基础初始化重建并训练对齐模块这条路线；不称原样官方复现。
- [ ] 修改后训练入口、精确参数加载/初始化和可训练参数清单验收；额外解冻恰为两类对齐模块，梯度有限且更新生效，固定骨干不变。
- [ ] 真实RGB前向、GT隔离、反向和保存恢复/下一步重放验收通过。
- [ ] question-only独立评分、解码上限、seed及采样重放检查通过。
- [ ] 训练目录映射、storage实测、最终命令/配置/快照固定。
- [ ] 用户确认最终冻结版本（含采样代理组、内部development、解码/失败处理、收敛/调度及精确命令）；路线确认不能代替此项。

## 6. 运行记录
无训练记录。数据准备和CPU工程检查见现有准备清单；不当作模型结果。

## 7. 结果
无训练loss、development/val指标或吞吐结果。

## 8. 判断
本文件是预填的训练协议，不是训练ready证明；P1混绑假设及方法收益仍未验证。

## 9. 收尾与交付
执行者不commit/push。回传命令、实际配置/代码版本、数据清单、seed/RNG、加载键、stdout/stderr、逐样本预测与指标、checkpoint/optimizer/scheduler索引、大小与SHA256、恢复测试及资源记录；未发表材料和完整运维日志不外传。
