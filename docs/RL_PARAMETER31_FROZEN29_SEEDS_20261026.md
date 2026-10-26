# Direct20、参数31接续与参数29冻结四种子诊断完成（2026-10-26）

Goal active，健康收敛尚未证明。本轮新增有限冻结诊断，回答固定参数策略在short0600是否也出现Task/Strict波动；它不替代全30最终冻结验证。正式Direct20和参数31继续，完整参数30已审查，原物理/MJB/SPT/gates/filter/执行器、正式全部network/optimizer/replay/RNG/history不变；无子agent、不推广辅助权重。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。
实验B/runs/parameter29_seeded_short0600_20261026_v1；冻结源码B/runtime/parameter29_seeded_short0600_20261026_v1。依据上一轮全部371250保存transition的归因，选择反复跨Strict标签的active_short_train_0600；这是结果可见后选条件的探索性问题，不能冒充预先选定的泛化评测。

## 冻结29最终结果：12回合完整结束

2026-10-26 23:53 UTC根REVIEW完成。I3280414/A3280415/V3280416和根3341627均退出，勿重启。所有12×55秒、16500动作、13200000物理子步，未abort；四seed未筛除/追加。三完整learner/optimizer/RNG、容量replay digest均初末精确一致，父checkpoint/冻结源码hash保持，0优化/正式replay写入。逐回合原生连续随机动作重放误差全0，物理/filter/torque核验、根hash汇总、另一次保存算术复核通过，图已查看。

|方法|Task / Strict（各4）|机器违规回合|reward范围|穿透峰值范围mm|
|---|---|---|---|---|
|阻抗|4 / 2|2|−34.862860至19.410963|.185763至.231028|
|导纳|2 / 2|2|−34.841332至16.658804|.184704至.215043|
|VMC|4 / 0|4|−34.816033至−34.616474|.202121至.223348|

阻抗与导纳在固定29 checkpoint下出现Task/Strict组合变化，证明学习更新不是这些观测切换的必要条件；不能将其归为历史在线波动的全部原因或估计因果占比。VMC四seed均Strict失败不证明其通过概率为0。全部无人接触，舒适指标NA；保留2/2/4机器违规，审计通过不等于安全通过。这是结果可见后选short0600的探索性诊断，非全30最终验证、独立训练seed、held-out或最终ESN/SPT比较，不扩预算。

三完整父与state digest、每条原证据hash见B/runs/parameter29_seeded_short0600_20261026_v1/REVIEW.json及各方法FINISHED；小证据completed_frozen29目录保存全部12条审查。先前入口/中途信息是历史执行记录，最终结果以上述全矩阵为准。

## 最新覆盖：完整参数30与正式31

本节覆盖下方参数30仍运行的启动快照。完整30三路全部30×55秒无abort；旧replay/history/2m marker保持、新41250 reward重建0误差、网络/优化器有限，REVIEW/health/FINISHED与图通过。旧30 learner2344423/2344425/2344430、归档2344573/review2344575，以及31准备2801577/CPU调度2801579已完成勿重跑。

|方法|steps / updates|Task / Strict|reward|末1000 q_loss|terminal MAE / inbag MAE|
|---|---|---|---|---|---|
|阻抗|1275750 / 1270751|18 / 17|−2.345184844|2.244239740|.847475710 / .340396370|
|导纳|1274750 / 1269751|13 / 13|−10.241592988|1.297072166|.638529317 / .256560712|
|VMC|1275750 / 1270751|17 / 16|−4.565540571|.808987631|.691559073 / .374958364|

I末loss升高、A/V回落，A/V必要soft上界超出比例.001220703/.001611328；没有宣称整体健康稳定。准确30父在B/runs/parameter_capacity_pool30_cycle30_archive_20261026_v1/{method}/cycle_00030.pt，SHA256分别：

- I 11f388a854f16f31fced2a1a07b92e851213898b38a17866fb0cf93c9949a4eb
- A 3d62e868c4a50c4b5bf28db800c3a081ce4514f594c8c1b2aa3098177ff8c1ac
- V 9fd484f264e8bef801eb8f80c54cb012bb04246ca9cf477fcae6b956cc4a2b67

三check-only全state/replay/下一65536/RNG精确通过，PRELAUNCH_SCIENTIFIC_REVIEW记录上述结果与继续一个有限原设置周期的依据。2026-10-26 23:35:24 UTC正式31 I3783467/A3783468/V3783469启动，B/runs/parameter_capacity_pool30_cycle31_20261026_v1；原GPU1/2/3、CPU13–51、30pool/batch65536/UTD1/terminal128/projection/pair/LR、2m历史入口23及全部state保持。startup3783471/归档3783472/完整review3783473，实际startup已通过，不自动32。

