# ESN 镜像等变读出确认性协议（2026-08-21）

## 动机

跨接触验证显示：上一轮在 `negative_y` cylindrical-rod 条件中取得优势的冻结 CEM-ESN，在 `positive_y` ellipsoidal hand-proxy 条件中失败。当前 ESN 的 readout 是固定世界坐标映射，缺少对已知几何反射的结构约束。本协议检验一个只修改 ESN 自身输出机制的等变变体。

## 算法

从上一轮 selected CEM ESN-303/5% checkpoint 加载，reservoir、readout、输入和 32-D observation 均冻结。镜像等变变体只启用已有 `mirror_gate`：使用可部署的 measured `pose_error` 做 soft sign，对 lateral `yield_vy` 和 yaw `yield_wz` 通道施加符号变换；其余通道不变。soft sign 的 epsilon 固定为原 config 的 `0.004 m` / `0.020 rad`。该机制不读取 contact force、接触方向标签、装置参数、障碍物状态、pulse timing/count 或未来 release time。

这不是把新环境信息追加给 ESN，而是对已有 output readout 施加反射等变结构约束。它在原 `negative_y` 条件的正常工作区间应近似保持原动作；在反向接触时允许相应 lateral/yaw 响应翻转。

## 新 split

- validation：`20261211–20261215`，每 seed 4 个 `positive_y + hand_proxy` finite-mass fixtures；
- held-out test：`20261216–20261220`，每 seed 4 个全新 fixtures；
- 所有新动态参数继续从已声明 contact-apparatus envelope 抽样；本协议不使用此前 `20260926–30`、`20261016–20` 或 `20261116–20` 的 test realization。

ESN candidates 为冻结原始 CEM-ESN 与镜像等变变体，均固定 5% budget；先在 validation 选择 ESN 变体。VMC 在完全相同的 validation realization 上独立搜索 `k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`。选择规则均为先最大化 success，再以最小 at-grasp error 破平局。测试只运行选中的 ESN 变体和 VMC 一次。

## 边界

这是一个冻结 observation、冻结 reservoir、冻结 readout 的结构算法验证。即使镜像变体改善了反向接触，也只能说明该几何反射结构有效；它不能证明 ESN 对任意接触几何或真实机器人环境自动泛化。
