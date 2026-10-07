# office-v6 最终公平比较结果（2026-10-07）

> 论文主表请使用[完全统一的单模型/24条件矩阵](RESEARCH72_UNIFORM24_MATRIX_20261007.md)。本文件下方原有的 `/72` 汇总保留为三 seed 敏感性结果；它不应与 `/24` 的经典控制器行直接并排作为唯一主表。

## 评测闭合

最终冻结后一次性开启 24 个 held-out 条件，评测 38 个冻结模型，共 912/912 条完整登记回合；没有缺失 pair。正式运行使用服务器上的冻结 a3b8c97 源、dt=5e-5、55 s horizon、原 gate、48D 本体输入和执行器限制。最终物理批次的 `SUMMARY.json` SHA256 为 `e6d29024bf0e80df16554325193f7a94c6ba8e1193cc31f168a08c9da7346660`，统一报告 `REPORT.json` SHA256 为 `100341d7cd42cac944fb5f28849c6028890faf160adfdd27201b0ed4d3fb8d45`。

最终任务成功总数为 284/912，strict success 为 218/912。最终交付后处理状态为 `complete`；15 个 RL 模型的 360/360 个物理回合完成独立冻结 actor replay，没有缺失回放。最终报告保留失败、提前终止和未暴露接触条件；没有按结果删除回合。

服务器证据根：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`

- 物理矩阵：`final_evaluation_v1/SUMMARY.json`
- 统一统计与原始逐模型行：`final_delivery_v1/comparison/REPORT.json`
- 最终回放、图和三视角媒体：`final_delivery_v1/`
- 开封收据：`FINAL_UNSEAL_RECEIPT.json`；模型锁由最终 transition 固定并核验

## 统一矩阵

下表是每个 family 在全部登记条件和 seed 上的均值。RMSE 是当前 task-stage goal 的时间加权距离，不是共同时间索引轨迹误差；因此必须和 task/strict 一起解读。`short` 是物理提前终止回合数，已保留在成功率分母中。

| Family | Task | Strict | RMSE (mm) | Peak torque (Nm) | Peak speed (m/s) | Work (J) | Short |
|---|---:|---:|---:|---:|---:|---:|---:|
| ESN (readout refit) | 60/72 | 43/72 | 33.780 | 49.734 | 0.372 | 191.645 | 0 |
| Matched RNN | 58/72 | 44/72 | 33.500 | 49.729 | 0.378 | 187.824 | 0 |
| Matched MLP | 28/72 | 26/72 | 41.465 | 46.826 | 0.381 | 179.892 | 10 |
| Ordinary RNN | 50/72 | 42/72 | 35.630 | 48.636 | 0.386 | 194.602 | 0 |
| Ordinary MLP | 21/72 | 17/72 | 43.760 | 44.027 | 0.394 | 145.154 | 0 |
| Memoryless | 43/72 | 33/72 | 39.740 | 48.634 | 0.381 | 186.259 | 12 |
| Parameter VMC RL | 0/72 | 0/72 | 28.415 | 38.270 | 0.377 | 77.657 | 0 |
| Parameter admittance RL | 0/72 | 0/72 | 29.453 | 40.267 | 0.377 | 156.159 | 0 |
| Parameter impedance RL | 0/72 | 0/72 | 44.034 | 38.407 | 0.381 | 54.568 | 0 |
| Direct metric RL | 0/72 | 0/72 | 288.026 | 50.311 | 0.400 | 222.676 | 4 |
| Direct office-task RL | 0/72 | 0/72 | 274.215 | 54.403 | 0.452 | 252.719 | 11 |
| Classical VMC | 0/24 | 0/24 | 32.329 | 38.585 | 0.377 | 74.015 | 0 |
| Classical admittance | 0/24 | 0/24 | 32.376 | 40.020 | 0.376 | 162.337 | 0 |
| Classical impedance | 0/24 | 0/24 | 54.924 | 39.023 | 0.384 | 21.138 | 0 |
| Enhanced teacher | 24/24 | 13/24 | 41.643 | 50.894 | 0.386 | 176.789 | 0 |
| Nominal zero | 0/24 | 0/24 | 26.846 | 37.430 | 0.377 | 63.280 | 0 |

## 可支持的结论

- 纯 ESN 的 task success 为 83.3%（60/72），高于 matched RNN 的 80.6%（58/72）、matched MLP 的 38.9% 和 memoryless 的 59.7%。
- ESN 的均值 RMSE 为 33.780 mm，低于 matched MLP、ordinary MLP、ordinary RNN 和 memoryless；matched RNN 为 33.500 mm，略低于 ESN。
- ESN 的峰值速度均值 0.372 m/s，在学习模型中最低；峰值力矩 49.734 Nm，与 matched RNN 的 49.729 Nm 几乎相同，低于 direct RL，但高于普通 MLP/部分经典控制器。
- strict success 为 ESN 43/72（59.7%），matched RNN 为 44/72（61.1%）。因此最终证据支持 ESN 的任务完成率和速度/RMSE 综合表现，但不支持“所有指标全面优于所有 baseline”。
- 经典控制器和 RL 调参/直接动作组在这套组合 office-v6 条件上均为 0 strict；它们仍作为完整 baseline 报告，不能用低 RMSE 替代任务成功。

## 局限与审计口径

严格门槛保持不变：外部穿透 ≤0.2 mm、原始动作与变化率限制、纯本体 actor 输入。接触力统计只在共同 strict、完整且实际暴露的 pair 上描述，不能作因果优越性结论。RMSE 不是共同参考轨迹误差；峰值接触力和早期球撞击的数值收敛也不等于硬件安全证明。报告没有构造标量 winner score，也没有声称 passivity、human safety 或真实机器人泛化。

正式批次的 912 条物理回合和 360 条 RL 独立回放均已完成；原始轨迹、逐子步指标、动作/储备池重放、源/config/seed/hash 和失败原因保存在服务器根目录。该结果可以作为 RAL 论文的诚实结果表和方法审计基础，但摘要应明确 ESN 的优势是任务成功率与速度/RMSE 权衡，而不是 strict 或峰值力矩的全面领先。
