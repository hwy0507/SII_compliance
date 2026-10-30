# v7 锁定模型在已见棍推训练轨迹上的动作拟合

## 结果

对已锁定的 ESN、RNN、MLP 各三个 seed，在训练集 `rod_00` 的 500 帧纯 teacher 序列上逐帧复放请求动作。脚本先验证 v7 拟合完成收据（75/75 候选、`FIT_AUDIT=passed`、9 个冻结模型）、训练数据 SHA、checkpoint SHA，并逐位确认这 500 条观测及动作标签与原 teacher 轨迹相同，且均为正权重训练行。没有重新训练、选模、物理仿真或访问 final108。

| 方法 | seed | 全序列 requested-action RMSE | 4.2–4.7 s RMSE | 4.7–5.0 s RMSE | 5–8 s RMSE |
|---|---:|---:|---:|---:|---:|
| ESN ridge | 01 | 0.002073 | 0.001746 | 0.006908 | 0.003480 |
| ESN ridge | 02 | 0.002138 | 0.001646 | 0.006082 | 0.003974 |
| ESN ridge | 03 | 0.001936 | 0.001770 | 0.005837 | 0.003405 |
| RNN scratch | 01 | 0.001933 | 0.001578 | 0.006336 | 0.003460 |
| RNN scratch | 02 | 0.002373 | 0.001606 | 0.010536 | 0.003993 |
| RNN scratch | 03 | 0.002429 | 0.001661 | 0.009775 | 0.004407 |
| MLP scratch | 01 | 0.005590 | 0.005281 | 0.017354 | 0.009954 |
| MLP scratch | 02 | 0.005781 | 0.003568 | 0.021876 | 0.009960 |
| MLP scratch | 03 | 0.005341 | 0.004717 | 0.016932 | 0.008962 |

在最靠近棍接触前的 4.2–4.7 s 窗口，三个 MLP 的动作 RMSE 为 ESN/RNN 的约 2.0–3.3 倍。窗口中位数分别为 ESN 0.001746、RNN 0.001606、MLP 0.004717。MLP seed01 虽在固定27中通过 Strict，其该窗口训练拟合误差仍为 0.005281；因此这个误差可以指向 MLP 族在该 teacher 序列上的拟合不足，但不是失败 seed 独有的现象。

按零起始的七维请求动作通道分解，MLP seed 的窗口平均 RMSE在通道0为0.001778，ESN/RNN为0.002045/0.001581，故 slowdown 通道并未显示 MLP 的额外误差；MLP 的差距主要在 residual 通道1（0.009275，对ESN/RNN的0.002801/0.001816）和通道5（0.005883，对0.002204/0.002242）。其余通道平均值差异较小。该定位有助于后续核查轴向动作拟合/网络容量，但通道误差不能单独推出哪个关节或物理接触导致穿透。此时间窗内若干 teacher residual 通道变化极小，故以绝对RMSE报告，不对接近常量的通道计算误导性的归一化误差。

这一结果为“MLP 对高动态棍推 teacher 动作拟合更差”提供了直接的已见训练集证据；它仍不能证明该差异导致 seed02/03 穿透。动作误差与闭环动力学、公共滤波器及窄安全裕度之间的因果关系尚未由该离线复放识别。fixed27 仍是 Task 27/27、Strict 25/27；ESN/RNN 各 9/9，MLP 7/9，MLP seed02/03 的冻结门穿透失败继续保留。禁止将训练拟合结果当作成功率或安全性证明。

## 复现与边界

- 脚本：[diagnose_contact_yield_v7_locked_rod_train_fit_20261031.py](../code/mujoco_6d_vmc_benchmark/experiments/diagnose_contact_yield_v7_locked_rod_train_fit_20261031.py)
- 哈希绑定结果：[CONTACT_YIELD_V7_LOCKED_ROD_TRAIN_FIT_20261031.json](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_LOCKED_ROD_TRAIN_FIT_20261031.json)
- 结果 JSON 绑定数据集 SHA256 `d771433db06103edb3e33264b8040d059c4df6fb19faa66043f458c61457f42a`。逐模型逐窗口七动作通道 RMSE、最大绝对误差、4.68 s 动作和模型 checkpoint hash 均在 JSON 中。
- `new_physics_steps=0`、`new_optimizer_updates=0`、`model_reselection=false`。六条纯 teacher validation仍是原登记选模依据；本分析没有据结果重选模型。
- 本轮已重新 fetch 并读取 GitHub：实时 `main=7ae9d9af`，`baseline=f6e8f8c2`；远端 main 的独立 history88 进度已通过普通 merge 与本地记录共同保留。
