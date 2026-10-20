# RL 与 ESN 未见条件比较（已完成证据）

本报告整理已有的 `office_v7_uniform24_20261008` 固定模型、未见条件评估。384 条回合均已
完成（16 个方法族、每族 24 条条件），所有方法使用相同冻结环境、55 s 回合和 `dt=5e-5`。
比较指标来自独立物理子步审计；失败回合保留并计入分母。

## ESN 与历史 RL 结果

| 方法 | Task/24 | Strict/24 | RMSE (mm) | 峰值力矩 (Nm) | 峰值速度 (m/s) | 最大穿透 (mm) |
|---|---:|---:|---:|---:|---:|---:|
| ESN | 20 | 16 | 29.041 | 49.486 | 0.362 | 0.696 |
| RL parameter VMC | 0 | 0 | 28.660 | 37.559 | 0.372 | 0.185 |
| RL parameter admittance | 0 | 0 | 28.805 | 39.476 | 0.377 | 0.188 |
| RL parameter impedance | 0 | 0 | 33.204 | 39.127 | 0.375 | 0.181 |
| RL direct metric | 0 | 0 | 73.896 | 41.124 | 0.323 | 1.019 |
| RL direct task | 0 | 0 | 154.763 | 49.363 | 0.393 | 1.123 |

在这套未见条件上，ESN 的 Task/Strict 明显高于这些历史 RL 配置（20/24、16/24 对 0/24、
0/24）。参数型 RL 的 RMSE、峰值力矩和穿透部分低于 ESN，但它们全部未完成任务，不能据此
称为 RL 优于 ESN。直接动作 RL 同时出现更大的 RMSE 或穿透。该结果不支持“历史 RL 胜过 ESN”。

## 证据边界

- 原始汇总：`code/mujoco_6d_vmc_benchmark/outputs/office_v7_uniform24_20261008/final/VERIFIED_SUMMARY.json`。
- 该批次的 RL candidate 是 `office_rl_parameter_*_2026100301` 和
  `office_rl_direct_*_2026100301`。它们不是 `rl_goal_acceptance_20261018_v3` 中最终四路
  RL checkpoint；最终 checkpoint 与本 24 条 office-v7 条件之间尚未完成 lineage-matched
  独立重放，因此本报告不把上述数字写成最终 RL 的泛化结论。
- 该批次明确记录为新 office-v7 24 条分层条件，不是旧 office-v6；也不代表任意新几何或真实
  机器人泛化。服务器归档根为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。

