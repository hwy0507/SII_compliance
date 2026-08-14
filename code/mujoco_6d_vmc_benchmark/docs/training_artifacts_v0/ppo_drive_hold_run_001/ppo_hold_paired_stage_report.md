# PPO run 001：因果滞回恢复门控上的配对结果

## 严格对照

对照是同一 52-D 可部署环境中的 `zero residual`：六维弹簧与 return-drive residual 均固定为零，但保留相同的 `0.28 s`、仅由测得轨迹误差触发的滞回恢复门控。所有指标均来自 rod/no-rod 配对物理 rollout；no-rod 是任务匹配参考，不是在线 WBC。

PPO 使用七维动作：六个弹簧残差加一个 virtual-carriage return-drive residual；后者不是第七根弹簧。actor 不使用接触、力、杆运动、障碍物或未来相位。

## 主 fixture（4 个有效碰撞）

所有 zero 和 PPO checkpoint 均为 `4/4` task success、`4/4` effective collision、`4/4` matched no-rod success，且无硬力矩限幅。

| 指标（均值） | Zero residual | PPO 100k | PPO 200k | PPO 300k |
|---|---:|---:|---:|---:|
| 峰值配对偏差 (mm) | 14.480 | 13.977 | 14.097 | **13.931** |
| 配对 RMSE (mm) | 2.146 | 2.035 | 2.041 | **1.999** |
| 回归 RMSE (mm) | 1.550 | 1.552 | 1.490 | **1.456** |
| 峰值力矩 (Nm) | 30.361 | 30.359 | 30.363 | **30.358** |
| Jerk 峰值 (m/s³) | 1236.7 | 1253.7 | 1266.6 | **1271.9** |

300k 相对 zero 的变化：峰值偏差 `-3.8%`、配对 RMSE `-6.8%`、回归 RMSE `-6.1%`、峰值力矩 `-0.01%`，但 jerk `+2.9%`。四个 fixture 的回归 RMSE 和峰值配对偏差均下降；jerk 上升主要出现在最强的第四个 fixture（约 `1411 -> 1549 m/s³`）。

策略确有实质介入：平均 log-stiffness 偏移 `0.0267`、平均 log-drive 偏移 `0.0356`，而不是上一轮几乎保持零动作的局部解。

## Held-out fixture（8 个预声明测试几何）

其中 2 个几何再次被有效碰撞门槛剔除（弱碰撞，而非任务失败）。在 6 个有效 held-out fixture 中，zero 与 PPO 都为 `6/6` task success、有效碰撞与 no-rod success。

| 指标（仅 6 个有效 held-out fixture） | Zero residual | PPO 300k | PPO − zero |
|---|---:|---:|---:|
| 峰值配对偏差 (mm) | 19.278 | 18.892 | -0.387 (-2.0%) |
| 配对 RMSE (mm) | 2.934 | 2.796 | -0.138 (-4.7%) |
| 回归 RMSE (mm) | 1.517 | 1.415 | **-0.102 (-6.7%)** |
| 峰值力矩 (Nm) | 30.410 | 30.421 | +0.011 (+0.04%) |
| Jerk 峰值 (m/s³) | 1578.8 | 1620.7 | +42.0 (+2.7%) |

六个有效 held-out fixture 的回归 RMSE 均下降。该改善具有跨 fixture 一致性，但 jerk 的增加使其尚不构成全指标 Pareto 超越。

## 结论与下一步

本轮已经克服“PPO 不比新静态机制更好”的学习瓶颈：PPO 在主 fixture 和未参与训练的有效 held-out fixture 上，都一致降低了回归误差与轨迹偏差，且不损失任务成功或力矩安全。

尚未克服的剩余瓶颈是 jerk。下一轮只改变 reward：在保留因果滞回门控和同一安全包络的前提下，向 PPO 加入显式 jerk 正则，并继续以相同 zero-residual 与 held-out protocol 验证。不得为了降低 jerk 而放松有效碰撞、任务成功或 no-rod 对照门槛。
