# 40 ms tapered-gate PPO：四随机种子复现

## 结论

此前 `seed=20260818` 的 100k checkpoint 在固定主/held-out 工况上恰好同时改善回归误差并略微降低 jerk。本次新增 `20260819`、`20260820`、`20260821` 三个独立训练 seed，固定所有训练、控制、评估参数，仅改变 PPO 随机数。

**已复现的结论**是：40 ms tapered-gate PPO 在四个 seed 中都保持任务成功和有效碰撞，并稳定降低碰撞后回归误差、配对轨迹偏差。

**未复现的结论**是：相对 zero residual 的峰值 jerk 不上升。只有原始 seed 的 jerk 略低于 zero；三个新增 seed 均有小幅 jerk 上升。因此不再把该策略描述为“严格安全 Pareto 改善”，而是“具有可复现恢复收益、但仍有小幅 jerk 权衡的 PPO 候选”。

## 固定协议

- 训练：100k PPO steps、8 并行环境、7 actions（六维弹簧刚度 residual + return-drive residual）。
- 控制：causal error-gated recovery hold `0.28 s`；末端 taper `0.04 s`；正常 action rate limits `1.6 /s`（kappa）和 `1.0 /s`（drive）。
- 策略观察不使用 rod contact、力、杆状态、障碍物状态或未来时间；门控只使用 nominal 与测得末端的位置误差。
- 主 benchmark：4 个预先固定的有效实体杆碰撞 fixture。
- held-out：8 个预声明 fixture，其中 2 个为弱碰撞，按既定规则不混入性能均值。
- 所有结果均为冻结、确定性策略下的 matched rod/no-rod MuJoCo 物理 rollout；no-rod 是任务匹配参考，不是在线 WBC。

## 主 fixture：4 个有效碰撞，四 seed 汇总

四个 seed 都为 `4/4` task success、`4/4` effective collision、`4/4` matched no-rod success，无硬力矩限幅。

| 指标（四 seed 均值 ± seed 标准差） | Zero residual | Taper PPO 100k（4 seeds） | 相对 zero |
|---|---:|---:|---:|
| 峰值配对偏差 | 14.480 mm | 13.967 ± 0.046 mm | -3.5% |
| 配对 RMSE | 2.146 mm | 2.025 ± 0.010 mm | -5.6% |
| 回归 RMSE | 1.550 mm | 1.519 ± 0.025 mm | -2.0% |
| 峰值力矩 | 30.361 Nm | 30.352 ± 0.007 Nm | -0.03% |
| 峰值 jerk | 1236.67 m/s³ | 1249.85 ± 13.66 m/s³ | +1.1% |

主工况各 seed 的 recovery RMSE 为 `1.523`、`1.548`、`1.517`、`1.488 mm`，均不高于 zero residual 的 `1.550 mm`。相反，jerk 为 `1235.98`、`1268.52`、`1245.55`、`1249.37 m/s³`：仅第一个 seed 低于 zero residual，说明单 seed 的小 jerk 下降不稳健。

## Held-out：6 个有效碰撞，四 seed 汇总

四个 seed 都为 `8/8` rod task success、`6/8` effective collision、`8/8` no-rod task success。有效碰撞仍是相同 6 个 fixture；另外两个 fixture 在每个 seed 中均为弱碰撞而不是任务失败。

| 指标（有效 fixture；四 seed 均值 ± seed 标准差） | Zero residual | Taper PPO 100k（4 seeds） | 相对 zero |
|---|---:|---:|---:|
| 峰值配对偏差 | 19.278 mm | 18.915 ± 0.022 mm | -1.9% |
| 配对 RMSE | 2.934 mm | 2.828 ± 0.005 mm | -3.6% |
| 回归 RMSE | 1.517 mm | 1.477 ± 0.022 mm | -2.6% |
| 峰值力矩 | 30.410 Nm | 30.418 ± 0.010 Nm | +0.03% |
| 峰值 jerk | 1578.8 m/s³ | 1588.15 ± 28.80 m/s³ | +0.6% |

这证明恢复与配对轨迹改善具有跨 seed、跨 held-out 碰撞几何的一致性；但 jerk 的均值轻微上升，并具有明显 seed 方差。因此 jerk 仍是下一阶段的实际研究瓶颈。

## 对主张的更新

| 原先的单 seed 观察 | 多 seed 后的严谨表述 |
|---|---|
| “不增加 jerk 的安全 Pareto 改善” | 不成立为可复现主张；仅在 1/4 seed 中观察到。 |
| “PPO 可改善回归和配对轨迹偏差” | 成立：主与 held-out 四 seed 汇总均改善，且成功/接触门槛保持。 |
| “旧 PPO 是最佳恢复精度” | 仍成立：旧 binary-gate PPO 300k 的 recovery RMSE 更低，但 jerk 代价也更明显。 |

## 原始文件

- `seed_20260819_main.json`、`seed_20260820_main.json`、`seed_20260821_main.json`：三个新增 seed 的主 fixture 完整记录。
- `seed_20260819_heldout.json`、`seed_20260820_heldout.json`、`seed_20260821_heldout.json`：三个新增 seed 的 held-out 完整记录。
- 原始 seed `20260818` 的记录位于相邻的 `ppo_drive_hold_taper_run_001/` 目录。

## 下一步

后续优化不应再依赖“单 seed 的 jerk 优势”。可保留 40 ms taper，因为它没有破坏静态回归机制且带来了可复现的恢复收益；随后需要针对 jerk 的来源设计受约束的 residual-direction smoothing 或控制器侧 safety filter，并继续要求多 seed 主/held-out 验证。
