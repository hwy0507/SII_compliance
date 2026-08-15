# Fan Ye ESN 状态条件 PPO：post-V4 development run001

## 一句话结论

这次训练已完成，并在未参与训练的 post-V4 validation 九个物理碰撞工况上完成了同环境、同随机种子、成对 rod/no-rod 评估。PPO 的确能把平均恢复 RMSE 从 zero-residual 的 **1.726 mm** 降至 **1.644 mm**（final，-4.75%），并把九个工况的有效碰撞率从 8/9 提升为 9/9；但代价是接触冲量上升 2.27%、峰值 jerk 上升 0.29%。因此它是一个有条件的恢复改善，**不是**对解析 VMC 的全面超越，也不能视为新的 final/generalization 结论。

本页是 post-V4 development 记录。已冻结的 V4 final 从未用于 PPO 训练、checkpoint 选择或本轮任何参数修改。

## 研究对象与控制接口

- 机器人与任务：MuJoCo 中固定底座 Franka Panda，沿 WBC nominal 下探、抓取与抬升；运动的物理杆在末端附近撞击，随后离开。
- 被控柔顺层：六维 virtual-carriage / VMC。六个动作通道是六个弹簧刚度的对数残差；第七个动作仅调节 return-drive，**不是第七根弹簧**。
- RL 观测：20 维可部署 WBC 状态 `q(7) + qdot(7) + WBC task twist(6)`，再拼接一个固定、预先按 Fan Ye 等人的时间尺度匹配方法选中的 64 维 reservoir state，共 84 维。
- 明确排除的 policy 输入：接触标志、接触力、杆位姿/速度/几何、穿透量、未来释放时刻、fixture ID 与 recovery gate。gate 只由已测量的末端跟踪误差因果产生。
- 安全层：残差动作在 25 Hz 低通/速率限制后，经过增量 return-drive 能量预算与方向平滑，才以 250 Hz 进入 virtual-carriage 力计算；这不是全局严格 passivity 证明。

固定 reservoir 的原始输入与选择详情见 `fan_ye_esn_rl_interface_smoke.json` 及项目的 Fan Ye preselection 工件。训练配置的原始元数据见 `ppo_run001_training_metadata.json`。

## 训练协议

| 项目 | 固定设置 |
|---|---|
| 算法 | PPO state-feedback（非 CEM、非按时间表开关） |
| 并行环境 | 8 |
| 请求步数 / 实际结束步数 | 400,000 / 401,408（向量环境按完整 rollout 收尾） |
| 随机种子 | 20260815 |
| 训练工况 | post-V4 development/train 的 9 个有效物理 fixture |
| 验证工况 | post-V4 development/validation 的另 9 个有效物理 fixture |
| action | 6D log-stiffness residual + 1D return-drive residual |
| 关键 reward 系数 | recovery error 0.075；progress 0.040；action change 0.003；jerk 0.020 |
| 动作速率上界 | stiffness 1.6 log/s；drive 1.0 log/s |

训练过程数值稳定：约 565 FPS，最终 `approx_kl=0.00465`、`clip_fraction=0.0536`，未发现 NaN/Inf 或 traceback。这些优化量只表示 PPO 训练稳定，不能替代物理效果判据。

## 评估协议

每个 validation fixture 都运行一对确定性 MuJoCo rollout：一条带物理撞击杆，一条移除杆但保留其他条件。以下表格的 recovery 指标只统计杆释放后至 grasp 前的窗口；`effective collision` 使用项目既定的有效接触阈值。所有方案均开启相同的 WBC、六维 VMC、return-drive residual 接口、energy safety 与 gate，唯一差异是 PPO 动作：

- **zero-residual**：全部 7 个 residual action 固定为零；这是当前最严格的同环境解析基线。
- **100k / 200k / final**：冻结的 PPO checkpoint，deterministic rollout。

原始逐 fixture 数据：

- `ppo_run001_validation_zero_residual.json`
- `ppo_run001_validation_100k.json`
- `ppo_run001_validation_200k.json`
- `ppo_run001_validation_final.json`

