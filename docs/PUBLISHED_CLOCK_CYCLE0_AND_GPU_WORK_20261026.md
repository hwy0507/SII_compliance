# 时钟在线首周期、旧固定策略矩阵与 GPU 补充工作

2026-10-26。当前目标仍是已发表方法适配、健康且充分的在线学习，以及最终冻结策略与指定 ESN 的公平比较；尚未达成。
开工 fetch main `6dc2b241215d1898f8e07916153f3e0754dfb3db`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，本地父提交 `9163bb3`。
本报告小型证据见同名 JSON。产物主位置为本集群
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；没有宣称已向其他主机归档。

## 新在线阶段的完整首周期

`runs/cheq_clock_online_seed20261025_v1`，冻结 `runtime/source_train17_clock`。
四路各 41,250 actions / 36,251 updates、30 个完整 55s 回合，无提前中止。

|方法|Task/30|Strict/30|平均 reward|末1000 Q loss|终端 Q MAE|
|---|---:|---:|---:|---:|---:|
|direct|0|0|-32.788830|6.513557|41.282927|
|impedance|18|16|-4.073308|2.570699|22.878064|
|admittance|13|13|-10.317198|9.130303|47.667490|
|vmc|17|16|-4.607349|9.767826|49.180070|

所有方法 passive 均 0/10，不据此宣称任务不可完成。Impedance 短期 0500/0600 的穿透分别
0.2064667513/0.2203517996mm，VMC 短期0600为0.2247919263mm，均超过原0.2mm阈值，Strict失败保留。
Direct失败阶段 approach18、carry11、retreat1；参数方法主要carry。
781源码、四checkpoint、120终端/模型/fixture/plan/reward以及165000 replay的current/next时钟和done均复核。
这次是已保存回放/终端审查，不是重新逐物理子步审查；采样中策略变化，不是固定策略acceptance。
相较旧无时钟首周期的差异只作描述：异步顺序与并发不同，不能当作时钟修复的因果证据。
继续原登记六周期，四原learner与归档/审计进程不重启，不因一个周期更换奖励或算法。

## 旧无时钟 cycle3 固定策略矩阵完成

`runs/fresh_cycle03_fixed_representatives_v1/COMPLETE_SCIENTIFIC_REVIEW.json`：12 learned条件加12已归档nominal。
24回合共2640万物理子步独立复算；learned物理/filter/torque核验通过；nominal有物理/filter核验，旧归档没有torque投影重放扩展，不能声称其也重放过该项。
Direct learned0/3 vs nominal2/3；Impedance、Admittance、VMC均learned2/3 vs nominal2/3（Task=Strict）。全部passive失败。
Impedance长期接触舒适比例12.6067% vs24.0739%，虽峰矩51.228 vs52.256Nm、完成时间20.48 vs20.52s，不能说全面改善。
Admittance短/长期完成时间40.80/38.48 vs45.28/42.48s；长期舒适比例双方100%。无接触NA。
这些是旧cycle3的三个预选代表条件，不是新时钟阶段、最终cycle5、完整30条件或ESN比较；未选最终Tref。

## 当前运行时性能证据

`runs/clock_online_profile_v1/SCIENTIFIC_REVIEW.json`：60s、10Hz、各主线程599样本，五个profile无lag/error。
Direct/Impedance/Admittance/VMC selector等待43.57/23.54/27.05/25.38%，learner更新43.07/59.43/56.43/56.76%。
代表sampler的88.31%时间在physics、10.52%等动作，最大leaf为mj_step24.04%。cgroup平均40.97核、无新增throttled periods。
正式GPU均值5.30/7.77/7.27/7.48%，未达50%。Direct尾部8→6 samplers，其余12；观测吞吐不作因果加速结论。
此证据不支持为了占用直接更改live UTD/batch/dt。原训练设置保持不变。

## 用户紧急要求后的有限辅助训练

新增 `tools/probe_recorded_return_capacity_20261026.py`，冻结至 `runtime/clock_cycle00_return_capacity_v1`。
`runs/clock_cycle00_return_capacity_v1/REGISTRATION.json`预登记后启动四路，每GPU一路。
固定新clock首周期checkpoint/回放，以原critic结构回归记录轨迹的无熵discounted return，比较parent/fresh初始化。
每类按condition名称排序最后两个作为本次拟合留出，共24训练/6留出条件，33000/8250 transitions。
父在线actor/critic此前已经见过这些条件；不能称真正未见策略评估。
目标来自不断变化的行为策略，且不含SAC熵项，因此这是固定标签可拟合性/优化诊断，不能当作SAC Q误差或actor改进。
全部ensemble头均拟合这些固定标签，非原Bernoulli mask训练目标。两臂fresh Adam、相同批采样seed。
每臂20000更新、四方法共160000辅助更新，batch2048、lr3e-4、gamma.9995；0新physics、0actor更新，不保存推广权重、不自动延长。
逐episode重建时序、next/current、terminal、reward与clock；独立return递推及手算短序列通过。
四进程全部通过数据核验并开始真实梯度更新。共享保留CPU52–54、nice10，在线CPU0–51不改。
`RESOURCE_BALANCE.json`记录启动后辅助CPU均衡变更，原登记与runtime不覆盖。

首个60样本混合窗口GPU平均 `[68.63333333333334, 52.15, 33.28333333333333, 35.78333333333333]`%，最低 `[27, 21, 11, 13]`%。含CPU均衡变更，不是纯正式训练利用率；尚未四卡都达50%。
辅助曲线和完成结果须独立复核，不能根据初步下降宣称策略收敛。预算结束后自动退出，当前措施不保证永久避免平台关机。
正式下一关键证据是已安排的cycle1及后续周期诊断；Goal持续active，最终ESN仍未指定，不以历史ESN替代。
本轮未改physics/MJB、gate、actor输入、公共filter、执行器限制、dt或live learner。
