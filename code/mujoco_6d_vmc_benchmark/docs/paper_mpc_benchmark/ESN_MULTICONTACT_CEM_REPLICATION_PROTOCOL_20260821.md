# 多接触 CEM-ESN 独立固定策略复现实验协议（2026-08-21）

## 动机

第一轮 confirmatory held-out test 的 CEM ESN 为 `19/20`、VMC 为 `17/20`，且误差点估计有利于 ESN，但 paired error confidence interval 跨零。因此本复现实验的目标不是调优，而是在新的、此前完全未见的样本上检验先前冻结的两种配置能否重复其相对表现。

## 完全冻结的对象

以下内容在复现前已冻结，不重新训练、不重新验证选择、不改超参数：

- ESN：`esn_multiscale_cem.npz`，训练期 CEM 后的 320-unit multi-scale ESN，5% residual budget；
- VMC：上一轮 validation-selected `k=1.0`、2% residual budget；
- ESN 32-D observation、reservoir、readout gain、PaperMPC nominal controller、FR3 torque limits 和 safety clamp；
- `positive_y + finite-mass ellipsoidal hand_proxy` 的物理 contact-apparatus distribution；
- fixture generator `fixture(seed*6151 + fixture_index + 1)`；
- 主要指标：task success；连续主指标：at-grasp error；安全指标：peak force、peak torque、contact bouts、hard-limit count。

部署 ESN 仍只有 `q, qdot, nominal_twist, pose_error, wbc_twist_error`；不增加力、装置参数、障碍物、方向标签、时序或 future 信息。

## 新样本

- replication seeds：`20261431–20261440`；
- 每个 seed：4 个 fixture；
- 总计：40 paired MuJoCo rollouts per method；
- 所有 seed 不与 CEM train (`20261401–04`)、selection validation (`20261411–15`) 或第一轮 held-out (`20261416–20`) 重叠，也不与此前任何实验 test seed 重叠。

无需新的 validation，因为 CEM checkpoint、ESN budget、VMC k 和 VMC budget 均已由先前流程冻结。只运行一次，结果生成后这些 replication seeds 也视为消耗，不能用于参数修改。

## 判读

若新样本仍表现为 ESN 成功率不低于 VMC，且 paired at-grasp error 的 95% CI 不含零，则可将第一轮和本轮作为相互独立的、同一冻结配置下的重复证据；仍只能主张声明的 MuJoCo contact distribution 内 superiority。若表现不重复，则必须如实降级为分裂不稳定的结果，不能靠重调参数消除矛盾。
