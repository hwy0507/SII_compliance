# 第66轮前5000、全1974终端锚点与后续审计交接

2026-10-28 17:19 UTC，Goal active，尚未整体收敛。实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Torch `B/env/bin/python`。完整65/checkpoint hash和66精确恢复见[完整65交接](RL_PARAMETER65_COMPLETE_20261028.md)，已发布d4e8d136e9f1bd895f2bd7f7db921039aef337bc。

## 原66继续

`B/runs/parameter_capacity_pool30_cycle66_20261026_v1` 三learner I1279033/A1279034/V1279035 start40268104，archive1279036/start40268105。17:18:43 steps2729399/2730136/2731235，原身份live、没有完成/失败。startup1000/1000/2000已通过，全旧2717898/2718500/2719500行replay/history/optimizer和30sampler/MJB保持、新reward0。原batch65536/UTD1/终端权重128/4m append/历史23和47 marker、reward/gate/物理/LR不变。

原全66loss1286574/start40270137继续；原65–67窗口3549846/start39897958、PLAN SHA256 `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0` 不变，尚待完整66/67，输出REVIEW.json而非FINISHED。原62–64/59–61失败及I56–58/V53–55通过保留，不移动端点。Direct33仅训练集经验数值收敛、Task/Strict0/0，不启动34。

## 固定前5000已审

`B/runs/parameter66_first5000_20261028_v1` 在原66启动且前缀可用之后登记。全部5000原字节前缀精确、连续步号、全数值有限、独立标量复算通过；实际loss.png已查看，REVIEW/SAVED_REVIEW/PLOT_INSPECTION完成。

|方法|critic首1000→末1000|critic最大值|actor首1000→末1000|
|---|---|---|---|
|impedance|2.097179783→2.113458636|16.084032059|25.168606546→25.185943863|
|admittance|1.263243710→1.209251718|3.635131121|-9.569554365→-9.563900227|
|vmc|0.747719643→0.835390660|6.839618683|-14.099602674→-14.101506604|

I critic浅U形且有有限尖峰、actor中段微升后较平；A critic初降后约1.2、actor小幅波动；V critic末段滚动均值回升约.84、actor约−14.10较平。只有前5000描述，不替代完整66或原65–67奖励稳定判定；没有新增有限尖峰失败阈值或收敛结论。

## 全1974终端锚点和等待

`B/runs/vmc66_terminal_anchor_followup_20261028_v1` 已从完整65 checkpoint提取全部1974×57终端输入，与已审65保存indices/reward/mask/Q/denominator精确；独立标量SSE6761.694451274101。anchor65.npz SHA256 `7d4ce7624687bcc3b26774cfad75c4ce5fcc83d4b85a59706ae6edc44c8d9e5d`。ANCHOR_REVIEW/ANCHOR_SAVED_REVIEW/SOURCE_REVIEW通过；0新网络前向/物理/优化。

waiter1692633/start40342791，CPU53/7200秒，PLAN SHA256 `97b840bb97dc0e4c35d26e8aadd88b28ef223102f2018af1b5fad90ea9404953`，绑定真实66三learner/归档/源码。完整66归档且原learner自然退出后才读取最终checkpoint，验证1974旧行不变并对照全部2004终端。原五focus2050526/2299142/2046571/2423133/2423122及历史58上下文保持；全体结果与新增30分开，零终端误差不是停止门。实际66结果、保存复算和图审尚待。

## 全标签66与67仅恢复

标签脚本 `B/runtime/parameter_task_label_audit66_20261028_v1`，结果 `B/runs/parameter_task_label_audit66_20261028_v1`。通用auditor与65版字节相同，只推进waiter到65→66；实际未完整66调用拒绝且没有输出，INCOMPLETE_REJECTION保留。等待1669332/start40338178、CPU53/7200秒，PLAN66 SHA256 `ce7e513e3e1b25226f815361db280899fc6955879f1af4651d1ad1b5c4bd3f16`。完整后输出COMPLETE65_66/FINISHED66，再运行独立保存审查，不把此前结果当新结果。

`B/runtime/prepare_parameter67_20261028_v1` 等待1669294/start40338171、CPU53/14400秒，REGISTRATION SHA256 `42359c627742c818dbd0b36bed624f51bec77552335991f535c7e3782cddcea6`。完整66归档/health通过并原learner退出后才做全state/replay/下一65536 check-only；不自动训练。真实缺DECISION67的launcher调用拒绝且未创建67训练目录，UNREVIEWED_LAUNCH_REJECTION保留。

源码采用数字边界同时映射、显式零填充周期、哈希保护和逆变换/AST/日期/owner核验。capture仅显式绑定完整65已核验checkpoint hash，原五focus不变。复制继续普通读写/fsync/逐字节回读；旧copyfile异常仍保留。没有改原66运行中的科学源码。

## 完整67 loss及66标签复核静态准备

`B/runtime/parameter67_loss_preparation_20261028_v1` 四脚本已准备：完整49–66历史保留并仅追加67，paired66→67、原0600及原53–55说明保持。精确字符串同时映射、逆变换/AST通过；没有67loss运行目录/PLAN/waiter或67训练。须完整66审查、精确恢复和真实67启动后才部署绑定。

`B/runtime/prepare_parameter67_20261028_v1/review_labels66.py` 由已实际通过的65保存审查器推进，逆变换/AST通过；完整66标签及全loss保存复核就绪后才能运行，目前无实际结果。上述静态准备不是科学完成证据。

## GPU和持久保存

`B/runtime/parameter66_verified_snapshot_1716_20261028_v1/SNAPSHOT.json` 已核验三learner、归档、全loss、全终端/标签/67仅恢复/原窗口及五guard原身份live。17:16 steps2727671/2728381/2729483，GPU80/98/94/93%；17:18:43独立即时GPU79/91/96/96%。

本轮17:11:55–17:16:22的53条guard采样min74/69/69/70%，mean78.75471698/90.20754717/90.33962264/90.60377358%，低于50全0，maxgap5.249742秒。包含合成保活，不等于纯科学吞吐/每瞬时保证，历史09:03全0事件保留。

实际v5 `/tmp/sii_gpu_util_guard_20261028_v5`，主管3256866/start37410686、workers3256867–3256870/start37410690/37410690/37410691/37410693；科学完成后仍继续，v5 STOP不存在、v4 STOP保留。目前不是跨重启服务；行动前核验PID+start ticks，观察器超时/自然退出不重启科学任务。

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER66_EARLY_ANCHOR_20261028_171823/SMALL_EVIDENCE.tar.gz`，73成员/1343652字节/SHA256 `3dcb8c300ef5b6a8fe22b168abfbe65fda80cf7a475e6417a5ed4b58b6922dc3`。逐字节/AST/tar成员大小/hash通过；[收据](RL_PARAMETER66_EARLY_ANCHOR_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER66_EARLY_ANCHOR_20261028/MANIFEST.json)。大checkpoint/replay/raw仍共享SSD，HDD只重写既有LATEST入口，非HDD/arm1全备份。

开工实际fetch/read maind4e8d136，收尾mainb77fd976470f0caf2fc9227884460f8327d1667f、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d。另一主机非RL intent teacher第一版失败/第二版在途日志及交接已读，fast-forward完整保留，无本机RL协议变化。下一步继续原66，完整loss/health/标签/固定终端和原65–67窗口按证据审查，之后再决定有限67。Goal active，无子agent。
