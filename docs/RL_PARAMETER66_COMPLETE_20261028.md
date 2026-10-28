# 完整66审查与准确续训67（2026-10-28 UTC）

Goal active。在线调参尚未整体数值收敛；继续原协议的有限67以完成原65–67窗口，不自动68。Direct33仅原训练队列经验数值收敛，Task/Strict仍0/0，不启动34。数值收敛不等于任务成功或泛化。

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；以下 `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，运行解释器 `B/env/bin/python`。大checkpoint/replay/raw在共享SSD；非HDD/arm1全备份。科学batch65536/UTD1、terminal权重128、4m append replay及历史23/47 marker、seed/30sampler、reward/gates/physics/LR/masks不改。

## 完整66

原三learner均自然结束，FINISHED为`stopped_at_complete_cycle`，各30×55秒/41250新增/noabort。完整65 replay/history/optimizer保持、新reward复算误差0、网络和优化器有限。证据 `B/runs/parameter_capacity_pool30_cycle66_review_20261026_v1/REVIEW.json` 与health/DIAGNOSIS.json；完整loss、独立SAVED_REVIEW和实际图审在 `B/runs/parameter66_loss_20261028_v1`。

|方法|steps / updates|mean reward|Task / Strict|critic首→末1000|critic mean / max|actor首→末1000|
|---|---|---|---|---|---|---|
|阻抗|2759148 / 2754149|−2.375253765|18 / 17|2.097179783→1.766867966|1.873477557 / 27.504137039|25.168606546→25.232664240|
|导纳|2759750 / 2754751|−10.217501638|14 / 13|1.263243710→1.606415380|1.273256378 / 29.879505157|−9.569554365→−9.279046515|
|VMC|2760750 / 2755751|−2.803235591|17 / 17|.747719643→.672560111|.728599707 / 13.846262932|−14.099602674→−13.794747125|

完整loss图中I actor早升/中段回落/末升，A critic约第34000条更新起出现密集有限尖峰并抬高均值，A/V actor持续上移。所有41250条连续更新的全部数值有限且独立统计通过，但不能据此声明loss已稳定或整体收敛；不新增有限尖峰阈值或零终端误差门。

health真实图已查看，右上长标题右侧被裁，但轴和数据可读；entropy接近原target，A alpha末段有峰，nextQ有限。I/A/V终端in-bag MAE .483714795/.270457497/.203710300，固定抽样TD MAE .250976461/.202749960/.148914031。诊断网络未变、优化0；不是全replay TD检查或成功门。

checkpoint位于 `B/runs/parameter_capacity_pool30_cycle66_archive_20261026_v1/{method}/cycle_00066.pt`：

- impedance SHA256 `ffe56a8b836374207f14333903c9044f1a8fb584c3237bd8123ea9a7e7d303ac`。
- admittance SHA256 `2d2ac343a670f5737e5083769d35d7d6eea4801ded319d2d6d0a28a909678a6a`。
- vmc SHA256 `da39afbb5af513044758446d9169e597073576ad02c66a9a81055435c8012bf5`。

## 全标签与固定终端

`B/runs/parameter_task_label_audit66_20261028_v1` 的COMPLETE65_66、独立保存复核和FINISHED66完成，全部180 rollout/90 reward对/Task与Strict计数通过，无Task-only变化遗漏。I long0000恢复Task/Strict；A long0200/0500恢复、short0200/0900失去Task/Strict，short0600 Task仍真但穿透.195247250→.230421531mm使Strict失效；V全部标签保持。A Task总数未变不能代表条件稳定。原物理门及全部失败保留。

`B/runs/vmc66_terminal_anchor_followup_20261028_v1` 固定全1974旧终端SSE6761.694451274→4299.918495240（−36.4076782%）；旧贡献.364396842603→.227989216354，按旧分母计算after为.231474479494；新30贡献.000719535134，全2004为.228708751488。旧观测/动作/reward/mask数组精确保持，网络/前向RNG不变，health重现；独立保存算术和实际follow66.png已审。

|原固定focus replay index|SSE65→66|变化|
|---|---|---|
|2050526|78.408266→753.755603|退化|
|2299142|178.948025→2.062169|改善|
|2046571|62.917002→443.491780|退化|
|2423133|38.257822→14.767521|改善|
|2423122|2250.259572→1.451758|改善|

保存values SHA256 `bf53eab14eb73b09f08a2e8494d7b39278686b200ee79b9d3e0f8907671f4f80`。图中原点附近文字重叠，完整精确值在REVIEW；不隐去退化或据子集宣称全体收敛。

`B/runs/vmc66_ranked65_terminal_followup_20261028_v1` 完整及独立float64向量复核通过，全部1974原65排名保持，1435改善/539退化。原65 top2索引2423122/2464220分别2250.259572→1.451758及849.536296→12.126328；固定top2不替代全体或原五focus。无新增前向/物理/优化/replay写入，无在线梯度因果或新停止门。

## 67准确续训与待办

`B/runtime/prepare_parameter67_20261028_v1/DECISION67.json` 绑定29项完整证据，三路check-only exit0，全learner/全部66 replay/下一65536采样精确。18:06:18 UTC启动 `B/runs/parameter_capacity_pool30_cycle67_20261026_v1`：I3260038/A3260039 start40649438，V3260040/archive3260041 start40649439；startup3260042/start40649440。每路30sampler、GPU1/2/3及CPU13–25/26–38/39–51保持。刚启动时首PROGRESS尚未写出，重新核验原PID并确认后续步数增长，没有因短暂缺文件重启。

实际67启动审查已通过：I/A/V新增1000/1000/2000，全部旧2759148/2759750/2760750行、history、optimizer参数、30sampler/MJB保持、新reward复算0。实际startup/REVIEW SHA256 `2c9a7924018300ede636446cafdc390762ecf55092cbab288b3a583eeabc10b7`，非仅check-only。18:11:55实际快照steps2762737/2763457/2764475，原learner/archive/loss/window/五guard身份保持，无完整/失败；GPU80/96/95/93%。

完整67 loss `B/runs/parameter67_loss_20261028_v1` 已部署，waiter3264983/start40650657/CPU54/7200秒，PLAN SHA256 `553234b74b056823d2cbb6751028de1f2b44768755f6bc0617fdf8a8b9a8ec32`。完整49–66历史保持追加67，paired66→67；实际完整67结果待。

原65–67窗口 `B/runs/parameter_capacity65_67_reward_stability_20261028_v1` 的PLAN SHA256 `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0` 不变，原waiter3549846/start39897958继续，约20:01 UTC期限。输出REVIEW而非FINISHED，完整67前不提前pass。原62–64/59–61失败和历史I56–58/V53–55通过均保留。后续需完整67评审及原窗口，不移动端点；观察期限不构成重启科学任务依据。

## GPU与保存

`B/runtime/parameter66_verified_wait_1742_20261028_v1` 完成17:41:28–18:01:28的41次实际观测，步数2746765/2747479/2748632→2759148/2759750/2760750不降，原身份或自然complete标记均核验。1200秒observer正常结束，未重启科学任务，独立REVIEW通过；loss waiter自然结束也有完整标记核验。

同期235条guard采样min76/67/67/69%，mean78.91063830/85.61276596/86.38297872/85.71489362%，低于50全0/maxgap5.287933秒。含合成保载，非纯科学吞吐/每瞬时保证。v5主管3256866/start37410686与四worker3256867–3256870/start37410690/37410690/37410691/37410693保持；v5 STOP无、v4 STOP保留，科学完成也继续guard。当前后台进程非跨重启服务。

开工实际fetch/read main482ff64f/baselinef6e8f8c，收尾main d19365115e57f3a14941b5fba338ed657d94ea78。另一主机非RL速度换算六项完整/office失败、full_velocity在途的日志和报告已读，fast-forward完整保留，无本机冻结RL协议变化、无子agent。

18:01:32–18:11:53切换阶段另122条guard采样min74/67/68/67%，mean78.86065574/79.13934426/79.52459016/79.36065574%，低于50全0/maxgap5.288471秒；保存于 `B/runtime/prepare_parameter67_20261028_v1/GUARD_TRANSITION_*`。该段包括归档/诊断/恢复与新67，含合成保载，不冒充纯训练或每瞬时保证。

本轮共享SSD小证据包 `B/repository/RL_PARAMETER66_COMPLETE_20261028_181156/SMALL_EVIDENCE.tar.gz`，175成员/1891438字节/SHA256 `0e7cef4d7fd1cbb80bedee948937d734c03516e9162aa30f647a76a12b609f99`。逐成员大小/hash/AST与归档回读通过；[收据](RL_PARAMETER66_COMPLETE_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER66_COMPLETE_20261028/MANIFEST.json)。大checkpoint/replay/raw仍原共享SSD，HDD只重写已有LATEST入口，非HDD/arm1全备份。
