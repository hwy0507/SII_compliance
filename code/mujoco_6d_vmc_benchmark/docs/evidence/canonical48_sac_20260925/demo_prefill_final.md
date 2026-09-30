# SAC固定最终8192步：独立审计

分支 `demo_prefill`，seed20260923；全8192在线Gym/reward、实际replay槽、全部8092次sample索引/online统计及actor/critic/entropy实际8092步已核。固定最终SAC模型与初始模型/normalizer来源绑定，非PPO384更新规则。

| 条件 | task/gate | stage | 当前阶段endpoint mm | lift mm | 步数/实际s |
|---|---|---:|---:|---:|---|
| train/zero | False/False | 3 | 187.670 | 60.324 | 600/24.00 |
| train/sac | False/False | 1 | 136.736 | -0.000 | 600/24.00 |
| validation/zero | True/True | 3 | 7.068 | 228.500 | 600/24.00 |
| validation/sac | False/False | 1 | 212.003 | -0.000 | 600/24.00 |

示范额外预算与实际采样数量、全部产物hash见同名JSON。失败和安全早停全部保留，不跨阶段平均endpoint。

sample实际返回张量由冻结runtime中的逐值断言核对，本离线审计核归档槽位、索引和当时仅online统计，并不声称未保存的sample张量、TD target、loss或梯度数值被独立重放。终态next仅为mask=0的占位；预算partial保留真next。

单seed、单训练fixture与小预算结果不代表收敛、泛化或论文复现；没有把低频训练日志当作50µs物理子步主表。
