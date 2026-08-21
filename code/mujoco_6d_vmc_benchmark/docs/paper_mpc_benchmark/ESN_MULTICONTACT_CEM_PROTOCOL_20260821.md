# 多接触多时间尺度 ESN 的 CEM 读出策略改进协议（2026-08-21）

## 问题与假设

在 `positive_y + finite-mass ellipsoidal hand_proxy` 接触中，mixed-contact BC 的 multi-scale ESN 虽比同条件 single-scale ESN 的 validation 表现更好，却仍落后于 validation-selected VMC。此前的负 test seeds 不再参与任何调参。本协议检验一个严格训练期的算法改进：在固定 multi-scale reservoir 和固定本体感知观测下，对 ESN 线性 readout 的七个输出行做有界 CEM policy improvement。

假设是：BC 的目标是复制由两个不同 VMC teacher 产生的离线动作，而 CEM 可直接优化同一 ESN 的闭环 task objective；其改变的是读出的时序响应增益，而不是部署信息集、接触模型或力矩安全边界。

## 固定算法契约

初始 checkpoint 是已有的 320-unit multi-scale Direct ESN：前 50% reservoir unit 的 time constant 为 `0.04 s`，后 50% 为 `0.20 s`。CEM 冻结：

- reservoir size、recurrent/input/bias matrices、leak vector 和 readout feature map；
- 32-D deployment observation：`q(7), qdot(7), nominal_twist(6), pose_error(6), wbc_twist_error(6)`；
- PaperMPC nominal controller；
- 5% residual-torque budget、FR3 original torque limits 与 safety clamp。

CEM 仅优化 seven-dimensional bounded log-gain `g`：

```text
readout_new[channel] = exp(clip(g[channel], -0.75, 0.75)) × readout_parent[channel]
```

这保持每个输出行的符号结构和 reservoir-dependent mapping。部署时仍是一个冻结 ESN；不发生在线探索、在线 trial-and-error 或模型再训练。

禁止加入以下 deployment inputs：接触力、装置参数、障碍物 pose/velocity/geometry、接触方向标签、脉冲 timing/count、future release。MuJoCo 场景参数和 rollout success/error/force/torque 只在 train-only CEM reward 中使用。

## CEM 开发配置与划分

- train-only CEM seeds：`20261401–20261404`，每 seed 2 个 fixture；
- target contact distribution：`positive_y` finite-mass ellipsoidal `hand_proxy`，阻尼 slide、force-limited servo、`solref` 接触柔度；
- CEM：6 iterations，population 16（每轮包含 parent），elite 5，initial std `0.18`，minimum std `0.035`，CEM RNG `20261471`；
- return：`1000 × success_rate − at_grasp_error_mm − 0.02 × peak_force_N − 0.05 × peak_torque_Nm − 0.1 × contact_bouts − 200 × hard_limits`。

每轮显式重测 parent (`g=0`)，防止 stochastic optimization 静默替换更好的 BC policy。

完成 CEM 后，checkpoint 将在 test 前冻结。接着使用：

- validation：`20261411–20261415`，每 seed 4 个全新 fixture；
- held-out test：`20261416–20261420`，每 seed 4 个全新 fixture；
- ESN candidates：frozen multi-scale BC parent 与 frozen CEM-improved model，均为 5%；
- VMC candidates：`k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`。

每个 family 的选择规则预先固定为：先最大化 validation task success，再以最小 validation mean at-grasp error 破平局。随后只对两个 family winner 各跑一次 held-out test。

所有上述 seeds 均不与先前 CEM、cross-contact、mirror 或 multi-scale test seeds 重叠。特别地，之前已经消耗的 `20261116–20`、`20261216–20`、`20261316–20` 不用于本轮 CEM/validation/test。

## 报告边界

若 CEM ESN 在 held-out 获胜，结论只能是：在已声明、训练覆盖的 hand-proxy contact distribution 中，`mixed-contact BC + train-only multi-scale ESN readout policy improvement` 优于 validation-selected VMC。它不是对任意接触几何的 automatic OOD generalization，也不是 sim-to-real 结论。若它失败，则不得回看本轮 test 调 gain、CEM hyperparameter、budget 或 checkpoint；下一研究轮须使用新 split。
