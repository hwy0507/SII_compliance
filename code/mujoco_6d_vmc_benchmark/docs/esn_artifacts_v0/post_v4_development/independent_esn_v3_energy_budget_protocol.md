# Independent ESN v3: Continuous Residual-Energy Budget

日期：2026-08-16。v3 是基于 stable-phase ESN 的独立算法候选。VMC 仍然是单独的解析 baseline，不与 ESN 叠加。

## 核心假设

stable-phase ESN 的 fast/slow reservoir 与 phase memory 负责识别“偏离—让位—回位—稳定”阶段；新的 residual-energy tank 不读取接触、力、撞击物类别、几何或 future release，而是根据本体感觉误差和已提出的 residual command 连续维护 authority budget。

每个控制周期维护：

\[
B_{t+1}=\mathrm{clip}(B_t+r_t-c_t,0,B_{max})
\]

其中 residual work 和 action-change 消耗 budget，nominal WBC 轨迹附近的低误差状态连续 recharge。预算映射为 [minimum multiplier, 1] 的 residual authority，并以有限 slew rate 变化。

## 与 v2.3 envelope 的区别

- v2.3 envelope 是基于当前误差的几何速度截断；
- v3 是带内部状态的连续能量预算；
- v3 在撞击前、撞击中和回位阶段都能约束 authority，不只作用于回位末端；
- v3 对 action-change 也计费，避免离散开关引入 jerk。

该机制通过 --residual-energy-tank 开启，默认关闭时不改变现有 baseline。它可以单独用于 MLP+budget ablation，也可以与 stable-phase ESN 配对形成 proposed lane。

## 进入正式训练前的 gate

one-seed matched smoke 必须满足：有效碰撞、抓取成功、no-impact 成功率均为 100%，hard torque-limit 为 0；相对同一冻结 v2.2 checkpoint，contact impulse 和 peak recovery jerk 不得恶化超过 5%，recovery RMSE 不得恶化超过 0.5 mm，rejoin latency 不得恶化超过 20 ms。否则回退参数或修改 budget dynamics，不启动多 seed。

## ICRA 贡献定位

论文贡献应表述为：一种具有 Fan Ye 多时间尺度记忆和连续残差能量预算的 WBC-aware ESN compliant controller。ESN 学习 phase-conditioned residual policy；energy tank 提供独立、可解释、可证明有界的 authority regulation。必须通过 ESN-only、budget-only、ESN+budget 和 no-memory ablation 证明收益来源。

## 当前 smoke 结论

250k one-seed 训练在 9 个 validation fixtures 上完成了 9/9 task success、9/9 no-impact success、0 hard torque limit；平均 contact impulse 为 3.77 N·s，rejoin latency 为 41 ms。但 effective collision 为 8/9，因此尚未通过正式 gate。当前版本应作为“冲量—碰撞有效性 trade-off” ablation，不得作为最终 proposed controller。

下一版不再单纯增大 energy penalty，而是研究 phase-conditioned predictive WBC feedback：利用 fixed reservoir 对 WBC error growth 的因果预测，在撞击前/偏离早期连续降低反馈注入；energy tank 作为辅助预算而不是唯一安全机制。这样可以在不把 residual authority 压到无碰撞的情况下减少瞬态力和 jerk。
