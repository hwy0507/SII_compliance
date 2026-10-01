# Temporal-consistency `delta=0.25` replication

The narrow-screen `delta_weight=0.25` ESN candidate was replicated with a
second training seed (`ESN=2026100152`, `MLP=2026100153`). The locked manifest,
7/2 identity split, canonical48D/action7 input/output, width 128,
`office-v5 combined-thick-corner-pillar-v4`, original gates, forbidden-input
contract, actuator limits, and 55 s development horizon were unchanged.

| method | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | penetration mm | ball rebound | rod longest run s |
|---|:---:|:---:|---|---:|---:|---:|---:|:---:|---:|
| ESN | no | no | lift | 72.223 | 44.403 | 0.125044 | 0.131457 | yes | 0.0471 |
| MLP | yes | no | retreat | 46.980 | 45.918 | 0.070165 | 0.151728 | yes | 0.4561 |

Both rows completed 55 s and 550000 physical substeps. The ESN replication did
not reach placement and lost the original screen's long rod-contact behavior.
The MLP completed the task gate but failed strict contact coverage. Action
replay maximum error was zero for both rows; ESN reservoir-state replay maximum
error was zero. The independently recomputed metrics and hashes are in
`outputs/esn_mlp_temporal_consistency_replication_20261001_s52/INDEPENDENT_AUDIT.json`.

This replication rejects a claim that the first `delta=0.25` ESN result is a
robust improvement. No strict row exists, so formal `dt=5e-5` remains locked.
