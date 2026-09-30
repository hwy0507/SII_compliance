# 配对PPO训练行为诊断：训练探索与确定性策略分开统计

只使用seed20260923的全部8192训练transition和最终train/zero、train/PPO。源hash、每episode日志hash与独立审计一致；没有读取validation轨迹或六条件验证，没有调参、重新训练或选择checkpoint。

| parameter6统计范围 | transition | 限速轴更新 / 总轴更新 | 至少一轴限速的步数比例 | K幅值触限比例 |
|---|---:|---:|---:|---:|
| training | 8192 | 13893/49152 (28.265%) | 85.828% | 0.000% |
| train_zero | 600 | 0/3600 (0.000%) | 0.000% | 0.000% |
| train_ppo | 600 | 98/3600 (2.722%) | 11.500% | 0.000% |

限速按每个episode的初态logscale=0逐步重建，核对实际更新等于clip后的目标差。幅值未触0.5×/2×界不代表限速器未激活；训练探索与最终确定性策略必须分别解读。

| 模式/范围 | slowdown均值 | slowdown恰为0比例 | yield绝对均值 | yield近界比例 |
|---|---:|---:|---:|---:|
| parameter6/training | 0.086388 | 2.222% | 0.060106 | 0.000% |
| parameter6/train_zero | 0.061567 | 2.167% | 0.041573 | 0.000% |
| parameter6/train_ppo | 0.025302 | 2.167% | 0.016374 | 0.000% |
| direct7/training | 0.065428 | 54.651% | 0.146613 | 0.000% |
| direct7/train_zero | 0.000000 | 100.000% | 0.000000 | 0.000% |
| direct7/train_ppo | 0.010618 | 86.000% | 0.137221 | 0.000% |

| 完整训练episode组 | episode数 | mean未折扣reward和 | mean折扣return | mean slowdown | final stage计数0/1/2/3 |
|---|---:|---:|---:|---:|---|
| parameter6/task=False | 6 | -2.275692 | 0.066666661 | 0.151122 | 0/0/0/6 |
| parameter6/task=True | 7 | 2.614618 | 0.314977325 | 0.033715 | 0/0/0/7 |
| direct7/task=False | 13 | -1.768923 | 0.066666661 | 0.064285 | 0/2/1/10 |

成功与失败组的reward差异包含终端基础奖励，不能当作额外独立性能指标。终端基础reward为0的完整轨迹，其折扣return受potential恒等式约束为−Φ(initial)，与其最终stage不同并不矛盾；invalid或upstream都可能触发−5终端基础奖励，不满足这个零基础奖励条件。两条392步partial各自保留在JSON，未混入完整episode组；其有限前缀return不等于完整任务return。本段已作文字澄清，未重算数值，保留原工具和JSON的hash来源。

| 最终train/zero→train/PPO | task | 当前阶段endpoint mm | 外部单对象力峰N | 同一最终target |
|---|---|---:|---:|---|
| parameter6 | True→True | 5.639→4.799 | 217.108→217.108 | True |
| direct7 | False→False | 187.670→192.173 | 217.614→524.452 | True |

parameter6的zero是名义解析VMC，direct7的zero是全零执行动作。执行动作及slowdown既受策略也受反馈轨迹影响，成功组较低slowdown或确定性PPO动作较小均是相关性，不能仅凭这些轨迹建立因果解释或泛化结论。

重现工具：`tools/diagnose_paired_train_behavior_20260925.py`，SHA256 `66bfd996a4929369dd41b9b4ac90dbdcca0e1774e166091289645d970212ad0a`。完整逐episode统计、公式、日志/审计hash见同名JSON。
