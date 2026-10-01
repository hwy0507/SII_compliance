# Pure ESN low-input-scale output-gain screen — 2026-10-01

This screen changed only the ESN output gain on the replicated
`input_scale=0.25` checkpoint. The teacher manifest, canonical 48D/action7
contract, frozen combined-v4 scene, original gate, forbidden actor inputs and
actuator limits were unchanged. All rows are development `dt=1e-4`, 55 s and
550000 physical substeps.

| output gain | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---:|:---:|:---:|---|---:|---:|---:|---:|
| 0.80 | no | no | lift | 60.590 | 37.618 | 0.1031 | 0.1257 |
| 0.90 | no | no | carry | 144.782 | 37.867 | 0.1395 | 0.1705 |
| 0.95 | no | no | lift | 73.919 | 37.051 | 0.1019 | 0.1150 |

All three completed the full horizon and passed independent action/reservoir
replay and physical-substep audit (`0` replay error, `550000` substeps). None
completed placement or valid pillar exposure, so no candidate is strict. The
0.90 candidate reached carry but did not clear the pillar requirement. These
results do not support ESN generalization or superiority over MLP.

Base checkpoint SHA256:
`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`.
Variant hashes and audit hashes are in
`outputs/esn_low_scale_gain_screen_20261001_v1/SCREEN_PLAN.json` and
`gain_{080,090,095}_audit.json`. Raw rollouts remain preserved locally. No
formal `dt=5e-5` rerun is unlocked.
