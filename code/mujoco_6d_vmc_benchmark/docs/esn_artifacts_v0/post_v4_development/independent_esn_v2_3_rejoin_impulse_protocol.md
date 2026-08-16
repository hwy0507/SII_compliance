# Independent ESN v2.3: Rejoin-Impulse Constrained Protocol

日期：2026-08-16。本文定义 stable-phase ESN v2.3 的算法假设、训练开关和 ICRA 级验证协议。ESN 与 VMC 保持两条独立算法线；v2.3 不改变 VMC baseline。

## 研究问题

当前 stable-phase ESN 在 3 seeds × 3 unseen impactors 上稳定降低 recovery RMSE，但冲量在 8/9 配对中增加，尤其 hand-palm proxy。v2.3 的目标不是单独追求更短 latency，而是在不牺牲有效碰撞、抓取成功和回位能力的前提下，降低冲量和 recovery jerk。

## 算法改动

v2.3 保留 Fan Ye fast/slow fixed reservoirs、causal phase memory 和 v2.2 hysteretic authority floor。在 safety adapter 的 phase-projected residual 之后增加 **rejoin velocity envelope**：

1. 只使用 measured WBC pose error 和 WBC twist error；
2. 仅当误差沿径向减小时启用，说明系统已经进入 measured rejoin；
3. 只限制指向 nominal WBC target 的 residual velocity 分量；
4. 允许的 inward velocity 与剩余误差成正比，误差接近零时连续降为零；
5. 不读取 contact flag、contact force、impactor type/geometry、future release time 或 fixture id。

这是一种可部署的 proprioceptive passivity-inspired envelope，核心作用是避免高 authority residual 在回位末端保留过大的 inward speed，从而减少 overshoot、jerk 和接触后瞬态冲量。机制通过 `--rejoin-velocity-envelope` 显式开启；默认关闭时，已有 MLP、VMC 和 v2.2 结果行为不变。

## 训练与公平性

- MLP、stable-phase ESN v2.2、v2.3 使用同一 Panda WBC、动作空间、torque/velocity/acceleration/slew safety adapter、fixture manifest、PPO 网络、seed 和 timesteps。
- v2.3 只在 post-V4 development split 训练和选择 checkpoint。V4 final holdout 只做一次最终报告。
- rod、ball、hand-palm proxy transfer 只用于冻结模型的 inference-only 外推，不能参与 reward 调权、checkpoint 选择或 envelope gain 搜索。
- hand-palm proxy 仅表示 MuJoCo 柔性手掌大小 ellipsoid 接触代理，不是人体生物力学或安全认证。

## 必须报告的指标

每个 seed、每个 impactor、每条 lane 都必须同时报告：task success、effective collision、recovery RMSE、paired-offset RMSE、rejoin latency、peak recovery jerk、contact impulse、peak torque、hard torque-limit、minimum feasible torque scale。结果以 matched no-impact episode 配对，并给出均值、标准差、95% bootstrap CI 和 win count。

## Gate 规则

进入三 seed 正式实验前，one-seed smoke 必须满足：

- 物理状态 finite，effective collision 和抓取成功率均为 100%；
- hard torque-limit 为 0；
- 相对 v2.2，contact impulse 与 peak recovery jerk 均不得恶化超过 5%；
- recovery RMSE 不得恶化超过 0.5 mm；
- rejoin latency 不得恶化超过 20 ms。

三 seed 结果只有在 9 个 matched pairs 中至少 7 个满足 impulse 不增、至少 7 个满足 jerk 不增，且 recovery RMSE 的 paired mean 不恶化时，才可声称 v2.3 在稳定性上优于 v2.2。若 trade-off 仍存在，应报告 Pareto frontier，不得声称全面支配。

## ICRA 级完整实验矩阵

1. Baselines：fixed WBC/rigid、impedance、VMC-gated、current-state MLP、stable-phase ESN v2.2、v2.3。ESN 不与 VMC 叠加。
2. Impactors：rod、ball、hand-palm proxy；另增加未参与调参的速度/质量组合。
3. Ablations：去掉 fast/slow disagreement、去掉 hysteresis、去掉 envelope、只加 reward penalty、只加 envelope。
4. Robustness：撞击时刻、冲击速度、接触高度、初始轨迹速度、WBC gain 和 MuJoCo timestep 扰动。
5. Sim-to-real readiness：记录控制周期、延迟、torque slew、关节速度/加速度余量，并在真实 Franka 上先做无物体、软物体、低速棍三阶段验证。

## 当前阶段

已完成 v2.3 envelope 的静态实现、参数校验、单元测试和服务器 smoke 准备。下一步是服务器 one-seed paired smoke；只有通过上述 gate 才启动三 seed PPO 训练和冻结 checkpoint transfer。
