# 第85轮前缀、第86轮恢复准备与第84轮终端输入诊断

2026-10-30T11:14:43.389216+00:00，Goal active。原第85轮三路继续，保存steps `{'impedance': 3504212, 'admittance': 3506439, 'vmc': 3508029}`；冻结82与原85—87统计窗口继续。未证明reward稳定且loss健康共同成立。第86轮只部署完整85后的精确恢复等待器，没有86训练或决定。上一轮[完整84交接](RL_RECOVERY84_COMPLETE85_RUNNING_20261030.md)与所有历史失败/限制保留，不启动Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`，checkpoint/replay/raw/runtime在共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。开工实际ls-remote、fetch/read main `ab8cbd7b75cfe9c3e16adc4564462c21c695662a` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按仓库sii-research-sync执行，保留另一主机非RL工作，无子agent。最终发布以SSD PUBLICATION.json的成功push与随后实际远端核验为准。

`runs/parameter_recovery85_first5000_20261030_v1` 固定原前5000条，登记在训练启动且前缀已可用后，没有按结果调整区段。三路原字节一致、连续step、全部数值有限、math.fsum独立算术通过，实际六栏图已查看。

|方法|critic首→末1000|最大|actor首→末1000|
|---|---|---:|---|
|impedance|2.205659→2.091351|25.844995|21.166167→21.189903|
|admittance|1.203930→1.180240|19.456699|-8.749444→-8.758313|
|vmc|1.052628→1.110197|12.595208|-11.977408→-11.977768|

阻抗仍反复尖峰、actor轻微上升；导纳孤立19.456699尖峰、均值略降；VMC critic均值略升、actor近乎平坦。只有前缀，不宣称完整85健康或取消84 Strict失败、critic间误差变化。未新增尖峰阈值。

`runtime/prepare_recovery86_20261030_v1` 的科学trainer与85逐字相同，5个metadata插入可逆；三路协议/父边界正例、每路19协议+8边界负例通过。真正未完整85的prepare入口被拒绝，没有提前86输出。原82500负例预算和20261078构造dummy seed保留；source/AST与health两个依赖实际导入通过。86 startup/archive/fullreview/health/full loss源码已准备，历史49—74/76—85及85→86配对保留，75明确拒绝。

恢复等待器PID `1064870`/start `573174027`，仅在完整85归档/replay/reward/health成功且原learner退出后，执行全部learner/replay/RNG和next65536检查。保存时实际86恢复完成=`False`。没有86决定/训练；后续决定必须读完整85、实际图、原全部窗口及本轮新固定输入跟踪，不能只凭首5000或局部梯度负余弦自动续训/改协议。

新增 `runs/recovery83_84_terminal_behavior_alignment_20261030_v1`：83→84全部90行为配对、导纳/VMC全部60终端预测配对、全部90终端写入后的更新机会已核。原trainer append→steps++→一次update以及41250连续日志绑定，机会不是实际minibatch抽样次数，同一batch也可能重复抽样。

VMC84 `short0600` 的replay index3478427，写入后仍有7573次更新机会；`long0400` index3478443有7557次，`short0200` index3478401有7599次。对应masked终端SSE为2624.382648、765.100376、553.110537。该误差不能用“本轮末最后一条只来得及更新一次”解释，原82导纳long0300的一次更新案例仍独立成立；这里也没有实际抽样日志，不能断言样本经过充分拟合。

VMC short0600两轮均完成Task/retreat，hold约26.00→25.64秒；84穿透.219398mm超过原.2mm门导致Strict失败，终端reward由83的+23.886206变为84的−28.434004。原55秒、物理、gate与奖励不改。83/84同条件状态、动作和mask不同，不是同一输入的策略因果对照。

原SOURCE_HASHES验证后逐条检查源码：canonical48明确为当前q/dq/command/error/command−twist/load/wrench/direction；learner缩放后添加混合系数和critic剩余时间，共50维，再接7维动作。没有显式累计最大穿透或历史Strict有效标记；Strict依赖整回合最大外穿透，原terminal项按Strict给+25或−25，加原shaping/completion项。这支持调查部分可观测性，不能仅凭字段缺失证明不可能拟合：当前信号可能间接携带历史信息，动作也不同。

两方法各全部2514终端、全部30新增84终端和所有mask内critic检查最近同/异reward符号邻居。距离使用实际57维网络输入坐标的Euclidean范数，不拟合尺度、不设阈值；选中距离用独立math.fsum复算。两种算法确认各2514无完全重复特征，不能宣称精确输入冲突或排除近似混叠。

VMC short0600与成功long0400的输入距离.096118240，其中50维观测距离.001375594、7维动作距离.096108396；对critic0/1这是最近异号reward邻居。short0600与成功short0200距离.170911633，对critic3是最近异号邻居。失败行mask为[1,1,0,1,0]，其mask内Q约[5.229,.228,−2.555]，target−28.434；成功近邻部分mask内Q也偏向中间值。全部其他样本/邻居保留，距离不是有效性或健康门。

为检验局部拟合方向，先登记900秒、最多1210forward/1200autograd、CPU53/torch1的冻结84只读诊断，再执行两方法全部30新终端、所有mask内critic及最近同/异号邻居。实际974 forward、964 autograd，69.412秒，0物理/0optimizer/replay写入；原2514批量Q逐位复现。单行forward浮点差异最大V 0.000095367、A 0.000087738，在预登记1e−4绝对容差内。每critic81921参数，全network/RNG不变、参数.grad缓冲未写，checkpoint原hash保持。

|方法|邻居reward符号|全部配对数|局部平方误差梯度负余弦数|
|---|---|---:|---:|
|vmc|same|116|27|
|vmc|opposite|116|60|
|admittance|same|125|43|
|admittance|opposite|125|56|

上述负余弦在同号、异号邻居和两方法中均存在，不是新异常阈值或VMC特有故障。分别计算Q Jacobian与平方误差梯度，所有点积/范数经math.fsum独立复算，保存标量关系回读通过。正terminal128权重和正分母不改变余弦；这不是实际随机minibatch或Adam更新方向。

|VMC short0600的critic索引|异号邻居replay index|输入距离|Q Jacobian余弦|局部平方误差梯度余弦|
|---|---:|---:|---:|---:|
|0|3478443|0.096118240|0.765841624|-0.765841624|
|1|3478443|0.096118240|0.971197893|-0.971197893|
|3|3478401|0.170911633|0.797726793|-0.797726793|

这三组在冻结84上存在可验证局部拟合竞争，但不能据此解释历史83→84全局漂移或直接决定科学改动。实际四栏图包含全部60新终端与482配对，已查看；没有优化训练、调奖励、放宽门或修改正式观测。

新增前瞻 `runs/recovery84_85_fixed_terminal_input_followup_20261030_v1` 在85完整结果未知时登记同一2514/all5 critic，比较固定84→85，另完整列出全部30条84新增样本；不只追踪三个突出案例。绑定原anchor84/输入梯度证据，原85完整review与两terminal保存成功、原进程退出后才做保存值标量审查，不做新网络forward。实际缺完整85入口拒绝通过，等待器PID `1604861`/start `573247782`。截止为原85 monitor+14400秒，不延长、不自动86；当前只是等待，未宣称结果通过。

观察11样本/300.005秒，26个原身份保持live或成功收据终止，进度单调、保存观测回读；最终另核新固定输入等待器共27身份。冻结82进度(完成条件,在途条件,动作) `{'impedance': (20, 'active_long_train_0000', 300), 'admittance': (19, 'active_short_train_0900', 1300), 'vmc': (19, 'active_short_train_0900', 900)}`，原三evaluator/rootreview/比较/全保存raw审计继续，全90及最终全learner/replay内存不变证明待。单动作seed/开发训练条件，非泛化或最终ESN比较。

原82—84 I近零不可判、A/V失败5%；76—78/79—81及partial75/74—76不可判、79安全中止保留。85—87原PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`/seed2026102858/5000/nearzero1/5%与原截止保持，窗口未完成。Direct33数值阶段接受但冻结Task/Strict0/0，原中断28最终不变证明缺失保持；指定ESN仍缺，不替换另一主机模型。Goal active。

GPU本轮281样本，最低[54, 63, 68, 67]%、低于50次数[0, 0, 0, 0]、末值[80, 93, 94, 72]%。原v7及四worker核验，科学完成后继续补载；包含合成负载，不是纯科学吞吐，不保证采样间每瞬时，历史低谷保留，不是重启自启服务。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY85_PREFIX86_INPUT_DIAGNOSIS_20261030/SMALL_EVIDENCE.tar.gz`，163成员/2495274字节，SHA256 `9d51090437bc9f82cc1c5a05b989893ddc8581b37466042ceffae2e256567758`；逐tar成员原字节/AST核验，Git index/commit blob另核。含两方法完整anchor84小数组和上轮已发布归档收据；大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD LATEST保持254字节原位更新。

下次先核85/冻结82/86restore/85—87/固定输入跟踪/guard原PID与start、FAILURE/FINISHED与时效。完整85后收齐全部reward/loss/health/标签/终端/实际图，审同2514的85表现及局部竞争是否持续，再作下一有限阶段的具体决定；当前仅准备恢复。若探索critic历史信息，必须另登记、核旧replay可重建性与公平协议，不可直接把隐藏评测信息塞入actor或改原输入/gate。保持所有原失败与未完成范围。
