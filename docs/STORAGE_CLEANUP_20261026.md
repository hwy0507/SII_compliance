# 旧实验产物清理与当前研究依赖

2026-10-26 用户明确要求：只围绕当前新指标研究，删除已经不再使用的旧实验输出。
本次在本机 airpig 执行文件级清理，未按日期整目录删除，未改当前研究结果。

## 实际清理结果

| 范围 | 删除文件数 | 文件系统可用空间实际增加 |
|---|---:|---:|
| 旧物理轨迹、逐子步记录、逐回合 MJB 副本与旧媒体 | 27,711 | 385,989,935,104 bytes（约359.48 GiB） |
| 已有后继 checkpoint 的旧 RL 中间二进制状态 | 11,249 | 60,165,271,552 bytes（约56.03 GiB） |
| 合计 | 38,960 | 446,155,206,656 bytes（约415.51 GiB） |

最终复核可用空间约 **419.86 GiB**，磁盘使用率从100%降至53%。
按实际文件系统增量报告，不将硬链接的多条路径重复计作已释放容量；元数据、压缩清单和
系统并发写入会使前后全盘差值与逐阶段增量略有差异。

第一阶段主要来自 `baseline_local_rl_20261009` 的旧训练/恢复回合、
`rl_full_retrain_20261014_v2`、`rl_tuned_20261015_v3b`、旧 reward 诊断、
旧经典参数搜索以及早期对比轨迹。第二阶段仅删除旧 RL 各父训练目录中编号低于最后
checkpoint 的二进制负载；每个父目录的最高编号 checkpoint 和其 JSON 收据仍保留。
目录名 `server_archive` 没有被当作已备份的证据。

## 当前保留范围

以下目录均相对于本机
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/`：

- 全部 `nonrl_*`，尤其 `nonrl_spt_matrix_20261025_v4` 的64回合、成功与失败、全部原始轨迹、
  源码、模型和审计；九个新拟合、数据执行链诊断与解析最优性诊断也完整保留。
- `fair_comparison_20261013_v2` 整体保留：冻结 source、数据/划分、全部候选和seed、
  checkpoint、经典控制参数、依赖和协议。七模型复测依赖仍位于登记路径。
- `teacher_student_15h_20261012_v3`、旧 teacher 系列和 `paper_esn_*` 保留原始示范与来源资料；
  未把这些旧日期目录直接判为无用。部分来源历史依赖尚未逐项证明可删，保守保留。
- `baseline_local_rl_20261009/runtime` 完整保留，包括 v6 MJB、menagerie、SimbaV2及奖励源码。
  `rl_tuned_20261015_v4` 完整保留，包含另一个 RL agent 的协议、conditions、teacher和参数源。
- 此前记录的最终四个 RL 模型所在两个 run、`rl_goal_acceptance_20261018_v3`、
  `paired_baseline_development_20261012_v2` 完整保留；未把旧模型当作新标准训练结果。
- 全部 Git 跟踪文件、源代码、运行环境、数据目录、学习目录、依赖目录、训练曲线日志、
  汇总报告和失败结论保留。未触碰项目以外的数据集、缓存或系统配置。

## 删除清单与验证

第一阶段证据：[计划](evidence/storage_cleanup_20261026/PLAN.json)、
[逐文件清单](evidence/storage_cleanup_20261026/DELETE_MANIFEST.jsonl.gz)、
[删除收据](evidence/storage_cleanup_20261026/DELETED.jsonl.gz)、
[结果](evidence/storage_cleanup_20261026/RESULT.json)。

第二阶段证据：[计划](evidence/storage_cleanup_checkpoints_20261026/PLAN.json)、
[checkpoint选择](evidence/storage_cleanup_checkpoints_20261026/CHECKPOINT_SELECTION.json)、
[逐文件清单](evidence/storage_cleanup_checkpoints_20261026/DELETE_MANIFEST.jsonl.gz)、
[删除收据](evidence/storage_cleanup_checkpoints_20261026/DELETED.jsonl.gz)、
[结果](evidence/storage_cleanup_checkpoints_20261026/RESULT.json)。

清单包含准确相对路径、device/inode、大小、mtime、分配块和硬链接数；删除前全量核验，
删除时再次核验身份，拒绝符号链接/越界/已变化文件。持有全局计算锁期间执行；
操作前 systemd 无 sii 服务，未发现活动训练或仿真 worker。只 unlink 清单文件，未递归移除根目录。

每阶段都核验其剩余文件清单：第一阶段281,321个、第二阶段270,072个文件，均无缺失或
device/inode/大小/mtime/分配块变化。第一阶段的“保留”是该阶段状态，第二阶段授权删除项
另有独立清单。两份压缩 `RETAINED_INVENTORY.jsonl.gz` 同目录保存，作为阶段性核对证据。
PLAN/RESULT 中的清单 SHA256 针对解压后的 JSONL；压缩文件 hash 见最终验证。

[最终验证](evidence/storage_cleanup_20261026/VERIFICATION.json) 记录：

- 当前64回合 `SHA256SUMS` 的2,280项 `sha256sum -c --quiet` 全通过；原清单本身hash不变。
- 七模型 checkpoint 和 metadata hash全部匹配；训练数据hash仍为
  `f00edd388a476879e56e51cf91c9cc04425a91d1df649eb9b78bf6197f33ddd6`。
- RL交接 protocol/conditions/teacher/PRIORS 与共享MJB hash匹配。
- 56回合复测 dry-run 的 `disk_admitted=true`（需11.5 GiB）；本轮未启动物理复测。

## 恢复边界与后续研究

**被删原始产物没有本轮核验的外部备份，可能无法恢复。** GitHub发布的是清单和小型证据，
不包含被删除的大文件，不构成原始数据备份。本轮没有向服务器导出或删除任何文件。
历史 execution/报告保持原样，因此其中某些旧路径现已不存在；不能据旧成功审计收据声称
历史 raw 仍齐全。第二阶段留下的中间 checkpoint 元数据目录也不再是可恢复训练的完整 checkpoint。
今后引用旧轨迹或续训前，先查这两份删除清单，不自动重新下载全部旧产物。

当前非RL研究的空间阻碍已经解除，但Goal科学目标尚未完成，新七模型闭环结果尚不存在。
后续沿用 `NONRL_OPTIMIZATION_AUDIT_20261026.md` 中已登记的56回合计划，启动前仍核对
进程、执行收据、冻结hash和资源准入；当前新指标与训练/测试划分不因清理而改变。
