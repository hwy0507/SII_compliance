# ESN-v2.2 Stable-Phase Recovery Protocol

v2.1 已经稳定改善 jerk、冲量和 torque，但 rejoin latency 仍有 seed 方差。v2.2 不改变 Fan Ye reservoir，也不改变 PPO reward；只把 phase-memory authority 的释放逻辑改为因果滞回：

- recovery 开始时 authority floor 快速建立；
- rejoin confidence 短暂下降时只按较慢速率释放；
- tracking error 接近 nominal path 时由 error envelope 连续压到零；
- MLP 与普通 phase-ESN 不受影响，stable-phase 作为独立算法分支评估；
- 所有动作继续经过共享 slew、joint velocity、acceleration 和 torque safety。

正式训练前必须完成：unit test、MuJoCo neutral smoke、单 seed paired gate，再跑三 seed checkpoint-Pareto campaign。