## Validation 结果

| 方案 | task / no-rod task | effective collision | recovery RMSE ↓ (mm) | rejoin ↓ (s) | torque peak ↓ (Nm) | jerk peak ↓ (m/s³) | impulse ↓ (N·s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| zero-residual | 9/9 / 9/9 | 8/9 | 1.726 | 0.0322 | 30.529 | 955.87 | 3.177 |
| PPO 100k | 9/9 / 9/9 | 8/9 | 1.735 | 0.0367 | 30.532 | 972.16 | 3.180 |
| PPO 200k | 9/9 / 9/9 | 9/9 | 1.694 | 0.0322 | 30.530 | 958.18 | 3.176 |
| PPO final (401,408) | 9/9 / 9/9 | 9/9 | **1.644** | **0.0322** | **30.526** | 958.63 | 3.249 |

补充的轨迹偏离指标（rod 相对 matched no-rod）：

| 方案 | peak paired offset ↓ (mm) | paired-offset RMSE ↓ (mm) |
|---|---:|---:|
| zero-residual | 12.921 | 2.215 |
| PPO 100k | 12.972 | 2.222 |
| PPO 200k | 12.908 | 2.201 |
| PPO final | **12.839** | **2.183** |

## 如何解读，而不是过度解读

1. **早期 checkpoint 不够好。** 100k 同时使 recovery RMSE、rejoin、jerk、impulse 变差，并仍有 1 个非有效碰撞，不能选用。
2. **200k 是保守的平衡 checkpoint。** 它首次达到 9/9 task、9/9 matched no-rod task、9/9 effective collision；相对 zero-residual，RMSE 降 1.83%，冲量几乎相同（-0.02%），但 jerk 仍高 0.24%。
3. **final 是恢复最优 checkpoint。** 相对 zero-residual，recovery RMSE 降 4.75%，paired offset RMSE 降 1.46%，peak paired offset 降 0.64%，并使有效碰撞覆盖达到 9/9；但 impulse 增 2.27%，jerk 增 0.29%，平均接触力也略增 0.72%。
4. **当前 checkpoint 选择。** 若后续展示强调“撞后回归/轨迹贴合”，采用 final；若强调碰撞载荷的保守性，采用 200k。报告中应同时给出这两个 checkpoint，不能只保留对 PPO 有利的一列。
5. **没有证据表明全面超越。** torque、jerk、impulse 不是全部同步下降，rejoin 延迟在 200k/final 与基线相同。因此本轮的合理表述是：在该 development 验证池上，ESN-state-conditioned PPO 学到了一点恢复误差改进，但还存在冲量/平滑性的 trade-off。

## 有效性边界与下一步

- 本轮只是在 MuJoCo、固定 Panda/WBC 接口及指定杆碰撞工况中验证；没有硬件结果、sim-to-real 结论、严格 passivity 证明或任意三维障碍泛化结论。
- 训练与本页的 checkpoint 选择只用 post-V4 development train/validation；V4 final 仍保持冻结，之后最多做一次完全不再改参的最终评估。
- 远端模型已从临时目录转存到 `/home/arm1/vmc_mujoco_runtime/artifacts/esn_wbc_fan_ye_ppo_dev_run001_20260815/`。`ppo_sixd_final.zip` 的 SHA-256 为 `a48c3c72d67e9a7860c8c8947ce765741d17c0f4833709c25fb89707fb4103ab`，`vecnormalize.pkl` 的 SHA-256 为 `c39da5fa52dc95f6d684a08a3dfc16029fb7714a32a77e11a70f4209ce1520b9`。权重不纳入 Git，避免把二进制 checkpoint 伪装成源码协作工件；本仓库保存的是可审计配置、逐 fixture JSON 和报告。
- 最优先的改进是：用多 seed 的独立开发重复检查 final 与 200k 的差异是否稳定；然后针对 jerk/impulse 加入明确的多目标 checkpoint 选择或约束，而不是继续单纯拉长训练步数。
