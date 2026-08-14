# 因果滞回恢复门控：zero-residual 预训练验证

## 目的

上一轮 PPO 的残差门控平均只开启约 `0.0543`，使策略在受撞后的实际恢复区间几乎没有连续介入机会。本次在不改变六弹簧通道定义、且不向 actor 提供接触力／杆状态／障碍物信息的前提下，增加了一个由**测得末端跟踪误差**触发的短暂滞回窗口。

触发条件为现有平滑位置误差门控达到 `0.05`；随后将残差与 return-drive 的可用窗口保持 `0.28 s`。它是一个可部署的因果状态机：仅保存“此前是否观测到显著偏离”的内部状态，不使用杆释放时刻或任何碰撞标签。

## 固定 zero-residual 配对实验

- 六弹簧刚度：`[27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858]`；
- contact carriage-drive=`8`，recovery target drive=`14`；
- 四个有效物理 rod fixture，均有同配置 no-rod 配对；
- 策略动作固定为零（因此差异仅来自新的静态、误差触发门控）；
- 有效碰撞门槛：峰力 ≥`15 N`、冲量 ≥`0.45 Ns`；
- 服务器原始结果：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/ppo_drive_hold_run_001/evaluation_zero/zero_drive_residual_paired_evaluation.json`。

| 指标 | 旧 zero-residual（无滞回） | 新 zero-residual（0.28 s 滞回） | 变化 |
|---|---:|---:|---:|
| task / effective collision / no-rod success | 4 / 4 / 4 | 4 / 4 / 4 | 无任务退化 |
| 平均残差门控 | 0.0543 | 约 0.173 | 约 3.2× 更长可用恢复窗口 |
| 峰值配对偏差 | 14.736 mm | 14.480 mm | -1.7% |
| 配对 RMSE | 2.214 mm | 2.146 mm | -3.1% |
| 回归 RMSE | 1.921 mm | 1.550 mm | **-19.3%** |
| 峰值力矩 | 30.381 Nm | 30.361 Nm | -0.06% |
| Jerk 峰值 | 1236.3 m/s³ | 1236.7 m/s³ | +0.03%，基本持平 |

## 决策

新的因果滞回门控本身已在四个严格配对的有效碰撞 fixture 中改善回归精度，且未牺牲抓取成功或力矩安全。因此可以作为第二轮 PPO 的固定 zero-residual 对照；第二轮 PPO 只能在这个更强的静态机制之上取得改进，才算有效 RL 增益。

本记录仅陈述 MuJoCo 物理仿真结果，不代表实机结论，也不将 no-rod 参考描述为在线 WBC。
