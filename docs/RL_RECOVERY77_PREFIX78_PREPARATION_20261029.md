# 恢复77早期loss审查与78仅恢复准备

2026-10-29T07:22:15.124574+00:00，Goal active。上轮完成完整76归档与77全标签/终端后续部署，本轮完成77前5000原始日志和实际图检查、新78恢复工具与等待部署。原77三路仍进行中，当前steps {'impedance': 3176605, 'admittance': 3177603, 'vmc': 3180779}，各30sampler；完整77结果尚无，不能判断收敛。完整76和77后续见[此前交接](RL_RECOVERY77_FOLLOWUPS_20261029.md)。

实际计算主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器env/bin/python。原30条件×55秒/最多41250新增、4m append/23与47标记、terminal128、batch65536、UTD1、LR/reward/masks/物理/gates不变。历史75仍中断，原74–76无法评定；原前瞻76–78的5%/nearzero1/seed2026102855/5000bootstrap/anchor55及历史失败窗口保持，近零保护不用于推离零；Direct33既有数值结论与Task/Strict0/0保持，无Direct34。

77前5000检查登记在训练启动且该前缀可用之后，只作描述。三路原字节前缀、连续步号、所有数值字段有限、独立scalar均值/极值复算通过，audit仅修改周期/path/描述且逆变换等于76原工具，无训练更新或新物理。实际查看完整六栏图：

|方法|critic首→末1000|max critic|actor首→末1000|
|---|---|---:|---|
|impedance|3.194033439→2.843472615|26.824150085|25.709771868→25.728026011|
|admittance|1.200749416→1.213774475|3.580255747|-9.172750109→-9.197644318|
|vmc|0.915801109→0.802039799|9.384779930|-12.789063289→-12.797391335|

I critic基线约2–3但反复高尖峰，rolling均值下降中仍有局部上升，actor约25.7且尾段略升；A critic约1.2、稀疏尖峰，actor缓慢下降；V critic约.8但仍有局部尖峰，actor约−12.8。没有非有限数值不等于loss健康；只是前5000，不代替完整77 loss/reward/终端审查，也不作收敛断言。

78恢复driver `runtime/prepare_recovery78_20261029_v1/resume_recovery77.py` 当前源码SHA `c9d5c383abc9f38001391166792e23739011be0e1c3d2364a1b4f286f906848c`。与77的科学trainer逐字相同；原五处仅metadata/初始state审查插入可逆还原冻结trainer。新的parent指向完整77，必须保留前一轮recovery_continuation且与父registration一致；递归验证原77 driver及其完整76证据，再验证原partial75恢复和历史科学依赖。新当前continuation替换上一层，但上一层通过准确parent文件/hash完整保留，不把历史completed_stage当当前连续轮号。

三路metadata正例、每路19协议拒绝和8边界拒绝通过，包括被改的上一轮continuation、丢失父checkpoint continuation、科学设置和伪造完整75；这些是标明fixture的metadata测试，不是实际77 checkpoint恢复。对真实尚未完整77调用prepare已拒绝，无78 run输出。没有重启77。

只恢复等待PID 110433 / start 45315607 已实际部署，REGISTRATION SHA `7d5a7dbf33c50a7ea586edd15844c23fd420729430c1bef0ece78a040da0ba29`。等待原77完整归档/health审查且三learner退出后，才执行三个CPU CHECK_ONLY，全learner/optimizer/RNG/replay和next65536必须精确；当前该实际恢复尚未运行，没有78物理/优化器更新。等待器不会派发训练；78启动仍需完整77 loss/全标签/两终端/实际图审查、明确有限续训决定及独立启动/归档检查准备。

原77及完整loss、全180标签/90reward对、V/A固定2274终端后续和原76–78窗口均保持。观察11样本/300.002秒共15原PID/start身份在观察期有效，steps {'impedance': 3172705, 'admittance': 3173863, 'vmc': 3176575}→{'impedance': 3176397, 'admittance': 3177311, 'vmc': 3180459}。观察器自然完成不代表科学完成，不因此重启。保存时所有原任务及仅恢复等待已重新核活跃、PLAN hash保持。

从前次保存起GPU guard 143样本，最低[72, 71, 67, 68]%，低于50次数[0, 0, 0, 0]。合成占用不计科学吞吐；按用户要求科学全部完成后继续保载。此前容器空档/v6预热两空闲样本保留，当前guard不是重启自启服务。

本轮实际fetch/read main1f581096、baselinef6e8f8c；另一主机非RL93→96记录已读且上轮已安全合并，无科学配置变化，不操作其进程。上轮本地7880fb64和68f3e0b4证据已核提交blob，GitHub push128缺HTTPS认证，不能声称已远端发布。发布前另fetch/read mainb1deda65及非RL第十一条件完整/99条进度交接，并安全合并保留双方新增日志逐字一致。当前本轮源基线1beb658bfb396b36ff1375213713990ea7e297e8；无子agent。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY77_PREFIX78_PREPARATION_20261029/SMALL_EVIDENCE.tar.gz`，55成员/990257字节，SHA `8cbf98846a47b4a12f373c7b46777bed33fa1207bf56c2fcdd82ac786ba15869`，逐成员字节与Python AST核验。[收据](RL_RECOVERY77_PREFIX78_PREPARATION_20261029_SAVE.json)。大型checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD最新入口仍指已补本报告链接的主恢复交接。

下一步保持原77和全部原审查及78仅恢复等待；完整77后实际查看全图，再决定有限78。reward稳定与loss健康仍待，Goal active。
