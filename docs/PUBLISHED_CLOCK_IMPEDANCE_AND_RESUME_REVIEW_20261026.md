# 时钟Impedance固定复测与完整恢复状态核验

2026-10-26。fetch main `c3124ba322853c1e561657b58c4204ed2a64a1b6`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新远端提交。
上一轮完成Direct全固定回合重放并实际交接并行评估，为实质进展；本轮继续原四learner和剩余矩阵，没有重启训练。

## Impedance固定首周期策略

原evaluator3479276完成三个回合，接管审计3825230完成；不可再因PID消失重启。
`runs/clock_parameter_fixed_review_v1/impedance/REVIEW.json`独立复算330万learned物理子步、物理/filter/torque均通过。
全部4125参数动作经冻结learner重放误差0，逐动作clock核验；参数action5维、公共action7维、raw48/actor49/critic50。
全部网络参数不变，0optimizer updates；原同接口nominal复用已有独立物理/filter审查并逐原始文件hash复核，本轮未重复计算nominal或声称缺失扩展的nominal torque审查。
同MJB/fixture/plan/dt，无privileged actor truth。learned和nominal的Task/Strict均2/3，被动失败、主动短期/长期成功。

|条件|learned完成s|nominal完成s|learned峰矩Nm|nominal峰矩Nm|learned接触舒适比例|nominal接触舒适比例|
|---|---:|---:|---:|---:|---:|---:|
|passive_corner_train_0000|NA|NA|48.6372|40.5833|NA|NA|
|active_short_train_0000|13.1600|12.9600|45.6446|45.3060|NA|NA|
|active_long_train_0000|20.0000|20.5200|46.4127|52.2561|13.0020%|24.0739%|

长期实际接触时长7.81685s vs7.76920s；峰矩/完成时间改善，但阈下舒适比例13.0020% vs24.0739%下降，不能声称全面优于nominal。
短期完成时间略慢、峰矩略高；被动两者失败且learned峰矩更高。无实际人体接触时比例NA。
这仍是cycle0/41250steps的三个预选代表条件，非最新充分收敛策略、完整30条件、最终Tref/SPT或指定ESN比较。
独立核验器首次路径替换导致语法错误，发生在执行前；失败脚本/收据保留，只修只读核验器，实际训练/评估没有失败或重跑。

## 四接口实际checkpoint的恢复能力

`runs/clock_full_state_resume_review_v2/REVIEW.json`：使用四个已复核cycle1完整边界checkpoint，没有启动接续训练。
检查覆盖actor、5个critic与target、三个优化器的moment/counter、alpha与log_alpha、learner计数/metrics、静态observation scale、各类RNG及整个replay。
实际load→state_dict逐值规范化hash与原状态相同；四份replay大小/cursor/数组/masks/RNG精确。
每路3批×256条replay抽样与从原RNG独立生成的索引逐值相同，抽样后的RNG也相同。
Python、NumPy、local generator、CPU Torch及全部4卡CUDA随机数的后续16个draw与独立原状态generator完全相同。
Adam scalar step保留原数值，按现有实现恢复到CPU；没有将actor与critic不同的历史步数强行统一。
critic_clock flag、actor49/critic50与新回合clock从0动作开始均核验；四接口均拒绝把有时钟checkpoint静默加载为无时钟架构。
原checkpoint/replay/source未改，不写新checkpoint、0physics、0optimizer updates。

此验证证明完整边界的状态值和抽样流可恢复，不是后续optimizer更新逐位等价测试，也不保证异步physics调度轨迹逐位相同。
没有选定/派发下一阶段，不把这次核验当作学习改善；真正接续必须使用届时审查的实际阶段末checkpoint。
首次v1只读工具缺少training runtime未包含的digest support模块，在任何checkpoint恢复/更新前退出；保留失败。
v2明确加载已有冻结诊断support并记录hash后四路全部通过，不修改训练runtime来补诊断依赖。

## 当前运行与边界

在线四路仍原PID1729888/1729892/1729893/1729897，归档1729901、诊断1729905继续；下一统一审计cycle3/5。
报告时进度：

|方法|steps|updates|cycle index|
|---|---:|---:|---:|
|direct|179172|174173|4|
|impedance|130519|125520|3|
|admittance|131111|126112|3|
|vmc|131077|126078|3|

`clock_fixed_parallel_v2`已完成Direct与Impedance共6/12，Admittance/VMC原并行进程继续；3996089有限汇总仍live，无失败收据。
旧串行2960898是有意交接停止，原Imp3479276与接管3825230现在属于正常完成，不重启。
GPU持续50%、充分健康收敛、完整30条件固定评估、最终SPT_empirical和指定ESN比较仍未完成。
不改physics/MJB、gate、actor输入、公共filter、执行器限制、dt、live reward/optimizer，也未推广任何辅助权重。
原始证据仅本集群`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，同名JSON记录hash与地址；无其他主机归档声明。
