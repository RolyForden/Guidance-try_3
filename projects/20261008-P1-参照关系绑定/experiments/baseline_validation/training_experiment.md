# Experiment - P1 20% Baseline Training

待审草案v0.1，仅准备，不是训练授权。先完成既有单样本链路验收，再由用户确认本协议。用户只审批，不填表；以下默认建议尚未冻结，不能把准备清单当运行记录。

## 0. 身份
- 类型：20%平台的同步baseline准备；无P1候选模块，不作方法有效性判决。
- run前缀：p1_base_screen20_s17 / p1_base_screen20_s29。
- 源码：固定HF f40fa586e28f644d5db19e6d8905f626a6b7fd13及已单列的question-only/生成对齐工程补丁；实际运行快照哈希在启动前固定。
- 初始化：LLaVA-v1.6-vicuna-7b deae57a8c0ccb0da4c2661cc1891cc9d06503d11 + 固定CLIP/SAM2；三片基础权重正在下载，不使用全DRSeg微调后的发布PixDLM初始化本训练。
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
| 主基线 | 固定PixDLM训练结构与监督，LLaVA基础初始化，仅使用提议训练子集 |
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
- 官方默认优化器：AdamW lr3e-4、betas(0.9,0.95)、weight_decay0；CE/Dice/BCE权重1/0.5/2，梯度裁剪1、WarmupDecayLR warmup100步、ZeRO2；不在本轮私自改成别的算法。
- 官方脚本设置batch1、accumulation1、bf16、CLIP448中心裁剪、细节图长边1024后标准化/补零。GPU恢复后核验bf16支持和真实参数加载；不把无卡2GiB模式称为训练可行。
- 训练按官方random-with-replacement采样，不能将日志epoch称为完整遍历。默认建议每604 optimizer更新核一次固定development；初始固定计划30个区间=18120更新，最早在20区间之后判基本收敛。
- 收敛判据建议：最近5个区间development gIoU极差<=0.002且训练总loss区间均值的相对极差<=1%，所有损失/梯度有限。此阈值是待批准的工程判据，不是已有实验结果或文献结论；未满足不称收敛。
- 若30区间仍未收敛，保留结果，明确需要继续及调度审查，不以计划结束宣称方向无效。18120是待冻结的学习率调度长度，不是算力/费用上限。
- checkpoint按内部development gIoU最高选，平分取更早一步，保留last与best、optimizer/scheduler/RNG；正式训练前必须验证保存恢复等价和磁盘够用。原脚本保存两份完整DeepSpeed状态，当前50G盘不能未经实测假定放得下；存储方案待核，不用skip_save绕过验收。
- 存储候选（尚未实现/验收）：安装中取得的DeepSpeed0.15.4源码支持save_checkpoint(exclude_frozen_parameters=True)。可减少固定骨干重复保存，但必须从固定初始化重建、严格核对遗漏键恰为冻结参数并验证冻结状态哈希、恢复预测/optimizer/scheduler/RNG等价后才可采纳；不能仅用load_module_strict=False掩盖缺键，不提前声称省盘或恢复成功。
- 唯一工程偏离：已有question-only生成输入与对齐修复；数据子集/internal development和独立评分入口须在快照中单列。实际启动命令仍待运行依赖、单样本、评分入口、seed注入与存储验收后填写；此时不提供看似可运行的占位训练命令。

## 5. 上机前自检
- [x] 提议清单回读核对604/302唯一ID、题型计数及整组归属；原数据未改写，test未读。
- [x] 基础初始化版本/预期大小/官方SHA256已固定；与发布PixDLM用途区分。
- [ ] 三片初始化权重完整验收；运行依赖、SAM2和训练入口导入通过。
- [ ] GPU模式恢复；真实RGB前向、GT隔离、反向和保存恢复验收通过。
- [ ] question-only独立评分、解码上限、seed及采样重放检查通过。
- [ ] 训练目录映射、storage实测、最终命令/配置/快照固定。
- [ ] 用户确认采样代理组、内部development、收敛/调度和本协议版本；未确认不启动训练。

## 6. 运行记录
无训练记录。数据准备和CPU工程检查见现有准备清单；不当作模型结果。

## 7. 结果
无训练loss、development/val指标或吞吐结果。

## 8. 判断
本文件是预填的训练协议，不是训练ready证明；P1混绑假设及方法收益仍未验证。

## 9. 收尾与交付
执行者不commit/push。回传命令、实际配置/代码版本、数据清单、seed/RNG、加载键、stdout/stderr、逐样本预测与指标、checkpoint/optimizer/scheduler索引、大小与SHA256、恢复测试及资源记录；未发表材料和完整运维日志不外传。
