# ESN-v2 Checkpoint-Pareto 三 Seed 结果

日期：2026-08-16。该实验使用 post-V4 development manifest；V4 final holdout 未用于训练、checkpoint 选择或调参。ESN 与 VMC 保持为两个独立算法，本实验的比较对象是固定 Panda WBC 上的 current-state MLP 与 Fan Ye multiscale ESN-v2。

## 协议

- ESN-v2：固定 fast/slow Fan Ye reservoir，各 64 nodes，时间常数分别为 0.04254 s 与 0.14002 s。
- MLP baseline：与 ESN-v2 使用相同的 32-D WBC/proprioceptive state、PPO 网络、奖励、seed、MuJoCo fixture、safety adapter 和训练预算。
- reward profile：`impulse_constrained`。
- 每条 lane：102,400 PPO steps，8 个并行环境，checkpoint 间隔 25,600 steps。
- 每个 checkpoint 在 validation split 上做 matched rod/no-rod rollout；先过 task/no-rod/effective-collision/hard-torque gate，再进入 Pareto archive。
- Pareto 目标全部最小化：recovery RMSE、rejoin latency、peak recovery jerk、contact impulse、peak torque。代表 checkpoint 使用预先声明的 equal ordinal-rank 规则，不使用事后加权分数。

三组代表 checkpoint 分别为：

| Seed | MLP representative | ESN-v2 representative | Gate |
|---:|---|---|---|
| 20260986 | 102400 steps | 102400 steps | 两者通过 9/9 task、9/9 no-rod、8/9 effective collision、0 hard torque |
| 20260987 | final | final | 两者通过同一 gate |
| 20260988 | 76800 steps | 76800 steps | 两者通过同一 gate |

## ESN-v2 减去 MLP 的配对差值

负值表示 ESN-v2 更好；均值和标准差为三个 seed 的 population statistics。

| 指标 | 平均差值 | 标准差 | ESN-v2 获胜 seed 数 |
|---|---:|---:|---:|
| Recovery RMSE | -0.198 mm | 0.329 mm | 2/3 |
| Rejoin latency | -22.2 ms | 40.9 ms | 1/3 |
| Peak recovery jerk | -6.52 m/s^3 | 1.76 m/s^3 | 3/3 |
| Contact impulse | +0.0095 N s | 0.2104 N s | 2/3 |
| Peak torque | -0.454 Nm | 0.369 Nm | 2/3 |
| Paired-offset RMSE | -0.221 mm | 0.125 mm | 3/3 |

## 结论与限制

这次 v2 优化最明确的收益是平滑性和接触后偏离控制：恢复段 jerk 与 paired-offset RMSE 在三个独立 seed 中都改善。峰值力矩和恢复 RMSE 多数 seed 改善，但不是每个 seed 都改善。回归时间仍然不稳定，冲量的平均差值接近零，因此不能声称 ESN-v2 全面支配 MLP。下一步应优先针对 rejoin latency 的 seed 方差做 phase-aware causal command filter 或更稳定的恢复期策略，并保持 MLP/ESN 共享同一滤波器与 gate。

远端原始结果目录：`/home/arm1/vmc_mujoco_runtime/outputs/esnv2_impulse_constrained_archive_campaign_20260816`。
