# 参数35接续与Direct22衔接

2026-10-27 UTC。持续Goal active，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。真实运行及大checkpoint/replay/raw保留SSD；不声称HDD或arm1全量备份。

完整参数34三路各30×55秒，无abort；旧replay全部字段/history/优化器及2m marker保持，每路新增41250奖励重建误差0。完整REVIEW、FINISHED、健康诊断及图已审查，网络/优化器有限、诊断不改网络。

|方法|steps / updates|Task / Strict（各30）|平均reward|首1000 / 末1000 q_loss|整轮loss均值 / 最大|
|---|---|---|---|---|---|
|阻抗|1440750 / 1435751|18 / 17|−2.369303|2.049970 / 2.889142|2.344579 / 46.892891|
|导纳|1439750 / 1434751|11 / 11|−13.719218|2.138450 / 1.459024|1.671923 / 18.900564|
|VMC|1440750 / 1435751|17 / 17|−2.815623|.853015 / .732462|.713314 / 12.712925|

terminal MAE/in-bag MAE为I .780232/.252584、A .595433/.202069、V .545358/.221415。soft-Q必要上界超出比例0/.0009277344/.0019042969。阻抗后段loss升高，A/V下降仍有尖峰；熵在方法原目标附近，temperature为正。回报尚有条件间成败切换，数值有限不等于健康收敛，不追加Task阈值或更改原稳定性定义。

完整34准确父SHA：I 149618c8b54b3945e392df0f4f414e20c2ddf47422efa957b8d9a438f71b2d93；A 8ff3f38801d28c885b3d12cda7ab17f1f4a496d1e93353708ecbec189b4cb6c9；V e6612fd8030a519b0710e7de68ff7712b9baf39f5f577733069266ea74a90e33。

01:57:25 UTC，三35正式启动：I1290927/A1290928/V1290929；startup1290931、archive1290932、review1290933。三check-only和PRELAUNCH科学审查通过，准确完整34全state续一个原设置有限周期；旧34已完成，禁止重启。实际启动证据以原startup/REVIEW为准。

新36准备1320079、原35审查释放CPU调度1320131，7200秒等待；只完整35后check-only，不自动训练。五入口同时替换并通过AST/父35/目标36/历史容量入口23/monitor适配守卫，实际36恢复尚待。参数33–35固定审计2585589、Direct20–22固定审计3124904继续原登记。

Direct21原2826774及归档2826823/完整review2826824、22准备2851849/调度2851880均完整结束，勿重启。冻结32原I2466385/A2466386/V2466387、根2466388继续原90回合/单外部动作seed，尚未根REVIEW，不重复已完成回合。

本轮重新查询/fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa及baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，均未变。GitHub认证原问题未解决，不重复索取凭据。指定ESN缺失原记录保留，不替换或重问。小证据docs/evidence/RL_PARAMETER35_SERL22_20261027。

34→35存在真实审查/恢复空档；35启动后瞬时四卡67/86/83/81%，仅瞬时快照，不作每时刻保证。后续固定窗口另记。

35实际启动审查已通过：I1441750/A1440750/V1442750，新增1000/1000/2000；旧I/V1440750、A1439750全部replay字段、history、优化器配置及2m marker/30MJB/30sampler/action/clock检查和新奖励0误差通过。原startup1290931已结束，归档和完整review继续。

完整Direct21为895782步/7126264 critic更新，30完整55秒无abort，Task/Strict0/30，reward−30.907792（20为−30.912666）。旧854532 raw/derived/history全部精确保留、新41250奖励和32步目标精确、pending0；末1000critic loss .012554185，首1000 .012990237，整轮均值.012792793、最大.028461456。660终端×10critic MAE .034666643，32步TD MAE .041525416，Qmean−20.53186798，temperature .000479878。完整REVIEW/DIAGNOSIS/FINISHED与图通过，健康诊断完整网络/优化器/RNG不变。回报近乎不变，低loss不证明任务学会；原部分前瞻20–22窗口尚待22，不追加成功门槛。

准确完整21父SHA 532f0939051e36ed3b7fc4f81038b0501e994bcc0ce9a7f1d20ab43e168334a8。02:04:07 UTC正式22 learner1584172，startup1584174、archive1584175、review1584176，完整21全state续一个原设置有限周期。恢复check-only和PRELAUNCH科学审查通过；实际startup仍以原REVIEW为准。10critic/随机2最小bootstrap/actor全10均值/noentropy/8:1/batch65536/32步目标与原动作映射保持。

新Direct23准备1605144、原22 review释放CPU调度1605145，仅完整22审查后check-only，7200秒，不自动23训练。五脚本同时替换/AST/准确父22目标23/720终端/原batch阶段保留守卫通过，实际恢复尚待。

新一次混合22/35/冻结32资源观察1628810，等两正式实际startup通过后固定60样本；结果以原PROFILE为准，不重采挑结果。两次换轮实际GPU空档保留；所有PIDs行动前查原LAUNCH和实际身份。

Direct22实际首1000新增审查通过：896782步/7134264 critic更新；旧895782 raw/derived/history与optimizer/clock保留，新136 mature+864 pending和奖励重建0误差，原30 MJB/sampler/动作映射通过。startup1584174已结束。固定混合22/35/冻结32 observer1628810已完成60样本/65.476863秒，均值58.85/64.066667/65.316667/69.083333%，七个原learner/evaluator身份全程保持，保存均值独立核验通过；不代表纯训练吞吐或每瞬时达标，不掩盖换轮空档，勿重采。

收尾实际进度及原18个句柄见小证据FINAL_LIVE_STATUS.json；下一轮先查原完整35/22审查和两稳定性结果，再决定36/23，禁止check-only自动推进训练。
