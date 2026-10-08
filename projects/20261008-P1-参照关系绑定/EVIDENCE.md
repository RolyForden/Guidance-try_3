# Evidence

只记录会影响研究问题、查重结论或论文主张的证据。摘要线索与正文、官方代码核验要明确区分。

| 结论或假设 | 核验范围 | 原始来源 | 与当前判断的关系 |
|---|---|---|---|
| 公共源码的 with/without-CoT 分支均可能使用标注回答；without-CoT 不等于 question-only | 2026-10-08 静态代码审查；HF revision f40fa586e28f644d5db19e6d8905f626a6b7fd13；未执行 | [eval.py](https://huggingface.co/WhynotHug/PixDLM/blob/f40fa586e28f644d5db19e6d8905f626a6b7fd13/eval.py):1115-1155,1206-1219；[llava_arch.py](https://huggingface.co/WhynotHug/PixDLM/blob/f40fa586e28f644d5db19e6d8905f626a6b7fd13/model/llava/llava_arch.py):134-157,278 | 需核定独立的干净输入协议；不能据此推断论文全部结果 |
| 官方发布评测脚本默认指向 test | 本轮读取固定 revision 的脚本全文，未运行 | [eval_drseg.sh](https://huggingface.co/WhynotHug/PixDLM/blob/f40fa586e28f644d5db19e6d8905f626a6b7fd13/scripts/eval_drseg.sh)，val_dataset=custom_seg\|test | 本轮禁止直接照抄执行，需显式 validation 路径 |
| 公开版本固定了来源，但不是下载后的内容哈希 | 本轮 git ls-remote 与 HF API 元数据 | GitHub HEAD 400aaeaec7b3a2dfa91aab0c60b7534c68199061；模型 f40fa586e28f644d5db19e6d8905f626a6b7fd13；数据 2b143f9a0721b7b5dbba4dd9f0bed9a22ede444d | 三者分别记录，不假定 GitHub/HF 源码相同 |

“已核实”必须写明实际读到的范围和可访问来源；二手材料、截图和转写只能作为待核线索。

## 尚缺的证据

- 权重/数据落地哈希、预处理与 evaluator 对齐、实际输入日志、自己的复现数字。
- 在未按错误结果挑样的固定样本上，关系可辨且目标混绑的频率。
- 相同监督与预算的简单位置方案是否消除混绑。
