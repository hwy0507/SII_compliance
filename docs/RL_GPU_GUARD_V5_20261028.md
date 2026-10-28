# GPU共同等待后的本机守护v5与原58续接

2026-10-28 09:11 UTC，Goal active。原58三路训练和冻结55评测均继续，没有重启科学任务。当前守护已从v4切换为本机文件运行的v5，恢复时必须读本文核对原PID，不能按旧文档再启动v4。[此前58科学交接](RL_PARAMETER58_EARLY59_PREP_20261028.md)、[完整57审查](RL_PARAMETER57_COMPLETE_20261028.md)继续有效。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。开工实际查询/fetch/read main `78e7b7a12d74241e2ad9428616b31ce0cef91345`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`和日志；无子agent，未改科学协议。

## 实际异常与恢复

09:03–09:04连续人工nvidia-smi观察四卡均0%，09:04:09仍0%，功率约16–28W。原58 learner1846052/1846053/1846054及v4 supervisor1629438/四worker均D状态，wchan为cxiWaitEventWait。训练PROGRESS同期停止更新；内存可用约805GiB、swap0，不能称正常训练或仅瞬时仪表抖动。

原v4 samples.jsonl从epoch1793178162.963458到1793178278.557077相隔115.593619秒；日志本身没有采到中途0%，因为监督进程也在等待，人工观察与日志缺口分开保留。/proc/PID/stack读取权限被拒绝，未获得完整内核栈；共享盘挂载为GPFS，现象与共享文件系统等待相符，但根因尚未确定，不能作已证实故障归因。

09:05:18原进程已自行恢复，GPU83/92/67/94%，原训练继续推进，没有信号/重启。此次事件不同于08:36单次低谷，两个事件各自记录保留。

## v5本机运行文件与受控交接

旧guard每个20ms周期都读取ROOT/CONTROL.json并检查STOP，另定期写worker状态，supervisor每5秒写采样和控制；旧ROOT在共享SSD。v5直接使用字节完全相同的guard.py，改变实际运行目录为 **`/tmp/sii_gpu_util_guard_20261028_v5`**，使稳态控制/STOP/状态/日志读写在本机overlay/tmp上，不再直接依赖共享ROOT。Python/Torch解释器仍使用原B/env，不能保证消除全部共享存储依赖或所有GPU低谷。

共享审计与源副本为`B/runtime/gpu_util_guard_20261028_v5`；这里是归档，**当前运行的CONTROL/STOP不在这里**。local_snapshot只是当时快照，真实状态读/tmp路径。算法、矩阵尺寸/图、20ms周期、70–90% duty、控制目标70/资源阈值50及CPU52–54均不变。零科学checkpoint/replay访问或优化更新。

新v5先启动，确认全部4个worker有真实graph进度、无FAILURE且身份存活，才向旧v4写STOP。随后确认旧supervisor和worker全部退出。短暂交接重叠仅合成负载，训练/冻结评测没有收到终止信号。

|角色|PID|/proc启动ticks|
|---|---:|---:|
|v5 supervisor|3256866|37410686|
|GPU0 worker|3256867|37410690|
|GPU1 worker|3256868|37410690|
|GPU2 worker|3256869|37410691|
|GPU3 worker|3256870|37410693|

当前STOP为`/tmp/sii_gpu_util_guard_20261028_v5/STOP`，正常继续时必须不存在；旧`B/runtime/gpu_util_guard_20261028_v4/STOP`现在**有意存在**，不要删除或误报v4故障。用户要求科学结束仍保持GPU运行，v5继续独立运行。它不是跨重启服务，/tmp不保证重启后保留；完整源码与启动依据已归档共享SSD。重启恢复前必须检查实际GPU/进程身份，确认没有存活v5才根据归档恢复，禁止重复启动。

## 切换后固定复核

旧v4退出后登记60次、间隔1秒检查，逐次v5全部身份及原58三learner身份保持。四卡最低65/65/70/65%，均值75.10/88.55/90.083333/88.883333%，低于50计数均0；所有60原样本及独立标量复算通过。包含合成保活，不是纯训练吞吐。此窗口没有持续低谷，不宣称此前等待根因已证明或未来每瞬时都保证≥50%。

09:10真实状态：原58步数2417451/2418257/2419911，各30sampler继续，尚未完整；冻结55原三evaluator完整20/20/19，root仍live。原archive1846055、loss1862646、56–58统计788599、59恢复2490236、VMC58终端2624191全部PID/start核验live。GPU即时80/94/95/94%。原58 learner start仍37173515/37173515/37173516，未重启或重置回放/优化器。

## 原统计独立复核准备

新增`B/runs/parameter_capacity56_58_reward_stability_20261028_v1/review_saved.py`，仅等原REVIEW存在后手动核验全部保存均值/相对变化/5%判定/配对差值及全loss算术；AST通过，实际统计未生成，因此未执行或冒称通过。原登记audit/waiter/窗口/阈值/seed/5000bootstrap/真实episode长度未改。脚本明确不独立重跑bootstrap区间，待实际结果后另外检查图。

## 保存和下一步

小证据`docs/evidence/RL_GPU_GUARD_V5_20261028`；共享SSD包`B/repository/RL_GPU_GUARD_V5_20261028_091123/SMALL_EVIDENCE.tar.gz`，28成员、10118字节、SHA256 `8d81383eecff7543eaf6655065a8938f8c268e8c30b01d15ce3a581a9c82c398`，逐成员字节核验。收据[RL_GPU_GUARD_V5_20261028_SAVE.json](RL_GPU_GUARD_V5_20261028_SAVE.json)。保存实际源/启动身份、旧守护退出、事件与采样缺口、全部60样本和独立算术、真实进度及原统计复核源码。大科学产物仍共享SSD，非HDD/arm1全备份。

继续原58、冻结55及全部既有等待任务。完整58后审查loss/health、全1734旧终端对照、原56–58统计与59check-only，再决定有限续训；不因观察期限结束重新启动原任务。Direct数值阶段仍保持、不启动34；整体收敛未证明。
