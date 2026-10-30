# 完整84与原82—84窗口已审；有限85续训

2026-10-30T10:50:57.623793+00:00，Goal active。第84轮三路完整结果已保存与审查，reward稳定和loss健康尚未共同成立。依据完整结果明确登记一轮85，三路精确恢复、实际startup及120.006秒观察通过；保存steps `{'impedance': 3486943, 'admittance': 3489172, 'vmc': 3490365}`。冻结82全90评测仍运行，无自动86/87、无Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。checkpoint/replay/raw/runtime在共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。开工真实ls-remote及fetch/read main `30d2010bb4210e6a5aaecc6b68a9110fe4d0f2c6`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按仓库sii-research-sync执行、保留另一主机非RL工作，无子agent。发布成功以SSD本轮PUBLICATION.json的push与之后实际远端核验为准。

|第84轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|3482698|-0.597523690|18/18|2.949788→2.277841|34.543396|21.546433→21.170464|
|admittance|3485000|-8.556481357|14/14|1.435059→1.177207|9.654222|-8.824433→-8.749274|
|vmc|3486000|-4.629474251|17/16|1.098345→1.052520|39.625248|-12.157161→-11.988865|

每路30个完整55秒条件、41250新增、无abort；旧replay全部字段保持，全部新reward由原物理区间journal重建误差0，网络与optimizer有限。完整loss独立保存算术、全标签184条保存rollout、health与两个终端审查以及实际四张图均已检查。reward重建不是重新仿真全部物理子步。

全部标签变化（含Task/Strict未变而physical_valid改变）保留：

