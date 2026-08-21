# ESN 读出策略改进确认性协议（2026-08-21）

## 动机

此前 contact-apparatus 难工况中的 ESN 是从单一 VMC teacher 做 behavior cloning（BC）。而公平选择协议允许 VMC 直接搜索 `k × residual budget`，最终选到 `k=2.2, 5%`；因此纯 BC ESN 没有明确超过被独立调优的 teacher/baseline 并不意外。为检验 ESN 是否还有算法改进空间，本协议加入一次训练期、simulation-only 的 readout policy improvement。

## 改进算法

从冻结的 ESN-303 BC checkpoint 初始化，保持以下内容不变：

- 160-unit reservoir、reservoir 权重、32-D observation contract 和 PaperMPC nominal controller；
- 输出仍为 7 维 residual torque，使用相同的 5% residual budget、FR3 hard torque limits 和 safety clamp；
- 部署 observation 仍只有 `q, qdot, nominal_twist, pose_error, wbc_twist_error`。

CEM 只优化 7 个输出行的有界 log-gain：`readout_new[channel] = exp(log_gain[channel]) * readout_parent[channel]`，log-gain 范围为 `[-0.75, 0.75]`。每轮显式评估 BC parent，避免仿真优化静默退化。目标函数为：

```text
1000 * success_rate - at_grasp_error_mm
- 0.020 * peak_force_N - 0.050 * peak_torque_Nm
- 0.100 * contact_bout_count - 200 * hard_limit_count
```

这使方法应表述为“BC initialization + train-only simulation policy improvement”，不再称为纯 BC。接触力、装置参数、障碍物状态、脉冲 timing/count 和未来 release time 只用于 MuJoCo 场景/训练期回报，绝不进入 deployed ESN input。

## 数据划分与预注册选择

- CEM development train-only seeds：`20261001–20261004`，每 seed 2 个 fixture；5 iterations，population 12（含 parent），elite 4，CEM RNG `20261071`。
- ESN validation candidates：BC parent 与 CEM checkpoint，固定 budget 5%。
- VMC validation candidates：`k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`。
- validation seeds：`20261011–20261015`，每 seed 4 fixtures。
- held-out test seeds：`20261016–20261020`，每 seed 4 fixtures；此前未用于 CEM、validation 或参数选择。

选择规则在测试前固定：每个 family 先最大化 validation success rate，再以 validation mean at-grasp error 最小者破平局。测试只运行选中的 ESN 与 VMC 一次。主指标为 task success；at-grasp error 为连续性能指标，force、contact bouts、peak torque、hard-limit 为安全/机制指标。

## 物理环境与真机边界

环境仍是有限质量 rod、阻尼 slide joint、受力上限 position servo、MuJoCo `solref` 接触柔度和 FR3 原始 torque limits 组成的双次 press–hold–retract 装置。参数范围沿用 [CONTACT_APPARATUS_PROTOCOL_20260821.md](CONTACT_APPARATUS_PROTOCOL_20260821.md)。结果只支持声明的 MuJoCo 物理包络内泛化，不构成 sim-to-real 保证；真机部署仍需 system identification、力矩/力传感器校验、碰撞安全停止和低速 dry-run。
