# 六维虚拟弹簧调参阶段结果

本轮在服务器 MuJoCo 上完成了第一阶段的六维刚度解耦和公平 hard-fixture 对比。刚度向量顺序为 `[x, y, z, roll, pitch, yaw]`；标量 `kappa` 仍向后兼容，会广播到六个通道。

## 实验设置

- Panda 官方 MuJoCo 模型；末端六维虚拟小车，平移部分使用显式三轴物理 carriage。
- 所有候选使用同一条可达抓取参考、同一根有限质量物理杆、同一接触参数、同一 torque limit 和同一 gripper task gate。
- hard 工况：rod stroke `0.18 m`、rod height `0.54 m`、碰撞时刻和方向相同、抓取闭合时刻 `2.40 s`。
- 每个带杆实验都有 matched no-rod 对照；只有满足真实 rod–hand 接触、稳定回归、lift + hold、有限仿真、无 hard torque limit 的结果才算 valid。
- `0.20 m` stroke 的额外压力测试会导致部分候选无法完成抓取，因此没有混入正式排名。

## 六维候选搜索

| 候选 | `[x,y,z,r,p,yaw]` | valid | paired 峰值偏移 (mm) | recovery RMSE (mm) | 回归延迟 (s) | 峰值力矩 (Nm) | 接触峰值 (N) |
|---|---:|---:|---:|---:|---:|---:|---:|
| isotropic_35 | `[35,35,35,35,35,35]` | 是 | 33.00 | 2.44 | 0.384 | 30.34 | 76.71 |
| isotropic_20 | `[20,20,20,20,20,20]` | 是 | 33.95 | 2.35 | 0.360 | 30.30 | 75.86 |
| isotropic_50 | `[50,50,50,50,50,50]` | 是 | 32.67 | 2.46 | 0.392 | 30.35 | 77.22 |
| y_soft | `[35,16,35,35,24,35]` | 是 | 34.87 | 2.16 | 0.348 | 30.34 | 75.67 |
| y_soft_pitch | `[42,14,42,32,16,30]` | 是 | 35.38 | 2.11 | 0.348 | 30.29 | 75.48 |
| supported_y_soft | `[55,18,55,38,20,34]` | 是 | 34.37 | 2.19 | 0.352 | 30.31 | 75.85 |
| very_y_soft | `[48,10,48,28,12,26]` | 是 | 37.08 | **1.99** | **0.344** | 30.30 | **75.03** |
| balanced_anisotropic | `[45,22,48,34,22,32]` | 是 | 33.76 | 2.23 | 0.356 | **30.30** | 76.08 |

这里的结果说明“六个弹簧独立调参”确实改变了恢复行为，但第一轮结构化候选尚未证明它能在所有指标上超过统一刚度。`very_y_soft` 在恢复 RMSE、回归时间和接触峰值上更好，`isotropic_50` 在 paired 峰值偏移上最好；这正是后续多目标优化需要保留 Pareto front 的原因。

## 与 rigid / impedance / VMC 的统一 hard-fixture 对照

| controller | valid | paired 峰值偏移 (mm) | 回归延迟 (s) | 接触冲量 (Ns) | 峰值力矩 (Nm) | jerk 峰值 (m/s³) | task |
|---|---:|---:|---:|---:|---:|---:|---|
| rigid | 是 | **13.54** | **0.012** | 9.23 | 48.03 | 3864.59 | lift + hold |
| impedance | 否 | 39.82 | 0.488 | **3.73** | 31.28 | 1428.37 | 未抓取 |
| VMC (`[50]*6`) | 是 | 32.67 | 0.392 | **4.05** | **30.35** | **1427.44** | lift + hold |

相对于 rigid，VMC 在这一 hard 工况下没有全面胜出：rigid 仍然具有更小的轨迹偏移和更快的回归；但是 VMC 的峰值电机力矩约低 `36.8%`，接触冲量约低 `56.1%`，jerk 峰值约低 `63.1%`，并且仍完成抓取。impedance 在相同公平工况下未通过 task gate，因此不能作为成功基线。

## 当前结论和下一步

1. 六维独立刚度接口和 explicit translation spring 已经可以用于参数搜索，且 scalar benchmark 仍兼容。
2. 当前更可靠的科研结论是“VMC 提供安全/冲击/力矩—轨迹精度的 Pareto trade-off”，不是“VMC 全面优于 rigid”。
3. 下一步应在 valid hard fixture 上增加 Sobol/CMA-ES 细化搜索，并将目标写成约束多目标：在 torque、jerk 和 task success 约束下最小化 paired offset、recovery RMSE 和 rejoin latency。
4. RL 适合放在这个低维静态搜索之后：策略只输出低频六维刚度倍率，并加入 action rate limit、阻尼比随刚度更新和 safety shield；rod contact boolean、未来碰撞相位等只能作为训练期 privileged signal，不能作为部署观测。

原始机器可读结果：

- `sixd_kappa_search_hard_summary.json`
- `baseline_ladder_hard_summary.json`
