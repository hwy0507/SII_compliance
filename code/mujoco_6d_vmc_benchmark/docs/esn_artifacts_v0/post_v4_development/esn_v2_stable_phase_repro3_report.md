# ESN-v2.2 Stable-Phase 三 Seed 稳定性结果

日期：2026-08-16。V4 final holdout 未用于训练、checkpoint 选择或调参。ESN 与 VMC 是独立算法；本报告只比较固定 Panda WBC 下的 current-state MLP 和 stable-phase ESN。

## 结论

stable-phase ESN 解决了 v2.1 最主要的不稳定点：在三个独立 seed 中，rejoin latency 都小于配对的 MLP，平均缩短 `80.0 ms`，且 ESN 自身的 seed 间标准差为 `5.5 ms`。同时 recovery RMSE、peak recovery jerk 和 paired-offset RMSE 都在 3/3 seed 改善。

这不是所有物理量的全胜：contact impulse 平均增加 `0.034 N s`，由第一组 seed 的 `+0.201 N s` 所致；peak torque 平均降低，但第一组 seed 有 `+0.143 Nm` 的小幅代价。因此 v2.2 可以作为当前主 ESN 候选和 v2.1 的稳定性消融对照，但论文表述应保留这种冲量/力矩 trade-off。

## 算法

v2.2 保持 v2.1 的固定 Fan Ye fast/slow reservoirs、PPO reward、WBC 和共享安全适配器不变，只替换 residual authority 的释放逻辑：

- fast/slow reservoir 的 causal state disagreement 继续给出 phase memory；
- history 和 measured rejoin confidence 较高时，authority floor 快速建立；
- confidence 短时波动时，floor 以较慢速率释放，避免 recovery action 突然收缩；
- tracking error 接近 nominal path 时，连续 error envelope 将 floor 自动压到零，避免在已回归后残留介入。

该分支不读取 contact、force、rod state、obstacle geometry、future release 或 fixture ID；所有输出继续经过相同的 action slew、joint velocity、acceleration 和 torque safety adapter。稳定机制对应 `fan_ye_stable_phase_esn` observation mode。

## 固定协议

- `impulse_constrained` reward profile；
- MLP 与 stable-phase ESN 共享每个 seed、PPO budget、MuJoCo fixtures、WBC、动作接口和 safety layer；
- 每条 lane：102400 PPO steps，8 个并行环境，checkpoint 间隔 25600 steps；
- 每个 checkpoint 只在 post-V4 development validation split 上评估；
- 先满足 task success、matched no-rod、effective collision 和 zero hard-torque-limit gate，再仅在 validation split 上建立 checkpoint Pareto archive；
- Pareto objectives：recovery RMSE、rejoin latency、peak recovery jerk、contact impulse、peak torque；以预声明的 equal ordinal-rank 从 Pareto front 选 representative checkpoint；
- seed：20260994、20260995、20260996。

三个 seed 的 MLP 和 ESN representative checkpoints 均通过 validation gate。正式远端结果目录：`/home/arm1/vmc_mujoco_runtime/outputs/esnv2_stable_phase_repro3_20260816`。

## 配对结果

以下为 stable-phase ESN 减去 MLP。负值表示 ESN 更好；均值和标准差为三个配对 seed 的 population statistics。

| 指标 | 平均差值 | 标准差 | 获胜 seed 数 | 相对 MLP 均值 |
|---|---:|---:|---:|---:|
| Recovery RMSE | -0.611 mm | 0.314 mm | 3/3 | -16.1% |
| Rejoin latency | -80.0 ms | 33.3 ms | 3/3 | -70.4% |
| Peak recovery jerk | -9.47 m/s^3 | 3.39 m/s^3 | 3/3 | -27.1% |
| Contact impulse | +0.034 N s | 0.119 N s | 2/3 | +1.0% |
| Peak torque | -0.107 Nm | 0.191 Nm | 2/3 | -0.3% |
| Paired-offset RMSE | -0.247 mm | 0.105 mm | 3/3 | -8.7% |

逐 seed 差值如下。

| Seed | Recovery RMSE (mm) | Rejoin latency (ms) | Peak jerk (m/s^3) | Impulse (N s) | Peak torque (Nm) | Paired offset (mm) |
|---|---:|---:|---:|---:|---:|---:|
| 20260994 | -0.325 | -71.1 | -4.71 | +0.201 | +0.143 | -0.173 |
| 20260995 | -1.048 | -124.4 | -12.32 | -0.035 | -0.142 | -0.171 |
| 20260996 | -0.460 | -44.4 | -11.39 | -0.066 | -0.321 | -0.396 |

## 直接稳定性证据

代表 checkpoint 的 raw validation 均值与 seed 间标准差：

| Lane | Recovery RMSE (mm) | Rejoin latency (ms) | Peak jerk (m/s^3) | Impulse (N s) | Peak torque (Nm) |
|---|---:|---:|---:|---:|---:|
| MLP | 3.786 +/- 0.202 | 113.7 +/- 30.9 | 35.01 +/- 3.47 | 3.485 +/- 0.145 | 31.597 +/- 0.178 |
| Stable-phase ESN | 3.175 +/- 0.163 | 33.7 +/- 5.5 | 25.54 +/- 1.51 | 3.518 +/- 0.036 | 31.490 +/- 0.060 |

因此此次改动的主要证据不只是平均时延降低，也是 ESN rejoin latency 的跨 seed 离散度从本次配对 MLP 的 `30.9 ms` 降至 `5.5 ms`。这符合滞回 authority floor 抑制短时 confidence 抖动的设计目标。

## 与 v2.1 的关系

v2.1 phase-memory 在另一组三 seed（20260990--20260992）上已经实现 recovery RMSE、jerk、impulse、torque 和 paired offset 的 3/3 改善，但 rejoin latency 仅 2/3 获益，配对差值为 `-10.4 +/- 14.7 ms`。v2.2 在新的三 seed 上把 latency 改善推进为 3/3，且 ESN raw latency 标准差为 `5.5 ms`。

两批实验的 seed 不同，不能将两组 raw mean 或标准差视为严格 head-to-head 的统计比较。可以作出的严谨结论是：v2.2 在预注册的独立三 seed replication 内验证了其稳定性目标；v2.1 是没有滞回释放的机制消融。若要声称 v2.2 严格优于 v2.1，下一步需要让两个 observation mode 在完全相同的 seeds、fixtures 和 checkpoint protocol 下直接配对。

## 当前定位与下一步

v2.2 已具备进入 proposed ESN 主实验的条件：回归精度、再并入速度和动作平滑性均为 3/3 稳定改善，并保留了安全层。它不应被描述为“无代价全面优于 MLP”，因为第一组 seed 的冲量和峰值力矩略有增加。

下一步应固定 v2.2 的安全参数，执行 stable-phase ESN 对 phase-memory ESN 的同-seed direct ablation，并针对 seed 20260994 的冲量代价做独立诊断（collision onset、peak-contact 时间和 floor trajectory）；只有在该诊断完成前，才避免继续凭 validation 结果调 safety 参数。
