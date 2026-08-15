# Fan Ye ESN-VMC：冻结 WBC-aware V4 one-shot final holdout

## Protocol integrity

This is the single frozen V4 evaluation after the analytic-teacher envelope
was selected on a separate ESN validation pool. No V4 metric was used to
change reservoir #22, teacher gains, filtering, action bounds, WBC, fixture
geometry, torque backend, or recovery timing.

Before simulation, the final runner rejected any mismatch unless all were true:

1. input manifest stage was the frozen V4 five-side holdout;
2. comparator used `reference_source=fixed_panda_wbc`;
3. comparator's `vmc_gated` fixture-ID set exactly matched the V4 manifest;
4. VMC-gated was valid on every fixture.

The frozen ESN candidate was the validation-only selection:

```text
translation softening = -0.35
rotation softening    = -0.20
recovery-drive boost  =  0.40
causal gate filter    =  0.00 s
```

## Final result

All ten V4 physical rod-collision fixtures, including the matched no-rod task,
were valid for the frozen Fan Ye ESN-VMC. Numeric comparison below is the same
ten-fixture common-valid set used by the existing fixed-WBC VMC-gated ladder.

| Metric | VMC-gated | Frozen Fan Ye ESN-VMC | Relative change |
|---|---:|---:|---:|
| valid fixtures | 10 / 10 | **10 / 10** | — |
| recovery RMSE | 1.836 mm | **1.772 mm** | **−3.47%** |
| release-to-rejoin | 0.197 s | **0.188 s** | **−4.46%** |
| post-contact jerk P95 | **509.41 m/s³** | 546.03 m/s³ | +7.19% |
| peak torque | **30.835 Nm** | 30.879 Nm | +0.14% |
| torque-rate peak | **125.583 Nm/s** | 126.861 Nm/s | +1.02% |
| peak contact force | **37.368 N** | 37.528 N | +0.43% |
| contact impulse | **3.110 N·s** | 3.192 N·s | +2.61% |

## Interpretation

The final holdout reproduces the validation direction for recovery: the ESN
reduces recovery RMSE and release-to-rejoin time while retaining 10/10 task and
collision validity. It also reproduces the limitation: current analytic-teacher
warm-start is more aggressive than fixed VMC-gated after contact, increasing
jerk and contact impulse. Therefore this final test supports a **recovery
accuracy / speed gain with a smoothness trade-off**, not a claim of universal
superiority, passivity, or hardware readiness.

The absolute V4 jerk scale is higher than the ESN validation pool because V4
contains a different frozen held-out impact timing/geometry realization. Only
the paired V4 comparison above should be used to interpret the final result.

## Scope and artifacts

- [one-shot final per-fixture artifact](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/v4_final_frozen_selection/fan_ye_esn_v4_final.json)
- [validation-only selection report](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/fan_ye_teacher_envelope_validation_report.md)
- [guarded final runner](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/scripts/run_fan_ye_esn_v4_final.py)

This is MuJoCo simulation only, across five axis-aligned approach sides;
`positive_z` remains excluded. It is not sign-complete 3-D collision coverage,
a strict-passivity proof, a hardware result, or a sim-to-real guarantee.
