# 容器预检 - 2026-10-08

范围：用户提供的容器，只读硬件、目录与包元数据检查。无模型加载、训练、评测、安装或大文件下载。连接凭据与完整交互转写不入Git。

## 实际观察

| 项目 | 结果/范围 |
|---|---|
| 系统 | Linux，内核5.15.0-94-generic |
| GPU报告 | NVIDIA GeForce RTX 4080 SUPER；32760 MiB总显存；查询时0 MiB已用；驱动580.76.05 |
| 系统盘 | df报告30G总量、17G可用；不用于大模型缓存 |
| 数据盘/root/autodl-tmp | df报告50G总量、约50G可用；顶层仅看到平台.autodl目录 |
| Python | /root/miniconda3/bin/python，3.12.3 |
| PyTorch | 包元数据版本2.8.0+cu128；未进行模型或CUDA算子兼容验证 |
| 缺少包 | importlib检查transformers、deepspeed、flash_attn、huggingface_hub、sam2均为ABSENT |
| 资产搜索 | 在/root下至深度4，以及指定数据盘/模型缓存等目录未发现名称匹配PixDLM、DRSeg、LLaVA、SAM2的目录；不声称整个系统绝无资产 |

## 命令与工程说明

SSH连接由用户授权，本机首次接入采用accept-new记录服务器公钥，后续StrictHostKeyChecking=yes；未通过独立渠道核验指纹，不将其称为已验证身份。

```bash
uname -a
nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv,noheader
df -h / /root /root/autodl-tmp
find /root/autodl-tmp /root/.cache/huggingface /root/autodl-fs /workspace /data -maxdepth 3 -type d \( -iname '*pixdlm*' -o -iname '*drseg*' -o -iname '*llava*' -o -iname '*clip*' -o -iname '*sam2*' \) 2>/dev/null
find /root -maxdepth 4 -type d \( -iname '*pixdlm*' -o -iname '*drseg*' -o -iname '*llava*' -o -iname '*sam2*' \) 2>/dev/null
/root/miniconda3/bin/python --version
/root/miniconda3/bin/python -c "import importlib.util as u; import importlib.metadata as m; names=['torch','transformers','deepspeed','flash_attn','huggingface_hub','sam2']; print({n:('PRESENT' if u.find_spec(n) else 'ABSENT') for n in names}); print({p:m.version(p) for p in ['torch','transformers','huggingface-hub'] if u.find_spec(p.replace('-','_'))})"
```

首次复合预检返回1，末尾ls含不存在的目录；SSH认证与前面的硬件查询已成功，不把返回1误报成连接失败。独立非登录bash没有conda PATH，初始python查询提示command not found；改用现存绝对路径后得到上述版本。这是运维查询修正，不是实验失败重跑。

## 下一步与边界

- 等待下载资产与准备独立环境授权，不覆盖基础Python/PyTorch。
- 逐项核定模型/数据版本、落地哈希、实际容量、缓存重复占用及许可；如果50G不足，停报，不擅自扩容或删平台目录。
- 冻结question-only输入与validation命令；公开脚本默认test，不能直接执行。
- 无自己的IoU、失败样本、吞吐或单样本显存数据，不能宣称底座就绪或P1成立。
