# Post-V4 PPO 多目标 pilot 结果

## 结论

两个预注册候选均没有通过全部硬约束，因此**不进入新的 multi-seed 复现或冻结 V4 final**。这是一项有效的开发结果：新目标成功消除了此前 PPO 平均 rejoin 变慢与 jerk 上升的问题，但还没有同时消除 contact impulse 的小幅上升。

## 独立 validation（9 fixture）

| 方法 | task / no-rod | effective collision | recovery RMSE ↓ (mm) | rejoin ↓ (s) | paired RMSE ↓ (mm) | jerk ↓ (m/s³) | impulse ↓ (N·s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| zero-residual | 9/9 / 9/9 | 8/9 | 1.726 | 0.0322 | 2.215 | 955.87 | 3.177 |
| smooth_medium | 9/9 / 9/9 | 8/9 | **1.717** | **0.0322** | 2.206 | **954.52** | 3.182 |
| smooth_strong | 9/9 / 9/9 | 9/9 | 1.721 | **0.0322** | **2.200** | 954.62 | 3.196 |

`smooth_medium` 因 effective collision 仅 8/9、且 impulse 高于基线而失败；`smooth_strong` 达到 9/9 effective collision、rejoin 不变、jerk 略低、recovery RMSE 略低，但 impulse 为 3.196 N·s（较基线 +0.61%），故同样未通过预注册的“jerk 与 impulse 均不高于基线”要求。

## 解释与后续

新 reward 的方向是合理的：相较于原 PPO 多 seed 的 0.0352 s mean rejoin 与 960.20 m/s³ mean jerk，pilot 把这两个数收敛到 0.0322 s 和约 954.6 m/s³，同时维持任务成功。但当前改动没有在这一固定 seed 上产生足够大的冲量改善；不能因为其他指标变好而选择它。

下一步应把 contact impulse 作为明确、受限的训练 reward/constraint（仍不输入 actor），并在 development 中预先扫描其权重，再进入新一轮多 seed。V4 final 继续冻结。
