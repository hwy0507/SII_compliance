# 多接触多时间尺度 ESN 的 CEM 读出策略改进结果（2026-08-21）

## 结论先行

在新的 `positive_y + finite-mass ellipsoidal hand_proxy` 接触分布中，train-only CEM readout improvement 消除了此前 multi-scale BC ESN 的严重失败：被冻结后，CEM ESN 在 held-out test 达到 `19/20` success，而 validation-selected VMC 达到 `17/20`。ESN 的 mean at-grasp error 为 `16.756 mm`，VMC 为 `19.979 mm`，点估计差 ESN−VMC=`−3.223 mm`。

然而，这个 20-fixture test 的主要成功率差仅有两例 ESN-only success，且 at-grasp error 的 paired fixture-level 95% t CI 为 `[-7.534,+1.088] mm`、seed-level CI 为 `[-9.419,+2.973] mm`，均跨零。因此该轮可以诚实地报告为：**CEM-improved multi-contact ESN 与 validation-selected VMC 至少相当，并呈现数值上的 success/error 优势；单轮样本尚不足以宣称统计显著地战胜 VMC。**

这是一项重要的算法进展，但不能将 point estimate 写成已证实的普遍 superiority。此前已消耗的 test seeds 以及本轮 test seeds 均不可再用于调参；若要把“胜过 VMC”作为强结论，必须做新的独立 confirmatory replication。

## Train-only CEM development（不是测试声明）

起始模型为 multi-contact-trained 320-unit fast--slow ESN；CEM 固定 reservoir、32-D observation、5% torque budget 和 FR3 safety envelope，只优化七个 output readout row 的 bounded log-gains。CEM 使用训练专用 seeds `20261401–20261404`、2 fixtures/seed、6 iterations、population 16（含 parent）、elite 5。

开发集最佳 checkpoint 为：

| 指标 | Train-only CEM result |
|---|---:|
| Success | 8/8 |
| At-grasp error | 15.712 mm |
| Peak contact force | 92.405 N |
| Peak torque | 34.150 N·m |
| Contact bouts | 2.375 |
| Hard limit | 0/8 |

相对 BC parent 的 output-row gain factors：

```text
[1.1507401, 1.2770411, 1.1853003, 1.1037766,
 0.9714060, 1.6422393, 1.0113997]
```

这些数字仅说明训练期优化过程，不能与独立 test 混用。

## Validation selection

validation 使用新的 `20261411–20261415`，每 seed 4 个 fixture。ESN family 在 frozen parent 与 CEM checkpoint 中选择；VMC 在同一 realization 上独立搜索 `k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`。两家族的规则均为 success 优先、error 破平局。

| Family | Candidate | Budget | Success | Mean error | Peak force | Peak torque | Contact bouts | Hard limit |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ESN | Multi-scale BC parent | 5% | 7/20 | 23.625 mm | 96.255 N | 32.662 N·m | 2.55 | 0/20 |
| ESN | Multi-scale CEM | 5% | **16/20** | **17.419 mm** | 96.267 N | 33.883 N·m | 2.70 | 0/20 |
| VMC | Selected k=1.0 | 2% | **16/20** | 20.018 mm | 96.442 N | 32.840 N·m | 2.45 | 0/20 |

因此 ESN 选择 CEM checkpoint，VMC 选择 `k=1.0, budget=2%`。这一步在 held-out test 运行前完成。

## Held-out test

held-out seeds 为 `20261416–20261420`，每 seed 4 个全新 fixture，共 20 个 paired realization。它们在 CEM 或 validation 阶段均未运行。

| Method | Success | At-grasp error (mean ± SD) | Peak force (mean ± SD) | Peak torque (mean ± SD) | Contact bouts | Hard limit |
|---|---:|---:|---:|---:|---:|---:|
| Selected multi-scale CEM ESN, 5% | **19/20** | **16.756 ± 1.792 mm** | 92.313 ± 31.203 N | 34.064 ± 0.630 N·m | 2.70 | 1/20 |
| Selected VMC k=1.0, 2% | 17/20 | 19.979 ± 8.723 mm | 92.719 ± 31.603 N | **32.825 ± 0.500 N·m** | **2.25** | 1/20 |

