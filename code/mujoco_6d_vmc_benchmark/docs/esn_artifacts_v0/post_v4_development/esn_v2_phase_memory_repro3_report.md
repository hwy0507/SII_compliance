# ESN-v2.1 Phase-Memory 三 Seed 结果

日期：2026-08-16。V4 final holdout 未用于训练、checkpoint 选择或调参。ESN 与 VMC 仍为两个独立算法；这里比较的是固定 Panda WBC 上的 current-state MLP 与 phase-memory ESN。

## 算法改动

phase-memory ESN 使用固定 Fan Ye fast/slow reservoirs。除 PPO readout 输入外，控制层还读取两个 reservoir 的 causal state disagreement，并以短时衰减保持该 phase memory。只有当当前 WBC pose error 与 twist error 显示出 measured rejoin confidence 时，才启用有界 recovery authority floor。该机制不读取 contact、force、rod state、obstacle geometry、future release 或 fixture id，并继续经过共享 action/velocity/acceleration/torque safety adapter。

## 实验协议

- `impulse_constrained` reward profile；
- MLP 与 phase-ESN 使用相同 seed、PPO budget、MuJoCo fixtures、WBC、动作接口和 safety layer；
- 每条 lane 102400 PPO steps，8 个并行环境，checkpoint 间隔 25600 steps；
- 每个 checkpoint 只在 development validation split 上评估；
- 先通过 9/9 task、9/9 matched no-rod、8/9 effective collision、0 hard torque gate，再进行 Pareto 选择；
- 三个 seed：20260990、20260991、20260992。

## 配对差值

以下为 phase-ESN 减去 MLP；负值表示 phase-ESN 更好。均值和标准差为三个 seed 的 population statistics。

| 指标 | 平均差值 | 标准差 | 获胜 seed 数 |
|---|---:|---:|---:|
| Recovery RMSE | -0.104 mm | 0.058 mm | 3/3 |
| Rejoin latency | -10.4 ms | 14.7 ms | 2/3 |
| Peak recovery jerk | -10.26 m/s^3 | 7.04 m/s^3 | 3/3 |
| Contact impulse | -0.322 N s | 0.144 N s | 3/3 |
| Peak torque | -0.261 Nm | 0.207 Nm | 3/3 |
| Paired-offset RMSE | -0.105 mm | 0.053 mm | 3/3 |

## 判断

相比原始 ESN-v2，phase-memory 分支已经把收益从“主要改善 jerk 和 offset”推进到“恢复误差、接触能量和峰值力矩同时稳定改善”。目前仍不能声称每个 seed 的 rejoin latency 都改善，但它已经是一个有明确控制机制、可复现且值得进入主实验的算法版本。

正式远端结果目录：`/home/arm1/vmc_mujoco_runtime/outputs/esnv2_phase_memory_repro3_20260816`。
