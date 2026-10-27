# 参数48完整审查、49实际续训及VMC尖峰跟踪

2026-10-27，Goal active。执行主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`；共享SSD根 B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，代码 B/repository/SII_compliance。实际查询并fetch/read远端main `29ca14dc7cf527b51de7e09452b5aae71841ff49`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留并行非RL记录。遵循仓库sii-research-sync，无子agent。

## 完整48结果与原46–48窗口

三路各30×55秒、41250新转换、无abort；完整旧replay/history保留，新reward重建0误差，网络/优化器有限，原设置不变。完整48 fullreview现已覆盖全部30终端与bonus，不再受早先跨界快照0终端范围限制。全health/独立保存算术/hash通过，完整health及固定窗口图已目视检查；审查通过指一致性，不等于loss健康收敛。

|方法|累计步数|Task/Strict（各30）|平均reward|首/末1000 Qloss均值|本轮最大Qloss|
|---|---:|---:|---:|---:|---:|
|impedance|2017430|18/17|-2.430897849|2.419197/2.375222|27.748669|
|admittance|2017250|13/13|-10.331551501|1.600403/1.301922|14.162022|
|vmc|2018250|17/16|-4.567467101|0.670887/0.666191|132.714996|

准确完整48 checkpoint位于 `B/runs/parameter_capacity_pool30_cycle48_archive_20261026_v1/<method>/cycle_00048.pt`，SHA分别I `e3a355182a20353236d8b5c4293d1489f9592d7a9afa56c12d1d892fb40037bb`、A `d36159371d2e10dca094cb6f8ca32f8ba3084328f0471b1da2e4aa5de687960b`、V `0dc2d16137782b7122218710413d6f2bc65bcb4e067a9704e91e7c4f167f7e1e`。

原46–48窗口完成：I均值−2.325234/−2.379693/−2.430898，首尾4.5442%，原5%检查通过；A−15.465871/−12.047563/−10.331552，首尾33.1977%，改善但未稳定；V−4.626438/−2.834140/−4.567467，首尾1.2746%但相邻变化未通过。保存复核核对原算术/hash/图，不重跑5000bootstrap，原seed2026102747/nearzero1不变。46–47为2m、48为4m，不能归因为单一容量效果。

47→48保存配对分解：I成功不变，reward均值−.051205；A均值+1.716011，成功变化贡献+1.806508，long0300丢成功、short0000恢复Strict、short0600恢复Task/Strict。V均值−1.733328，short0600穿透.178476→.202503mm跨原.2mm门而丢Strict（Task保持），贡献−1.750700。原MJB/gate核验，不据此解释loss因果。

## VMC48尖峰与前瞻49早期诊断

完整48最大loss132.714996位于step2010577；前/后100均值1.538679/1.185930，前/后1000为.838851/.859982；末1000均值.666191、最大7.281683。整轮loss>10为16次、>50为2次、>100为1次，全部有限。记录了同step转换和附近终端，但这些不是实际replay batch日志，不能证明尖峰原因；未修改optimizer、参数或正式权重。

在49尚少于5000新步且0完整条件时已固定前5000更新，原观察1826532已完成：准确steps2018251..2023250，平均loss.614562540、最大6.557824135，>10/>50/>100均0；五个1000块均值.628992/.620974/.577792/.672089/.572964，entropy均值−6.986003，alpha范围.000533107–.000600949。独立保存算术/hash复核通过，原前缀SHA `62f6d0f759e7f156c99e15d9ad4bb9576f87d1493c7d97f99f788eb4c8e04d64`。仅早期5000诊断，不扩展前缀、不冒充整轮健康或收敛。

## 正式49与后续准备

12:39:37 UTC正式49 I1717020/A1717023/V1717024，GPU1/2/3与原CPU13–51组、各30sampler。准确完整48全state/next65536 check-only、原完整48/health/窗口审查及PRELAUNCH通过才启动。实际startup新增1000/1000/2000通过，全部2017430/2017250/2018250旧行、历史、优化器配置保持，新reward0误差、30MJB及动作/clock审查通过。4m容量，历史entry23和entry47不可重标；terminal128、I目标min/A-V mean、actor min、batch65536、UTD1与LR均不变。startup1717078已结束，原archive1717080/fullreview1717082继续。实际进度见LIVE_STATUS。

第50轮准备 `B/runs/parameter50_preparation_20261027_v1`，waiter1864402；冻结10源码，两个4m helper/driver与health逐字节不变，仅当前父/目标49→50，历史followup父47保持。SOURCE_DIFF已读，AST/标签通过。7200秒等待49全review/health和父退出，1000秒外层/900秒内层check-only，无自动训练。尚未声称实际完整49恢复通过。

新固定49–51窗口 `B/runs/parameter_capacity49_51_reward_stability_20261027_v1`，waiter2064574；49零完整条件、50/51未启动时登记，原公式/5%/nearzero1/5000，前瞻seed2026102748。要求三轮均4m、原entry23/47和所有依赖不变；显式移除46–48扩容边界分支，保留原统计体并核对字节等价（仅窗口字段标签改变）。有限10800秒，无自动训练/停止。

48→49进程退出至spawn界：I287.832–289.833秒、A329.912–331.914、V337.923–339.925；是进程界，不是GPU精确idle。原observer1132161仍等Direct29→30，PARAMETER_PARTIAL_RECEIPT只覆盖参数，未称observer全部完成。12:47:54四卡瞬时72/82/82/81%；先前纯29/48固定窗口均值59.2167/70.7/57.5833/57.5833%仍仅适用原窗口，不保证每瞬时。

Direct29原learner241542持续推进，原完整review241549、固定27–29统计336744和保存复核1132169/1219181待完整结果；第30轮准备464829仅check-only，冻结29准备3802347仅check-only。原冻结41及32→41比较已完整完成勿重跑。完整29后先审查reward稳定性和loss，再决定是否继续30或进入冻结验证；不因Task0另加收敛门槛，也不把低loss当任务成功。

本轮小证据 `docs/evidence/RL_PARAMETER49_PROGRESS_20261027` 共98文件，逐hash/大小与Python AST核验。原raw/checkpoint/runtime及VMC前5000原件在共享SSD；HDD满仅更新已有LATEST。不是HDD/arm1全量备份。整体尚未达到reward稳定且loss无异常，Goal active。
