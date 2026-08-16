# Stable-Phase ESN 多撞击物 Transfer 三 Seed 结果

日期：2026-08-16。该实验以冻结的 stable-phase ESN 与 current-state MLP representative checkpoints 做 inference-only cross-geometry evaluation。棍、球、手掌代理 fixture 未参与 PPO 训练、checkpoint Pareto 选择或 V4 final holdout。ESN 与 VMC 为独立算法：本报告只比较两条 independent WBC velocity-residual lane，不将 ESN 叠加到 VMC。

## 协议

- 三个已完成 stable-phase campaign seed：20260994、20260995、20260996；
- 每个 seed 的 MLP 和 stable-phase ESN 均使用其原 validation-only Pareto archive 已选 representative checkpoint；
- 固定 Panda WBC 抓取任务：下探、开爪受撞、回位、闭爪、抬升保持；
- 三种真实 MuJoCo slide impactor：rod (`0.170 m`)、ball (`0.145 m`)、hand-palm proxy (`0.145 m`)；
- 所有 lane 共享 WBC command source、action filter、joint velocity/acceleration/torque/torque-slew safety adapter；
- ESN actor输入只包含 Panda 本体感觉、WBC command/error history 和 fixed reservoir state；不读取 contact、force、impactor type、geometry 或未来 release。

每个 `seed × impactor × lane` 都有 matched no-impact episode。共 18 个带 impact episode 和 18 个 no-impact episode；9/9 ESN-vs-MLP 配对均为有效碰撞、抓取成功、末端保持且无 hard torque limit。

`hand-palm proxy` 是柔性手掌大小的 ellipsoid 接触代理，不是人体生物力学模型，也不构成真实人机安全认证。

## 总体配对差值

以下为 stable-phase ESN 减去 MLP；负值代表 ESN 更好。统计范围为三种撞击物、三个 seed，共 9 个有效配对。

| 指标 | 平均差值 | 标准差 | ESN 获胜 |
|---|---:|---:|---:|
| Recovery RMSE | -0.851 mm | 0.810 mm | 9/9 |
| Rejoin latency | -177.8 ms | 136.1 ms | 8/9 |
| Peak recovery jerk | -15.46 m/s^3 | 26.20 m/s^3 | 6/9 |
| Contact impulse | +0.059 N s | 0.082 N s | 1/9 |
| Peak torque | +0.003 Nm | 0.013 Nm | 5/9 |
| Paired-offset RMSE | -0.391 mm | 0.170 mm | 9/9 |

## 按撞击物聚合

| 物体 | Recovery RMSE | Rejoin latency | Recovery jerk | Impulse | Peak torque | Paired-offset RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Rod | -0.984 mm, 3/3 | -186.7 ms, 3/3 | -11.38 m/s^3, 2/3 | +0.004 N s, 1/3 | +0.006 Nm, 2/3 | -0.415 mm, 3/3 |
| Ball | -1.031 mm, 3/3 | -200.0 ms, 3/3 | -7.62 m/s^3, 2/3 | +0.028 N s, 0/3 | +0.010 Nm, 1/3 | -0.415 mm, 3/3 |
| Hand-palm proxy | -0.538 mm, 3/3 | -146.7 ms, 2/3 | -27.37 m/s^3, 2/3 | +0.145 N s, 0/3 | -0.006 Nm, 2/3 | -0.343 mm, 3/3 |

表中 `x/y` 为负差值获胜的 seed 数。

## 严谨判断

1. **跨几何回归优势成立。** ESN 在 9/9 配对中都降低 recovery RMSE 和 paired offset；在 rod 与 ball 上 rejoin latency 为 3/3 改善。说明 stable-phase memory 对不同接触形状具有一定 transfer 能力。
2. **冲量安全性没有迁移。** ESN 在 8/9 个配对中冲量增加，尤其手掌代理的平均增量为 `0.145 N s`。这不是可忽略的副作用，不能把当前 ESN 描述为“更安全的碰撞缓冲算法”。
3. **力矩基本持平。** 平均峰值力矩差只有 `+0.003 Nm`，当前不足以声称 ESN 降低或增加力矩峰值。
4. **恢复 jerk 仍有方差。** 总体 6/9 改善，但 ball/hand-palm 的 seed 20260996 出现 jerk 退化，因此下一轮不能只优化 latency。

## 下一轮算法约束

稳定性改进应采用“rejoin-impulse constrained”方向：保持 v2.2 的因果滞回 phase-memory floor，但根据自身的 measured WBC error/twist history 约束 residual authority 的高频变化，并在训练 reward 中强化 contact impulse 与 recovery jerk 的联合罚项。撞击物身份、接触力、contact flag 和未来 release 仍不得成为策略输入。

在该算法改动前，本报告中的 fixture、MLP/ESN checkpoint、WBC、安全 adapter 和 baseline 均冻结。

## 复现入口

- Transfer manifest：[impactor_matrix_transfer_manifest.json](impactor_matrix_transfer_manifest.json)
- Transfer evaluator：[evaluate_stable_phase_impactor_transfer.py](../../../scripts/evaluate_stable_phase_impactor_transfer.py)
- 物理 impactor matrix：[impactor_matrix_report.md](impactor_matrix_dev_20260816/impactor_matrix_report.md)
- 正式远端输出：`/home/arm1/vmc_mujoco_runtime/outputs/esnv2_impactor_transfer_repro3_20260816` 和 `/home/arm1/vmc_mujoco_runtime/outputs/esnv2_impactor_transfer_smoke_20260816`。
