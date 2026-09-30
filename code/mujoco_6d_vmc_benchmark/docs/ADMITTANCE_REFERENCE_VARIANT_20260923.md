# Panel reference-admittance development variant

当前 r2 variant 的 controller 名称为 `cartesian_admittance_reference_v2`，结果版本为 `shifted_wbc_reference_r2_snapshot_aligned`，入口为 `scripts/run_panel_admittance_reference_20260923.py`。它保持现有 panel 几何、名义任务、状态机、WBC 参数和 7D action 后的安全执行链；没有修改旧导纳 runner 或历史结果。不是论文最终 baseline，需要新的同 fixture 对照。

## r1 失败与 r2 修正

r1 的 8 s smoke 未暴露接口时序错误，24 s 的 9300/9301 在 8 s 后触发 nominal scalar guard。MuJoCo `mj_step` 返回时，qpos 已更新，但 `xpos/xmat/J` 仍可能对应积分前运动学；共享 runner 打包了这个现有控制快照。r1 从新 qpos 单独重建 FK，导致重构的 Jacobian 与观察到的名义 WBC 不同。

真实 MuJoCo 7-joint 回归例（dt=5e-5 s）中，fresh-q FK 与原快照末端差约 4.06e-6 m；scalar-fit residual norm 约 4.29e-7，超过 1e-7 guard；使用相同 robot snapshot 后误差降为约 7.78e-18，公共 scale 恢复 0.8。因此 r2 使用共享 runner 同一时刻的只读机器人 q/J/hand pose，不改共享环境、不额外调用 `mj_forward`，且保留原 1e-7 guard。此修正涉及控制输入运动学时间戳，不是放宽判定或改变实验物理。

r1 失败文件和 source snapshot 必须保留；r2 三条 development 回合须全部重跑并使用新目录，不能拼接 r1 的成功/失败。r2 错误时另存 `admittance_reference_failure.json`，包含 observation、observed/reconstructed nominal、fitted scale、vector residual/norm、虚拟状态和已完成动作数。

## 修正的接口问题

旧实现积分 `M z̈ + D ż + K z = ŵ`，但只发送 `ż`。恒力稳定时 `z=ŵ/K` 而 `ż=0`，名义 WBC 仍指向原始目标，因此控制器内部虽然保留虚拟位移，执行器却没有维持该位移的命令。

新实现积分同类对角虚拟动力学，同时将位移和速度传给一个只读的 WBC 二次求值：

```text
virtual_position = nominal_position + z_translation
virtual_rotation = Exp(z_rotation) nominal_rotation
virtual_angular_velocity = J_left(z_rotation) zdot_rotation

nominal = WBC(q, nominal_pose, feedforward=0)
shifted = WBC(q, virtual_pose, feedforward=virtual_twist/s)
requested_residual = s (shifted.task_twist - nominal.task_twist)
action = [0, requested_residual / original_action_units]
```

`s` 是 panel 对整个已限幅 WBC command 的公共比例（当前 reach 为 1，loaded lift 为 0.8）。通过 observation 中的 nominal twist 与重构的 nominal WBC twist 最小二乘比值获得，不读取阶段标签或 fixture 时钟。两者不是同一标量比例时立即报错。名义 twist 近零时比例不可辨识，保留上一比例（初值 1），并记录 `nominal_scale_unobservable_steps`。此退化可能造成阶段切换近零瞬间的幅度偏差，不能声称每个时刻都精确识别。

在未限幅、局部笛卡尔速度伺服近似下，该残差成为 `s K_wbc z + ż`，所以恒力稳态仍有抵消名义拉回的非零残差。实际实现不是直接加未限幅 `K_wbc z`，而是用同一个 WBC 计算有位置/角速度限制、阻尼伪逆、nullspace posture 与关节速度限制的两次 command 差值。

## 输入与执行边界

