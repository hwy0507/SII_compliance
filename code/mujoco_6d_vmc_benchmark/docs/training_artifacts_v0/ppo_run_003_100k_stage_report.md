# PPO 六维刚度状态反馈：100k checkpoint 阶段记录

> 结论：正式 PPO 的物理闭环、有效碰撞门槛与抓取任务门槛均已通过；此阶段**不能**宣称 PPO 已优于 static VMC，下一步必须在独立 held-out fixture 上做同协议的 paired comparison。

## 本阶段对象

- 算法：Stable-Baselines3 PPO，非 CEM、非预设时间刚度表。
- 动作：25 Hz 的六维刚度动作 `[x, y, z, roll, pitch, yaw]`，log-space 映射、`[8, 70]^6` 安全边界和 `1.6 s^-1` log-rate safety shield。
- 观测：51 维可部署本体状态。策略没有获得 rod contact、contact force、rod displacement/velocity、障碍物位置/几何、或未来碰撞阶段。
- 物理：MuJoCo Panda；物理杆通过 slide actuator 撞击末端；三平移通道是显式 MuJoCo 虚拟小车，SO(3) 通道是已验证的 controller-integrated virtual carriage。
- 训练：8 个 `SubprocVecEnv` MuJoCo worker 并行，约 605 control steps/s；checkpoint 同步保存 PPO 权重与 `VecNormalize` 状态。

## Fixture gate

第一版 6 个候选 fixture 先通过冻结 policy 物理筛选。剔除：

- `stroke=0.155 m, height=0.538 m, start=1.040 s`：峰值接触力 8.94 N、冲量 0.105 Ns，低于有效碰撞门槛（15 N / 0.45 Ns）。
- `stroke=0.180 m, height=0.540 m, start=1.115 s`：接触有效但杆扰动下抓取任务失败。

正式训练/100k 测试只使用剩余四个场景；因此 episode 的终端 reward 不会由策略不可控制的弱擦碰或不可行 fixture 主导。

## 冻结 100k checkpoint 的 matched paired 评测

每个场景运行两次：相同 fixture、相同冻结 deterministic PPO、一次有杆、一次无杆。配对 offset 是两次实际末端轨迹的欧氏距离；障碍物诊断只用于评测，不进入 actor。

| 指标 | 结果（4 fixture，mean ± std） |
|---|---:|
| 杆扰动下任务成功 | 4 / 4 |
| 有效碰撞 | 4 / 4 |
| 匹配无杆任务成功 | 4 / 4 |
| 峰值配对末端偏移 | 17.17 ± 7.00 mm |
| 配对偏移 RMSE | 2.89 ± 1.13 mm |
| 卸载后恢复轨迹 RMSE | 2.24 ± 0.29 mm |
| 重回 nominal tube 延迟 | 22.5 ± 9.0 ms |
| 峰值电机力矩 | 30.31 ± 0.12 Nm |
| 峰值 jerk | 1233.25 ± 126.47 m/s³ |
| 峰值接触力 | 38.97 ± 14.15 N |
| 接触冲量 | 1.77 ± 0.53 Ns |

原始可复算记录：[ppo_paired_evaluation.json](ppo_paired_evaluation.json)。

## 可说与不可说

可以说：在预筛的有效物理杆碰撞中，PPO 闭环刚度调节保持了 4/4 的抓取和无杆配对可行性，并产生了可量化的偏离与回归轨迹。

不可以说：这 100k 结果尚未证明 PPO 在 tracking、torque、jerk 和 contact impulse 的 Pareto 前沿全面超过 static VMC、CEM phase schedule 或 rigid/impedance baseline。当前四个 fixture 被用于训练，且静态/CEM 的 policy-matched paired evaluation 尚未完成；它们不能被事后替代或弱化。

## 接下来

1. 继续 run_003 至 1M steps，并保存每 100k checkpoint 的 paired normalizer。
2. 选取 validation/test 的独立有效碰撞 fixture，冻结后评测 static `[35]^6`、CEM schedule 和 PPO。
3. 仅在统一的有效碰撞率、任务率、paired offset、recovery RMSE、rejoin latency、peak torque、jerk、force/impulse 表上给出 Pareto 结论和图。

## Run_003 提前停止记录（100k--500k）

该 run 原计划训练到 1M steps，但在 500k 时提前停止并保留所有 checkpoint。理由是每 100k 的冻结 paired evaluation 已显示核心指标平台化，而不是为了只保留表现最好的 checkpoint：

| checkpoint | task/effective/no-rod | peak paired offset (mm) | recovery RMSE (mm) | peak torque (Nm) | PPO KL / clip fraction |
|---|---|---:|---:|---:|---:|
| 100k | 4/4, 4/4, 4/4 | 17.17 | 2.240 | 30.312 | — |
| 300k | 4/4, 4/4, 4/4 | 17.09 | 2.229 | 30.298 | — |
| 400k | 4/4, 4/4, 4/4 | 17.17 | 2.193 | 30.306 | 0.034 / 0.315 |
| 500k | 4/4, 4/4, 4/4 | 17.11 | 2.186 | 30.293 | >0.036 / >0.32 near end |

因此最小的 recovery-RMSE 改善约为 0.054 mm（100k 到 500k），而峰值偏移、力矩、jerk 与 rejoin latency 基本不变；继续相同的 fixed-LR PPO run 预计不能形成有意义的科研增益。下一轮应改为带 `target_kl` / learning-rate schedule 的 PPO，并增加有物理意义的 post-contact recovery objective；该修改会作为新 run，与本 run 分开报告。

后续 checkpoint 结果：

- [300k paired evaluation](ppo_run_003_300k/ppo_paired_evaluation.json)
- [400k paired evaluation](ppo_run_003_400k/ppo_paired_evaluation.json)
- [500k paired evaluation](ppo_run_003_500k/ppo_paired_evaluation.json)
