# ESN-v2.1 Phase-Memory Recovery Protocol

当前 ESN-v2 的主要瓶颈不是 reservoir 是否能表示历史，而是 residual authority 只由当前空间误差 gate 决定。误差刚开始下降时，authority 会迅速收回，导致回归动作被截断，rejoin latency 的 seed 方差较大。

v2.1 新增 `fan_ye_phase_esn` 分支。它仍使用固定的 Fan Ye fast/slow reservoirs 和相同的 32-D WBC/proprioceptive 输入，但把两个 reservoir 的状态差用于控制层：

1. 计算 fast/slow state 的 cosine disagreement；
2. 通过因果衰减保持短时 `phase_memory_hold`，避免接触后刚开始回归就丢失历史扰动信息；
3. 用当前 WBC pose error 与 twist error 的负余弦作为 measured rejoin confidence；
4. 仅在 disagreement memory 和 measured rejoin confidence 同时较高时，给 residual authority 一个有界的 recovery floor，最高为 `0.55`；
5. 继续经过原有 action gate、slew limiter、joint-speed/acceleration/torque safety layer。

因此该分支改变的是 ESN 的控制逻辑，而不是简单增加观测维度或修改 reward。它不读取 contact、force、rod state、obstacle geometry、future release 或 fixture id。MLP 对照仍运行同一 shared safety adapter 和相同 action contract。

## 必须执行的验证顺序

1. adapter phase-memory unit test；
2. MuJoCo zero-residual 与随机动作 smoke；
3. 单 seed matched MLP/phase-ESN paired gate；
4. 至少三 seed；
5. 使用 validation-only checkpoint Pareto archive，禁止使用 V4 final holdout。

如果 phase-memory 分支只提高 authority 而没有降低 recovery RMSE、rejoin latency 或 recovery jerk，则保留为消融，不晋升为主结果。