新32准备等待3878413/原31 review CPU调度3878414已登记，限定替换、真实根/pool30/历史23、适配AST通过，仅完整31后prepare+check-only，7200秒有界，无自动正式32；原固定30–32稳定性等待2830862继续。

冻结29完整结果见上方最终段，原12回合预算已全部结束；不得追加种子或提前将单条件结论推广为全30验证。

## 预算与原始策略

固定准确完整29的I/A/V父checkpoint，动作种子2026102633/34/35/36，每方法4×55秒，共12回合/最多16500动作/13200000物理子步。所有种子在启动前登记；失败/提前abort保留，不追加种子、延长或挑选最好结果。物理fixture和物理seed不变，动作seed经SHA256(seed:case)映射；仍调用原CHEQ随机act和原context/mixing递推，step固定为父训练步数，不改网络、温度或混合律。

复用完整29精确checkpoint：I389ec24c…、A353ff964…、V744e1f6f…，完整SHA见REGISTRATION和RL_PARAMETER30_STABILITY_20261026.md。恢复必须capacity replay和pair learner，2m历史入口23保留；全部replay字段/RNG和完整learner state先digest对照父。没有仅加载actor或重置optimizer。

新ExternalActions仅将外部随机流临时安装到Python/NumPy/local RNG/Torch CPU及CUDA，调用原reset/act后收回外部随机状态，并在finally恢复训练RNG。混合器和已知episode clock按原递推演进，权重/optimizer和checkpoint持久RNG不动。每个完整回合后单独检查full learner digest不变；全部4回合后再检查完整replay digest和原checkpoint/source hash不变。上述最终检查现已全部通过，见各方法FINISHED。

## 已通过的入口验证与实际运行

原check-only I3235252/A3236869/V3239268均完成、无FAILURE；完整learner/replay恢复精确，原生一次连续采样和外部逐步切换流在同输入/同seed下3步obs/raw/mixed/context逐值精确，不同seed改变raw action，两种非法seed拒绝且state不变。0新物理/优化。实际评估启动又执行原入口gate并通过STARTUP_REVIEW。

完整learner digest I0a39561fc98ac305060fd0f4c1f72a37c10b829c293f7c94abd77e6e843092a9、A74219ec7ea61c41c8ae6279e35dde574bf979d7dbcd4e78d487dabde2bf41d1a、V734679dbebf2a60075655c0a1a98b120f71fb9caec5440ebc92a29d4d722db79。完整replay digest均记录CHECK_ONLY_REVIEW/STARTUP_REVIEW，2m marker和父精确。

实际原evaluator I3280414/A3280415/V3280416，CPU52/53/54、对应GPU1/2/3、单线程/nice10。各方法串行4个种子，物理子进程使用相同CPU与冻结B/env/bin/python；GPU只推理/动作重放，不做优化。现各4条均完整完成并退出，最终RESULTS/FINISHED通过，不重启。

每条物理回合记录原audit_substeps、filter和torque日志，结束后复用已验证审查工具独立重算物理指标、重放filter/torque；另在同checkpoint用原生连续随机流重放所有1375保存观测的参数动作，校验时钟和误差≤1e-7，独立于评估时逐动作安装外部RNG。原SPT逐interval重建reward和completion bonus，不改门槛。全部12回合现已执行上述审查并通过；物理失败标签仍如实保留。

根review原3341627按7200秒有界等待完成，全3 FINISHED后核所有原证据hash、12格覆盖/预算/失败、完整state不变、Task/Strict/回报和穿透范围，已生成图与REVIEW；不追加训练/物理/神经前向。四动作seed精度低，同结果不证明失败率0；观察到变化也不能估计历史在线波动中随机性和策略学习各占多少，更不是独立训练seed/held-out/ESN最终比较。

## Direct19完成、第20轮接续及第17–19轮稳定性

完整19为813282 steps / 6466264 critic，全部30×55秒无abort，Task/Strict0/30；reward−31.581989682，旧772032 raw/derived/history保持，新增41250精确、pending0。600终端×10critic MAE .045845315/max .799560547，32步TD .042494051、单步TD .057471283，Q均−20.539611816，alpha .000541544519。完整REVIEW/DIAGNOSIS/FINISHED与图已审查，network/optimizer/RNG不变。

准确完整19父：B/runs/serl_multistep_batch65536_cycle19_archive_20261026_v1/direct/cycle_00019.pt，SHA256 6505b308e18165b0a2040ab5114b3b1331f42b043f04782ade66c49f81c6e5eb。旧learner1326215、归档1326258/review1326260及20准备2086366/调度2086367均结束，勿重跑。

