# 完整第86轮已审；有限第87轮实际续训

2026-10-30T13:15:46.365522+00:00，Goal active。完整86三路全replay/reward/health/loss/186保存标签/两终端/固定2514三checkpoint和5张实际图审查通过；reward稳定与loss健康尚未共同成立。明确登记一个有限87周期已实际运行，PID `{'impedance': 2291679, 'admittance': 2291680, 'vmc': 2291681}`，start573936642；保存steps `{'impedance': 3571619, 'admittance': 3573937, 'vmc': 3575105}`。冻结82及原85—87统计继续，不自动88，无Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`；大checkpoint/replay/raw/runtime在共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。实际ls-remote、fetch/read main `f3a48112e015997eb486d9f0c9ae2026d0219ad0` 和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留其他主机非RL成果，无子agent。按仓库sii-research-sync工作，发布以SSD本包PUBLICATION.json的成功push与之后实际远端核验为准。

|第86轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|3565198|-2.408940764|18/17|2.025225→1.851771|36.815956|21.173302→21.008418|
|admittance|3567500|-6.690039706|15/15|1.382426→1.197119|18.374575|-8.632879→-8.652332|
|vmc|3568500|-2.831541823|17/17|1.335809→1.026898|26.790501|-11.874822→-12.097775|

全部各30个完整55秒回合、41250新增、无abort，旧replay所有字段精确保持、新reward重建误差0，network/optimizer有限。loss独立保存算术和完整health均通过，5张实际图已查看。A/V完整后段尖峰减少且均值下降，I仍多次有限尖峰；actor I先轻微上拱再下降、A小幅波动、V下降后趋平。entropy接近原I−5/A,V−7，alpha有限正值，nextQ尺度未崩溃。单轮改善不是健康稳定证明，不追加事后尖峰阈值。

完整85→86条件变化：阻抗short0600 Task保持真、Strict真→假，外穿透0.185890→0.221793mm。导纳short0600 Strict恢复0.211649→0.188750mm；long0200 Task恢复，short0900 Task退化，总Task仍15。VMC short0000 Strict恢复0.219979→0.179105mm。186保存rollout独立标签审计通过，条件交换和失败均保留。原0.2mm门不改。

Q超过当前固定alpha全局上界采样比例I0/A0.000390625/V0.001074219，仅诊断；终端mask内MAE分别0.347034/0.214563/0.172202，mask外3.433353/2.377991/1.910886，mask外不参与对应critic拟合。所有诊断checkpoint哈希与完整86绑定，网络/RNG保持。

固定同一2514输入/actions/rewards/masks与全部5critic的原前瞻84/85/86审查按PLAN SHA `2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041` 完成，全部5028保存行/三checkpoint的独立标量复核通过，六栏新图实际查看。VMC总SSE9046.060766→3556.824879→1158.553497；导纳1283.626104→3932.822648→2110.926268。

|方法|critic|84 SSE|85 SSE|86 SSE|
|---|---:|---:|---:|---:|
|vmc|0|2318.696533|461.400601|137.918873|
|vmc|1|3152.315248|1854.871716|362.804540|
|vmc|2|55.165155|306.261351|99.795864|
|vmc|3|2182.845493|475.614724|317.052869|
|vmc|4|1337.038337|458.676487|240.981350|
|admittance|0|201.933897|788.800261|355.428301|
|admittance|1|193.083580|925.438875|593.315490|
|admittance|2|251.938208|843.942836|269.152194|
|admittance|3|485.369323|1305.991028|195.430409|
|admittance|4|151.301096|68.649647|697.599873|

VMC从85到86全部5critic改善，但c2仍高于84；导纳c0—3改善，c4由68.649647恶化至697.599873，总误差仍高于84。VMC旧84short0600 index3478427 SSE2624.382648→328.452727→64.701597；相邻正reward long0400 index3478443 765.100376→733.931484→0.860001，critic1从−3.207513改为23.042877；旧short0100 0.804835→122.004646→4.669285。全部30新增84 cohort均保留。当前原输入可以继续改善这些样本，不能由84局部负梯度余弦断言必然无法拟合，也不据此重建历史Adam因果。

完整2544旧终端群体V SSE9991.012435→1172.629322、A8131.029796→2606.867028；旧focus仍有恶化：V index2423133 5.912702→56.484323、2423122 7.332240→21.173519；A index2752093 41.328919→56.984262。两终端保存值逐标量复核、原观测/actions/rewards/masks和网络/RNG不变证明通过。

新增 `PRIOR85_COHORT86_REVIEW.json` 将全部30新增85终端按原episode global index匹配到同一2544群体：V总6434.187555→14.075826，A4198.207147→495.940761；另独立与full2544减fixed2514总量一致。V上轮short0000失败行6149.693743→4.540179，A short0600失败行3688.808975→8.350587。所有60行和改善/退化保留，不只选择失败例，没有新forward或physics。

本轮新30终端贡献V0.001348028，最大long0500占29.3085%；A0.015094606，short0900任务失败占59.0944%，long0500占22.0499%。全部90终端更新机会已按真实append→steps++→update和连续41250日志核对，实际minibatch包含次数未知，不能把机会数当采样次数或充分拟合证明。上一交接10,577,448旧replay历史重建继续有效，只是数据可行性证据，没有历史特征模型修订。

本次有限87科学决定原文：

完整86三路各30个完整55秒条件/41250新增/noabort，全replay旧字段精确保留、全部新reward重建误差0、optimizer/network有限；完整loss/保存算术/health/186保存标签/两终端/固定2514三checkpoint及5张实际图均审查通过。三路87全learner/optimizer/replay/RNG/next65536精确恢复通过。I/A/V reward−2.408940764/−6.690039706/−2.831541823，Task/Strict18/17、15/15、17/17。阻抗short0600 Strict真→假（外穿透0.185890→0.221793mm）；导纳short0600 Strict恢复（0.211649→0.188750mm），long0200 Task恢复但short0900 Task退化，总Task仍15；VMC short0000 Strict恢复（0.219979→0.179105mm）。失败、条件交换和原0.2mm门均保留。
完整86critic首→末1000均值I2.025225→1.851771、A1.382426→1.197119、V1.335809→1.026898；最大36.815956/18.374575/26.790501，均有限。A/V后段尖峰减少，I仍反复尖峰；actor I21.173302→21.008418、A−8.632879→−8.652332、V−11.874822→−12.097775。entropy接近原I−5/A,V−7，alpha有限正值、Q尺度未崩溃。采样Q超当前固定alpha全局上界比例I0/A0.000390625/V0.001074219仅诊断，不能用新增阈值宣称健康。
固定同一2514输入/actions/rewards/masks、all5critic的原前瞻84/85/86跟踪已完整审查。VMC总SSE9046.060766→3556.824879→1158.553497，所有5critic从85改善，但c2仍99.795864高于84的55.165155。导纳1283.626104→3932.822648→2110.926268，c0/1/2/3从85改善，c4由68.649647恶化至697.599873；当前总误差仍高于84，不隐藏回归。VMC旧84short0600 SSE2624.382648→328.452727→64.701597，相邻正reward long0400 765.100376→733.931484→0.860001；critic1现在对正reward预测23.042877，旧异号问题消失，旧short0100由122.004646改善至4.669285。这再次反对仅凭84局部负梯度余弦断言现有输入无法拟合；不作历史Adam或minibatch因果解释。
同一2544旧终端群体V总SSE9991.012435→1172.629322、A8131.029796→2606.867028；原历史focus仍有退化，V index2423133 5.912702→56.484323、2423122 7.332240→21.173519，A index2752093 41.328919→56.984262。全部30新增85群体另按episode索引与原values绑定并和2544减2514总量一致：V6434.187555→14.075826，A4198.207147→495.940761。此前85V short0000失败行SSE6149.693743→4.540179，A short0600失败行3688.808975→8.350587；这说明实际旧失败样本正在原协议下被拟合，不需要因85单轮高误差立即改输入。
新增86终端贡献V0.001348028，最大long0500占29.3085%；A0.015094606，short0900失败占59.0944%、long0500占22.0499%。90新终端更新机会已按真实append→steps++→update和连续日志检查，实际采样次数仍未知。上一turn完整85全10,577,448旧replay因果历史重建与独立保存/90旧84数组检查通过，但这只是数据可行性，不证明历史特征可改善在线策略；没有修改当前actor canonical48或critic输入。
明确只执行一个有限87周期，保持原协议，检验86旧样本拟合改善是否保持、导纳c4回归是否持续、阻抗short0600新Strict失败及导纳条件交换是否继续，并完成原已登记85—87窗口的最后一轮。原85→86导纳/VMC reward相邻变化已超过5%，因此无论87结果如何都不能让原该窗口通过全部相邻5%检查；完成窗口是为了保留完整固定统计和bootstrap，不是声称有望追认该窗口稳定。阻抗85近零限制仍适用。当前没有非有限状态、恢复错误或新安全中止，A/V旧误差与完整loss实际改善，证据支持此一次有限延续，不支持无界续训或已经收敛。完整87后必须再审全窗口、所有失败和loss/固定样本；若仍无稳定证据，应据已完成诊断评估单独登记的训练修订，不自动88。
87每方法最多41250真实transition，30条件×最多55秒，4m append-only、23/47历史marker、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates均不变。原85—87 PLAN SHA6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e、seed2026102858、5000bootstrap、nearzero1、5%、anchor55、原4小时截止不变，不重启统计或延长旧预算。partial75/原74—76不可判、76—78/79—81/82—84原结论、79安全中止、Direct33数值阶段与冻结0/0及中断28缺最终不变证明保持；指定ESN仍缺且不替换，冻结82完整90/最终in-memory不变/独立审计/比较继续。GPU原v7在科学结束后继续合成保载，但占用不是科学续训理由。Goal active。


87科学trainer同86，五metadata扩展可逆，19协议+8边界负例与实际缺前置拒绝保持。全learner/optimizer/replay/RNG/next65536准确恢复通过；实际startup检查新增步数 `{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}`，30sampler、MJB、旧replay/历史markers、新动作/clock/reward0误差通过。87每方法最多41250新transition、30条件×最多55s，4m append-only/23与47markers/terminal128/batch65536/UTD1/LR/reward/masks/physics/filter/gates不变。

87 archive2291682/start573936642、loss2291685/start573936646，startup及全部labels/两终端后续已部署。原完整86 anchor2574→预期87共2604，锚点保存复核通过。具体新等待PID/start读各LAUNCH.json，避免猜测或重复派发。原86完成观察28样本/810.250秒，29身份核验；新87观察7样本/120.009秒、29身份保持live或原成功结束、steps单调且保存逐行回读。观察完成不重启科学。

原85—87 PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`、seed2026102858、5000bootstrap、nearzero1、5%、anchor55、原4小时deadline保持。现完整85/86、87运行。A/V的85→86相邻变化已超过5%，后续87不能使该窗口全部相邻检查通过；完整窗口与bootstrap尚在等待，不能用部分数据冒充最终统计。原76—78/79—81/82—84、partial75/原74—76不可判和79安全中止全部保留。

