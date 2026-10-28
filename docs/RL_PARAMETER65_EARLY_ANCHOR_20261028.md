# 第65轮前5000审查、全1944终端锚点与接续交接

2026-10-28 16:25 UTC，Goal active，尚未整体收敛。实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；Torch `B/env/bin/python`，Direct JAX `B/serl_env/bin/python`。完整64结论和checkpoint hash见[完整64交接](RL_PARAMETER64_COMPLETE_20261028.md)，已发布 `3cd622f01462b7a7d60a6dc575cf883080b39c11`。

## 原65训练继续

`B/runs/parameter_capacity_pool30_cycle65_20261026_v1` 于16:00:07 UTC启动。原I/A/V learner分别3518809/start39892318、3518810/start39892318、3518811/start39892319，archive3518812/start39892319。16:24:48实际步数2694726/2695431/2696705，身份保持，尚无完整/失败标记。startup已完成1000/1000/2000检查，全64 replay/history/optimizer/RNG及30sampler/MJB保持，新reward复算0。

原reward/gate/物理/LR/终端权重128/batch65536/UTD1/4m append和历史23/47 marker不变。不因对话退出或观察器结束重启科学进程。Direct33仅原训练集经验数值收敛而Task/Strict0/0；不为占用GPU启动34。原62–64窗口三路均未过描述性5%，I近零保护，A/V相邻变化大；保留原59–61失败、I56–58和V53–55通过。

## 前5000与全量终端锚点

`B/runs/parameter65_first5000_20261028_v1` 的REVIEW/SAVED_REVIEW/PLOT_INSPECTION已完成，实际loss.png已查看。全部5000原字节前缀、连续步号、全数值有限及独立算术通过。登记发生在65启动且前缀可用之后，仅描述早期数据。

|方法|critic首1000→末1000|critic最大值|actor首1000→末1000|
|---|---|---|---|
|I|1.729979808→1.593778171|19.049345016|25.632912064→25.621734503|
|A|1.297140518→1.207391113|6.546500206|−9.895209580→−9.892515387|
|V|1.000113431→1.007972671|16.365324020|−14.039191906→−14.122810424|

I/A actor在此短前缀较平，V actor仍下降；V critic约1.0且有有限尖峰。不能替代完整65/奖励稳定或收敛判定，不新增尖峰失败阈值。

`B/runs/vmc65_terminal_anchor_followup_20261028_v1` 已从完整64提取全部1944×57固定终端输入，与已审64保存数组精确一致；独立标量SSE12834.46422473921。anchor64.npz SHA256 `42d35d2f3e8706530329ce0578af924f87ff1ec53709590e51846841492ddfa4`，ANCHOR_REVIEW/ANCHOR_SAVED_REVIEW/SOURCE_REVIEW通过，无新前向/物理/优化。原五focus保留，完整65预计1974终端；旧全体与新30分别报告，零终端误差不是停止门。

## 已运行的审计与仅恢复准备

所有进程行动前必须核对PID及/proc/PID/stat start ticks；以下等待超时或自然退出不代表训练失败。

|任务|PID / start ticks|证据与约束|
|---|---|---|
|全65 loss|3549843 / 39897957|`B/runs/parameter65_loss_20261028_v1`，CPU54/7200秒；完整49–64历史保留并追加65，paired64→65和0600不变|
|全1944终端65对照|4103562 / 39997944|CPU53/7200秒；完整65归档及learner自然退出后运行track.py/review_values.py，实际结果与图审待|
|全标签64→65|4014641 / 39981812|`B/runtime/parameter_task_label_audit65_20261028_v1`，CPU53/7200秒；auditor原字节保持，真实不完整65拒绝且无输出|
|66仅恢复检查|4014576 / 39981805|`B/runtime/prepare_parameter66_20261028_v1`，CPU53/14400秒；完整65归档/health及learner退出后check-only，无自动66训练|
|原65–67窗口|3549846 / 39897958|`B/runs/parameter_capacity65_67_reward_stability_20261028_v1`，CPU54/14400秒，约20:01 UTC到期；65/66/67均待，输出REVIEW.json|

原PLAN SHA256：loss `d92fb5a877cb1aaef7cb1a1a580374629427d4baa65ac274e435b5d9720b0412`；terminal `9ee4197eda1360ee8653a4e3bd8682b3c09345dd77d7be8190301bffa4c4088a`；label PLAN65 `69ba11f35c8287c59a0e55ae3ec0c6cac891196d81a21ba2125240a4e0c28810`；prepare66 REGISTRATION `c58ca88feb2a38c0f5cbfcf5e3fe0e8e85c948e7146756e595578946b4a7cd75`；原65–67 PLAN `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0`。

prepare66实际缺DECISION66启动拒绝且无训练目录；沿用普通读写/fsync/精确回读复制。源码映射采用数字边界同时替换，包含零填充周期，逆变换/AST/日期/owner/hash通过；没有修改运行中的科学源码。旧copyfile异常保留在prepare64/packaging_failure_v1，原因未确定。完整66 loss静态准备和65标签独立保存审查仍待。

## GPU持续保活

用户再次明确：科学完成后也保持GPU负载，监测阈值50%。v5仍运行于 `/tmp/sii_gpu_util_guard_20261028_v5`，共享源码 `B/runtime/gpu_util_guard_20261028_v5`。主管3256866/start37410686，GPU0–3 worker3256867/37410690、3256868/37410690、3256869/37410691、3256870/37410693。v5 STOP不存在，v4 STOP保持，禁止恢复旧v4。当前不是跨重启服务，/tmp不能视为重启持久存储。

16:18保存快照逐项身份通过，GPU79/94/95/95%；16:10:02–16:18:44实际103条guard采样min74/66/68/66%、mean78.80582524/88.96116505/89.04854369/89.71844660%，低于50全0，maxgap5.2911005秒。证据 `B/runtime/parameter65_verified_snapshot_1618_20261028_v1`。16:24:48即时查询77/92/93/97%。均包含合成保活，不等于纯科学吞吐或每瞬时保证；09:03历史全0事件仍保留在GPU guard文档。

## 保存与下一步

已核验共享SSD包 `B/repository/RL_PARAMETER65_EARLY_ANCHOR_20261028_161931/SMALL_EVIDENCE.tar.gz`，55成员/1322274字节/SHA256 `495c20dc4422c804a12891b7f7a21487d53177d861c07098285294d0ba2bdc4e`。逐字节、tar成员大小/hash、Python AST通过；[收据](RL_PARAMETER65_EARLY_ANCHOR_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER65_EARLY_ANCHOR_20261028/MANIFEST.json)。大checkpoint/replay/raw仍原共享SSD；HDD配额满，仅重写既有LATEST入口，非HDD/arm1全备份。

接续实际fetch/read main `3cd622f01462b7a7d60a6dc575cf883080b39c11`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未见新的协议变化，非RL并行工作完整保留，无子agent。下一步继续原65，完成全loss/health/标签/固定终端的独立算术和实际图审，结合原65–67窗口判断；经完整证据及精确恢复后再决定有限66。Goal active。
