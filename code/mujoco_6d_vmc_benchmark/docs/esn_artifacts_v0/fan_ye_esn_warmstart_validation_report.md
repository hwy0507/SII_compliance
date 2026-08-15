# Fan Ye-aligned ESN-VMC：解析 teacher warm-start 的闭环验证

## 结论

Fan Ye 时间尺度对齐 reservoir #22 已成功接入 Panda 的同一 WBC → VMC → torque safety backend，并在 ESN validation pool 的 **11/11** 个有效物理 collision fixture 上完成抓取、抬起和稳定 rejoin。该 ESN warm-start 相比固定 `vmc_gated` 在 recovery RMSE 和 release-to-rejoin latency 上有小幅改善，但 jerk 和 contact impulse 变差。因此它是可工作的闭环起点，不是“ESN 全面优于 VMC”的结论。

本轮只使用 ESN train pool 拟合 readout、只使用 ESN validation pool 检查 teacher/closed-loop 表现；冻结 WBC-aware V4 final test 没有被读取或用于选择。

## 链路与信息边界

```text
physical train traces → Fan Ye CR/ESPI-selected reservoir #22
                     → causal analytic VMC teacher labels
                     → ridge readout warm-start
                     → 25 Hz ESN residual action
                     → bounded six-kappa + recovery-drive projection
                     → existing VMC / torque feasibility / torque slew backend
```

ESN student 输入严格是 `q(7), qdot(7), wbc_task_twist(6)`。`recovery_gate` 只在离线阶段生成 teacher label；它不进入 ESN feature。rod contact/force/state、obstacle pose/geometry、future release 和 fixture ID 既不进入 student 输入，也不被 readout trainer 读取。

teacher 的 7D 行为模板是：当现有 VMC 的因果 tracking-error gate 增强时，降低 translation/rotation stiffness residual，并提高 recovery-drive residual。所有 ESN 输出仍会经过 `[-1,1]` 截断、正值/范围/速率受限的 spring-drive projection、共享 torque feasibility scaling 和 torque slew limiter。

## Readout 训练与离线保持验证

| 项目 | 结果 |
|---|---:|
| selected Fan Ye reservoir | candidate #22 |
| train physical trace | 11 |
| train samples after washout | 1,650 |
| train teacher-action MSE | 0.003636 |
| held-out validation teacher-action MSE | 0.004039 |

这两个 MSE 是“ESN 对解析 teacher action 的拟合误差”，不等于任务 tracking error，也不是相对 VMC baseline 的优势指标。

## 11-fixture WBC-aware validation ladder

所有指标都在两种方法共同有效的 11 个 validation fixture 上按 fixture 平均：

| 指标 | VMC-gated | Fan Ye ESN-VMC | 相对变化 |
|---|---:|---:|---:|
| valid / 11 | 11 | 11 | — |
| recovery RMSE | 2.240 mm | **2.208 mm** | **−1.42%** |
| release-to-rejoin | 0.304 s | **0.292 s** | **−4.06%** |
| post-contact jerk P95 | **274.13 m/s³** | 292.66 m/s³ | +6.76% |
| peak torque | **31.221 Nm** | 31.269 Nm | +0.15% |
| torque-rate peak | 130.44 Nm/s | **128.91 Nm/s** | **−1.18%** |
| peak contact force | **44.499 N** | 44.572 N | +0.16% |
| contact impulse | **3.869 N·s** | 3.961 N·s | +2.39% |

### 如何解释

- ESN 的 4.06% rejoin 改善和 1.42% recovery RMSE 改善说明：从 `q/qdot/WBC twist` 的时序中学习到的 residual 确实已经影响了物理闭环，而不是只在离线拟合得好。
- 代价是 jerk P95 上升 6.76%，接触冲量也上升 2.39%。这与单 fixture 的观察一致：当前 teacher 在回归阶段略偏激进。
- peak torque 几乎不变，torque-rate 略有下降，且所有 fixture 没有 hard torque limit；安全 backend 的边界正常工作。
- 因此不能声称该 warm-start 已在安全、精度、平稳性上全面胜过 `vmc_gated`。下一步应该在 validation split 内降低 teacher drive boost 或调整 softening envelope，优先消除 jerk/impulse trade-off，然后才冻结配置进入 V4。

## 可复现工件

- [Fan Ye CR/ESPI preselection](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/fan_ye_timescale_screen_train.json)
- [readout train summary](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/fan_ye_esn_readout_train_summary.json)
- [held-out teacher generalization](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/fan_ye_esn_readout_validation.json)
- [11-fixture closed-loop ladder](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/fan_ye_esn_validation_ladder.json)
- [one physical closed-loop trace with ESN action audit](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/closed_loop_negative_y_0955/rod_perturbation_kvec_27.6_52.6_48.7_35.9_40.7_34.8_trace.npz)

## 限制

- 该 readout 来自解析 VMC-gate teacher，因此应被称为 `analytic-teacher warm-start`，而不是端到端 ESN discovery 或 RL 结果。
- 当前仍只覆盖五种轴对齐 rod approach（`+z` 不在有效 pool 中），不是任意连续 3D collision。
- 本文结果仅限 MuJoCo simulation；不构成硬件实验、全局 strict passivity proof 或 sim-to-real guarantee。
