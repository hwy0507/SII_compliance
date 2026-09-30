# paired PPO8192训练行为诊断

完整的逐episode return/阶段关联，以及训练探索与确定性train策略分开的限速统计，见更新报告`PAIRED_TRAINING_BEHAVIOR_DIAGNOSIS_20260924_REVISED.md`及同名JSON。

这是对已审计两条seed20260923训练日志的描述性诊断，使用全部8192条实际transition和各自train fixture的zero/PPO最终评估；没有读取validation数据进行选择，没有重训、调参或更换checkpoint。统计是相关性，不是因果解释。

两分支都使用相同potential reward、8192步和PPO预算，但action接口不同：parameter6请求六维参数，实际执行仍是VMC生成的action7；direct7直接输出action7。训练日志中的动作是Gym边界后实际动作，无法反推出策略高斯分布的未clip样本。

| 训练日志 | 总reward | 阶段样本0/1/2/3 | 实际slowdown均值 / P95 / 最大 | yield绝对值均值 / P95 | yield饱和比例 |
|---|---:|---|---:|---:|---:|
| parameter6 | 4.2773 | 456/737/217/6782 | 0.0864 / 0.2390 / 0.3987 | 0.0601 / 0.2952 | 0 |
| direct7 | −23.2649 | 293/3148/626/4125 | 0.0654 / 0.2860 / 0.7141 | 0.1466 / 0.3695 | 0 |

parameter6六轴log-scale的各轴最小值范围约−0.451至−0.333，各轴最大值范围约+0.312至+0.477，均未达到声明的±log(2)幅值边界。这里尚未统计逐步变化率，不能据幅值未饱和推断rate limiter是否激活。direct7的参数字段固定为名义值，只作inactive metadata，不能与parameter6的K偏移量比较。

在train fixture的最终评估中，parameter6 PPO相对其zero VMC的实际action幅度更小：slowdown均值0.0253 vs 0.0616，yield绝对值均值0.0164 vs 0.0416；两者均无yield饱和。该条件task/gate均通过；按zero→PPO顺序，endpoint为5.639→4.799 mm，单对象外部力峰217.108→217.108 N。direct7 PPO相对zero7从全零执行动作变为slowdown均值0.0106、yield绝对值均值0.1372，仍无饱和；对应train task/gate均失败，endpoint 187.670→192.173 mm，力峰217.614→524.452 N。

这些数值只说明最终train fixture上的动作和结果伴随关系。parameter6训练样本阶段3占比更高、direct7阶段1占比更高，说明两次在线轨迹所见阶段分布不同；不能把样本分布差异归因于接口本身，更不能据此推断跨fixture或验证性能。zero与PPO比较使用同一train fixture，但parameter6 zero是解析VMC nominal，direct7 zero是action7全零，二者物理含义不同。

完整训练episode的任务标签、奖励重建、VMC重播和partial末next已在独立final audit中核验；本诊断不重新计算奖励，也不把四项验证数据纳入统计。训练reward总和只用于同reward定义下的日志描述，不比较两种控制接口的reward大小来宣称方法优劣。
