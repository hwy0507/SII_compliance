# 完整第85轮已审；有限第86轮实际续训

2026-10-30T12:01:50.689413+00:00，Goal active。第85轮全部三路完整结果已保存与审查；reward稳定和loss健康尚未共同成立。明确登记原协议一个有限86周期，PID `{'impedance': 3407146, 'admittance': 3407147, 'vmc': 3407150}`；三路完整state精确恢复、实际startup及120.007秒观察通过，保存steps `{'impedance': 3528493, 'admittance': 3530701, 'vmc': 3531577}`。冻结82及原85—87统计继续；不自动87，无Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`，大checkpoint/replay/raw/runtime在共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。本轮实际ls-remote、fetch/read main `74b2d54efbfd2bdc6ac39ea6fcc6048766ec26e1`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留其他主机非RL成果，无子agent。按仓库sii-research-sync工作，发布以SSD本包PUBLICATION.json中的成功push及之后实际远端核验为准。

|第85轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|3523948|-0.590929712|18/18|2.205659→2.129187|28.610832|21.166167→21.173226|
|admittance|3526250|-8.629324177|15/14|1.203930→1.545221|24.233294|-8.749444→-8.626322|
|vmc|3527250|-4.586652405|17/16|1.052628→1.348879|40.826614|-11.977408→-11.869401|

全部三路30个完整55秒回合、各41250新增、无abort；旧replay所有字段精确保持，全部新reward由原journal重建误差0，optimizer和network有限。完整loss独立保存算术、health、185保存标签/rollout、两终端保存复核、原固定2514/all5跟踪，以及五张实际图均已检查。奖励重建不是独立重跑物理子步。

实际loss六栏图：阻抗critic均值略降但反复尖峰，actor先上拱后回到接近起点；导纳/VMC的末段出现尖峰簇且末1000均值上升，actor上漂。这和仅首5000观察的范围不同，不能用前缀替代完整周期。entropy接近原I−5/A,V−7，alpha保持有限正值、nextQ尺度没有数值崩溃；有限值并非loss健康证明，没有追加事后尖峰阈值。

全部标签变化：

- admittance active_short_train_0600：[{"cycle": 84, "task": false, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.2243485087358635}, {"cycle": 85, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.21164936091845318}]。
- vmc active_short_train_0000：[{"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.1401979011506065}, {"cycle": 85, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.21997940040468758}]。
- vmc active_short_train_0600：[{"cycle": 84, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.21939809384274578}, {"cycle": 85, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.17197366715728415}]。

因此导纳Task14→15仍Strict14；VMC两个条件一退一进使总Strict仍16。行为不等同于相同总成功率，穿透门保持0.2mm。

|方法|采样Q超当前固定alpha全局上界|终端mask内MAE|终端mask外MAE|
|---|---:|---:|---:|
|impedance|0.00000000%|0.467945|3.545313|
|admittance|0.09277344%|0.315943|2.458247|
|vmc|0.13183594%|0.303968|2.003067|

诊断使用精确85checkpoint，网络状态保持；上界仅诊断，mask外不参与对应critic训练，终端非零误差不是新增健康门。

- vmc：旧2514终端SSE 9046.060766→3556.824879，新增30贡献0.267283990；新30贡献前三为 active_short_train_0000 95.578%、active_short_train_0200 1.325%、active_short_train_0300 1.106%。
- admittance：旧2514终端SSE 1283.626104→3932.822648，新增30贡献0.174403454；新30贡献前三为 active_short_train_0600 87.866%、active_long_train_0900 9.573%、active_short_train_0900 0.615%。

同一2514固定84输入/actions/rewards/masks的前瞻85跟踪按原PLAN SHA `7703cce3f9428f187fdd796df22e540eb945411b55108cf7e8d3aaee70306494` 完成。全部5028保存行和25140 Q配对经标量重算，原数组与报告一致；没有新网络forward。所有5critic结果如下，保留改善和退化：

|方法|critic索引|84 SSE|85 SSE|mask内异号数84→85|
|---|---:|---:|---:|---|
|vmc|0|2318.696533|461.400601|1→0|
|vmc|1|3152.315248|1854.871716|2→1|
|vmc|2|55.165155|306.261351|0→0|
|vmc|3|2182.845493|475.614724|0→0|
|vmc|4|1337.038337|458.676487|1→0|
|admittance|0|201.933897|788.800261|0→0|
|admittance|1|193.083580|925.438875|0→0|
|admittance|2|251.938208|843.942836|0→0|
|admittance|3|485.369323|1305.991028|0→0|
|admittance|4|151.301096|68.649647|0→0|

VMC旧84 short0600（index3478427）SSE2624.382648→328.452727，有效Q从[5.229,.228,−2.555]改善至约[−27.687,−10.844,−24.135]；相邻正reward long0400（index3478443）765.100376→733.931484，critic1仍给负值−3.207513。旧84 short0100另由0.804835恶化至122.004646；全部30新增84群体保留，四栏新图实际查看。局部误差竞争仍有残留，但85不改输入也能改善旧失败行，不能由84负梯度余弦推导“现有输入必然不可拟合”。这不是历史Adam或样本抽取因果证明。

新增完整85全部90终端的更新机会审查：绑定实际trainer的append→steps++→一次update与连续41250日志，每个终端按真实写入step和完整末step计算。VMC新Strict失败short0000在index3522137写入后仍有5113次更新机会；导纳short0600在index3520919后仍有5331次。实际minibatch包含次数未知，同一batch可重复抽样；不能解释成只剩最后一次更新，也不能断言已充分抽到。新30终端贡献分别95.5782%/87.8657%集中在这两个条件，旧样本退化同时存在。

实际有限86的科学决定（原文保留）：

完整85三路各30个完整55秒条件/41250新增/noabort；旧replay所有字段精确保留，新reward重建误差0，optimizer/network有限。完整loss独立保存算术、health、185保存标签、两终端保存值/原固定2514输入跟踪和五张实际图已审。三路86全learner/optimizer/replay/RNG及next65536精确恢复通过。I/A/V reward−0.590929712/−8.629324177/−4.586652405、Task/Strict18/18、15/14、17/16。导纳short0600由Taskfalse变true，但穿透0.224349→0.211649mm仍超过原0.2mm门；VMC short0600 Strict恢复(0.219398→0.171974mm)，short0000新增Strict失败(0.140198→0.219979mm)。改善和退化均保留，不把总成功率不变当各条件稳定。
完整85critic首末1000 I2.205659→2.129187、A1.203930→1.545221、V1.052628→1.348879；最大28.610832/24.233294/40.826614。A/V末段尖峰簇和均值上升保留，不称健康。actor I中间上拱后回到21.173226，A/V上漂；entropy接近原I−5/A,V−7，alpha有限正值，无数值崩溃证据。固定alpha Q上界超限比例I0/A0.0009277344/V0.0013183594仅诊断，不增加事后门槛。
固定同一2514输入/actions/rewards/masks、全部5critics的前瞻84→85跟踪已完整审查：VMC总SSE9046.060766→3556.824879，c0/1/3/4改善，c2由55.165155恶化至306.261351；导纳总1283.626104→3932.822648，c0/1/2/3均恶化，仅c4由151.301096改善至68.649647。VMC旧84 short0600 SSE2624.382648→328.452727、三个有效Q改善至约−27.687/−10.844/−24.135，但相邻正reward long0400 SSE765.100376→733.931484，c1仍预测负数−3.2075；short0100另由0.804835恶化至122.004646。原历史focus的改善/退化和全部30新84群体保留，不混淆旧2454与当前2514锚点，不作历史Adam因果或无法拟合断言。
完整85新增30终端贡献中，VMC新Strict失败short0000占95.5782%，导纳short0600占87.8657%；新增样本拟合与旧样本回归漂移都在发生，当前还没有证明训练已进入稳定状态。上一轮90回合/123750动作的源绑定因果历史审查说明累计穿透信息可在动作前取得，但没有证明全历史replay都能重建或历史特征修订必然改善。VMC已在不改输入的85里改善旧short0600拟合，进一步说明仅凭84局部梯度竞争不能宣称现有输入必然不可拟合。
上述证据支持再运行且只运行一个有限86周期：观测A旧样本退化是否持续、VMC局部改善是否保持以及新Strict失败样本的拟合变化，同时推进原85—87窗口所需的第二轮。此前VMC旧样本误差跨轮曾回落，目前没有非有限状态/恢复错误/新安全中止，尚无充分的全历史重建与对照证据支持立即改学习协议。此决定不是健康或收敛判定，也不是合成GPU占用的科学理由；不自动87。86仍每方法最多41250真实transition、30条件×最多55秒，4m append-only/23和47历史marker/terminal128/batch65536/UTD1/LR/reward/masks/physics/filter/gates全部保持。完整86后必须重新审查固定旧输入和全部标签/损失，再决定下一有限阶段或登记科学修订。
原82—84 I近零不可判、A/V失败5%，原76—78/79—81、partial75与原74—76不可判、79安全中止、Direct33数值阶段与冻结0/0及中断28缺最终不变证明全部保持；指定ESN仍缺且不替换。原85—87 PLAN SHA6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e/seed2026102858/5000bootstrap/nearzero1/5%/anchor55与原截止不变；统计等待不是后续训练授权。冻结82原完整90/最终全state不变证明/保存审计/比较继续。GPU原v7补载在科学结束后继续，Goal active。

86科学trainer与85逐字相同、metadata扩展可逆；19协议+8边界负例、缺完整85/决定/LAUNCH/固定输入85真实拒绝保留。完整learner/optimizer/replay/RNG及next65536精确恢复；实际startup新增检查步数 `{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}`，每路30sampler/MJB/旧replay/历史markers/新动作clock和reward0误差通过。86仅每方法30条件×最多55秒、最多41250新增，4m append-only、23/47历史容量标记、terminal128、batch65536、UTD1、LR/reward/masks/物理/滤波/gates不变。无自动87。

标签86/完整loss86/全回放及health86/两终端86后续已部署；终端锚点为完整85全部2544→预期86共2574，旧锚点和保存值标量复核通过。新增 `runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1` 在86启动后且结果未知时前瞻登记同一2514/all5，比较84/85/86并保留全部30新84 cohort，PID3516235/start573524462，PLAN SHA `2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041`。复用原三checkpoint标量算法，仅推进准确轮次/计数并补cohort映射；缺完整86实际入口拒绝通过。等待原86全review和两终端成功及原进程退出，截止为原86monitor+14400秒；0新forward/physics/update，不新增健康门、不自动87。下一轮决定必须检查这项结果。

原85完成观察器自然成功，57样本/1680.389秒、27身份核验。新86连续观察7样本/120.007秒、28身份保持live或原成功终止，steps单调且保存观测逐行回读。启动检查后所有后台任务继续，观察结束不重启科学。

原85—87窗口与标量bootstrap等待器继续：PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`、seed2026102858、5000bootstrap、nearzero1、5%、anchor55及原4小时截止不变，当前只有完整85，86在途/87未启动。原82—84 I近零不可判、A/V失败5%，原76—78/79—81、partial75/原74—76不可判和79安全中止全部保持。两个相邻均值接近不是完整三轮窗口，也不是健康收敛。

