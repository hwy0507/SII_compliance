# Inclined-board yaw sweep（MuJoCo）

日期：2026-08-21  
代码版本：本地分支 `paper-mpc-baseline`，基于 `2ffba3a` 的角度扩展  
服务器：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`  
输出目录：`/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_sweep_20260821/`

## 实验定义

- 木板是 MuJoCo 中的静态 box，半尺寸 `0.18 × 0.05 × 0.008 m`，摩擦参数 `0.15 0.02 0.002`，倾角 `40°`。
- `yaw=0°` 是原始侧向接触基准；增加 yaw 是绕世界 z 轴旋转木板，姿态为 `Rz(yaw) Rx(tilt)`。
- 所有学习策略输入仍为原来的 32-D：`q, qdot, nominal_twist, wbc_pose_error, wbc_twist_error`。木板位姿、接触力、法向和接触时刻只用于离线审计。
- 四种方法均使用 2% torque-residual budget：PaperMPC、VMC、MLP、ESN。MLP/ESN 使用之前在 yaw=0° 的斜板 teacher traces 上训练的 checkpoint，以下角度结果属于跨角度泛化测试，没有把 yaw 或接触信息喂给策略。
- 每个核心角度 5 个 held-out seeds，木板中心 y 方向加入确定性 ±8 mm 范围内的随机扰动；所有 30/30 核心 episodes 的首次接触均晚于抓取时刻 `2.4 s`。
- 入射角审计量：
  `normal_speed_fraction = |v_hand · n_board| / ||v_hand||`。
  它越接近 1，越接近法向/正面撞击；越接近 0，越接近沿板面切向滑移。

## 核心角度结果

下表为 5-seed 均值；成功率是任务最终物块保持成功率，`Fpeak` 为木板峰值接触力，`J` 为接触冲量，`ηn` 为首次接触法向速度占比。

| yaw | PaperMPC | VMC | MLP | ESN | 解释 |
|---:|---|---|---|---|---|
| 0° | 5/5; Fpeak 94.0 N; J 51.9 N·s; ηn .242 | 5/5; 92.4; 37.8; .418 | 5/5; 91.3; 37.6; .291 | 5/5; 97.4; 36.6; .301 | 原始侧向/斜向接触基准 |
| 30° | 5/5; 21.6; 14.8; .016 | 5/5; 21.7; 11.8; .009 | 5/5; 23.8; 11.5; .009 | 5/5; 19.8; 8.0; .076 | 近切向擦碰，法向分量很小 |
| 45°* | 5/5; 52.6; 9.4; .172 | 5/5; 53.1; 8.5; .303 | 5/5; 55.2; 9.0; .196 | 5/5; 64.5; 7.1; .256 | 斜前角补充角度，见下方说明 |
| 60° | 5/5; 103.1; 15.9; .628 | 1/5; 100.9; 33.7; .711 | 5/5; 102.5; 21.9; .705 | 5/5; 106.0; 25.6; .655 | 强斜向/接近法向 |
| 90° | 5/5; 124.7; 91.1; .693 | 5/5; 125.5; 34.4; .794 | 5/5; 116.4; 72.1; .787 | 5/5; 116.5; 70.2; .553 | 正面候选：法向分量最高的一组 |
| 120° | 5/5; 134.2; 93.6; .140 | 5/5; 117.6; 16.3; .236 | 5/5; 120.6; 29.3; .147 | 5/5; 121.4; 31.8; .243 | 另一侧斜向接触 |
| 150° | 0/5; 112.8; 86.3; .609 | 5/5; 108.1; 24.9; .196 | 5/5; 107.9; 39.8; .162 | 5/5; 108.7; 44.2; .730 | 反向斜前角；PaperMPC 失败 |

整体（核心 6 角度 × 5 seeds）：

| 方法 | 成功率 | 平均峰值力 | 平均冲量 | 平均接触后峰值位姿误差 |
|---|---:|---:|---:|---:|
| PaperMPC | 25/30 = 83.3% | 98.4 N | 58.9 N·s | 208.7 mm |
| VMC | 26/30 = 86.7% | 94.4 N | 26.5 N·s | 154.6 mm |
| MLP | 30/30 = 100% | 93.8 N | 35.4 N·s | 157.8 mm |
| ESN | 30/30 = 100% | 95.0 N | 36.1 N·s | 153.6 mm |

`*` yaw=45° 的 5-seed 结果单独运行，使用同一 2% budget 和同一几何门控；它是斜前角补充实验，不改变核心 6 角度总表。

## 当前可汇报结论

1. yaw=90° 是当前最接近“末端正面撞到斜木板”的可复现实验：首次接触平均约 2.95 s，法向速度占比约 0.55–0.79，接触发生在抓取之后；不存在初始穿模。
2. 在同一 2% 残差预算、相同 32-D 输入和相同 MuJoCo 力学模型下，ESN 在 6 角度 × 5 seeds 中为 30/30 成功，且平均接触后误差略低于 VMC；这说明当前 yaw 泛化测试中 ESN 没有出现原先“学习策略明显不如物理策略”的现象。
3. 这不是“ESN 已经学习了 yaw”的证据：checkpoint 只在 yaw=0° 斜板 teacher traces 上训练，yaw 是测试时的场景变化。若要把多角度作为 proposed method 的正式训练能力，需要另行采集多 yaw teacher traces，并做角度分离的 train/validation/test。
4. `normal_speed_fraction` 仅用于离线分型，不会进入部署策略。接触力和板法向也没有作为 ESN/MLP 输入。

## 复现实验与动图

完整核心 JSON：

`/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_sweep_20260821/four_method_core_angles.json`

本地同步 JSON：

`code/mujoco_6d_vmc_benchmark/outputs/inclined_lift_angle_sweep_20260821/four_method_core_angles.json`

正面候选 yaw=90° GIF：

`/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_sweep_20260821/gifs_yaw90/`

斜前角 yaw=45° GIF：

`/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_angle_sweep_20260821/gifs_yaw45/`

对应脚本：`scripts/evaluate_inclined_lift_four_method.py`、`scripts/probe_inclined_lift_contact.py`、`scripts/render_inclined_lift_four_method_gifs.py`。

## 限制

- 当前角度 sweep 是单一倾角 `40°`；不能把它表述成对所有木板姿态的泛化。
- 90° 的“正面”是通过法向速度占比定义的运动学类别，而不是仅依据相机视角命名。
- 角度变化改变了碰撞几何和接触时序；若要做论文主结论，下一轮应以 yaw 作为训练/验证/测试划分变量重新训练 ESN 和 MLP，并保留未见角度测试。
