# Independent ESN dual-phase robustness result（2026-08-22）

这是独立于 `dual_phase_longitudinal_20260822` 的新协议。ESN 不再拟合 VMC residual：训练从零 readout 开始，固定随机 reservoir，并用 antithetic random search 直接根据 ESN 自己在 MuJoCo 中的 rollout return 更新 readout。

服务器执行目录：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`。

## 协议

场景仍是 FR3 + Panda Hand 的双板双阶段实体接触：抓取前 link-7/hand 下探碰有限水平板，真实手指抓取物块，上提时 hand/link-7 再碰竖直板并滑开。新协议在固定 world MuJoCo 模型上加入预注册的共同扰动：

- 双板 y/z 安装偏差；
- contact `solref` time constant；
- 所有 residual controller 共享的关节速度测量噪声；
- 所有 residual controller 共享的 40 ms residual action delay。

ESN/MLP 的在线输入仍严格为 `q(7), qdot(7), nominal_twist(6), WBC pose error(6), WBC twist error(6)`。ESN 训练和部署不读取 VMC checkpoint、VMC teacher trace、VMC action 或 VMC 参数；板位置、法向、接触力、接触标签、物块状态只用于环境内部物理审计/训练 scalar return，绝不进入 policy。

## 物理 gate

PaperMPC zero-residual 在 development + held-out 共 8 条条件上全部通过：

- 8/8 双阶段任务成功；
- 8/8 几何/接触审计有效；
- 0 条初始板接触；0 条物块—板接触；
- 最大 pre penetration 0.314 mm，最大 post penetration 0.130 mm。

因此该协议不是依靠穿模或不可完成场景制造差异。

## 独立 ESN training

入口：[train_dual_phase_esn_ars.py](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709-paper-mpc-baseline/code/mujoco_6d_vmc_benchmark/scripts/train_dual_phase_esn_ars.py)

训练参数：reservoir 240，spectral radius 0.94，input scale 0.45，time constant 0.08 s，32 个固定随机 readout basis，8 iterations × 8 antithetic directions，development 条件每个方向随机匹配 2 条。零 readout 起点到最终模型的 development return：16.25 → 28.55；最终 development 物理审计 4/4。

模型：[esn_ars_independent_best.npz](esn_ars_independent_best.npz)

训练摘要：[ars_summary.json](ars_summary.json)

## Held-out 结果

Held-out 是 4 个全新 seed/condition，未用于 ESN 更新或 checkpoint 选择。四种方法每条条件都通过物理审计并成功完成任务。

| 方法 | 成功率 | Pre 峰值力 N | Pre 冲量 N·s | Post 峰值力 N | Post 冲量 N·s | 总板冲量 N·s | Peak jerk m/s³ | 最终抬升 mm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PaperMPC | 4/4 | 21.033 | 5.589 | 9.573 | 1.208 | 6.797 | 1061.8 | 195.37 |
| VMC | 4/4 | 21.202 | 6.386 | 9.572 | 0.921 | 7.308 | 1067.9 | 199.18 |
| MLP | 4/4 | 28.016 | 4.916 | 12.814 | 0.386 | 5.302 | 1388.5 | 211.68 |
| ESN independent proposed | 4/4 | **20.541** | **4.867** | **6.788** | 0.969 | 5.836 | **1030.3** | 191.52 |

相对 VMC 的配对分析（4 个 seed cluster，20,000 bootstrap replicates）：

- pre peak force：−0.661 N，95% CI [−1.583, 0.259]；
- pre impulse：−1.519 N·s，95% CI [−1.716, −1.152]；
- post peak force：−2.785 N，95% CI [−3.150, −2.420]；
- post impulse：+0.048 N·s，95% CI [−0.044, 0.139]；
- peak jerk：−37.6 m/s³，95% CI [−97.1, 19.1]；
- 五项柔顺指标综合比值：**0.8994，95% CI [0.8634, 0.9355]，越低越好**。

## 严谨结论

在这个预注册的双阶段 cross-physics MuJoCo 协议中，独立训练的 ESN 相对 VMC 显著降低了 pre-contact impulse 和 post-contact peak force，五指标柔顺综合比值约低 10.1%；四个 held-out 条件全部成功且物理审计通过。这个结果支持“ESN 作为独立时序柔顺策略具有优势”。

但 ESN 的 post impulse 与 VMC 没有明显差异，最终物块抬升低约 7.66 mm；MLP 的总冲量更低但峰值力和 jerk 更高。因此不能声称 ESN 在所有指标上全面最优，也不能把该结果外推为真机结论。下一步应做更多 held-out seed、观测/执行延迟标定、FR3 摩擦惯量 system identification，并测试真机可用的统一传感信息。

## 结果文件

- [protocol.json](protocol.json)
- [papermpc_physics_gate.json](papermpc_physics_gate.json)
- [development_four_method.json](development_four_method.json)
- [heldout_four_method.json](heldout_four_method.json)
- [heldout_independent_esn_stats.json](heldout_independent_esn_stats.json)