- impedance active_short_train_0100：变化['strict', 'physical_valid']；[{"cycle": 83, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.2100327364091106}, {"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.19148206682726507}]。
- impedance active_short_train_0600：变化['strict', 'physical_valid']；[{"cycle": 83, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.2405063496429653}, {"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.1884636141424925}]。
- admittance active_long_train_0900：变化['task', 'strict']；[{"cycle": 83, "task": false, "strict": false, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.03888669000460347}, {"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.08301578630439369}]。
- admittance active_short_train_0000：变化['strict', 'physical_valid']；[{"cycle": 83, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.20778484747334328}, {"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.13205976742764602}]。
- admittance active_short_train_0900：变化['task', 'strict']；[{"cycle": 83, "task": false, "strict": false, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.10396341448643912}, {"cycle": 84, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.10047411629883374}]。
- vmc active_short_train_0600：变化['strict', 'physical_valid']；[{"cycle": 83, "task": true, "strict": true, "physical_valid": true, "abort_reason": null, "penetration_mm": 0.1932174430334041}, {"cycle": 84, "task": true, "strict": false, "physical_valid": false, "abort_reason": null, "penetration_mm": 0.21939809384274578}]。

实际loss六栏显示阻抗均值下降但反复尖峰、actor下降；导纳critic下降且尖峰收小，actor先降后升；VMC有39.625248孤立尖峰和末段簇、actor上漂。有限值及平均下降不是健康证明，没有追加事后尖峰阈值。

|方法|采样Q超当前固定alpha全局上界|终端mask内MAE|终端mask外MAE|
|---|---:|---:|---:|
|impedance|0.00000000%|0.337516|3.623520|
|admittance|0.09277344%|0.190440|2.375316|
|vmc|0.24902343%|0.296343|1.985467|

health网络状态不变、checkpoint与full review绑定。固定alpha上界仅诊断，mask外不参与对应critic训练；不把终端零误差作为新门槛。

- vmc：旧2484终端SSE 22462.380852→5040.057465，新增30贡献0.168425379；新30贡献前三为 active_short_train_0600 65.513%、active_long_train_0400 19.098%、active_short_train_0200 13.806%。
- admittance：旧2484终端SSE 6004.143682→1251.597167，新增30贡献0.001346049；新30贡献前三为 active_short_train_0900 18.177%、active_short_train_0000 13.406%、active_short_train_0200 11.777%。

上述终端跟踪锚点为83全部2484，末84为2514。另一个前瞻登记的固定2454样本跟踪只取82原锚点，逐字段绑定同一features/actions/reward/masks，对82/83/84全部5critic比较；不同分母/样本范围不能混用。原数组和独立标量保存审查通过，无额外网络forward/physics/optimizer：

|方法|critic索引|82 SSE|83 SSE|84 SSE|mask内异号数82→83→84|
|---|---:|---:|---:|---:|---|
|vmc|0|60.902519|49.829924|764.345448|0→0→0|
|vmc|1|214.744777|109.880103|1769.469744|0→0→1|
|vmc|2|2565.466778|364.069127|50.420307|1→0→0|
|vmc|3|47.424399|21831.056697|1095.788192|0→5→0|
|vmc|4|1264.776112|49.337808|1332.997990|1→0→1|
|admittance|0|2817.292285|559.172810|188.736078|1→0→0|
|admittance|1|357.102069|354.594526|184.890052|0→0→0|
|admittance|2|3419.175024|797.130989|222.884092|1→0→0|
|admittance|3|1432.968459|261.920596|475.273205|1→0→0|
|admittance|4|2383.230346|558.919316|136.597163|1→0→0|

原第82—84窗口按原PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c` 完成，实际图和独立保存算术已审；原seed2026102855/5000bootstrap/nearzero1/5%/anchor55及原截止保持：

- impedance：nearzero=True，相邻变化=None，端点变化=None，原5%描述检查=False，condition bootstrap95% delta=[-0.07750658417617189, 5.441110844389148]。
- admittance：nearzero=False，相邻变化=[0.005884936991751158, 0.37069131742791056]，端点变化=0.3743947593732092，原5%描述检查=False，condition bootstrap95% delta=[0.11123332931833337, 10.195830242626023]。
- vmc：nearzero=False，相邻变化=[0.0019058418774931664, 0.647143339755923]，端点变化=0.6502825345110638，原5%描述检查=False，condition bootstrap95% delta=[-5.349793455237576, -0.031029547140606913]。

原标量bootstrap补充全部5000抽样以math.fsum/manual quantile复核通过；共享NumPy RNG，不是独立训练seed，也不是新收敛门。原PLAN reason有陈旧“79–81”文本，实际cycles/路径/registration_state/seed/source明确82–84；原字节不改，单独保存ORIGINAL_PLAN_TEXT_CLARIFICATION。

实际有限85决定：

完整84三路各30个完整55秒条件/41250新增/noabort，旧replay全字段保持、新reward重建误差0、optimizer/network有限；完整loss保存算术、health、184保存标签、两个终端保存复核及四张实际图已审，原82—84图和5000 bootstrap独立标量复核已完成。I/A/V reward为−.597523690/−8.556481357/−4.629474251，Task/Strict为18/18、14/14、17/16。I short0100/0600 Strict恢复；A short0000 Strict恢复及short0900/long0900 Task恢复；V short0600穿透.193217→.219398mm导致Strict退化，原.2mm门不放宽。
原82—84 I触发nearzero1，不能判相对稳定；A端点37.4395%、V65.0283%均未通过原5%稳定检查。I均值改善仍不稳定，A改善也不是稳定，V reward与Strict实际退化。I/A/V critic首末1000为2.949788→2.277841、1.435059→1.177207、1.098345→1.052520，最大34.543396/9.654222/39.625248及V末段尖峰簇保留。Q上界超限A约.0927734%、V约.2490234%，有限不等于loss健康。
同一2454旧样本全5critic的前瞻跟踪完成，V总SSE22404.173660→5013.021680，但仍高于82的4153.314586。V critic3从21831.056697恢复到1095.788192，仍高于82的47.424399；critic0/1/4分别49.829924→764.345448、109.880103→1769.469744、49.337808→1332.997990变差，critic2改善364.069127→50.420307。V异号数critic3的5归0，但critic1/4各新1；误差分布在critic间变化，不能宣布故障消失或归因某个梯度。A总2531.738238→1208.380589，但critic3由261.920596增至475.273205，其余4改善。完整2484锚点的V/A SSE22462.380852→5040.057465、6004.143682→1251.597167，历史focus2423122和2752093仍退化，全部保留。不同锚点范围不混用。没有历史minibatch抽样记录，不作充分抽样或策略因果判断。
上述有限阶段有可量化critic拟合与部分行为改善，未发现非有限状态、恢复错误或新安全中止，也没有已证实需改变原学习协议的因果证据。因此仅登记继续原配置一个有限85周期，观察改善是否保持以及V不同critic的误差变化；不称稳定/收敛，不重置或挑选checkpoint，不改变LR/奖励/掩码/terminal128/65536/UTD1/4m append-only/物理/滤波/gates。下一完整轮后重新审查，不自动86/87。85—87非重叠窗口在实际85启动前登记，seed2026102858、原5000/nearzero1/5%/anchor55及4h预算，保留所有旧窗口和失败，统计登记不授权后续训练。
Direct33与原冻结0/0、原中断28缺最终不变证明、partial75/原74—76不可判、79安全中止、原76—78和79—81失败保持；冻结82原全90及最终内存不变/保存审计/比较继续，指定ESN仍缺不替换。三路85精确恢复及next65536检查已通过，GPU原v7补载持续，科学结束后仍保持。Goal active。

85的scientific trainer与84逐字相同，metadata扩展可逆，三路19协议+8边界负例以及实际未完整84拒绝通过。全部learner/optimizer/replay/RNG及next65536准确恢复，实际startup通过。仅每路一轮30条件×最多55秒/最多41250新增；4m append-only、23/47历史标记、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates保持。全loss/回放/health/标签/两终端后续已部署，85终端锚点2514→预期2544。旧82—84与固定2454等待器按成功收据自然结束，不以进程退出冒充成功。

新85—87非重叠窗口在85实际LAUNCH前登记：seed2026102858、5000bootstrap、nearzero1/5%/anchor55与原算法；所有85—87结果尚未知。实际85启动后才部署4小时窗口等待器及标量补充，原截止不延长。登记仅统计等待，不授权自动86/87；每一轮仍需完整结果决定。原76—78 I近零不可判/A失败/V仅reward描述通过，79—81 I描述通过/A,V失败、partial75及74—76不可判、79安全中止均保留。

完整84 checkpoint `runs/parameter_partial75_recovery_cycle84_archive_20261029_v1/<method>/cycle_00084.pt`：

- impedance：`c45c891b0608d9f3b196736c432ada8674f0780da41a4c9e72aaba0fa1ec054b`。
- admittance：`aba2872c60e85226d57b4843961ae72b8095b007088314153d1881540a390bd4`。
- vmc：`fa31370979d3c91c1ebe9b1de2d9c9ad7e0958f42deddd5a2dca87bbb34a92ae`。

冻结82保存进度(完成条件,在途条件,动作数) `{'impedance': (16, 'active_short_train_0500', 700), 'admittance': (16, 'active_short_train_0500', 1100), 'vmc': (16, 'active_short_train_0500', 200)}`。原三evaluator/rootreview/55→82比较/全保存raw审计身份保持，原全90预算、action_seed2026102638、55秒/dt5e−5不变。全90结果、最终全learner/replay内存不变证明、独立保存审计、实际图及配对比较尚待；只在开发训练条件/单动作seed上验证，不证明泛化或最终ESN排名。Direct33数值阶段接受但冻结30 Task/Strict0/0，原中断28最终内存不变证明缺失继续披露；指定ESN仍缺，不替换为另一主机非RL模型。

GPU 539样本，最低[65, 60, 64, 60]%、低于50次数[0, 0, 0, 0]、末值[80, 97, 96, 94]%。原v7 supervisor及四worker PID/start核验，科学全部结束仍保留补载。合成负载单列，不算科学吞吐；采样不保证每瞬时，历史v6的31/33/44和v7预热0保留。这是当前主机进程，不是重启自启服务。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY84_COMPLETE85_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，590成员/8512678字节、SHA256 `a8882b3e987a9512ab198bd94773db3bfc0b4b04c4d57f2b05b83dbabaab3ef0`；逐tar成员字节与Python AST核验。Git force-add ignored nested runs，小证据与提交blob另核。大checkpoint/replay/raw在原SSD，非HDD/arm1全备份；HDD LATEST原位保持254字节，运行日志是快照。

后续先查85、冻结82、窗口和所有审查的PID/start、FAILURE/FINISHED与guard时效，不重复派发。85完整后审全部reward/loss/health/标签/终端和实际图，再决定下一有限轮。新85—87完整前不报稳定；冻结82全证据齐前不报完整验证，Goal active。
