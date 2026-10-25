# SAC最新完整周期审计与冻结策略随机性诊断（2026-10-25）

目标仍为有已发表方法依据、训练充分且可公平比较的四接口RL。当前结果尚不满足健康收敛。本轮不改在线trainer、physics/MJB、gate、actor输入、公共filter、执行器限制或dt。

四路source09 SAC的最新完整归档已独立审计。Direct为cycle4，另外三路为cycle2；预算不等，不能横向排名。全部120个条件/终端/model收据、冻结输入hash和奖励重建验证通过，网络未改，0新physics/更新；曲线已目视复核。

| 接口 | 完整周期 | 累计步数 | Task/Strict（各30） | 平均return | cycle1末critic loss → 当前末critic loss | 当前Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| direct | 4 | 223990 | 0/0 | -35.2752 | 624.17 → 69660.35 | 32509.98 |
| impedance | 2 | 146028 | 17/17 | -2.2373 | 401.61 → 2532.79 | 2488.46 |
| admittance | 2 | 144265 | 11/11 | -13.5460 | 10654.33 → 146716.73 | 18097.47 |
| vmc | 2 | 144759 | 17/16 | -4.6103 | 14230.63 → 537784.59 | 28847.92 |

四路critic loss和Q均较cycle1增加。Direct训练30例全失败，3例因原2mm全局穿透gate提前终止，失败保留。参数接口被动条件均0/10 Strict；Impedance短/长10/7、Admittance7/4、VMC9/7。VMC当前alpha必要Q上界未超限，但不代表价值准确，terminal MAE仍11169.43。不能以熵接近target或loss有限当作收敛。四路原训练继续，未停机/重启/改学习率。

为区分Direct训练成功与固定确定性失败的来源，新增独立冻结cycle9动作随机性诊断。原三个0000代表条件×三个动作种子2026102541/42/43，共9完整55s评估；固定checkpoint a9b11de1…，保持条件seed及MJB，动作seed按case ID派生，避免条件排序影响随机流。默认确定性评估保留，既有确定性0/3结果作为对照；不挑最好seed、不替代最终评估口径。

真实checkpoint预检在64个归档observation上做320次推理：同seed逐动作精确复现、异seed改变动作、确定性动作与seed无关、网络不变/0更新/0physics。预检不是轨迹或任务成功证明。三物理评估已启动，初始checkpoint/MJB/dt核验，首批各253/262/305条journal记录；完整结果仍待结束及三类审计。后续首个被动回合三个seed均完成1375动作、55s物理运行并Task/Strict成功；同checkpoint确定性该条件失败。后处理审计仍待原协调器整组三条件结束，不能称3例全审计通过或外推其他条件。

集群路径：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/fixed_direct_cycle09_stochastic_v1`；coordinator590268/590269/590270，evaluator590314/590313/590312，CPU0/1/2，GPU0/1/2推理，行动前须重验。冻结源为SSD sii_rl根目录`runtime/stochastic_evaluation_v1`，原evaluation_audit_v6及live source09/12未修改。

较早CHEQ cycle7代表矩阵现12/12完成、原coordinator803220退出。Strict Direct0/3，Impedance/Admittance/VMC各2/3；被动全失败，两主动参数接口成功。全部55s且物理/filter/torque审计通过，无机器安全违规。VMC短期27.48s、47.1963Nm、无接触NA；长期31.88s、46.6762Nm、6.67185s接触、100%工程舒适比例。Impedance长期接触合规仅4.7492%，不能把成功率等同于舒适性。这是旧source08的cycle7，非当前cycle9、非全30条件排名；最终Tref未选定。

当前cycle9参数矩阵继续；Impedance三条件已全55s并通过物理/filter/torque审计、无机器安全违规：被动失败，短期13.04s/46.2532Nm成功、无接触NA；长期20.04s/51.7783Nm成功、接触7.734s、舒适比例22.0727%。该比例高于旧cycle7的4.7492%，仍低于配对nominal的24.0739%，不能据此称全面优越。contact加速候选已7/12完整精确通过，未部署。下一步复核固定随机策略结果及剩余cycle9评估，结合两种learner的价值漂移再登记在线调整，不能用辅助试验权重或历史ESN替代目标交付。