- 只消费 `contact45_v2` / `proprio48_action7_6d_v1` 的 q7、qdot7、nominal twist6、pose error6、estimated joint load7。通过机器人运动学 Jacobian 和与原导纳一致的 `equivalent_tool_wrench` 获得估计 wrench。其余 observation 字段不影响动作。
- 使用与 observed nominal 完全相同的只读机器人 `qpos/J/xpos/xmat` snapshot，并验证 q7 与 observation 一致；不自行更新 live data，不运行 FK/接触求解，不读取 live contacts、物体状态、障碍位置、event flags、未来状态或 fixture clock。policy 保留 model/data 供既有 WBC 和机器人 Jacobian 使用，不保留 env/task；在真实 FR3 上对应同步的编码器/运动学快照契约。
- 名义 pose 由编码器 FK 和 observation 的名义 pose error 重构。仅支持当前固定目标、零 feedforward 的 BlindTask/TableCornerTask。替换高层任务为移动 reference 时，必须扩充 feedforward observation 契约，不能沿用零值假设。
- `task.goals`、`task.index` 和任务目标不因虚拟位移改变。状态机仍根据真实编码器状态及原始目标判定，持续受力时可能保持在当前阶段；这是保留共同任务带来的真实行为。
- 仍是同一个 7D twist action，slowdown=0。动作幅度、slew、IK、joint velocity/torque limits 和 torque slew 由原环境执行。新 variant 没有替换 torque backend。

## 数值与物理限制

- `D=2ζsqrt(MK)`。每 40 ms action 周期对常值估计 wrench 做 20 次隐式 Euler 子步；与旧显式积分不同，以免在刚度扫描时产生纯数值发散。恒力平衡点不变，但瞬态含数值阻尼。
- wrench 平滑饱和为平移每轴 `30 N`、转动每轴 `3 Nm`；位移每轴限制 `0.08 m / 0.25 rad`；速度每轴限制 `0.16 m/s / 0.6 rad/s`。虚拟位移触顶时移除向外速度。限幅区的响应不再严格等同线性 M-D-K。
- 旋转动力学是在有限世界 rotation-vector 坐标上的局部模型，使用 SO(3) 指数映射和左 Jacobian 转换角速度；不宣称全局 SE(3) 被动性。
- `shifted.task_twist - nominal.task_twist` 经环境再次阻尼 IK 投影和安全过滤，action 又在 40 ms 内保持、nominal WBC 可在子步重算。因此它是受限 Cartesian reference residual，**不是精确替换 shifted joint command，也不保证严格达到 z 的静态位移**。
- 观察器误差、输入/动作饱和、奇异位形、nullspace 投影、任务阶段切换、物理接触均可改变实际平衡。与旧 variant 的新实验须保留同 M/D/K、fixture、seed、nominal task、安全参数与观察器；名称明确区分 velocity-only 与 reference variant。

## 运行与证据

沿用 `PANEL_CONFIG`、`UNIFIED_6D_TEACHER`、`PRIMITIVE_RUNNER_PATH` 环境变量及 panel CLI 参数。可传 `--classical-controller admittance`（默认即为 admittance），以及旧 `--classical-stiffness`、`--classical-rot-stiffness`、`--classical-mass`、`--classical-inertia`、`--classical-zeta` 参数。必须使用新建/空的 rollout 输出目录，避免覆盖 panel runner 的固定 sibling trace 名称。

每次结果保留 panel 原始 audit，并新增 `admittance_reference` 配置/限制、控制周期、源码 SHA-256、以及 `admittance_reference_state.npz`。其 `trace` 每行 26 列，依次为 offset6、velocity6、effective_wrench6、requested_residual6、nominal_scale1、action_clipped1；与主 rollout 的 action 逐 tick 对齐。该 trace 记录过滤前请求，实际执行仍应结合环境的 state/action trace 分析。

单元验证覆盖：零力零偏置返回零残差；恒力下虚拟偏移达到饱和后有效力/K，速度趋零且维持非零 offset-holding residual（公共 scale 1 / 0.8）；撤力后位移和残差归零；nominal WBC 不匹配时拒绝运行。运行命令（仓库根目录，环境需 numpy/pytest）：

```bash
PYTHONPATH=scripts python -m pytest tests/test_admittance_reference_20260923.py -q
```

截至 r2 实现验收，原 5 个数值单元测试与新增 45D/48D 真实 `mj_step` 快照时序回归共 7 个测试全部通过。后者显式复现 r1 的 guard 失败，并验证 r2 零力全零 action、公共比例 0.8、原 live data 完全未修改。此为运动学接口测试，不等同 panel contact rollout；r2 闭环表现待独立 development 回合验证。
