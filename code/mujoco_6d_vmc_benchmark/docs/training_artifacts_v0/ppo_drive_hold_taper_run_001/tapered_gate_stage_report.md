# PPO tapered-gate run 001：小幅 Pareto-safe 阶段结果

## 结论

本轮在上一版因果二值滞回门控上只加入了 `40 ms` 的**末端平滑渐变**。在主 fixture 和预声明 held-out fixture 中，`100k` checkpoint 都相对同环境 zero residual 同时降低回归误差，且 jerk 没有升高。因此它是目前第一个跨两组测试的 **Pareto-safe 候选**。

这一收益幅度很小，不能称为最终方法突破；相对旧 PPO 的最佳恢复精度，它仍有回归误差差距。`300k` checkpoint 提供更强的恢复精度，但也重新引入少量 jerk 上升，故作为第二个精度优先候选保留。

## 机制与因果性

旧门控在可测末端轨迹误差超过阈值时，持续打开 `0.28 s`，并在窗口结束时二值关断。新机制仅在误差下降、保持窗口倒计时时，把门控从 1 通过 smoothstep 连续衰减到 0：

- hold：`0.28 s`；
- taper：`0.04 s`；
- PPO action：六个弹簧刚度残差 + 一个 virtual-carriage return-drive residual；return-drive 不是第七根弹簧；
- PPO 仍不观察接触、接触力、杆状态、障碍物几何或未来释放时刻；门控只使用 nominal 与实测末端位置误差。

选择 `40 ms` 的依据是静态 zero-residual 扫描：完整 `280 ms` 渐变会使恢复 RMSE 恶化为 `1.624 mm`，而 `40 ms` 渐变保留 `1.550 mm` 的静态恢复性能与全部任务/接触门槛。故它是最小、可解释的控制器改动，而不是事后为图形调参。

## 主 fixture：4 个有效实体杆碰撞

所有 checkpoint 均为 `4/4` task success、`4/4` effective collision、`4/4` matched no-rod success，无硬力矩限幅。有效碰撞保持预固定双门槛：峰值接触力至少 `15 N`、接触冲量至少 `0.45 Ns`。

| 指标（均值） | Zero residual | 旧 PPO 最优 300k | Taper PPO 100k | Taper PPO 200k | Taper PPO 300k |
|---|---:|---:|---:|---:|---:|
| 峰值配对偏差 (mm) | 14.480 | **13.931** | 13.932 | 13.986 | 14.010 |
| 配对 RMSE (mm) | 2.146 | **1.999** | 2.018 | 2.027 | 2.018 |
| 回归 RMSE (mm) | 1.550 | **1.456** | 1.523 | 1.494 | 1.474 |
| 峰值力矩 (Nm) | 30.361 | 30.358 | **30.352** | 30.358 | 30.375 |
| 峰值 jerk (m/s³) | 1236.67 | 1271.9 | **1235.98** | 1246.64 | 1256.68 |

相对 zero residual，100k 的回归 RMSE 从 `1.550` 降至 `1.523 mm`（`-1.7%`），jerk 从 `1236.67` 微降至 `1235.98 m/s³`（`-0.06%`）。300k 将回归 RMSE 降至 `1.474 mm`（`-4.9%`），但 jerk 升至 `1256.68 m/s³`（`+1.6%`）。

## Held-out：8 个预声明测试几何

所有 8 个几何均完成 rod 与 no-rod 任务。其中 fixture 2 与 fixture 3 的接触分别约为 `14.89 N / 0.350 Ns`、`11.04 N / 0.075 Ns`，不同时通过有效碰撞门槛；它们作为弱碰撞完整保留，但不混入性能均值。下表只聚合 6 个有效 held-out 碰撞。

| 指标（6 个有效 fixture 均值） | Zero residual | 旧 PPO 最优 300k | Taper PPO 100k | Taper PPO 300k |
|---|---:|---:|---:|---:|
| 峰值配对偏差 (mm) | 19.278 | **18.892** | 18.897 | 18.935 |
| 配对 RMSE (mm) | 2.934 | **2.796** | 2.822 | 2.808 |
| 回归 RMSE (mm) | 1.517 | **1.415** | 1.481 | 1.431 |
| 峰值力矩 (Nm) | **30.410** | 30.421 | 30.433 | 30.438 |
| 峰值 jerk (m/s³) | 1578.8 | 1620.7 | **1577.7** | 1602.9 |

100k checkpoint 相对 zero residual：回归 RMSE `-2.4%`，配对 RMSE `-3.8%`，峰值配对偏差 `-2.0%`，jerk `-0.07%`。这与主 fixture 的方向一致，且保持了任务与有效碰撞门槛。300k checkpoint 则将 held-out 回归 RMSE 降到 `1.431 mm`（比 zero 低 `5.7%`），但 jerk 高于 zero、低于旧 PPO 最优。

## 当前结果层级

| 目标 | 应采用的候选 | 原因 |
|---|---|---|
| 最低回归误差 | 旧因果滞回 PPO 300k | 主 `1.456 mm`，held-out `1.415 mm`，但 jerk 上升。 |
| 安全 Pareto 对照 | 新 taper PPO 100k | 主与 held-out 均相对 zero residual 降低回归误差，且 jerk 不上升。 |
| 精度—jerk 折中 | 新 taper PPO 300k | 回归显著优于 zero，jerk 显著低于旧 PPO 最优，但仍略高于 zero。 |

因此，当前可以严谨地展示两条互补的学习结果：旧 PPO 展示更强的**恢复精度上限**；taper PPO 100k 展示不以 jerk 增加为代价的**安全 Pareto 改善**。二者均不替代静态基线，也不能把 no-rod 匹配参考写成在线 WBC。

## 原始结果

- `taper_040ms_zero_validation.json`：40 ms 门控尾部的静态机制验证。
- `main_evaluation_100k.json`、`main_evaluation_200k.json`、`main_evaluation_300k.json`：主 fixture 完整配对记录。
- `heldout_evaluation_100k.json`、`heldout_evaluation_300k.json`：held-out 完整配对记录，含弱碰撞条目。

## 下一步

不要进一步延长 taper：静态扫描已经表明 80–280 ms 会撤掉必要的 return drive。下一步应围绕已验证的 `40 ms` 门控，把 PPO 的训练选择从“时间步数越多越好”改为受主/held-out safety envelope 约束的 checkpoint 选择，并进一步研究只针对 residual **变化方向**而非全局速率的平滑正则。任何候选都必须继续满足主/held-out task success、有效碰撞和 no-rod 匹配成功。
