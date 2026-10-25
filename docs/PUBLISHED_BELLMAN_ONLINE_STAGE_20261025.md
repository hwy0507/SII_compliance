# Bellman目标在线试验及Direct固定随机评估完成（2026-10-25）

当前新阶段已真实启动，不再只是source14准备。原四路CHEQ actorLR阶段在cycle9正常结束后，依据完整优化审计、有限配对target-min诊断及真实恢复验证，登记两轮10/11在线敏感性试验。两轮是有限阶段审查点，不是整体训练预算或收敛条件。目标仍为充分训练、健康优化和公平最终比较。

固定Direct9的原三个代表条件×三个预登记动作seed共9回合现全部55s完成，物理/filter/torque审计完成：Task9/9、Strict7/9、机器安全违规2/9。两个违规为短期条件外部穿透超过原0.2mm门槛，保留失败。被动3/3 Strict、短期1/3、长期3/3；原确定性同三个条件0/3仍保留。长期三seed完成时间53.40/52.84/25.28s，接触舒适77.38%/80.59%/100%，明显有随机差异。被动和短期无实际人接触，舒适比例NA。三条件九试验不是完整30条件成功率，不挑最好seed、不宣称收敛、不替代最后的评估口径，最终Tref仍未选择。PNG/PDF已生成、图已检查。

本轮有明确的科学决策更新：无需等剩余参数固定评估全部结束才启动候选，因其仍读取不变的父cycle9 checkpoint；后续训练不会改变这些结果，原评估继续、没有取消或重选。候选选择依据完成的优化审计和预登记配对目标诊断，不依赖尚未产生的参数评估结果。Direct三seed评估全部结束并释放CPU后才派发。

在线唯一算法干预为Bellman目标取全部五target critic的最小值；actor仍原随机pair。保留父actor/critic/targets、Adam、alpha、RNG、replay/masks、actorLR3e-5、criticLR3e-4、gamma、batch16384和UTD2。只重新开始不同算法阶段的plateau聚合，父历史原样保存，不导入辅助权重。名称应为CHEQ-core all-five-target敏感性变体，不称论文原样或性能等价优化。未修改physics/MJB、gate、actor输入、公共filter、执行器限制或dt。

每接口仍9个仿真worker、一张GPU。Direct CPU0–9，Impedance learner移至CPU54、worker14–22，给仍在途的固定评估保留CPU13；Admittance26–35，VMC39–48。其余资源保持。CPU重定位检查保留worker容量、禁止接口间重叠，7个阶段/资源测试和2个诊断target测试通过。新诊断器按checkpoint记录的target规则计算TD，避免把all5继续按pair审计。

四新learner启动及真实更新已核验：Direct1325445、Impedance1328516、Admittance1333006、VMC1338945（行动前重验）；dispatcher1316612正常完成、archive1349161在途。四EXECUTION确认target_count5、actorLR3e-5、9workers，四父state保留收据通过；首36个模拟器model/dt/plan身份均核验。原四SAC09继续，原参数固定评估继续；没有STOP旧在途任务。

60样本/67.47s窗口四卡平均利用率40.63/36.95/37.95/30.93%，最低0/5/0/5%，无辅助GPU学习。新四路分别新增1186/1051/1150/1165真实步与2372/2102/2300/2330更新；四SAC分别新增551/509/302/274步。GPU≥50%尚未实现，不能把此前辅助窗口当作当前正式训练吞吐。没有为提高数字改变本阶段batch/UTD。

审计1346884、配对review1346887已确认在等待完整10/11归档，比较父9→10、父9→11、10→11；3小时只限制观察器，不停止训练。科学结论仍需完整阶段审查，启动与数值有限均不代表收敛。contact读取候选现9/12完整精确通过未部署，不能凭局部验证提前迁入live source14。

集群根目录BASE：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。训练在`BASE/runs/bellman_minimum_online_seed20261025_v1`，科学决策`BASE/runs/BELLMAN_ONLINE_SCIENTIFIC_REVIEW_V1.json`，完整随机策略审计`BASE/runs/fixed_direct_cycle09_stochastic_v1/FINAL_REVIEW.json`，runtime为`BASE/runtime/source_train14`，调度器/审计器分别`bellman_online_dispatch_v1`、`bellman_online_audit_v1`。runtime manifest中的prepared_only保留构建时真实状态；实际启动由新登记和EXECUTION证明，不改写冻结manifest。

最终收敛、全训练集SPT与指定ESN比较仍未完成。
