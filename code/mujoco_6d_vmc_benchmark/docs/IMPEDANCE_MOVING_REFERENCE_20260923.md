# 积分平衡点阻抗变体：开发协议

实现：`scripts/run_panel_impedance_reference_20260923.py`。这是独立 runner，没有修改正在运行的 `run_panel_classical_adapter_20260923.py`、panel runner 或 historical task。尚未执行长时间场景 rollout；单元检查通过不代表闭环稳定或任务成功。

## 问题与控制定义

原有阻抗直接取 `command.target_position_m` / `command.target_rotation` 做弹簧平衡点。任务切换 waypoint 时，目标存在离散跳变，而 nominal WBC 原本通过有界速度命令处理它。直接用该 waypoint 计算 `K e` 会绕过这层速度整形，产生大的弹簧力和关节力矩。

新变体将现有 WBC 的 `task_twist_world` 作为输入，称为 **velocity-reference-to-impedance adapter**。它捕获原 `_wbc_command` 的返回值，不重算或修改 task、WBC、任务阶段或目标，不把内部阻抗平衡点写回 nominal reference。轨迹误差等指标仍由原 runner 相对原任务目标计算。

控制周期为传入 torque adapter 的 `dt`。令实际末端位置/姿态为 `p,R`，速度为 `v`，nominal WBC twist 为 `v_nom`：

```text
v_bar = [norm_clip(v_nom.linear, v_max), norm_clip(v_nom.angular, omega_max)]
首次调用：p_eq = p，R_eq = R，不执行积分，所以初始弹簧位姿误差为零。
后续调用：p_eq_next = p_eq + alpha_p * dt * v_bar.linear
          R_eq_next = Exp(alpha_R * dt * v_bar.angular) @ R_eq
e_raw = [p_eq_next - p, Log(R_eq_next @ R.T)]
e = [norm_clip(e_raw.position, e_p_max), norm_clip(e_raw.rotation, e_R_max)]
D = 2 * zeta * sqrt(diag(M) * diag(K))
w = K * e + D * (v_bar - v)
tau_residual = J.T @ w
tau = shared_box_and_slew(bias + tau_residual)
```

`alpha_p,alpha_R` 位于 `[0,1]`。若完整积分一步未增加越界误差，则取 1；否则二分搜索可接受的步长比例，使下一步参考误差不大于 `max(当前误差范数, 误差界)`。因此机器人受阻时平衡点不会无限向前积分。若外力让实际末端离平衡点已经超过误差界，不瞬间把平衡点拉到实际位置，而只允许误差不增长的积分；同时弹簧项使用饱和误差。

这种条件积分保持每步平衡点增量的线速度/角速度上界。外力位移可能让原始位置误差超过界，所保证的是有界弹簧误差和无继续向外 windup，不是声称实际末端或原始误差永远受界约束。

当 `e=0` 且 `v_bar=v` 时 Cartesian residual wrench 为零。初始位姿无跳变并不意味着非零运动指令下初始 damping torque 也为零。默认 nullspace damping=0；可通过参数启用 `-d_null (I-J.T pinv(J.T)) qdot`，启用后它应作为额外关节耗散项单独报告。

## 默认参数（尚未调优）

| 参数/CLI 后缀（前缀均为 `--reference-`） | 默认 | 含义 |
|---|---:|---|
| `stiffness` | 300 | 平移刚度 N/m，三个轴相同 |
| `rot-stiffness` | 15 | 转动刚度 Nm/rad |
| `mass` | 1 | 计算临界 damping 的平移质量 kg |
| `inertia` | 0.08 | 计算转动 damping 的惯量 kg m² |
| `zeta` | 1 | 阻尼比 |
| `max-linear-speed` | 0.35 | 平衡点平移速度范数界 m/s |
| `max-angular-speed` | 1.2 | 平衡点角速度范数界 rad/s |
| `max-position-error` | 0.04 | 弹簧平移误差范数界 m |
| `max-rotation-error` | 0.20 | 弹簧旋转误差范数界 rad |
| `nullspace-damping` | 0 | 可选 nullspace 关节 damping |

其中 M 仅用于设定 D，不执行 admittance 动力学。默认平移弹簧力范数至多 12 N，转动弹簧力矩范数至多 3 Nm；damping 项会随实测速度变化，因此这不是总末端 wrench 硬限幅。最终仍调用原 `safe_velocity_tracking_torque`，复用其 bias-aware torque feasibility scaling、绝对力矩限制和 torque slew。编码为等价速度误差仅用于调用同一投影器，不代表另加一个 velocity servo。

## 公平性边界

- 控制器只能读取原 WBC twist、末端位姿/速度、Jacobian、qdot 和 bias compensation；不读取接触标签、接触力真值、障碍物信息或事件阶段/时钟。`data.time` 只用于避免同一物理状态重复积分，没有时间触发行为。
- 相同 panel、payload、事件、physics solver、task/reference 和 metric target 应沿用配对运行协议。无需更改 `PANEL_CONFIG` 或已有模型。
- 这是直接 Cartesian torque impedance controller，替换原有 velocity servo。虽然复用最终 torque box/slew，**不会继承原 `safe_joint_velocity_command` 对实际执行速度/加速度的保证**；平衡点速度界也不能宣称是机械臂速度界。
- 比较 ESN/VMC 时应报告此低层差异；不能称作完全相同 action7 execution backend。原始 waypoint impedance、moving-reference impedance、admittance 应使用不同方法名及独立目录。
- 默认参数固定后先做一次配对开发 smoke。任何后续调参只看 development split；不能根据最终 office blind test 选择参数。

## 小验证与后续运行

测试文件 `tests/test_impedance_moving_reference_20260923.py` 检查初始无位姿跳变、有界积分速度、受阻时不继续 windup、零位姿/速度误差无 residual、外部位移不造成参考重置跳变、旋转世界坐标左乘及非法 dt 拒绝。另有轻量 integration test：用假的环境状态安装真实 torque hook，捕获同一 WBC command，调用真实共享 torque projection/slew，确认首次可触达、同一状态不会重复积分、下一控制步正常积分。它没有启动 MuJoCo rollout。

本机 `.venv-rl/bin/python -m pytest -q .../tests/test_impedance_moving_reference_20260923.py`：**9 passed in 0.32s**（2026-09-23）。该结果不验证真实场景中的速度、接触稳定性或任务成功。

服务器 smoke 应复制现有 panel invocation 的全部 fixture/physics flags 和环境变量，只将入口替换为新 runner，并使用全新 `--output`；`--classical-*` flags 改为上表的 `--reference-*`，不传 `--classical-controller`。runner 保留 `teacher-profile=memory` 作为 panel 元数据要求，但设置 mixture=0 且使用内存 ZeroAction policy，并在结果中断言 `teacher_called=false`。

结果额外记录全部参数、variant SHA256、积分次数、防 windup 触发次数和平衡点实际最大积分速度。要判断是否解决原失控，还必须检查物理 rollout 的实际末端速度、峰值关节力矩、接触/穿透、阶段进度和任务成功；本文件不预告结果。
