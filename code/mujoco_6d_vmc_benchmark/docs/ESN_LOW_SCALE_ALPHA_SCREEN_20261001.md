# Pure ESN low-input-scale alpha screen — 2026-10-01

This pre-registered screen tested action-readout smoothing on the only previous
`input_scale=0.25` ESN checkpoint that had completed `task_success` in one
development seed. The checkpoint, teacher bank, canonical 48D/action7 contract,
office-v5 combined-thick-corner-pillar-v4 fixture, gate, forbidden-input list,
and actuator limits were unchanged. Only the ESN `alpha` readout parameter was
changed. All rows are development results at `dt=1e-4`, 55 s and 550000 physical
substeps; no row is a formal `dt=5e-5` result.

| alpha | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) | longest rod run (s) |
|---:|---:|:---:|---|---:|---:|---:|---:|---:|
| 0.25 | no | no | lift | 68.485 | 35.127 | 0.1010 | 0.1423 | 0.0056 |
| 0.50 | no | no | carry | 138.424 | 39.585 | 0.1275 | 0.1373 | 0.6642 |
| 0.75 | no | no | lift | 59.341 | 37.282 | 0.1041 | 0.1101 | 0.0064 |

All three rollouts completed the full horizon and passed the independent
replay audit: action replay max error `0`, reservoir-state replay max error `0`,
and exactly `550000` physical substeps. None completed placement. The required
pillar exposure was absent in all three rows, so `contact_coverage_valid=false`.
Alpha 0.50 extended rod contact but stopped in carry; alpha 0.75 also failed the
ball-rebound condition. These are failure diagnostics, not evidence of ESN
generalization or superiority over MLP.

The base checkpoint is
`outputs/esn_mlp_input_screen_20261001_low/esn_input.npz`, SHA256
`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`.
Materialized variant hashes and per-row audit hashes are recorded in
`outputs/esn_low_scale_alpha_screen_20261001_v1/SCREEN_PLAN.json` and
`alpha_{025,050,075}_audit.json`. The complete raw rollouts remain preserved
locally. The run used the local `.venv-rl` interpreter, one CPU thread, and
observed peak RSS of approximately 667 MiB per rollout.

Because no unchanged strict pass exists, the formal `dt=5e-5` gate remains
locked. Server archival was attempted after the run; if SSH is unavailable the
artifacts remain explicitly local and pending synchronization.
