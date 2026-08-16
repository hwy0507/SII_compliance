# ESN v2.3 Rejoin-Impulse Envelope Smoke

日期：2026-08-16。该结果是服务器上的 one-fixture matched smoke，不是正式多 seed 结论。使用 stable-phase ESN seed `20260995` 的冻结 representative checkpoint、同一 validation fixture、同一 MuJoCo/WBC/safety adapter，分别开启和关闭 v2.3 envelope。

## Gate

两种配置都满足：有效碰撞 `1/1`、抓取任务成功 `1/1`、matched no-impact 成功 `1/1`、hard torque-limit `0/1`。因此 v2.3 机制没有破坏场景构建、碰撞或任务完成。

## Matched values

| 指标 | v2.2 envelope off | v2.3 envelope on | 变化 |
|---|---:|---:|---:|
| Recovery RMSE | 3.457 mm | 3.752 mm | +0.295 mm |
| Paired-offset RMSE | 1.295 mm | 1.326 mm | +0.031 mm |
| Rejoin latency | 30 ms | 30 ms | 0 ms |
| Peak recovery jerk | 7.24 m/s^3 | 18.76 m/s^3 | +11.52 m/s^3 |
| Contact impulse | 5.469 N s | 5.469 N s | 0 |
| Peak torque | 31.416 Nm | 31.669 Nm | +0.253 Nm |

## 判断

v2.3 的 causal envelope 在这个 one-fixture smoke 上没有达到预设 gate：jerk 和 RMSE 变差，冲量没有改善。原因是 envelope 只作用于回位方向 residual action，但当前 checkpoint 的主要冲量发生在接触瞬间，且 envelope 的离散开关会增加动作轨迹的相位变化。不能据此启动多 seed 正式训练，也不能声称 v2.3 已经优于 v2.2。

## 下一步

保留代码开关但不启用该版本作为 proposed result。下一轮应改为连续、带状态的 **rejoin energy tank**：以 residual work/速度积分为预算，在接近 WBC 轨迹时连续释放剩余 authority，并加入 matched no-impact 约束；先做 one-seed smoke，再决定是否训练。contact impulse 必须作为训练目标而不是通过 privileged contact signal 做在线门控。
