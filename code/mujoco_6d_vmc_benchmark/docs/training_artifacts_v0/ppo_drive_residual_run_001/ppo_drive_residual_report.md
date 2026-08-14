# PPO：六弹簧残差 + return-drive residual（run 001）

## 对照定义

所有策略都运行在同一 52-D、可部署的误差门控 return-drive 环境。`zero residual` 对照使用完全相同的物理环境、四个 fixture、rod/no-rod 配对和安全门槛，但把 PPO 的七维残差动作固定为零。因此 checkpoint 与 zero 的差异可以归因于策略残差，而不是由新增静态 return-drive 机制本身造成。

注意：该 PPO 评估中的回归时延采用“连续 80 ms 处于 5 mm 内”的离线定义；它不能同 earlier static runner 的 phase-analysis 时延混用。

## 有效性

zero residual 与三个 checkpoint 均为 `4/4` task success、`4/4` effective collision、`4/4` matched no-rod success。

## 物理指标（均值；PPO − zero）

负值代表对应数值下降；对于偏差、RMSE、力矩、jerk 通常更好。

| Checkpoint | 峰值偏差 (mm) | 配对 RMSE (mm) | 回归 RMSE (mm) | 峰值力矩 (Nm) | Jerk (m/s³) |
|---|---:|---:|---:|---:|---:|
| zero residual | 14.736 | 2.214 | 1.921 | 30.381 | 1236.3 |
| PPO 100k | 14.582 (-0.153) | 2.190 (-0.024) | 1.933 (+0.012) | 30.373 (-0.007) | 1231.0 (-5.3) |
| PPO 200k | 14.699 (-0.037) | 2.219 (+0.005) | 1.940 (+0.019) | 30.368 (-0.013) | 1231.3 (-4.9) |
| PPO 300k | 14.547 (-0.188) | 2.195 (-0.020) | 1.919 (-0.001) | 30.380 (-0.001) | 1231.5 (-4.8) |

## 结论

300k 是三个 checkpoint 中回归 RMSE 最低者（`1.919 mm`），但相对同环境 zero-residual 的变化仅为 `-0.001 mm`。策略的平均 log-stiffness 偏移为 `0.0112`，平均 log-drive 偏移为 `0.0048`，而可测误差门控平均仅 `0.0549`；这表明残差实际介入很弱。

因此该 run 证明了 7-action / 52-D PPO 接口的训练与物理任务均稳定，但**没有证明 PPO 在静态、部署可用的 error-gated return-drive 基线上取得实质 Pareto 改善**。不应把它称为 RL 突破，也不应继续按同一奖励与动作参数盲目延长训练。
