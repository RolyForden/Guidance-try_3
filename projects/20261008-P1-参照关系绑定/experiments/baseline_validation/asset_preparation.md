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

上一轮用户本地即将关机时：未留下后台下载任务，SSH退出、隧道关闭。服务器文件不随本地关机删除。后续镜像测速与后台准备另见下节；网络准备不改变P1研究判断，尚无模型输出。

## 镜像测速与后台准备

用户批准尝试hf-mirror.com，并随后要求在本地三分钟后关机前尽快完成安排。仅下载此前获批的四个公开大资产；版本与官方源端期望大小/哈希不变。下载过程不上传私有材料或凭据。

- 容器直连镜像API返回200；SAM固定revision、898083611字节及LFS SHA256与前述官方元数据相同。
- 前8MiB请求返回206，8388608字节，15.677171秒，535084 bytes/s；SHA256为0acf013594236fdc40fb26a7a38313d01a3d76b907ce9d3fe29268c19741c3b1，与现有官方源.partial前8MiB逐字节一致。
- 两路并发读取第二、第三个8MiB片段，均返回206，各8388608字节；总墙钟28.181秒，合计约595KB/s。两个片段与官方源.partial对应区间逐字节一致。并发收益有限，不能承诺所有文件持续同速或一晚完成，也不能从结果确定旧链路具体瓶颈。
- 启动容器侧`nohup timeout 43200 curl --parallel --parallel-immediate --parallel-max 2 ...`，PID2173（timeout）；每个传输HTTP/1.1、直连镜像、固定resolve revision、续传、15秒连接超时、21600秒传输上限、最多2次重试、10秒间隔、120秒重试预算。总任务最多12小时。不是定时任务，不自动开关机、不扩盘、不训练。
- 目标为数据盘assets/sam2/sam2.1_hiera_large.pt.partial、assets/clip/model.safetensors.partial、assets/drseg/DRSeg.zip.partial、assets/pixdlm/pytorch_model.bin.partial。日志为`/root/autodl-tmp/p1-prep/logs/mirror-download.log`；stdin为/dev/null，输出写远端日志，网络明确不走本地代理。保留已有SAM部分文件续传。
- 文件未验收前保持.partial；curl传输完成不等于哈希合格。下一次复连先检查日志、大小与前述完整SHA256，不加载模型、不读取或解包test。预计下载体积与当前容量允许保留10GiB余量；若出错停报，不无界重启。
- 启动后断开SSH并重新连接核实：PID2173的PPID已为1，curl子进程2174仍运行；SAM由56029184增至57110528 bytes，CLIP由7139328增至8155136 bytes。说明实际后台传输在断连后继续，不是仅凭nohup命令推断。短测速度不能作为当前后台持续吞吐保证。复检后再次退出SSH，未建立本地代理隧道。

## 2026-10-09下载验收

复连后PID2173/2174均不存在，原后台任务已结束。远端日志保留，不删除或覆盖；未重新启动下载、安装推理依赖或运行模型。

| 文件 | 实际字节数 | 官方期望字节数 | 结果 |
|---|---:|---:|---|
| CLIP model.safetensors.partial | 1710540580 | 1710540580 | sha256sum为a2bf730a0c7debf160f7a6b50b3aaf3703e7e88ac73de7a314903141db026dcb，与官方源一致；完整验收，暂保留原文件名 |
| SAM sam2.1_hiera_large.pt.partial | 150288598 | 898083611 | curl 18，传输提前关闭；不完整 |
| PixDLM pytorch_model.bin.partial | 173391299 | 13611289441 | curl 18，传输提前关闭；不完整 |
| DRSeg.zip.partial | 未创建 | 2641097515 | HTTP 404；原命令漏了dataset的/datasets/前缀 |

四个目标文件现有字节合计2034220477（约2.03GB），其中通过完整验收的只有CLIP约1.71GB。不能把部分字节当作可用模型；短测约0.54MB/s没有转化为稳定的整体下载速度。

DRSeg错误由主agent构造URL时混淆model/dataset仓库类型造成，不是数据不存在或镜像不可用。固定revision的镜像dataset API返回版本、大小和LFS SHA256均与此前官方值相同；正确地址为`https://hf-mirror.com/datasets/WhynotHug/DRSeg/resolve/2b143f9a0721b7b5dbba4dd9f0bed9a22ede444d/DRSeg.zip?download=true`。仅将路径类型修正后，单字节Range测试返回206、1字节、3.382762秒；这验证了正确地址可读，不等于完整数据集已下载。

