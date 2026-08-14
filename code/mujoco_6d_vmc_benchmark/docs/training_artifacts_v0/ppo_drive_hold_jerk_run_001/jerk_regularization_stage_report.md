# PPO jerk regularization stage：结果与失败诊断

## 设置

本轮沿用第二轮的因果 `0.28 s` 滞回恢复门控、52-D deployable observation 和 7-D action，在恢复奖励中加入 `recovery_jerk_weight=0.04`，参考 jerk 为 `1200 m/s³`。zero-residual 物理环境不变。

## 主 fixture（均值）

四个 fixture 均为 task success、effective collision、matched no-rod success `4/4`，且无硬力矩限幅。

| 指标 | Zero residual | 第二轮 PPO 300k | 本轮 jerk-aware PPO 300k |
|---|---:|---:|---:|
| 峰值配对偏差 (mm) | 14.480 | 13.931 | 13.916 |
| 配对 RMSE (mm) | 2.146 | 1.999 | 1.999 |
| 回归 RMSE (mm) | 1.550 | **1.456** | 1.468 |
| 峰值力矩 (Nm) | 30.361 | 30.358 | 30.357 |
| Jerk 峰值 (m/s³) | 1236.7 | 1271.9 | **1297.9** |

第三轮没有降低 jerk，反而比第二轮更高。按 fixture 看，最强碰撞工况的 jerk 为：

```text
zero residual: 1411.1 m/s³
第二轮 PPO:   1549.2 m/s³
第三轮 PPO:   1656.4 m/s³
```

同时第三轮平均 log-stiffness / log-drive 偏移分别为 `0.0322 / 0.0436`，高于第二轮的 `0.0267 / 0.0356`。这说明当前 jerk reward 没有形成有效约束，反而诱发了更大的动作偏移。

## Held-out

8 个预声明 held-out fixture 中有 6 个有效碰撞。第三轮 300k 的 6 个有效 held-out 结果为：

- 回归 RMSE：`1.4195 mm`；
- 峰值配对偏差：`18.89 mm` 左右；
- 配对 RMSE：`2.80 mm` 左右；
- 峰值力矩：`30.36 Nm` 左右；
- jerk 全集均值为 `1397.6 m/s³`，且最大值约 `2541 m/s³`。

回归精度仍然比 zero-residual 好，但 jerk 目标没有解决。

## 诊断与下一步

当前失败不是 PPO 数值发散，而是 reward 形式与动作动力学不匹配：奖励在一个 40 ms 控制周期结束后才惩罚 jerk 峰值，策略却可以通过更激进的刚度／drive 更新获得更强的短期恢复收益。下一轮改为控制器侧的 log-action rate limiter / residual bandwidth 限制，并把动作变化率直接加入可观测的安全约束；不再单独提高 jerk reward 权重。
