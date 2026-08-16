# ESN v4 Phase-Predictive WBC Feedback：One-Seed Development Result

日期：2026-08-16。本报告记录 post-V4 development validation 上的单 seed 研究结果，不是 V4 final holdout，也不是多 seed 论文结论。ESN 与 VMC 保持独立：本实验只涉及 independent WBC velocity-residual controller。

## 方法

v4 在 stable-phase ESN 基础上加入两条因果信号：

1. 固定 Fan Ye multiscale error forecaster 预测 120 ms WBC pose-error change；
2. fast/slow reservoir disagreement 形成 phase-memory score。

只有当预测误差沿径向外扩且 phase-memory score 超过阈值时，v4 才连续降低 fixed WBC 的 feedback 项；参考轨迹 feedforward 不变。feedback scale 通过 engage/release slew 连续变化。PPO actor 仍使用 fast/slow reservoir state 和同一 residual safety adapter。

输入不包括 contact、force、impactor type、geometry、future release 或 fixture ID。

## Validation-only checkpoint scan

同一 seed、同一训练 run、同一 9 个 development validation fixtures；所有点均为 task 9/9、no-impact task 9/9、hard torque limit 0/9、effective collision 8/9。有效碰撞 8/9 不是 v4 特有问题：同一 fixture 集上的 v2.2 representative 也是 8/9。

| v4 checkpoint | Recovery RMSE (mm) | Rejoin latency (ms) | Recovery jerk (m/s^3) | Impulse (N s) | Peak torque (Nm) |
|---|---:|---:|---:|---:|---:|
| 50k | 3.770 | 112 | 79.53 | 3.631 | 31.652 |
| 100k | 2.845 | 41 | 39.95 | 3.862 | 31.988 |
| 150k | 2.939 | 41 | 22.89 | 3.904 | 32.661 |
| 200k | 2.761 | 28 | 23.54 | 4.027 | 32.665 |
| 250k | 2.788 | 32 | 34.15 | 3.912 | 32.378 |

200k 是快速回位/低 jerk 的 Pareto representative；250k 的 impulse 稍低，但回位 jerk 较高。

## Min-feedback-scale 重新训练

初版 v4 训练使用 minimum feedback scale 0.60，调制偏强。将最小反馈 scale 固定为 0.90 后重新训练 250k steps，最终 validation 为：

| 指标 | v2.2 reference | v4 min-0.90 | v4 - v2.2 |
|---|---:|---:|---:|
| Recovery RMSE | 3.011 mm | 2.639 mm | -0.372 mm |
| Rejoin latency | 27.8 ms | 36.7 ms | +8.9 ms |
| Peak recovery jerk | 27.02 m/s^3 | 26.64 m/s^3 | -0.38 m/s^3 |
| Contact impulse | 3.568 N s | 3.765 N s | +0.197 N s |
| Peak torque | 31.407 Nm | 32.074 Nm | +0.667 Nm |
| Task / no-impact / hard-limit | 9/9 / 9/9 / 0/9 | 9/9 / 9/9 / 0/9 | same |
| Effective collision | 8/9 | 8/9 | same |

## 严谨判断

v4 已产生可报告的 recovery-accuracy contribution：在相同 validation fixtures 上降低 recovery RMSE，且 recovery jerk 没有恶化。它尚未解决 impulse/torque safety：两者都有小幅代价，故不可声称全面优于 stable-phase ESN v2.2。

v3 energy-budget 和 v4 phase-predictive feedback 分别揭示了两种不同 trade-off：

- v3：更强的 residual authority budget 可压低 impulse，但会牺牲有效碰撞/回位；
- v4：预测式 feedback 调制改善回位误差，但若调制过强会提高 torque/impulse。

## 下一轮算法条件

下一轮应研究 torque-margin-aware phase-predictive feedback：在保持 feedforward 轨迹的同时，利用当前 joint velocity、bias torque、joint velocity command 和共享 torque adapter 的可部署预测余量，限制 phase-predictive feedback 的最小 scale/变化率。该层必须不读取 contact force 或碰撞物信息。

所有 tuning 继续限定在 post-V4 development split；V4 final holdout 和 rod/ball/hand-palm transfer 均不参与参数选择。
