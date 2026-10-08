# 无卡资产与环境准备 - 2026-10-08

授权：用户批准下载资产、准备环境，并要求避免下载期间GPU空耗。未授权训练、新增租卡或test评测。当前状态：仅本地核定来源，尚未远端安装/下载。

## 切换方式

[AutoDL官方说明](https://www.autodl.com/docs/save_money/)：控制台先关机，再选择无卡模式开机；0.5核/2GB内存/无GPU，公布费用0.1元每小时，环境和数据保留。会释放GPU，再正常开机可能缺空闲卡。不是实例完全关机时通过SSH下载。

只有SSH容器权限，不假定具有平台计费/开关机权限；不执行shutdown，也不索取平台Token。等待用户控制台切换并确认SSH是否改变。无卡内存不适合加载7B、跑评测或重型编译；此阶段仅下载、建环境和小型CPU检查。

## 固定来源与容量

以下是HF API的源端LFS元数据，不是本地下载后已验证哈希。2026-10-08查询?blobs=true。

| 首轮资产 | revision | 选择文件 | 字节数 | 源端SHA256 |
|---|---|---|---:|---|
| WhynotHug/PixDLM | f40fa586e28f644d5db19e6d8905f626a6b7fd13 | pytorch_model.bin | 13611289441 | fc3f8ec17e57c17068be371c33bbe06b156be779f0087a5bb63d9f658729b220 |
| WhynotHug/DRSeg | 2b143f9a0721b7b5dbba4dd9f0bed9a22ede444d | DRSeg.zip | 2641097515 | 1378bb70c789730fe38b7a3dd28f47f36c63c4e3bafb7e89367a6232e647317b |
| openai/clip-vit-large-patch14 | 32bd64288804d66eefd0ccbe215aa642df71cc41 | model.safetensors | 1710540580 | a2bf730a0c7debf160f7a6b50b3aaf3703e7e88ac73de7a314903141db026dcb |
| facebook/sam2.1-hiera-large | 665f8e2ad61cf5f53d65644ff27c8ee525124610 | sam2.1_hiera_large.pt | 898083611 | 2647878d5dfa5098f2f8649825738a9345572bae2d4350a2468587ece47dd318 |

四个大文件共18861011147 bytes，约18.86 GB/17.57 GiB；另有源码、配置、tokenizer、环境、缓存、解包与日志。不能据此称总占用仅18.9GB。下载前重新查询可用空间；解包体积未知，先读取zip目录尺寸，不读/解出test内容。至少保留10GiB自由空间；容量不足停报，不自动扩盘或删除平台文件。

按固定revision选择必要文件，不整仓下载TF/Flax与重复PyTorch格式；模型缓存与临时文件放/root/autodl-tmp。配置/tokenizer应按HF实际目录映射，Pix的tokenizer/config位于pretrained/pixdlm-7b，不假定全在仓库根目录。

训练基础权重暂缓：liuhaotian/llava-v1.6-vicuna-7b revision deae57a8c0ccb0da4c2661cc1891cc9d06503d11，三个分片总14125909456 bytes，约14.13GB。先审发布Pix加载路径，若必需则报告新增容量并核实空间，不偷偷把它作为20%初始化；正式训练初始化与发布全DRSeg权重隔离。

## 环境策略

- 保留现有Python3.12/PyTorch2.8，不在base上升级降级；独立环境建在数据盘，建议Python3.10，包版本最终锁定后记录。
- 作者requirements规定torch>=2.3、torchvision>=0.18、transformers==4.31等；其余下限不是可复现锁文件，不无条件升级到最新版。
- 无卡阶段可以安装适配的预编译包并做import检查，不加载模型、不进行需要GPU/大内存的FlashAttention/SAM扩展编译；编译必需时留到另批有卡阶段，记录具体依赖缺口。
- 官方download_assets.py未传revision，且根级allow_patterns不覆盖实际嵌套config/tokenizer；不直接照抄执行。后续下载实现必须显式固定revision和文件路径。
- HF不可达、权限/许可问题、哈希不符、磁盘不足或依赖冲突时停报；不更换模型/数据版本或任意镜像绕过访问约束。

## 准备交付

记录代码版本、文件来源/revision/大小/期望与落地SHA256、下载实际路径、环境包清单、日志、耗时和失败。只回传必要的脱敏摘要，不把SSH凭据或完整私有运维日志push。主工作区准备文件自动commit/push；容器执行者不推送主仓库。
