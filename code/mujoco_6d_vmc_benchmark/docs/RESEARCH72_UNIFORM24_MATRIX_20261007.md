# office-v6 完全统一单模型矩阵（2026-10-07）

## 口径

上一版汇总把神经网络/RL 的三个 seed 合并为 72 条，而经典控制器和 teacher 只有一个冻结模型、24 条条件，因此出现了 `/72` 与 `/24` 混用。本文件给出论文主表采用的统一口径：

- 所有方法都使用相同的 24 个 `heldout_000`–`heldout_023` 条件；
- 每个 family 只取一个冻结模型；神经网络和 RL 固定采用模型锁中列出的第一个、也是 seed `2026100301` 的模型，经典控制器/teacher/zero 使用其唯一冻结模型；
- 选择规则只看模型锁的固定顺序，不查看任务结果，不按成功率挑 seed；
- 所有指标直接从同一批 24 条原始 `REPORT.json` 回合重算，没有新仿真、没有更改 gate、环境、actor 输入或执行器限制。

评测仍是服务器上的 frozen office-v6、MuJoCo 3.11.0、正式 `dt=5e-5`、55 s horizon。`Task` 和 `Strict` 的分母全部为 24；`short` 保留提前终止回合。RMSE 是任务阶段目标的时间加权误差，必须和成功率一起解释。

原始报告：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/final_delivery_v1/comparison/REPORT.json`

报告 SHA256：`100341d7cd42cac944fb5f28849c6028890faf160adfdd27201b0ed4d3fb8d45`

## 统一 24 条条件结果

| 方法 | 固定模型 | Task | Strict | RMSE (mm) | 峰值力矩 (Nm) | 峰值速度 (m/s) | Work (J) | Short |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ESN | `readout_refit_esn_2026100301` | 20/24 | 16/24 | 31.451 | 49.945 | **0.360** | 189.933 | 0 |
| Matched RNN | `readout_refit_matched_rnn_2026100301` | 16/24 | **15/24** | **32.678** | 49.160 | 0.375 | 184.643 | 0 |
| Matched MLP | `gated_matched_mlp_2026100301_point` | 12/24 | 11/24 | 43.555 | 47.077 | 0.376 | 188.389 | 1 |
| Ordinary RNN | `readout_refit_ordinary_rnn_2026100301` | 14/24 | 13/24 | 39.322 | 47.272 | 0.396 | 192.873 | 0 |
| Ordinary MLP | `ordinary_mlp_2026100301_point_lr0001` | 15/24 | 11/24 | 44.911 | 47.673 | 0.370 | 165.259 | 0 |
| Memoryless | `gated_memoryless_2026100301` | 18/24 | 14/24 | 39.397 | 48.768 | 0.379 | 190.084 | 0 |
| Classical VMC | `vmc_11` | 0/24 | 0/24 | 32.329 | 38.585 | 0.377 | 74.015 | 0 |
| Classical admittance | `admittance_03` | 0/24 | 0/24 | 32.376 | 40.020 | 0.376 | 162.337 | 0 |
| Classical impedance | `impedance_02` | 0/24 | 0/24 | 54.924 | 39.023 | 0.384 | 21.138 | 0 |
| Parameter VMC RL | `office_rl_parameter_vmc_2026100301` | 0/24 | 0/24 | 28.834 | 37.948 | 0.377 | 78.105 | 0 |
| Parameter admittance RL | `office_rl_parameter_admittance_2026100301` | 0/24 | 0/24 | 30.124 | 40.003 | 0.378 | 152.520 | 0 |
| Parameter impedance RL | `office_rl_parameter_impedance_2026100301` | 0/24 | 0/24 | 34.314 | 39.272 | 0.379 | 66.212 | 0 |
| Direct metric RL | `office_rl_direct_metric_2026100301` | 0/24 | 0/24 | 74.294 | 40.932 | 0.327 | 212.689 | 0 |
| Direct office-task RL | `office_rl_direct_office_task_2026100301` | 0/24 | 0/24 | 154.561 | 49.219 | 0.398 | 191.386 | 0 |
| Enhanced teacher | `teacher_09` | 24/24 | 13/24 | 41.643 | 50.894 | 0.386 | 176.789 | 0 |
| Nominal zero | `nominal_zero` | 0/24 | 0/24 | 26.846 | 37.430 | 0.377 | 63.280 | 0 |

## 解释

在完全统一的单模型/24 条件口径下，ESN 的 task 为 20/24，strict 为 16/24，速度均值最低；RNN 的 strict 为 15/24、RMSE 为 32.678 mm。经典控制器、参数 RL 和直接动作 RL 在这 24 条组合条件上均未完成 task，因此它们的低 RMSE 不能作为成功或柔顺性优势。

原始全三 seed 的 72 条结果仍保留在 `RESEARCH72_FINAL_RESULTS_20261007.md`，作为 seed 敏感性附录；论文主表应使用本文件的统一 `/24` 矩阵，避免把不同分母并排比较。