第20轮check-only完整恢复通过，PRELAUNCH_SCIENTIFIC_REVIEW记录19较18回报/TD恢复、继续一个有限原设置周期的依据。正式20 learner46632，startup46742、归档46745/review46750；GPU0、CPU0/1–12、官方10critic/random2 min bootstrap/actor全10均值/noentropy/8:1/batch65536/32步/gather保持，0辅助权重推广。真实首1000新步达到814282/6474264；全部旧813282 raw/derived/history、优化器设置、30MJB/30sampler及新reward0误差，143新mature+857pending通过。完整20预期854532/6796264、630终端，完整结果尚待。

新增只读17–19稳定性原150716已完成：B/runs/serl_cycles17_19_reward_stability_20261026_v1。16作上个已审计端点，17–19为新窗口；完整165000优化记录/120回合/协议和输入hash核验，0新物理/优化/神经前向。沿用原5%与近零1、5000分类配对bootstrap；这是看过结果后登记的回顾性审计。相邻reward变化4.04964%/2.03931%、窗口首尾1.92775%，原描述性检查通过；绝对相邻差1.254768/.657463，range1.254768，无新增绝对阈值。末1000 critic loss .014546117→.013881322→.013401587，全部有限，无观察到发散。

16→19配对均值−.649860247，30条件均退步，条件构成敏感性95%区间[−.771891,−.514305]；相较先前稳定平台仍退步，低loss不代表任务学会。Task0单独报告，不把成功率或精确policy不变增加为收敛门槛。保存算术独立复核及图已查看；全项目仍待参数30–32/最终验证，原冻结16全30已完成不重跑。

新21准备等待87882、原20审查CPU调度87883，仅完整20 FINISHED/REVIEW后prepare+check-only，7200秒有界，不自动训练21。源码限定命名替换、真实B根、AST/当前review适配/660终端预期静态检查通过；实际21恢复未执行。正式21启动仍需读取完整20科学结果。

参数31三原learner及归档3783472/review3783473继续，32准备3878413/原31 CPU调度3878414、固定30–32稳定性等待2830862保持。冻结29退出前GPU1–3含辅助推理，不能称纯正式占用；旧纯19/30窗口57.3/67.9833/67.9/69.1333%仅代表当时，交接实际空闲保留。

## 同步

重新查询/fetch/read真实main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变。GitHub认证尚待已问不重复。三新源码AST和实际恢复/随机入口/完整12条物理矩阵/根review/Direct17–19保存日志审查通过。小证据docs/evidence/rl_parameter29_frozen_seeds_20261026保存登记、源hash、gate与实际启动；大轨迹/回放/checkpoint仍SSD，HDD小交接/收据，非全量HDD/arm1备份。指定ESN仍缺已问勿重复，Goal active。

三路首动作seed2026102633均完整完成并审查：各1375动作/110万子步，全部原生随机动作重放误差0、物理/filter/torque与完整learner state不变通过。I/A/V Task真/假/真，Strict均假；穿透.231028/.205819/.205658mm，均超过原.2mm，无abort但保留原物理有效性失败/机器违规标签。此为首seed历史结果；最终全部12条结果已在文首汇总。

参数31实际启动审查已通过：I/A新增1000至1276750/1275750、V新增2000至1277750；全部旧1275750/1274750/1275750行replay字段/history/优化器配置/2m marker/30MJB/30sampler/action/clock及新reward0误差通过。原startup3783471已完成，归档3783472/完整review3783473继续。

纯20/31新固定60样本observer258985已登记，待冻结29退出且两正式startup通过后采集，逐样本只允许四正式GPU PID；先查B/runs/batch20_parameter31_gpu_profile_20261026_v1/PROFILE.json，不重采或挑窗口。

冻结29退出后的纯正式20/31固定窗口已完成（原258985退出）：60样本、67.982567秒，四卡均值56.5833% / 69.3833% / 74.2333% / 74.7667%，逐样本GPU PID恰46632/3783467/3783468/3783469且learner身份存活；保存均值独立复核。它是此次运行窗口，不保证每瞬时≥50%，不隐藏阶段衔接空闲。正式最新实际进度与全部原句柄见小证据FINAL_LIVE_STATUS.json。

归档与发布：科学提交7467875ecdf5067ede467c70ea86d5bcff21405d本地完成，push因GitHub Username认证失败未发布。129成员完整小证据SSD B/repository/RL_PARAMETER31_FROZEN29_20261026_235542/FULL_SMALL_EVIDENCE.tar.gz，1608684字节，SHA256 0031eda33a9dce621a996188492b958f2ee1794cf108c3e4cc22ca2cd69adf1f，逐成员大小/hash通过。HDD sii_shutdown_backup_20261026_v1/RL_PARAMETER31_FROZEN29_STATUS_20261026_235542/HANDOFF.md及LATEST_RL_HANDOFF.md已更新核验；大产物仍SSD，非全量HDD/arm1备份。收据docs/evidence/rl_parameter29_frozen_seeds_20261026/ARCHIVE_RECEIPT.json。
