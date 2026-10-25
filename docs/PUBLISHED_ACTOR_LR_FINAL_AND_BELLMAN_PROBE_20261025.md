# 四接口 actor 学习率阶段完整复核与 Bellman 目标诊断（2026-10-25）

原登记的 actorLR 两轮8/9已全部结束，四个learner正常退出。降低actor LR到3e-5未产生健康收敛；不能以部分训练成功替代固定策略评估，也不自动继续source13。四路source09 SAC仍继续原训练。

| 接口 | cycle9累计真实步 | Task /30 | Strict /30 | 平均return | 末1000 critic loss | replay Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| direct | 491694 | 12 | 10 | -15.174827 | 4194.208 | 1244.610 |
| impedance | 492221 | 18 | 18 | -0.499599 | 337248.323 | 5974.666 |
| admittance | 493070 | 15 | 15 | -6.927026 | 144168.723 | 2017.731 |
| vmc | 493776 | 17 | 17 | -2.834474 | 973517.622 | 12899.183 |

四路末段critic loss均较7/8增加，固定当前策略/alpha的必要Q上界亦存在超限；上界不是未来alpha变化时的保证。terminal MAE还可能含actor缺失剩余时间造成的混叠，不以零MAE作为收敛要求。训练回合是变化中的策略；CHEQ近期context仍为0.2，不能称为纯RL控制器成功。

Direct固定cycle9的三个预选0000代表条件现已完成：全部55s、Task/Strict均false、失败stage均approach；物理、filter和torque投影审计通过，无机器安全违规。被动/短期无实际人接触，舒适比NA；长期接触7.1099s、舒适比100%，但任务失败，因此SPT为0。三例不足以代表完整30条件。其余三接口同cycle9代表评估已在CPU13顺序执行，不重复Direct。

独立科学review：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/ACTOR_LR_FINAL_SCIENTIFIC_REVIEW_V1.json`。训练、诊断、配对报告和图已复核；原CYCLE09_ALL_TRAINING_REVIEW保留其生成时尚未完成value review的原始字段，不改写历史。

新诊断只研究Bellman目标悲观程度：原版随机两个target critic取最小值，对比全部五个target critic取最小值。Actor仍使用原随机pair，NumPy抽样保留；各arm从相同完整权重、Adam、alpha、RNG、replay/masks恢复，LR、gamma、batch/UTD、reward和控制物理合同不变。这是算法敏感性候选，不是论文原样复现或等价性能优化。

真实Direct9预检各做1次更新：独立重算loss与实际loss精确相等（原版7354.85986328125，候选7116.8037109375），终端target等于reward，all5 target不高于同状态同随机流pair target，父checkpoint不变。三个Bellman辅助测试及三个已有LR测试通过。四接口各2×5000更新已单独登记；辅助权重不保存或导入，不产生新physics。

运行及源：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/bellman_minimum_cycle09_v1`；冻结源在同SSD根目录`runtime/bellman_minimum_probe_v1`。正式physics/MJB、gate、actor输入、公共filter、执行器限制及dt未改。

60样本/67.54秒GPU窗口四卡均值61.03/54.87/56.73/54.52%，最低12/0/12/1%。窗口包含有限辅助更新和正式SAC/固定评估，只能说明该窗口平均超过50%，不代表每时刻或纯在线训练吞吐达标。辅助任务会按登记结束，不能保证集群后续不触发空闲策略。

接触读取加速候选已6/12完整精确通过（Direct/Impedance三类），剩余继续，未部署。nominal矩阵96/120；最终共享Tref尚未选定。训练reward的舒适超幅积分与接触时间合规比例不等价，保留为独立目标一致性问题；本诊断不改reward。指定ESN checkpoint仍缺，最终收敛/全矩阵SPT/ESN比较未完成。

有限诊断现已全部完成：4×2×5000=40,000辅助更新，四进程正常退出；完整恢复state、相同采样流、父replay不变及登记hash验证通过，0physics、无辅助权重导入，图已检查。

| 接口 | 初始Q | pair末Q | all5末Q | 初始terminal MAE | pair末MAE | all5末MAE |
|---|---:|---:|---:|---:|---:|---:|
| direct | 1249.22 | 1352.90 | 1065.74 | 368.55 | 394.76 | 296.48 |
| impedance | 6020.04 | 6468.19 | 5445.43 | 2161.96 | 2422.43 | 2153.96 |
| admittance | 2236.85 | 2408.66 | 1974.45 | 3744.50 | 4246.12 | 3933.32 |
| vmc | 12964.15 | 13066.74 | 11270.86 | 10876.30 | 10896.49 | 9771.59 |

all5相对pair四路Q/terminal MAE均较低，但Admittance的terminal MAE仍比父状态增加；Impedance只略回到初始水平。必要上界超限仍约10.00/39.54/26.39/15.42%，CHEQ最低权重比例仍100%。因此不是修复/收敛证据。暂不导入辅助权重、不自动启动下一在线CHEQ阶段；应完成当前固定策略评估，并将可能的target-pessimism在线试验明确归为算法消融，不能替代忠实已发表基线。
