# 物理接触装置难工况协议（2026-08-21）

## 目的

本协议检验一个物理上合理、面向 FR3 真机接触装置的难工况：外部有限质量推杆在阻尼滑轨上由受力上限的位置伺服驱动，机械臂在一次抓取前经历两次 press–hold–retract 接触。难度来自外部装置惯量、滑轨阻尼、驱动能力和接触柔软度的不确定性，而不是向 ESN 注入抽象噪声或特权标签。

研究假设是：ESN 的 reservoir 状态可以利用 `q, qdot, nominal_twist, pose_error, wbc_twist_error` 的时间历史，学习接触前后瞬态响应的补偿；这只是待检验假设。VMC 同样保留其解析 Jacobian/虚拟小车机制，不能将其描述为无记忆控制器。

## MuJoCo 力学模型

外部 rod 是场景中有限质量的刚体，通过 slide joint 沿既有 rail 运动。slide joint 具有黏性阻尼；position actuator 具有显式 `kp` 和对称 force range；rod 与 hand 的法向接触使用 MuJoCo `solref="time_constant 1"`，并保留原有几何、摩擦、碰撞组、FR3 torque limits 和 torque-residual safety clamp。场景构建代码为 `scripts/fr3_scene.py`，fixture/观测接口为 `scripts/wbc_velocity_residual_env.py`。

训练和评测的 declared physical envelope 为：

| 参数 | 范围 |
|---|---:|
| impactor mass | 0.18–0.50 kg |
| slide damping | 0.6–4.0 N·s/m |
| position-servo kp | 2.5–9.0 kN/m |
| driver force limit | 150–300 N |
| contact time constant | 8–25 ms |
| stroke | 0.160–0.176 m |
| height | 0.539–0.542 m |
| first-pulse start | 0.90–1.03 s |
| cycle period | 0.66–0.72 s |
| pulse count | 2 |

这些参数只写入 MuJoCo XML 和结果 manifest，不进入 ESN 或 VMC 的 controller observation。rod 的运动波形在第二次 retract 后仍早于既有 `2.40 s` grasp deadline；没有为学习策略改变 deadline 或提供未来释放时刻。

## 数据与公平协议

- 训练：generator seed `20260901`，16 条随机物理 two-pulse VMC teacher traces，加 1 条 no-rod neutral trace；ESN-101/202/303 使用固定 reservoir seed，观测契约保持冻结。
- validation：seeds `20260921–20260925`，每个 seed 4 个 fixture，共 20 条 realization。
- held-out test：seeds `20260926–20260930`，每个 seed 4 个 fixture，共 20 条 realization；与训练/validation disjoint。
- ESN candidates：3 个 frozen checkpoints × budget `{2%, 3%, 5%}`。
- VMC candidates：`k ∈ {1.0, 1.5, 2.2, 3.2}` × 相同 budget 集合。
- 选择规则在测试前固定：先最大化 validation task-success rate，再以 validation mean at-grasp error 最小者破平局；ESN 与 VMC 各自只选一次全局配置。
- 测试集只跑选中配置一次。测试结果不用于再选 seed、预算、刚度、checkpoint 或物理范围。

测试主指标是 task success；连续指标为 at-grasp tracking error。peak contact force、contact bout count、peak torque 和 hard-limit count 作为安全/机制指标，不参与配置选择。

## 真机边界

MuJoCo rod 可近似带 force cap 的直线推杆、滑台或受控外部接触装置。真实部署前必须重新做装置 system identification、FR3 FT/torque validation、碰撞安全停止、passivity/energy analysis 和低速 dry-run。MuJoCo `solref` 只表示仿真接触时间尺度，不等价于完整材料参数识别。本协议证明的是 declared MuJoCo physical envelope 内的 held-out generalization，不是 sim-to-real 保证。

