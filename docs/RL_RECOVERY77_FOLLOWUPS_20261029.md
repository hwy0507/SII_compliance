# 恢复77完整标签与固定终端后续

2026-10-29T07:10:05.151870+00:00，Goal active。原77三路继续，当前steps {'impedance': 3167637, 'admittance': 3168965, 'vmc': 3171126}，各30sampler；未完成77，不判断收敛。完整76审查和实际77启动见[此前报告](RL_RECOVERY76_COMPLETE77_RUNNING_20261029.md)。原科学配置、历史75中断及前瞻76–78 PLAN保持，无自动78、无Direct34。GPU保底在全部科学工作完成后仍继续，合成占用不计科学吞吐；非重启自启服务。

实际计算主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器env/bin/python。

77标签等待已部署，比较两个完整周期76→77，检查全部180保存回合/90reward对/Task及Strict-only变化、原.2mm物理gate、model和evaluator hash；再独立对照全loss的reward与标签计数。真实未完成77已拒绝，无输出，无新积分/优化器更新；中断75仍拒绝，不补造完整75。

导纳及VMC完整76终端锚点已完成并独立复核。每路全部2274条（包含76新增30条）的索引、reward、masks、Q和分母与先前已审values逐项相等；observations/actions来自准确完整76 checkpoint。只复用此前审查过的Q，无新网络前向/训练/物理。VMC总masked SSE3883.440215203、贡献.180412988282；导纳2815.605065203、贡献.130720576160，独立scalar复算通过。它们是全2274基准，不能与此前仅旧2244 SSE混为一谈。

两路77后续已登记并实际等待，完整77预期2304终端：固定全部2274旧样本与新增30分栏，保留原历史focus、更新分母和旧分母两种贡献；全群体改善与退化均保留。等待原训练及完整归档/health审查结束后才做CPU只读前向与独立标量检查，原训练权重、replay、采样和gates不变。后续实际图仍须查看，当前只有基准没有77结果。

|任务|原PID / start ticks|
|---|---|
|77 impedance|3187668 / 45169092|
|77 admittance|3187669 / 45169092|
|77 vmc|3187670 / 45169092|
|77 archive/health|3187671 / 45169092|
|parameter_recovery77_task_labels_20261029_v1|3693087 / 45236452|
|vmc_recovery77_terminal_followup_20261029_v1|3835143 / 45254904|
|admittance_recovery77_terminal_followup_20261029_v1|3835144 / 45254905|
|parameter_recovery77_loss_20261029_v1|3187674 / 45169097|
|parameter_recovery76_78_reward_stability_20261029_v1|436148 / 44768306|

连续观察11样本/300.002秒，全部14原PID/start身份在观察期live，steps {'impedance': 3163427, 'admittance': 3164901, 'vmc': 3166807}→{'impedance': 3167280, 'admittance': 3168355, 'vmc': 3170719}。观察器自然完成不表示训练完成，不重启科学。保存时重新核原训练、归档和五等待器活跃、PLAN/source hash保持。

从前次保存起guard 120样本，四卡最低[76, 72, 68, 68]%，低于50次数[0, 0, 0, 0]；合成保载保持。原容器中断和v6预热两空闲样本在此前记录中保留，不声称跨重启无间断。

完整76证据提交68f3e0b4共316manifest条目已逐大小/SHA核暂存及提交Git blob；本轮开工实际fetch/read mainba9748b1、baselinef6e8f8c，新增非RL第十条件/接触范围说明已读，并以606c3162安全合并，双方日志新增块逐字保留。禁交互push返回128缺GitHub HTTPS用户名认证，仍仅本地提交，远端未发布；这不阻断共享SSD训练/归档。发布前又实际fetch/read main1f581096（非RL93→96）和对应交接并安全合并，双方新增日志逐字保留。没有操作他机非RL任务，无子agent。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY77_FOLLOWUPS_20261029/SMALL_EVIDENCE.tar.gz`，59成员/954249字节，SHA `d670aed2ba5f6ef42619e69f6fb1b952f5a498f516f46bd63d47426ee3e6144c`，逐成员字节/源码AST已核。[收据](RL_RECOVERY77_FOLLOWUPS_20261029_SAVE.json)。大型checkpoint、回放及raw在共享SSD；不是HDD或arm1完整备份。HDD入口就地更新且不增加文件大小。

下一步保持原77、归档、全loss、标签、两终端跟踪与原76–78窗口；等完整77全审和实际图后才决定有限78，reward稳定与loss健康尚未证明。用户要求全部工作完成后保留GPU保底。
