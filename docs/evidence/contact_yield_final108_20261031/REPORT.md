# 特化场景 unseen108：ESN、MLP、RNN 正式结果（2026-10-31）

本报告由已完成的 108 格正式矩阵和独立复核收据生成；没有重新拟合、重新选模或重新运行物理。完整逐回合证据仍以被忽略的本地结果目录中的 `FINAL_REVIEW.json` 为准，仓库提交只保存本摘要、表格、图和哈希。

## 结论

- 正式矩阵 108/108 完成；`execution.json` 为 `complete_pending_independent_review`，`FINAL_REVIEW.json` 为 `verified_complete_isolated_unseen_matrix`。独立 replay 覆盖 108/108 格，actor/filter replay 最大误差均为 0。
- 全矩阵双成功回合的共同 `T_ref = 8.92 s`。SPT 只在同一回合同时 Task 成功和 Strict 成功时计算；SPT 越高表示相对共同参考完成得更快。
- 人舒适度为 NA：本轮没有人体力/接触通道。扰动接触代理只在完整收据中单列，不能写成人体舒适度。
- 测试条件是登记的插值组合，不是广义 OOD；终态成功由 13 个 25 Hz 状态覆盖 0.48 s 确认，不等价于逐物理子步的连续保持证明。

## 按方法汇总

| 方法 | 回合 | Task | Strict | 双成功 | 双成功 SPT | 平均峰值力矩 (Nm) | 机器合规率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| esn_ridge | 36 | 35/36 (97.2%) | 32/36 (88.9%) | 32/36 | 0.7913 | 42.37 | 97.2% |
| mlp_scratch | 36 | 36/36 (100.0%) | 25/36 (69.4%) | 25/36 | 0.7548 | 41.70 | 86.1% |
| rnn_scratch | 36 | 36/36 (100.0%) | 32/36 (88.9%) | 32/36 | 0.7614 | 42.51 | 100.0% |

机器合规率和峰值力矩保留全部回合作为分母；MLP 的平均峰值力矩最低，但其机器合规率和棍推 Strict 明显较低。ESN 与 RNN 的 pooled Strict 均为 32/36；RNN 机器合规率为 36/36，ESN 为 35/36。

## 按场景汇总

| 方法 | 场景 | Task | Strict | 双成功 SPT | 平均峰值力矩 (Nm) | 机器合规率 |
|---|---|---:|---:|---:|---:|---:|
| esn_ridge | ball | 12/12 (100.0%) | 9/12 (75.0%) | 0.7178 | 39.54 | 100.0% |
| esn_ridge | corner | 11/12 (91.7%) | 11/12 (91.7%) | 0.7332 | 51.78 | 91.7% |
| esn_ridge | rod | 12/12 (100.0%) | 12/12 (100.0%) | 0.8997 | 35.80 | 100.0% |
| mlp_scratch | ball | 12/12 (100.0%) | 9/12 (75.0%) | 0.7070 | 39.29 | 100.0% |
| mlp_scratch | corner | 12/12 (100.0%) | 12/12 (100.0%) | 0.7298 | 50.47 | 100.0% |
| mlp_scratch | rod | 12/12 (100.0%) | 4/12 (33.3%) | 0.9371 | 35.33 | 58.3% |
| rnn_scratch | ball | 12/12 (100.0%) | 9/12 (75.0%) | 0.6912 | 39.36 | 100.0% |
| rnn_scratch | corner | 12/12 (100.0%) | 12/12 (100.0%) | 0.7314 | 50.76 | 100.0% |
| rnn_scratch | rod | 12/12 (100.0%) | 11/12 (91.7%) | 0.8515 | 37.41 | 100.0% |

## 模型/seed 汇总

| 模型 | Task | Strict | 双成功 | SPT | 平均峰值力矩 (Nm) | 机器合规率 |
|---|---:|---:|---:|---:|---:|---:|
| special_esn_ridge_s2026102801 | 11/12 | 10/12 | 10/12 | 0.7838 | 43.10 | 91.7% |
| special_esn_ridge_s2026102802 | 12/12 | 11/12 | 11/12 | 0.7923 | 42.24 | 100.0% |
| special_esn_ridge_s2026102803 | 12/12 | 11/12 | 11/12 | 0.7972 | 41.79 | 100.0% |
| special_mlp_scratch_s2026102801_w384 | 12/12 | 9/12 | 9/12 | 0.7511 | 40.91 | 83.3% |
| special_mlp_scratch_s2026102802_w384 | 12/12 | 8/12 | 8/12 | 0.7567 | 41.88 | 83.3% |
| special_mlp_scratch_s2026102803_w384 | 12/12 | 8/12 | 8/12 | 0.7569 | 42.29 | 91.7% |
| special_rnn_scratch_s2026102801 | 12/12 | 10/12 | 10/12 | 0.7012 | 43.35 | 100.0% |
| special_rnn_scratch_s2026102802 | 12/12 | 11/12 | 11/12 | 0.7777 | 41.77 | 100.0% |
| special_rnn_scratch_s2026102803 | 12/12 | 11/12 | 11/12 | 0.7998 | 42.41 | 100.0% |

## 失败保留

共有 19 个回合至少一项 Task、Strict 或机器合规未通过；全部仍保留在原始收据和分母中。最集中的模式是 MLP 棍推：棍推场景 Strict 为 4/12，机器合规为 7/12。ESN 仅有一个 Task/Strict/机器合规同时失败的 corner 回合（`corner_unseen_03`, seed 2026102801），峰值外穿透约 4.613 mm。逐回合失败字段见 [`failure_rows.csv`](failure_rows.csv)，完整审计见本地结果目录的 `FINAL_REVIEW.json`。

## 可复核来源

- 登记：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/REGISTRATION.json`，SHA256 `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6`。
- 执行：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/execution.json`，SHA256 `b45b51cad36c30324e1d9f1e906bc2a7dfbaa8a361435e27c0e8e0c6371e0e5c`。
- 独立复核：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/FINAL_REVIEW.json`，SHA256 `bb24b9660364565a5d8ac4bfb4acb256d1a11a0a5cb0a699b5bf42bc67dc2afa`。
- 本提交中的 `RESULTS_SUMMARY.json`、CSV、SVG 图和哈希是从上述收据生成的紧凑发布证据；9.5 GB 原始 episode 目录不纳入 Git。
- 历史 office/composite108 结果保持独立，不被本矩阵覆盖。

