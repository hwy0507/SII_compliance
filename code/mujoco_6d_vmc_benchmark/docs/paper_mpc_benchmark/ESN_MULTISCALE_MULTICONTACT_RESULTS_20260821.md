# 多时间尺度 ESN × 多接触训练结果（2026-08-21）

## 结论先行

多时间尺度 reservoir 确实让 ESN 在 validation 上略有改善，但没有解决跨接触条件中的性能差距。最终被 validation 选中的 multi-scale ESN 在 held-out test 上为 `4/20` 成功，独立 validation-selected VMC 为 `18/20`；ESN 的平均 at-grasp error 高 `5.454 mm`。因此本轮不能支持“multi-scale ESN 战胜 VMC”，也不能把它写成已解决的跨接触泛化方案。

更具体地说：multi-scale 相比同数据、同 reservoir、同 readout 拟合流程的 single-scale ESN，在 validation 上 success 从 `3/20` 提升到 `5/20`，mean error 从 `25.645` 降到 `24.128 mm`；但在 held-out test 上只得到 `4/20` success，说明 validation 上的小幅收益没有稳定迁移。

## Validation selection

### ESN candidates

| Candidate | Budget | Success | Mean error | Peak force | Peak torque | Contact bouts | Hard limit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-scale τ=0.12 s | 5% | 3/20 | 25.645 mm | 95.996 N | 32.479 N·m | 3.00 | 0/20 |
| Multi-scale τ=0.04/0.20 s | 5% | **5/20** | **24.128 mm** | 96.079 N | 32.633 N·m | 2.70 | 0/20 |

因此选择 multi-scale ESN。注意这不是根据 held-out test 选择的结果。

### VMC candidates

VMC 在同一 validation realization 上独立搜索 `k × budget`。按 success 优先、error 次优选择 `k=1.0, budget=2%`，其 validation 表现为 `17/20` success、`18.118 mm` mean error、`0/20` hard limits。高刚度或高预算候选在该 hand-proxy 条件下出现明显更差的 tracking、接触力和 hard-limit 事件；因此预算不是事先固定为 5%。

## Held-out test

测试 seeds 为 `20261316–20261320`，每个 seed 4 个此前未见 fixture，共 20 个 paired rollouts。

| Method | Success | At-grasp error (mean ± SD) | Peak force (mean ± SD) | Peak torque (mean ± SD) | Contact bouts | Hard limit |
|---|---:|---:|---:|---:|---:|---:|
| Selected multi-scale ESN, 5% | **4/20** | 24.150 ± 2.190 mm | 90.405 ± 21.356 N | 32.643 ± 0.182 N·m | 2.75 | 0/20 |
| Selected VMC, k=1.0, 2% | **18/20** | **18.696 ± 5.262 mm** | 90.721 ± 21.372 N | 32.718 ± 0.340 N·m | 2.15 | 0/20 |

at-grasp error 的 rollout-level 95% t CI 为：

- ESN：`[23.125, 25.175] mm`；
- VMC：`[16.233, 21.159] mm`。

在相同 `(seed, fixture_index)` 下匹配，ESN−VMC 的差异为：

- at-grasp error：`+5.454 mm`，fixture-level 95% CI `[+2.482, +8.427] mm`；按 seed 内 4 个 fixture 先聚合，seed-level 95% CI `[-0.544, +11.452] mm`；
- peak force：`−0.316 N`，fixture-level CI `[-0.486, -0.146] N`，实际量级相同；
- peak torque：`−0.075 N·m`，fixture-level CI `[-0.300, +0.150] N·m`；
- contact bouts：`+0.600`，fixture-level CI `[+0.216, +0.984]`；
- peak post-impact error：`−65.294 mm`，说明 ESN 的统计定义下 post-impact 峰值误差较低，但它仍未能在 grasp 时刻恢复到 success threshold，不能用该次指标替代 task success。

成功事件的配对方向为：1 个 fixture ESN 成功而 VMC 失败，15 个 fixture VMC 成功而 ESN 失败，4 个 fixture 两者均失败；没有出现两者均成功的 fixture。这与总体 `4/20` 对 `18/20` 一致，说明差距不是由少数离群点造成的。

## 物理条件与安全性

held-out fixture 实际采样范围为：

| 参数 | 实际范围 |
|---|---:|
| Impactor mass | 0.210–0.489 kg |
| Slide damping | 0.739–3.729 N·s/m |
| Driver kp | 2.565–8.613 kN/m |
| Driver force limit | 154.5–298.2 N |
| Contact time constant | 8.54–24.28 ms |
| Stroke | 0.1601–0.1759 m |
| Height | 0.5392–0.5418 m |
| Start time | 0.903–1.029 s |
| Cycle period | 0.661–0.710 s |

两种方法均 `0/20` hard torque-limit。ESN 平均峰值接触力略低 `0.316 N`、峰值 torque 略低 `0.075 N·m`，但 contact bouts 平均多 `0.60`；不能据此声称 ESN 在整体安全性上优于 VMC。

## 科研解释与限制

这轮结果支持一个较窄但重要的判断：ESN 的 reservoir time-scale 是可影响闭环行为的算法因素，multi-scale 在 validation 上比 single-scale 更好；但仅靠固定 fast–slow leak dynamics 和混合 BC 训练，仍不足以克服 VMC 在未见 hand-proxy 条件下的结构迁移优势。multi-scale ESN 没有获得接触力、方向标签、装置参数、障碍物状态或未来信息。

因此当前应汇报为：

> CEM readout improvement can outperform VMC inside the original declared contact-apparatus envelope, but the cross-contact failure motivated a multi-contact, multi-time-scale ESN. That modification improved validation behavior but did not beat a validation-selected VMC on the held-out opposite-direction hand-proxy condition (4/20 vs 18/20 success; 24.15 vs 18.70 mm error).

这不是 sim-to-real 结论。当前 test seeds `20261316–20261320` 已消耗，后续若要继续优化，必须另立全新 train/validation/test split。下一轮优先候选为：在多接触训练分布上的 train-only CEM/RL policy improvement，或只使用现有 deployable proprioception 的受约束在线 readout adaptation；不能回看本轮 test 调 fast/slow 常数、teacher mix、budget 或 checkpoint。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_esn_multiscale_fair_20260821/fair_results.json`。
本地归档结果：`outputs/paper_mpc_esn_multiscale_fair_20260821/fair_results.json`。
SHA-256：`dfe8920f738f41efdeb1f3892ee0b6da585a85598e89fd3f0a1e3d07f1332042`。
