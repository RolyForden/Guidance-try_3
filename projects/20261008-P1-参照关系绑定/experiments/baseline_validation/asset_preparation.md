# 无卡资产与环境准备 - 2026-10-08

授权：用户批准下载资产、准备环境，并要求避免下载期间GPU空耗。未授权训练、新增租卡或test评测。无卡模式与下载链路已核实；独立Python与下载工具已安装，完整推理环境和大文件完成情况见本文件的实际准备记录。

## 切换方式

[AutoDL官方说明](https://www.autodl.com/docs/save_money/)：控制台先关机，再选择无卡模式开机；0.5核/2GB内存/无GPU，公布费用0.1元每小时，环境和数据保留。会释放GPU，再正常开机可能缺空闲卡。不是实例完全关机时通过SSH下载。

只有SSH容器权限，不假定具有平台计费/开关机权限；不执行shutdown，也不索取平台Token。用户重新提供连接后，已确认无GPU、0.5核、2GiB内存。无卡内存不适合加载7B、跑评测或重型编译；此阶段仅下载、建环境和小型CPU检查。

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

## 实际准备记录

- HF直连失败；AutoDL官方内置加速访问原HF API返回200，固定SAM单字节Range请求返回206。不是镜像切换，也不是完整文件验收。
- 用户说明本地有代理并授权自行查看。仅查询Windows系统代理设置及相关监听进程，发现Clash HTTP回环代理；未读取订阅、节点配置或认证信息。
- 经SSH反向隧道将该代理提供给容器，远端仅绑定127.0.0.1；原HF API返回200。隧道随SSH退出关闭，不修改公网监听、防火墙或系统代理配置。仅用于本轮公开资产/包下载，不传私有研究材料。
- 数据盘独立环境：`/root/autodl-tmp/p1-prep/env`；conda包缓存：`/root/autodl-tmp/p1-prep/conda-pkgs`。官方Anaconda main源创建Python3.10.22，原base仍为Python3.12.3。
- 下载工具安装：从官方PyPI安装`huggingface_hub==0.26.5`，未安装torch、transformers或模型运行依赖。此环境目前只具备准备工具，不是已验收的PixDLM推理环境。

```bash
CONDA_PKGS_DIRS=/root/autodl-tmp/p1-prep/conda-pkgs /root/miniconda3/bin/conda create --yes --prefix /root/autodl-tmp/p1-prep/env --override-channels --channel https://repo.anaconda.com/pkgs/main python=3.10 pip
HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890 /root/autodl-tmp/p1-prep/env/bin/python -m pip install --index-url https://pypi.org/simple --no-cache-dir huggingface_hub==0.26.5
```

代理地址在命令中是容器侧回环隧道，不含代理认证；后续使用必须先重建隧道。运行包版本仍须结合固定源码审计后锁定，不直接安装作者所有下限到最新版。

SAM首轮下载使用上表固定revision的原HF resolve地址，保存为`/root/autodl-tmp/p1-prep/assets/sam2/sam2.1_hiera_large.pt.partial`。curl在162.591803秒后报错92：HTTP/2流CANCEL；响应200，接收33554432 bytes，平均206372 bytes/s。该文件仅为32MiB部分文件，不可作为权重加载，未声称通过完整SHA256校验。不得将这个速度直接当作后续全部资产的稳定吞吐或完成时间。

为检查续传，HTTP/1.1从33554432偏移读取1MiB到/dev/null：本地隧道返回206、1048576 bytes、8.515989秒（123130 bytes/s）；平台内置加速相同范围返回206、1048576 bytes、11.058507秒（94820 bytes/s）。只验证小段可读，不能由此宣称解决完整大文件中断。两次探测未追加到.partial，不删除已有部分文件；未继续启动其余大文件，也未无界重试。

固定Pix revision已下载requirements与pretrained/pixdlm-7b下6个配置/tokenizer文件到`/root/autodl-tmp/p1-prep/assets/pixdlm-source`，未下载/读取test标注。6个非LFS文件的Git blob SHA1与固定revision API元数据一致。首次统一Git blob校验在tokenizer.model处失败，因为该文件为LFS对象、blob_id对应指针而非文件内容；随后单独按LFS源端SHA256与大小校验，不将这次校验方式错误称为资产损坏。详细清单与检查结果见[准备清单](preparation_manifest.json)。

实际小文件下载命令（需先重建回环隧道）：

```bash
HTTPS_PROXY=http://127.0.0.1:17890 HTTP_PROXY=http://127.0.0.1:17890 HF_HOME=/root/autodl-tmp/p1-prep/hf-cache HF_HUB_DISABLE_PROGRESS_BARS=1 timeout 150 /root/autodl-tmp/p1-prep/env/bin/python -c "from huggingface_hub import hf_hub_download; files=['requirements.txt','pretrained/pixdlm-7b/config.json','pretrained/pixdlm-7b/generation_config.json','pretrained/pixdlm-7b/added_tokens.json','pretrained/pixdlm-7b/special_tokens_map.json','pretrained/pixdlm-7b/tokenizer_config.json','pretrained/pixdlm-7b/tokenizer.model']; [print(hf_hub_download('WhynotHug/PixDLM',f,revision='f40fa586e28f644d5db19e6d8905f626a6b7fd13',local_dir='/root/autodl-tmp/p1-prep/assets/pixdlm-source'),flush=True) for f in files]"
```

独立环境`pip check`返回`No broken requirements found`；仅验证当前下载工具依赖，不代表Pix推理兼容。数据盘df报告50G、已用504M、约50G可用。

用户本地即将关机：本轮未留下后台下载任务，SSH已退出、隧道已关闭。服务器文件不随本地关机删除。后续若需离线持续下载，应在容器侧使用独立网络及tmux等持久会话，明确日志、容量、重试上限与验收；目前未创建这样的任务。网络准备不改变P1研究判断，尚无模型输出。
