# Targeted PPO reward ablation：500k 阶段结果

## 目的

Run_003 暴露了固定学习率 PPO 的 KL 漂移，但其物理指标在 300k 后平台化。本 run 定向修改了 PPO 数值稳定性和碰撞后恢复 reward：

- `n_epochs=5`、`clip_range=0.15`、`target_kl=0.015`；
- 学习率从 `2e-4` 线性衰减到 `5e-5`；
- 杆加载窗口降低轨迹惩罚，杆释放后的 recovery window 增加位置误差和 recovery-progress reward；
- actor 仍只接收 51 维部署本体状态，reward 内部的释放窗口不进入 actor observation。

## 结果

| checkpoint | task / effective / no-rod | peak paired offset | paired RMSE | recovery RMSE | peak torque |
|---|---|---:|---:|---:|---:|
| 100k | 4/4 / 4/4 / 4/4 | 17.24 mm | 2.907 mm | 2.224 mm | 30.311 Nm |
| 400k | 4/4 / 4/4 / 4/4 | 17.39 mm | 2.930 mm | 2.201 mm | 30.295 Nm |
| 500k | 4/4 / 4/4 / 4/4 | 17.63 mm | 2.974 mm | 2.206 mm | 30.297 Nm |

500k 的 rejoin latency 仍为 `22.5 ± 9.0 ms`，峰值 jerk 为 `1232.79 ± 126.25 m/s³`，峰值接触力为 `38.69 ± 13.93 N`，冲量为 `1.731 ± 0.519 Ns`。

## 判断

这次修改成功解决了数值层面的 KL 漂移：训练期间 KL 约 `0.005`，而 run_003 后期约 `0.03--0.036`。但它没有解决物理层面的退化：峰值偏移和配对 RMSE 没有改善，500k 反而略差；恢复 RMSE 只在误差范围内小幅波动。因此该 ablation **不是成功的 RL 优化结果**，不能宣称超过 static VMC。

Run 已在 500k 完成后停止，所有 checkpoint 与冻结配对评测均保留。下一步应优先检查动作是否真的在碰撞后偏离 warm-start，以及重新设计“安全让步—恢复”的可辨识 credit assignment，而不是继续增加相同训练预算。