完整85checkpoint `runs/parameter_partial75_recovery_cycle85_archive_20261029_v1/<method>/cycle_00085.pt`：

- impedance：`8b7ae0f860cefb5ac679c6c73c0294c4435031bd3ebd3a854390fa4264aef136`。
- admittance：`a019232059b9b6fb56e39cf07dd1238c7b6d7d3bf82b1826335cc84da09bc183`。
- vmc：`7a9f3640dd5fbcb4cdb4777dd04420353b5a4a2287c4b9a0636f34597dc669d7`。

冻结82进度(完成条件,在途条件,动作) `{'impedance': (24, 'active_long_train_0337', 900), 'admittance': (22, 'active_long_train_0200', 1000), 'vmc': (23, 'active_long_train_0300', 100)}`。原三evaluator/rootreview/55→82比较/独立全保存raw审计继续，仍需完整90、最终全learner/replay内存不变证明、实际图和完整比较。单动作seed2026102638/开发训练条件，不证明泛化或最终ESN排名。Direct33数值阶段接受但冻结30 Task/Strict0/0；原中断28最终内存不变证明缺失仍披露，指定ESN仍缺且不替换。

GPU 346采样，最低[75, 66, 66, 64]%、低于50次数[0, 0, 0, 0]，末值[80, 92, 94, 94]%。原v7 supervisor及四worker保持，即使所有科学任务结束也继续合成补载；合成负载不计科学吞吐，采样间瞬时不能保证，历史低谷保留，不是重启自启服务。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY85_COMPLETE86_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，388成员/4289127字节、SHA256 `b1e98771482817c7bd3652d659bee436c3eafae108c6670d18616374b431bfd9`；逐tar成员原字节/Python AST核验，Git index/commit blob另核。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；HDD LATEST原位保持254字节。运行日志是归档时快照。

后续先核86/冻结82/85—87/固定2514/guard原PID与start及FAILURE/FINISHED，避免重复派发。完整86后审全部结果、实际图、固定2514三checkpoint变化，再作87或科学修订的具体决定。原完整85全部失败、近零限制和未完成范围保留，Goal active。
