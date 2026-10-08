# 工作区桥接：完成第二个本地仓库改名

> 已完成（2026-10-08）：`Z:\My_PAPER` 已原子改名为 `Z:\Guidance-try_2`。改名前后 HEAD 均为 `f21e82273434e21c8827cb621d6715ce611a4c27`，Git 状态未变，1282 个文件的相对路径、大小和修改时间一致；origin 指向 `https://github.com/RolyForden/Guidance-try_2.git`。本地路径说明已更新。以下保留原交接快照，不再执行改名步骤。

## 任务与权限

用户要把两个旧仓库的云端名称、本地文件夹和名称索引统一。当前只剩第二个本地文件夹尚未改名。先完成这个维护任务，不开展新课题或实验。

用户已授权：每次修改检查完成后默认 commit + push，除非明确说不提交。只提交本次自己的改动，保留他人 WIP。不得强推、重写历史、删除实验或终止未知进程。

## 已完成与当前状态

| 仓库 | 本地目录 | 状态 |
|---|---|---|
| `RolyForden/Guidance-try_1` | `Z:\Guidance-try_1` | 已改名，README 路径更新已推送到 `codex/lean-research-workflow`，提交 `d6bdf45`。 |
| `RolyForden/Guidance-try_2` | **仍为 `Z:\My_PAPER`** | 云端已改名，origin 已指向新 URL；本地改名被 Windows 拒绝，报告目录被进程占用。 |
| `RolyForden/personal-paper` | `Z:\personal-paper` | 母本，跨仓库名称与链接更新已推送。 |
| `RolyForden/Guidance-try_3` | `Z:\Guidance-try_3` | 已从母本初始化，main 已推送；尚未确定题目或建立课题目录。 |

两个旧云端仓库改名时已核对 repository ID 不变、仍为私人仓库。已有 Git 历史及实验文件未删。此前一次 Move-Item 发生部分移动，已经恢复原内容；随后第一目录原子改名成功。遗留的两个空恢复目录已清理，不需要重复处理。

旧会话绑定 `Z:\My_PAPER`，可能是占用来源之一，**未确认具体进程**。请用户离开旧工作区后，从本工作区执行；不要把猜测写成已核实根因。

## 接手步骤

1. 读取本工作区根 `AGENTS.md`、`README.md` 和本文件。所有维护命令显式指定 `Z:\Guidance-try_3` 或 `Z:\` 为工作目录，不要进入待改名目录启动常驻进程。
2. 核查源 `Z:\My_PAPER`、目标 `Z:\Guidance-try_2`、Git origin 与工作区状态。预期 origin 为 `https://github.com/RolyForden/Guidance-try_2.git`。记录 HEAD；已有 WIP 原样保留。目标已存在时先检查内容，不覆盖、不把源移进目标形成嵌套目录。
3. 若源存在且目标不存在，用下列同盘原子目录改名。**不要使用会逐项搬动内容的 Move-Item 代替。** 错误必须中止，不能失败后继续打印成功。

```powershell
$ErrorActionPreference = 'Stop'
$source = 'Z:\My_PAPER'
$target = 'Z:\Guidance-try_2'
if ((Resolve-Path -LiteralPath $source).Path -ne $source) {
    throw 'Source path mismatch'
}
if ([IO.Path]::GetFullPath($target) -ne $target) {
    throw 'Target path mismatch'
}
if (Test-Path -LiteralPath $target) {
    throw 'Destination already exists; inspect before proceeding'
}
[IO.Directory]::Move($source, $target)
Write-Output "Renamed: $target"
```

4. 成功后核查新路径中的 Git HEAD、status 与 origin，确认未出现文件删除或原有 WIP 丢失。HEAD 应与移动前一致；旧路径应不再存在。
5. 更新 `Z:\Guidance-try_2\README.md` 中这条已经核实存在的旧工作区说明：目前写“本地工作区仍为 `Z:\My_PAPER`，文件夹名称未随云端改名”，改成实际新路径。扫描两个旧仓库、母本及本工作区里的活动索引，修正真正指向旧工作区的引用；不要全局替换原始日志、历史执行命令、PDF 或本交接文件里的历史说明。
6. 在改动所属仓库运行 diff 检查与相关项目入口校验，只暂存本次实际改动，commit 后 push 到该仓库当前分支。文件夹改名本身不会产生 Git 提交，不为它制造空提交。
7. 汇报实际成功路径、提交与推送结果。若仍被占用，立即报告具体错误和已确认状态；不自动杀 Codex、终端或其他未知进程，不复制整个仓库冒充完成改名。

## 之后的工作

用户准备在 `Guidance-try_3` 开新方向，仍会在这里给出材料。目前没有获批的新题目、底座论文或实验。完成改名后等待用户提供新方向，不复活 FocalAfford、SceneFun3D 或 OpenAD。

本文件是维护交接快照，不是长期项目状态或新的科研规则；任务完成后可在文件顶部注明完成，避免下次误执行。
