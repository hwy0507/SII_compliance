# Fan Ye ESN 状态条件 PPO：3-seed post-V4 development 复现

## 结论

run001 的恢复改善**没有在三次独立训练中稳定复现为全面优势**。final checkpoint 的三 seed 平均 recovery RMSE 为 **1.696 ± 0.050 mm**，比确定性的 zero-residual 基线 1.726 mm 低 1.74%；但只有 2/3 seed 改善，seed 20260816 为 1.763 mm、反而比基线高 2.16%。同时，平均 rejoin latency 从 0.0322 s 变为 0.0352 s（+9.2%）。

因此，目前可说的是“PPO 有时可改善撞后 recovery RMSE”，不能说“RL 已稳定优于解析 VMC”，更不能将 run001 单一最佳结果作为普适结论。

## 锁定的复现协议

所有 seed 均锁定 run001 的以下要素，仅改变 PPO 随机种子：

| 项目 | 固定值 |
|---|---|
| 仿真与任务 | MuJoCo 固定底座 Franka Panda；fixed Panda WBC nominal；物理杆撞击末端后离开 |
| 训练 / 验证数据 | post-V4 development train 9 fixtures / 独立 validation 9 fixtures |
| ESN | 固定 Fan Ye 时间尺度匹配 reservoir #22；actor 为 84D 可部署观测 |
| actor 禁止输入 | 接触、力、杆状态、障碍姿态/几何、未来相位、fixture ID、recovery gate |
| 动作 | 6D log-stiffness residual + 1D return-drive residual |
| 安全 | 相同 causal tracking-error gate、rate limit 与 incremental energy safety |
| PPO | 8 env、请求 400k steps、实际 401,408 steps、相同 reward/learning-rate schedule |
| 验证 | 每个 seed 的冻结 200k 与 final checkpoint；确定性 matched rod/no-rod rollout |

新增的独立 seed 为 20260816（run002）和 20260817（run003）。它们与 run001（20260815）共同构成 3-seed 汇总。V4 final 继续冻结，未用于训练、选择或调参。

## 每 seed 的完整验证摘要

| checkpoint | seed | task / no-rod | effective collision | recovery RMSE ↓ (mm) | rejoin ↓ (s) | paired RMSE ↓ (mm) | jerk ↓ (m/s³) | impulse ↓ (N·s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| zero-residual | — | 9/9 / 9/9 | 8/9 | 1.726 | 0.0322 | 2.215 | **955.87** | 3.177 |
| PPO 200k | 20260815 | 9/9 / 9/9 | 9/9 | 1.694 | 0.0322 | 2.201 | 958.18 | 3.176 |
| PPO 200k | 20260816 | 9/9 / 9/9 | 8/9 | 1.791 | 0.0367 | 2.245 | 991.93 | **3.090** |
| PPO 200k | 20260817 | 9/9 / 9/9 | 9/9 | 1.711 | 0.0367 | 2.222 | 957.77 | 3.200 |
| PPO final | 20260815 | 9/9 / 9/9 | 9/9 | **1.644** | 0.0322 | **2.183** | 958.63 | 3.249 |
| PPO final | 20260816 | 9/9 / 9/9 | 8/9 | 1.763 | 0.0367 | 2.242 | 964.57 | 3.120 |
| PPO final | 20260817 | 9/9 / 9/9 | 9/9 | 1.681 | 0.0367 | 2.197 | 957.42 | 3.253 |

## 跨 seed 汇总

下表的均值和标准差以三次训练的“每 seed、9 fixture 平均指标”为统计单元；不是把 27 条 episode 当作独立 RL 训练重复。zero-residual 是确定性控制器，只有一个值。

| 方法 | task / no-rod（27 episode） | effective collision（27 episode） | recovery RMSE ↓ (mm) | rejoin ↓ (s) | paired RMSE ↓ (mm) | jerk ↓ (m/s³) | impulse ↓ (N·s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| zero-residual | 27/27 / 27/27 | reference 8/9 | 1.726 | **0.0322** | 2.215 | **955.87** | 3.177 |
| PPO 200k | 27/27 / 27/27 | 26/27 | 1.732 ± 0.042 | 0.0352 ± 0.0021 | 2.223 ± 0.018 | 969.29 ± 16.01 | **3.155 ± 0.047** |
| PPO final | 27/27 / 27/27 | 26/27 | **1.696 ± 0.050** | 0.0352 ± 0.0021 | **2.207 ± 0.025** | 960.20 ± 3.12 | 3.208 ± 0.062 |

相对 zero-residual 的变化：

- **PPO 200k**：recovery RMSE +0.36%（更差），rejoin +9.2%，paired RMSE +0.34%，jerk +1.40%，impulse -0.68%。
- **PPO final**：recovery RMSE -1.74%，paired RMSE -0.36%，但 rejoin +9.2%、jerk +0.45%、impulse +0.97%。
- 两个 PPO checkpoint 的 task 与 no-rod task 都是 27/27；但 effective collision 皆为 26/27，而 zero-residual 的单次基线为 8/9。这个计数受某个工况接触峰值恰好跨越 effective-force 阈值影响，不能单独被用作 PPO 优势证据。

## 科研解释与决策

1. **run001 是最优 seed，不是代表 seed。** final 的 RMSE 三个值为 1.644、1.763、1.681 mm；其中第二个 seed 退化，说明训练方差不能忽略。
2. **final 比 200k 更可能带来恢复收益。** 三 seed 上 final 的平均 RMSE 与 paired RMSE 都低于 200k；但它仍未同时改善 rejoin、jerk、impulse。
3. **不进行显著性宣称。** 这里只有 3 次独立训练，且标准差与均值改善同量级；当前没有足够证据声称 statistically reliable improvement。
4. **当前推荐。** 将 zero-residual 作为主解析 baseline；将 PPO final 标为“有条件的 recovery-improving candidate”，而不是主方法的定论。200k 可作为较低冲量的 checkpoint，但其平均 recovery 并无优势。
5. **下一项应改变的不是 test。** 保持 V4 final 冻结；在 development 中先以多目标约束/选择直接约束 rejoin 与 jerk/impulse，再做额外 seed。只有在该改动预先冻结后，才应进入一次最终 V4 holdout。

## 工件与可追溯性

新增逐 fixture JSON：

- `ppo_run002_seed20260816_validation_200k.json`
- `ppo_run002_seed20260816_validation_final.json`
- `ppo_run003_seed20260817_validation_200k.json`
- `ppo_run003_seed20260817_validation_final.json`

权重不进入 Git。远端持久保存目录为：

- `/home/arm1/vmc_mujoco_runtime/artifacts/esn_wbc_fan_ye_ppo_dev_run002_seed20260816/`（final SHA-256：`3059c3a369e0a47390bf1b97302463773db99325287e3a0e097aee85609e950d`）
- `/home/arm1/vmc_mujoco_runtime/artifacts/esn_wbc_fan_ye_ppo_dev_run003_seed20260817/`（final SHA-256：`67a3e85115aebe419e32ef4dfcd47b29eb8ff6749a3a6ea3e637f91d32bc77b9`）

评估启动时有一次仅涉及日志重定向目录未创建的 preflight 失败；该命令在 Python 进程启动前退出，未产生任何评估结果。目录创建后重新启动的四项评估均正常完成，上述 JSON 是唯一纳入统计的输出。
