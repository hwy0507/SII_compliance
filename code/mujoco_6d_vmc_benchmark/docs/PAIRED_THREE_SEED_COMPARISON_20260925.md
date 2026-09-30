# 配对PPO：三个预声明训练seed的最终对照

全部六run完成独立审计，固定每run8192步/384更新，最终模型seed显式匹配。旧报告、新报告、flat奖励审计及模型/normalizer/manifest hash均逐项绑定；原执行源、基础协议hash、fixture、资产和除seed外的学习参数一致。未选择中间checkpoint，未丢弃失败。

| 训练seed | 模式 | 完整训练episode task/gate成功数 | 完整episode数 | partial步数 |
|---|---|---|---:|---|
| 20260923 | parameter6 | 7/7 | 13 | [392] |
| 20260923 | direct7 | 0/0 | 13 | [392] |
| 20260924 | parameter6 | 4/4 | 13 | [392] |
| 20260924 | direct7 | 0/0 | 13 | [392] |
| 20260925 | parameter6 | 4/4 | 13 | [392] |
| 20260925 | direct7 | 0/0 | 13 | [392] |

训练episode来自不断更新且带采样探索的策略，其成功数不能当作最终模型的独立重复测试；三个训练seed才是本对照的训练重复单位。

| seed | 模式 | 最终评估 | task/gate | stage | 当前阶段endpoint mm | lift mm | 步数/实际s/早停 |
|---|---|---|---|---:|---:|---:|---|
| 20260923 | parameter6 | train/zero | True/True | 3 | 5.639 | 242.989 | 600/24.00/False |
| 20260923 | parameter6 | train/ppo | True/True | 3 | 4.799 | 243.871 | 600/24.00/False |
| 20260923 | parameter6 | validation/zero | False/False | 3 | 111.724 | 129.550 | 600/24.00/False |
| 20260923 | parameter6 | validation/ppo | False/False | 3 | 107.095 | 135.123 | 600/24.00/False |
| 20260923 | direct7 | train/zero | False/False | 3 | 187.670 | 60.324 | 600/24.00/False |
| 20260923 | direct7 | train/ppo | False/False | 3 | 192.173 | 59.196 | 600/24.00/False |
| 20260923 | direct7 | validation/zero | True/True | 3 | 7.068 | 228.500 | 600/24.00/False |
| 20260923 | direct7 | validation/ppo | False/False | 3 | 17.185 | 235.694 | 600/24.00/False |
| 20260924 | parameter6 | train/zero | True/True | 3 | 5.639 | 242.989 | 600/24.00/False |
| 20260924 | parameter6 | train/ppo | False/False | 3 | 70.332 | 179.512 | 600/24.00/False |
| 20260924 | parameter6 | validation/zero | False/False | 3 | 111.724 | 129.550 | 600/24.00/False |
| 20260924 | parameter6 | validation/ppo | False/False | 3 | 113.158 | 118.819 | 600/24.00/False |
| 20260924 | direct7 | train/zero | False/False | 3 | 187.670 | 60.324 | 600/24.00/False |
| 20260924 | direct7 | train/ppo | False/False | 1 | 44.875 | -0.000 | 600/24.00/False |
| 20260924 | direct7 | validation/zero | True/True | 3 | 7.068 | 228.500 | 600/24.00/False |
| 20260924 | direct7 | validation/ppo | False/False | 1 | 49.623 | -0.000 | 600/24.00/False |
| 20260925 | parameter6 | train/zero | True/True | 3 | 5.639 | 242.989 | 600/24.00/False |
| 20260925 | parameter6 | train/ppo | False/False | 3 | 89.420 | 167.314 | 600/24.00/False |
| 20260925 | parameter6 | validation/zero | False/False | 3 | 111.724 | 129.550 | 600/24.00/False |
| 20260925 | parameter6 | validation/ppo | False/False | 3 | 108.059 | 133.834 | 600/24.00/False |
| 20260925 | direct7 | train/zero | False/False | 3 | 187.670 | 60.324 | 600/24.00/False |
| 20260925 | direct7 | train/ppo | False/False | 0 | 55.733 | -0.000 | 600/24.00/False |
| 20260925 | direct7 | validation/zero | True/True | 3 | 7.068 | 228.500 | 600/24.00/False |
| 20260925 | direct7 | validation/ppo | False/False | 3 | 24.173 | 208.408 | 600/24.00/False |

| 最终PPO条件 | parameter6成功seed数 | direct7成功seed数 |
|---|---|---|
| train/ppo | 1/3 | 0/3 |
| validation/ppo | 0/3 | 0/3 |

stage1仍是抓取对齐、尚未闭爪抬升；stage2闭爪，stage3抬升。endpoint指当时阶段目标，不能跨stage平均后宣称共同精度改善。零控制也不同：parameter6 zero是训练名义参数的解析VMC，direct7 zero是全零action7。

direct7的seed20260923最终train/validation均到stage3，seed20260924均停在stage1。对应两个fixture的同模式zero原始轨迹/MJB已精确核对，seed20260924最终模型部署输入回放也与存档执行动作逐值一致，证据hash已绑定到JSON。因此这里看到的是改变训练seed后初始化/采样整体不同所伴随的策略差异，不能分离归因给其中一个因素，也不能据此声称同seed不可复现。部署输入回放不是新造的闭环物理轨迹。

这套配方只在同一个训练fixture学习，每分支三个seed合计24576条在线transition，无示范数据注入。parameter6含VMC隐状态、反馈先验与六维参数接口，direct7直接输出七维控制；结果不能解释成只改变网络输出维度的消融。三个seed仅描述小预算配方的重复性，不能保证收敛或跨场景泛化。

本报告不包含六条件部署矩阵，也不把训练日志中的低频力矩/速度混入50µs子步主表。后续六fixture应先按训练seed聚合，再描述三个训练seed，不能把相关fixture或训练episode当作额外独立训练重复。

完整数值和每个原报告/模型hash见同名JSON；汇总工具SHA256 `d51ee659335e5a0c6a91e90e06cfa368626fa8a011d8f0a23967cb7758b234f2`。
