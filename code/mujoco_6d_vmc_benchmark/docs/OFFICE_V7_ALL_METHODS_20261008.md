# Office-v7 three-obstacle unified comparison (2026-10-08)

This is a separate development protocol. It does not replace or amend the sealed office-v6 `/24` or `/72` results. Every completed row below uses the same archived office-v6 MJB (`d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`), formal `dt=5e-5`, 55 s horizon, canonical 48D proprioceptive/reference-relative input, action7, the unchanged actuator limits and the unchanged task/strict gates.

The registered schedule is: ball at 2.0 s, person push from 4.5 s, rod push from 14.0 s for 5 s, then thick-corner placement. The actor receives no contact truth, obstacle state, event time, visual or distance field. The condition and all raw artifacts are preserved at:

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_three_obstacle_20261008/run_003/`

The run contains 17 registered methods. Twelve completed physical rollouts; five RL transfer rows failed before simulation because the pinned JAX/Orbax checkpoint loader raised `ValueError: sharding passed to deserialization should be specified`; their failed logs and denominators are retained. Two additional infrastructure-only retries used an invalid short Git SHA or unsupported schedule label; these are `run_001` and `run_002`, not physical failures.

| Method | Task | Strict | RMSE (mm) | Peak torque (Nm) | Peak speed (m/s) | Penetration (mm) | Status / failure |
|---|---:|---:|---:|---:|---:|---:|---|
| zero | 0 | 0 | 26.543 | 37.233 | 0.376 | 0.172 | complete; carry |
| original_vmc_native | 0 | 0 | 29.694 | 41.764 | 0.384 | 0.156 | complete; carry |
| fixed_vmc | 0 | 0 | 30.156 | 38.129 | 0.377 | 0.169 | complete; carry |
| fixed_admittance | 0 | 0 | 27.567 | 38.764 | 0.384 | 0.179 | complete; carry |
| fixed_impedance | 0 | 0 | 22.708 | 45.148 | 0.334 | 0.141 | complete; retreat |
| parameter_vmc | — | — | — | — | — | — | infrastructure failure; JAX/Orbax sharding |
| parameter_admittance | — | — | — | — | — | — | infrastructure failure; JAX/Orbax sharding |
| parameter_impedance | — | — | — | — | — | — | infrastructure failure; JAX/Orbax sharding |
| direct_metric_74001 | — | — | — | — | — | — | infrastructure failure; JAX/Orbax sharding |
| direct_office_task_74001 | — | — | — | — | — | — | infrastructure failure; JAX/Orbax sharding |
| recovery_lift0.035_distance0.02 | 1 | 0 | 29.153 | 51.658 | 0.384 | 0.253 | complete; strict failed penetration |
| recovery035_esn_fixed | 1 | 1 | 29.306 | 49.377 | 0.380 | 0.174 | complete |
| paired_recovery035__fp64 | 0 | 0 | 49.383 | 39.172 | 0.380 | 0.165 | complete; carry |
| paired_recovery035_rnn_fp64 | 0 | 0 | 35.016 | 40.670 | 0.392 | 0.173 | complete; carry |
| recovery035_esn_memoryless | 1 | 1 | 28.523 | 54.024 | 0.385 | 0.181 | complete |
| paired_feature_matched_mlp | 1 | 1 | 29.185 | 53.355 | 0.360 | 0.141 | complete |
| paired_feature_matched_rnn | 0 | 0 | 47.405 | 53.475 | 0.373 | 0.423 | complete; pillar penetration/load-transfer failure |

The completed physical denominator is therefore `12` rows, with task `4/12` and strict `3/12`; the registered comparison denominator is `17`, with five RL rows explicitly `not run` because of infrastructure failure. A low RMSE, low torque or low speed row is not a success claim. In particular, `recovery_lift0.035_distance0.02` completed the task gate but failed strict on penetration, while both ESN rows passed task and strict in this single development condition. This is a useful stress-case result, not evidence of cross-condition generalization or a replacement for the sealed office-v6 matrix.

All completed rows have full 55 s horizon, action replay and source/model hashes in their `AUDIT.json`; contact force channels and substep traces are preserved per method. The corrected campaign source SHA256 is `b19d414801ce6694693525887e361995a07a49e7cce59509d041d0aa51e7842f`.