冻结82的阻抗已完成30条件/41250动作/3300万子步，Task18/Strict17；FINISHED证明full learner与full replay保持不变，initial/final learner digest均19c27c3792cd06067f042fd455d92306b82634f42c2fd6c6f8255a8c8ffffd1d，0optimizer updates，原evaluator正常退出，不重启。该方法PROGRESS仍停29条件是旧进度快照，最终状态以FINISHED为准。剩余方法进度(已完成条件,在途条件,动作) `{'admittance': (26, 'active_long_train_0500', 400), 'vmc': (27, 'active_long_train_0600', 200)}`；rootreview/55→82比较/全保存raw审计继续，完整90及其余方法最终全state证明/实际图/完整比较仍未齐。单动作seed2026102638和开发训练条件，不证明泛化或指定ESN最终排名。Direct33数值阶段接受但冻结30 Task/Strict0/0，无Direct34；中断28缺最终内存不变证明仍披露，指定ESN仍缺且不替换其他主机模型。

完整86checkpoint位于 `runs/parameter_partial75_recovery_cycle86_archive_20261029_v1/<method>/cycle_00086.pt`：

- impedance: `33774b41e085814bd674b0d188be01544034d2fa3e042979816787ce122e9b37`。
- admittance: `2816eb38027943e7dcb5b5a74eda6129f8ae45219d22ead0daa3b2fd2940b5e6`。
- vmc: `44045de32e9e37c24d87fd76b6fc186f8e597700877593683d6766baf03a3413`。

GPU原v7 supervisor和四worker继续；380保存样本最低[73, 64, 65, 65]%、低于50次数[0, 0, 0, 0]，末值[80, 93, 94, 94]%。科学任务结束仍合成保载，合成占用不算科学吞吐；历史v7预热0和v6低谷保留，采样间瞬时不能保证，非重启自启服务。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY86_COMPLETE87_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，372成员/4657989字节，SHA256 `7700e82201ddea47a67eac8d7f9666521b5b6a51bc5043a42063d89ab4cbf49d`。逐tar成员原字节/AST核验，Git index/commit blob另核。大checkpoint/replay/raw/history sidecar仍原共享SSD，非HDD/arm1全备份，HDD LATEST原位保持254字节。归档中的运行日志为快照。

后续先核原87/冻结82/85—87/labels与终端/guard身份及FAILURE/FINISHED。完整87后审原完整窗口与bootstrap、全部loss/health/标签/旧新样本，判断是否需要独立登记训练修订，不自动88；不能只因87结束、部分loss下降或GPU有占用标记Goal完成。
