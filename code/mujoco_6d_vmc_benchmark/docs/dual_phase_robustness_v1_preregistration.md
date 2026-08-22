# Dual-phase robustness v1（服务器执行前预注册）

这是一组独立于已锁定 `dual_phase_longitudinal_20260822` 结果的新实验。
旧结果不覆盖、不重解释；新协议只有在服务器上的 MuJoCo 物理审计通过后才进入报告。

## 研究问题

当前 ESN 在双板任务上相对 VMC 的优势很小，原因可能有两类：

1. 原协议的板位和接触参数变化较窄，四种策略都能轻松完成任务；
2. ESN 是 VMC behavioral cloning，长时间零残差样本淹没了稀疏的接触响应标签。

因此本协议同时检验统一的 sim-to-real 难度和独立 ESN 的直接策略学习。

## 物理与公平性

- 仍使用 FR3 + Panda Hand 的 MuJoCo 实体模型；板固定在 world，不在 episode 内移动；抓取仍由真实手指接触完成。
- PaperMPC、VMC、MLP、ESN 使用同一条件、seed、双板/reference、4% residual budget、torque clamp。
- qdot 噪声由环境统一加入所有残差控制器的测量通道；残差 FIFO delay 在控制器输出之后统一加入 VMC/MLP/ESN。PaperMPC 的零残差不受该 FIFO 影响。
- ESN/MLP 在线输入仍为 `q(7), qdot(7), nominal_twist(6), WBC pose error(6), WBC twist error(6)`。板位、法向、接触力、接触标签、接触时刻、物块状态和未来轨迹均不进入 policy。
- 所有条件必须通过：无初始接触、双阶段顺序正确、板只接触 hand/link7、无 object-board contact、有限状态、penetration ≤ 2 mm。

## 预注册条件

条件表直接写在 `scripts/evaluate_dual_phase_robustness.py` 的 `CONDITIONS` 中：

| split | board y (m) | board z (m) | contact `solref` time constant (s) | qdot noise (rad/s) | residual delay |
|---|---:|---:|---:|---:|---:|
| development × 4 | 0.0015–0.0060 | ±0.0015–0.0025 | 0.010–0.022 | 0.004–0.008 | 0 / 1 frame |
| held-out × 4 | 0.00225–0.00525 | ±0.0010–0.0030 | 0.012–0.024 | 0.005–0.009 | 0 / 1 frame |

数值在看到任何方法得分前固定。先运行 `--methods PaperMPC --split all`，若这个零 residual 的几何/物理 gate 失败，调整的是场景可行性而不是策略；不得把失败条件纳入成功率。VMC、MLP 和 ESN 的首次运行开始即是策略结果，不能再据此修改条件表。

## 独立 ESN 策略学习

`scripts/train_dual_phase_esn_ars.py` 从**零 readout**的 Direct ESN 开始。它不读取 VMC checkpoint、VMC teacher trace、VMC action 或 VMC 参数；VMC 仅在最终公平评测时作为 baseline。

- 固定随机 recurrent reservoir 是 policy 的时序状态/特征；
- 低维、固定随机 readout basis 参数化完整 7-D readout；
- antithetic random search 对同一批 development MuJoCo 条件执行正负成对扰动；
- 更新信号仅是 ESN 自己 rollout 的标量回报；
- 回报先要求双阶段 task/物理审计通过，之后才优化 pre/post force、pre/post impulse 和 peak jerk。

接触、板和物块的 metadata 只在训练环境内部生成 scalar reward，不会进入 ESN observation、reservoir 或 action function。所有 selection 只在 development 条件完成；held-out 条件不能参与 ESN 更新或 early stopping。

## 服务器执行顺序

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
export MUJOCO_GL=osmesa
export PYTHONPATH=.
python=/home/arm1/vmc_mujoco_runtime/.venv/bin/python

# 1. 只写预注册 manifest；不产生仿真结果
$python evaluate_dual_phase_robustness.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --out /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_robustness_v1/protocol.json \
  --manifest-only

# 2. 物理 gate（四方法尚未进入选择）
$python evaluate_dual_phase_robustness.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --out /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_robustness_v1/gate.json \
  --methods PaperMPC --split all

# 3. 独立 ESN policy search（仅 gate 通过后；不输入、不读取 VMC teacher）
$python train_dual_phase_esn_ars.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --out-dir /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_robustness_v1/esn_ars_independent

# 4. 用 ARS 的 best development checkpoint 跑 held-out 四方法
$python evaluate_dual_phase_robustness.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --out /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_robustness_v1/heldout.json \
  --esn /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_robustness_v1/esn_ars_independent/esn_ars_independent_best.npz \
  --mlp /home/arm1/vmc_mujoco_runtime/outputs/dual_phase_longitudinal_20260822/models/mlp_h128_s20265601.npz \
  --split held_out
```

ARS 的 `esn_ars_independent_best.npz` 只能由 development return 决定；不能先看 held-out 指标再选择 checkpoint、迭代数或难度条件。

## 结果解释边界

如果 ESN 在 held-out 仍不能稳定超过 VMC 或 MLP，应报告“该困难协议下未胜出”。如果只改善峰值力而牺牲抓取/搬运或物理审计，也不能称为更优。所有结论必须同时列出成功率、pre/post peak force、pre/post impulse、peak jerk、最终抬升和审计失败数。
