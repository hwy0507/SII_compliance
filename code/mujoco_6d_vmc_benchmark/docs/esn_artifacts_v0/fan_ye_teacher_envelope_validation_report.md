# Fan Ye ESN-VMC：解析 teacher envelope 的 validation-only 选择

## 结论

已完成固定 Fan Ye reservoir #22 的解析 teacher envelope 扫描，并冻结一个**仅用于下一次 V4 one-shot 测试的候选策略**：

```text
translation_log_kappa_softening = -0.35
rotation_log_kappa_softening    = -0.20
recovery_drive_boost            =  0.40
gate_filter_time_constant_s     =  0.00 s
```

它不是“ESN 全面优于 VMC”的结论。它是目前 validation pool 上最合理的 Pareto 点：相较固定 `vmc_gated`，保持 11/11 有效并改善回归，但仍有小幅 jerk / contact-impulse 代价。此前默认 analytic-teacher warm-start 的 jerk / impulse 代价已明显压缩，但尚未消失。

## 严格实验边界

- 固定不变：Fan Ye CR/ESPI 预选的 reservoir #22、`FixedBasePandaWBC`、physical rod fixtures、`vmc_gated` torque backend、ESN action projection、torque feasibility scaling 与 slew limiter。
- readout 只从 11 条 **ESN train** physical rod-contact trace 拟合。
- ranking 只使用 11 条独立 **ESN validation** fixture；每个候选都为独立的 MuJoCo closed-loop replay。
- 复用 baseline 前，脚本逐项验证 validation fixture IDs 和 `reference_source=fixed_panda_wbc` 完全相同；VMC-gated comparator 必须为 11/11 valid。
- 冻结 WBC-aware V4 final test 没有被读取、写入或用于选择。
- student 输入始终仅为 `q(7), qdot(7), wbc_task_twist(6)`；`recovery_gate` 只作为离线 analytic teacher label，不进入 ESN。rod contact / force / state / fixture ID 也不进入 student。

## 选择约束

每个候选必须满足：11/11 valid、无 hard torque limit、峰值 torque 与 peak contact force 不高于 baseline 的 102%。在这些 safety-eligible 候选中，优先要求 jerk P95 和 impulse 不高于 baseline；若无候选满足，再比较 jerk/impulse 与 recovery RMSE/rejoin latency 的约束式 Pareto trade-off。

本轮没有任何非零 ESN residual 同时满足“平稳性不差于 baseline”的强偏好，所以没有虚构 domination claim。

## 基准与所选结果

所有数值是 11 个共同有效 validation fixture 的均值；相对变化以固定 `vmc_gated` 为分母，负值代表更低（更好）。

| 方法 / teacher | valid | recovery RMSE (mm) | rejoin (s) | jerk P95 (m/s³) | peak torque (Nm) | contact impulse (N·s) |
|---|---:|---:|---:|---:|---:|---:|
| VMC-gated baseline | 11/11 | 2.240 | 0.304 | 274.13 | 31.221 | 3.869 |
| 初始 warm-start：−0.55 / −0.25 / 0.65 | 11/11 | 2.208 (−1.42%) | 0.292 (−4.06%) | 292.66 (+6.76%) | 31.269 (+0.15%) | 3.961 (+2.39%) |
| **selected：−0.35 / −0.20 / 0.40 / no filter** | **11/11** | **2.212 (−1.27%)** | **0.295 (−3.23%)** | **281.52 (+2.70%)** | **31.259 (+0.12%)** | **3.939 (+1.83%)** |

因此，所选 envelope 相较初始 warm-start：

- jerk excess：`+6.76% → +2.70%`；
- contact-impulse excess：`+2.39% → +1.83%`；
- recovery RMSE 仍低于 baseline 1.27%，rejoin 仍快 3.23%；
- peak torque 增量仍很小（+0.12%），所有 fixture 都没有 hard-limit event。

## 扫描证据与负结果

### Phase 1：recovery-drive（translation −0.45，rotation −0.20）

| drive boost | RMSE 相对变化 | rejoin 相对变化 | jerk 相对变化 | impulse 相对变化 |
|---:|---:|---:|---:|---:|
| 0.25 | +1.92% | 0.00% | +2.59% | +0.80% |
| 0.40 | +0.07% | −1.79% | +2.72% | +1.64% |
| 0.55 | −1.61% | −4.06% | +5.09% | +2.26% |
| 0.65 | −2.71% | −5.14% | +8.60% | +2.37% |

增大 drive 确实加快回归，但 jerk/impulse 单调升高；这验证了原 teacher 的激进 recovery-drive 是主要 trade-off 来源。

### Phase 2：translation softening（rotation −0.20）

| translation / drive | RMSE 相对变化 | rejoin 相对变化 | jerk 相对变化 | impulse 相对变化 |
|---|---:|---:|---:|---:|
| −0.35 / 0.40 **(selected)** | −1.27% | −3.23% | +2.70% | +1.83% |
| −0.35 / 0.55 | −2.95% | −4.54% | +5.56% | +2.45% |
| −0.55 / 0.40 | +1.32% | −1.31% | +5.31% | +1.44% |
| −0.55 / 0.55 | −0.39% | −3.23% | +6.82% | +2.07% |

### Phase 3–4：rotation 与因果 label smoothing

- rotation `0.00 / −0.10 / −0.25`（其余为 selected 参数）都没有优于 `−0.20`；最小 jerk excess 仍为 `+2.84%`，且 `rotation=0` 的 torque-rate 反而升高 3.17%。
- 新增的 label-side causal low-pass（40 / 80 / 120 ms）默认关闭时完全等价旧 teacher；开启后仍 11/11 valid，但 jerk excess 分别为 `+5.11% / +4.44% / +3.02%`，不优于无滤波的 `+2.70%`。这说明当前回归能力主要来自及时响应，单纯滤波并不能解决全部平稳性差距。

这些负结果保留在本报告中，防止后续重复扫同一无效方向。

## 可复现工件与下一步

- [所选配置的逐 fixture validation scan](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/teacher_envelope_validation_selected/scan_result.json)
- [冻结候选的 readout summary](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/teacher_envelope_validation_selected/fan_ye_esn_readout_train_summary.json)
- [冻结候选的 readout 权重](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/teacher_envelope_validation_selected/fan_ye_esn_warmstart.npz)

下一步应是将这一配置作为**冻结候选**进行一次 WBC-aware V4 final-test one-shot evaluation，并报告完整失败/成功 fixture，而不是继续在 V4 上调参。若 final test 仍显示 jerk gap，后续研究方向应转向带安全约束的 readout / RL residual 或更明确的 contact-state-estimation，而非把 collision diagnostics 偷渡到 ESN 输入。

## 限制

结果仅限 MuJoCo simulation 的当前五类轴向有效 physical fixtures；不是 sign-complete six-side coverage、任意连续 3D collision、硬件验证、strict passivity proof 或 sim-to-real guarantee。