Rollout-level 95% t CI：ESN at-grasp error `[15.917,17.595] mm`，VMC `[15.897,24.062] mm`。

### Matched statistics

在相同 `(seed, fixture_index)` 下计算 ESN−VMC：

| Metric | Mean difference | Fixture-level 95% t CI | Seed-level 95% t CI |
|---|---:|---:|---:|
| At-grasp error | **−3.223 mm** | `[-7.534,+1.088] mm` | `[-9.419,+2.973] mm` |
| Peak post-impact error | **−46.308 mm** | `[-50.603,-42.014] mm` | `[-49.383,-43.233] mm` |
| Peak contact force | −0.406 N | `[-0.696,-0.116] N` | `[-0.776,-0.036] N` |
| Peak torque | +1.239 N·m | `[+0.753,+1.725] N·m` | `[+0.439,+2.039] N·m` |
| Contact bouts | +0.450 | `[+0.095,+0.805]` | `[+0.045,+0.855]` |

成功配对：2 个 fixture ESN 成功且 VMC 失败；0 个 fixture VMC 成功且 ESN 失败；17 个两者都成功；1 个两者都失败。两种方法的唯一 hard-limit event 发生在同一个 paired fixture，因此均为 `1/20`。

## 物理条件与安全解释

test fixture 实际范围：

| Parameter | Held-out range |
|---|---:|
| Impactor mass | 0.220–0.497 kg |
| Slide damping | 1.040–3.999 N·s/m |
| Driver kp | 2.654–8.921 kN/m |
| Driver force limit | 154.4–287.7 N |
| Contact time constant | 8.56–24.52 ms |
| Stroke | 0.1608–0.1750 m |
| Height | 0.5391–0.5418 m |
| Start time | 0.902–1.021 s |
| Cycle period | 0.663–0.716 s |

ESN 和 VMC 接触力几乎相同，ESN 的峰值 force 略低；但 ESN 的 peak torque 高 `1.239 N·m`、contact bouts 多 `0.45`，并与 VMC 同样出现 1 次 hard-limit。因而不能称它在所有 safety dimensions 上更好。真实机器人部署前，必须将 hard-limit event 作为风险项单独诊断，并进行 system identification、torque sensing validation、外部安全停止和低速 dry-run。

## 方法边界与下一步

该正向结果来自：multi-contact BC initialization + train-only MuJoCo CEM readout policy improvement。部署 ESN 仍只接收 proprioceptive 32-D observation；没有接触力、接触方向/几何标签、装置参数或未来信息。它表明此前 cross-contact failure 并非 ESN 机制不可修复，但也表明 BC alone 与 fixed fast--slow dynamics 不够。

可汇报表述应为：

> On a new held-out positive-y finite-mass hand-proxy contact protocol, a multi-contact, multi-time-scale ESN improved by train-only CEM achieved 19/20 success versus 17/20 for a separately validation-selected VMC, with lower mean at-grasp error (16.76 versus 19.98 mm). The paired error confidence interval crossed zero, so this is a favorable but statistically inconclusive single-split result rather than a confirmed general superiority claim.

本轮 `20261416–20261420` test seeds 已消耗。任何后续强 superiority claim 都需要新的、独立的预先冻结 replication split；不得依据本轮 test 重调 CEM gain、budget、CEM hyperparameter、VMC stiffness或 ESN checkpoint。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_multicontact_multiscale_cem_20260821/fair_results.json`。

- fair-results SHA-256：`b21973c6dc7108a5abe9e8e57739f4e6ace3659e6b71dc6a9108c2dd3fe6fb84`；
- CEM train-summary SHA-256：`0a57736f3f98a0158b5c1fbb2d1e15fcb4ed8fedf120a2bfcc807d6b22394ae7`。