```bash
ps -p 2173,2174 -o pid,ppid,stat,etime,comm
stat -c '%s %n' /root/autodl-tmp/p1-prep/assets/sam2/sam2.1_hiera_large.pt.partial /root/autodl-tmp/p1-prep/assets/clip/model.safetensors.partial /root/autodl-tmp/p1-prep/assets/drseg/DRSeg.zip.partial /root/autodl-tmp/p1-prep/assets/pixdlm/pytorch_model.bin.partial
tail -n 20 /root/autodl-tmp/p1-prep/logs/mirror-download.log
sha256sum /root/autodl-tmp/p1-prep/assets/clip/model.safetensors.partial
df -h /root/autodl-tmp
```

stat因为DRSeg文件不存在返回非零，这与其他三个文件大小查询有效并不矛盾。日志记录SAM传输2487.980427秒、接收116734166新字节；Pix传输2261.150258秒、接收173391299字节；CLIP传输10576.412464秒、接收1710540580字节。不能由这些日志确认后台任务整体退出码或两个传输提前关闭的网络根因，不能声称因本地关机而失败。数据盘df报告50G总量、2.4G已用、48G可用。下一步修正dataset路径并使用可恢复的下载方式处理剩余资产；保留负结果和原日志，不无界重试。

## 2026-10-09继续下载

用户明确授权继续。复检无GPU、数据盘约48G可用。安装aria2 1.36.0：最初apt缓存无法定位软件包，刷新容器现有发行版源后成功安装aria2、libaria2-0、libc-ares2、libssh2-1（0个升级，4个新包）；未改Python/PyTorch或软件源配置。安装触发ldconfig报告平台NVIDIA空文件警告，未修复这些平台文件，不据此宣称推理兼容。

下载输入文件：[resume_downloads.aria2](resume_downloads.aria2)，三个URI分别固定SAM、DRSeg（dataset路径已修正）与PixDLM；每项配置官方源端SHA256，排除已验收CLIP。通过scp传到数据盘，源/目标SHA256同为1e205db41b143ff10021fb1989bb77cf15b99061f71aba284f274c6faa951b99。为防首次接管时丢失已有前缀，分别保留SAM/PixDLM的.pre-aria2备份（150288598、173391299字节）；未覆盖旧日志。

```bash
nohup timeout --signal=INT --kill-after=60s 43200 env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY aria2c --no-conf=true --input-file=/root/autodl-tmp/p1-prep/resume_downloads.aria2 --continue=true --always-resume=true --check-integrity=true --allow-overwrite=false --auto-file-renaming=false --file-allocation=none --max-concurrent-downloads=2 --split=2 --max-connection-per-server=2 --min-split-size=16M --max-tries=12 --retry-wait=15 --connect-timeout=15 --timeout=60 --lowest-speed-limit=1K --auto-save-interval=30 --summary-interval=60 --console-log-level=notice > /root/autodl-tmp/p1-prep/logs/aria2-resume-20261009.log 2>&1 < /dev/null &
```

PID28779为timeout，28780为aria2；总12小时上限，到时先INT保存进度、60秒后必要时终止；每项最多12次尝试，不无限重启。每30秒保存.aria2控制文件；不支持续传时停止，不悄悄覆盖已有文件。下载完整后按配置SHA256校验；之后仍须审阅日志和实际大小，不能将.partial文件名或稀疏文件表观长度当作完成证据。原始日志含上游临时签名跳转URL，只留容器，不上传完整日志；检查进度时过滤DL行。

断开SSH后重新连接：PID28779的PPID为1，28780仍运行；日志显示SAM约220MiB/856MiB、DRSeg约40MiB/2.4GiB，瞬时总速度约1.1MiB/s；两者.aria2控制文件已存在。说明SAM原前缀已接管、DRSeg正确地址实际开始传输。PixDLM在队列中；速度不是完成时间保证，所有未完整校验资产仍标未完成。数据盘报告约2.8G已用、48G可用，预期全部资产及备份仍保留10GiB余量。复检后退出SSH，无本地代理依赖、无模型运行。
