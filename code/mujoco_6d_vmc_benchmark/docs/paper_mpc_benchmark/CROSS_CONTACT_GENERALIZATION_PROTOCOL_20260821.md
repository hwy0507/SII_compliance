# 跨接触条件确认性协议（2026-08-21）

## 问题与冻结规则

本协议检验上一轮 selected CEM-improved ESN 是否能跨越未见的接触方向和接触几何泛化。ESN checkpoint、reservoir、七个 CEM readout gains 和 5% residual-torque budget 在协议开始前全部冻结；本协议中不训练 ESN、不选择 ESN seed、gain、checkpoint 或 budget。此前所有 train、validation 和 held-out seeds 均不复用。

## 新物理接触条件

训练及先前 CEM 改进使用的是从 `negative_y` 进入的有限质量 cylindrical rod。本实验使用：

- `positive_y` 进入，即相反接触方向；
- finite-mass ellipsoidal `hand_proxy` 接触探头，代表有软接触外形的受控掌形探头，而非人体生物力学模型；
- 同样的 MuJoCo damped slide joint、force-limited position actuator、contact `solref`、FR3 torque limits 和 residual safety clamp；
- 仍为两次 press–hold–retract；质量、阻尼、servo `kp`/force cap、contact time constant、stroke、height 和 timing 均从此前声明的物理范围随机抽样。

方向与几何均未进入 ESN 或 VMC 的控制输入；二者仅接收相同的可部署 32-D observation：`q, qdot, nominal_twist, pose_error, wbc_twist_error`。

## 数据划分与选择规则

- 接触存在性校准只用 `20261101–20261103`，仅验证 MuJoCo 物理接触产生，绝不比较 ESN/VMC、不用于 validation/test。
- validation：`20261111–20261115`，每 seed 4 fixture，共 20 realization。ESN 仅记录其冻结 checkpoint 的 validation 性能；VMC 在 `k={1.0,1.5,2.2,3.2}` 与 budget `{2%,3%,5%}` 中选择。
- held-out test：`20261116–20261120`，每 seed 4 fixture，共 20 realization；在 VMC validation selection 完成前绝不运行。
- VMC 选择规则：先最大化 validation success，再以最小 validation mean at-grasp error 破平局。

主要指标为 success；连续比较指标为 matched at-grasp error。peak force、peak torque、contact bouts、hard torque-limit 记录为安全/机制指标。测试后不得依据 test 结果重新调任何 ESN 或 VMC 配置。

## 解释边界

这是一项 frozen-policy OOD generalization test，不是对 ESN 再次训练后的 in-distribution 评测。即使 ESN 胜出，也只能说明它在这一定义明确的 MuJoCo 接触方向/几何变化下优于该协议 validation-selected VMC；仍不能外推为真实人体接触安全或 sim-to-real 保证。
