# v7 MLP 全候选棍推训练拟合复放

## 结果

对v7注册的36个MLP候选逐一复放训练集`rod_00`的500帧纯teacher序列。复放前验证了75候选拟合完成、FIT_AUDIT通过、9个模型已冻结，以及数据、teacher轨迹和每个候选checkpoint的哈希。`rod_00`的观测与requested-action标签逐位匹配原teacher演示，全部是正权重训练行。

| seed | validation选中候选 | 选中模型rod00 RMSE | 36候选中的最低rod00 RMSE | 该最低候选 | 选中/最低比 |
|---:|---|---:|---:|---|---:|
| 2026102801 | candidate05 | 0.005590 | 0.005497 | candidate08 | 1.017 |
| 2026102802 | candidate03 | 0.005781 | 0.005763 | candidate02 | 1.003 |
| 2026102803 | candidate08 | 0.005341 | 0.005341 | candidate08 | 1.000 |

全部36个候选在该训练序列上的RMSE范围为0.005341–0.006112。按原登记的六条纯teacher validation MSE选出的模型，几乎也位于rod00训练拟合最优处；所以这两者间的差距不能合理归因于validation选模误选了一个明显较差的候选。上一项锁定模型复放中，ESN/RNN全序列RMSE约为0.00194–0.00243，明显低于MLP约0.00534–0.00578。

## 候选搜索范围

神经候选均训练32,000次更新。MLP网格为4个学习率（`1e-4`、`3e-4`、`1e-3`、`3e-3`）乘3个weight decay（`0`、`1e-5`、`1e-4`），每个seed共12个候选。所有MLP候选都固定使用单隐层宽度128、5,504个可训练参数；本轮没有搜索宽度、深度或时序输入。作为架构背景，v7的128单元RNN有21,888个可训练参数，ESN有3,780个可训练readout参数及128维固定reservoir。候选数与更新预算公平，不等于参数量或FLOPs相同。

这使目前最直接的待检验项变成MLP容量与时序表征，而不是已搜索范围内的学习率/weight decay。它仍是待检验解释：单条已见训练序列上的动作误差不能确定闭环穿透根因，也不能单独判断更宽的无状态MLP是否足够。

## 复现与边界

- 脚本：[diagnose_contact_yield_v7_mlp_candidate_grid_train_fit_20261031.py](../code/mujoco_6d_vmc_benchmark/experiments/diagnose_contact_yield_v7_mlp_candidate_grid_train_fit_20261031.py)
- 哈希绑定结果：[CONTACT_YIELD_V7_MLP_CANDIDATE_GRID_TRAIN_FIT_20261031.json](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_MLP_CANDIDATE_GRID_TRAIN_FIT_20261031.json)
- 数据集SHA256：`d771433db06103edb3e33264b8040d059c4df6fb19faa66043f458c61457f42a`。JSON保留36候选逐模型逐窗口RMSE、validation MSE、架构元数据和checkpoint哈希。
- `new_physics_steps=0`、`new_optimizer_updates=0`、`model_reselection=false`。报告中的“最低训练拟合候选”是事后诊断标签，没有改动模型锁。
- fixed27仍为Task 27/27、Strict 25/27；ESN/RNN各9/9，MLP 7/9。此复放不是新的闭环测试，也不是unseen test结果。
- 本轮容器的`/proc/self/cgroup`指向Chromium scope；实际读数为`memory.max=max`、`memory.swap.max=max`，且`cpu.max`不可用，不满足登记要求的MemoryMax≤3GiB、swap=0和CPU配额，故没有启动新的拟合或物理作业。GitHub本轮已重新fetch并读日志，main=`39d5363e`、baseline=`f6e8f8c2`且无新提交。
