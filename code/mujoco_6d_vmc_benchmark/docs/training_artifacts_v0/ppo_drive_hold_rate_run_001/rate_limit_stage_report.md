# PPO rate-limit run 001：训练完成后的严格配对评估

## 一句话结论

`ppo_drive_hold_rate_run_001` 已完成 300k steps。对 PPO 残差施加更低的变化率上限后，策略仍保持所有主工况成功，并相对 zero residual 改善轨迹偏差与回归误差；但是它**没有**同时把 jerk 降到上一版因果滞回 PPO 或 zero residual 以下。因此，这一轮是一个可解释的速度—恢复精度折中，不能替换当前的最佳恢复精度策略 `ppo_drive_hold_run_001`。

## 本轮唯一改动

除残差动作变化率外，训练协议与上一版因果滞回 PPO 一致：

- 动作：6 个虚拟弹簧刚度残差 + 1 个 virtual-carriage return-drive 残差；return-drive 不是第七根弹簧。
- actor 仍不接触 `rod_contact`、接触力、杆状态、障碍物几何或未来碰撞相位。
- 控制器保留只由可测轨迹误差触发的 `0.28 s` 因果滞回恢复门控。
- 新的速率上限：`kappa_max_log_rate_per_s = 0.8`、`drive_max_log_rate_per_s = 0.5`；此前为 `1.6` 和 `1.0`。
- 所有指标均来自冻结、确定性 PPO 下的 rod/no-rod 配对 MuJoCo rollout。no-rod 是相同任务的匹配参考，**不是**在线 WBC。

## 主 fixture：四个有效实体杆碰撞

三个 checkpoint 都为 `4/4` task success、`4/4` effective collision、`4/4` matched no-rod task success，且无硬力矩限幅。有效碰撞仍采用预先固定的门槛：峰值接触力至少 `15 N` 且接触冲量至少 `0.45 Ns`。

| 指标（均值） | Zero residual | 上一版 PPO 300k | 限速 PPO 100k | 限速 PPO 200k | 限速 PPO 300k |
|---|---:|---:|---:|---:|---:|
| 峰值配对偏差 (mm) | 14.480 | **13.931** | 14.227 | **14.191** | 14.201 |
| 配对 RMSE (mm) | 2.146 | **1.999** | 2.076 | **2.063** | 2.065 |
| 回归 RMSE (mm) | 1.550 | **1.456** | 1.540 | 1.481 | **1.479** |
| 峰值力矩 (Nm) | 30.361 | 30.358 | 30.362 | 30.363 | **30.357** |
| 峰值 jerk (m/s³) | **1236.7** | 1271.9 | **1262.0** | 1269.0 | 1276.6 |
| 回归到 5 mm 的平均时延 (s) | — | — | 0.0225 | 0.0225 | 0.0225 |

### 主工况判读

- 300k 限速 PPO 相对 zero residual：回归 RMSE 从 `1.550` 降至 `1.479 mm`（`-4.6%`），但 jerk 从 `1236.7` 升至 `1276.6 m/s³`（`+3.2%`）。
- 与当前最佳恢复精度的上一版 PPO 300k 相比，300k 限速策略的回归 RMSE 增加 `0.023 mm`（`+1.6%`），jerk 也增加 `4.7 m/s³`（`+0.4%`）。
- 100k checkpoint 的 jerk 最低，但仍高于 zero residual，并且回归改善几乎消失（`1.540 mm`）。因此没有一个 checkpoint 达到“更快回归且更低 jerk”的 Pareto 改善。

## 预声明 held-out：八个测试几何

300k checkpoint 在全部 8 个 held-out 几何中均完成任务，且 no-rod 匹配任务均成功。其中 fixture 2 与 3 分别只有 `14.89 N / 0.349 Ns`、`11.05 N / 0.075 Ns`，未同时越过有效碰撞门槛；它们是**弱碰撞**，不混入性能均值，也不是任务失败。

下表只聚合 6 个有效 held-out 碰撞：

| 指标（仅 6 个有效 fixture） | Zero residual | 上一版 PPO 300k | 限速 PPO 300k |
|---|---:|---:|---:|
| 峰值配对偏差 (mm) | 19.278 | **18.892** | 19.080 |
| 配对 RMSE (mm) | 2.934 | **2.796** | 2.863 |
| 回归 RMSE (mm) | 1.517 | **1.415** | 1.458 |
| 峰值力矩 (Nm) | **30.410** | 30.421 | 30.422 |
| 峰值 jerk (m/s³) | 1578.8 | 1620.7 | **1558.8** |
| 回归到 5 mm 的平均时延 (s) | — | — | 0.0216 |

### Held-out 判读

- 限速 PPO 相对 zero residual 仍降低回归 RMSE（`-3.9%`）和配对 RMSE（`-2.4%`），同时把 jerk 降低 `1.3%`。
- 但其回归 RMSE 比上一版 PPO 高 `0.043 mm`（约 `+3.0%`）。这说明限速确实在未见工况中削弱了激进动作，却也牺牲了上一版最明显的回归收益。
- 主工况的 jerk 没有改善，故不能把 held-out 的 jerk 下降单独解读成整体突破。

## 原始可复核结果

- `main_evaluation_100k.json`：100k checkpoint 的四工况完整记录。
- `main_evaluation_200k.json`：200k checkpoint 的四工况完整记录。
- `main_evaluation_300k.json`：300k checkpoint 的四工况完整记录。
- `heldout_evaluation_300k.json`：300k checkpoint 的八个预声明 held-out 完整记录，含弱碰撞标记。

服务器可复现 checkpoint 位于：`outputs/ppo_drive_hold_rate_run_001/checkpoints/ppo_sixd_{100000,200000,300000}_steps.zip`；评估时必须传入与训练一致的 `0.8 /s` 与 `0.5 /s` 速率上限。

## 决策

保留本轮作为“**控制器动作带宽约束的负/折中对照**”，不将其升级为主方法。当前主结果仍采用：

- **最佳恢复精度**：`ppo_drive_hold_run_001` 的 300k checkpoint；
- **最稳妥静态基线**：固定六维 CEM 刚度、contact drive `8`、recovery drive `14`、因果滞回恢复门控；
- **下一阶段的重点**：不要继续简单收紧全局速率上限。应针对接触后短时段设计平滑的、状态条件化的残差参数化或 safety filter，并在相同主/held-out 协议下验证是否能保留约 `1.456 mm` 主工况回归误差，同时把 jerk 至少压回 zero residual 的水平。
