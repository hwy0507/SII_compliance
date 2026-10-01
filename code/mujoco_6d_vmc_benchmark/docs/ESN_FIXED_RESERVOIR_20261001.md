# 2026-10-01 fixed-reservoir ESN decomposition

After the isolated `input_scale=0.25` screen produced one task-completing ESN seed, this registered experiment fixed the reservoir seed at `2026100101` and varied only the ESN readout/optimizer seeds `2026100121/22/23`. Input scale remained `0.25`; the paired MLP used the corresponding readout seed plus one. The nine teacher traces, 7/2 identity split, canonical48D/action7 contract, forbidden input list, office-v5 combined-thick-corner-pillar-v4 scene, gate, actuator limits, 55 s horizon, and development `dt=1e-4` were unchanged.

The configuration [`configs/esn_fixed_reservoir_screen_20261001.json`](../configs/esn_fixed_reservoir_screen_20261001.json) has SHA256 `c5f31edb3263fa16702229bfd14d74f7f6b584d0f9a8136f5c51d521385e4828`; the trainer [`tools/train_esn_mlp_fixed_reservoir_20261001.py`](../tools/train_esn_mlp_fixed_reservoir_20261001.py) has SHA256 `9e30fd12ed056bedcdafe80a32deb67786aa20e6f22b4612b8ebfecdccea5d2f`.

| readout seed | method | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---:|---|---:|---:|---|---:|---:|---:|---:|
| 21 | ESN | no | no | lift | 459.354 | 47.153 | 0.2614 | 0.1393 |
| 21 | MLP | yes | no | retreat | 35.651 | 45.832 | 0.0703 | 0.1483 |
| 22 | ESN | no | no | carry | 177.133 | 47.071 | 0.1210 | 0.6323 |
| 22 | MLP | yes | no | retreat | 42.980 | 44.431 | 0.1088 | 0.1442 |
| 23 | ESN | no | no | carry | 148.377 | 45.021 | 0.1630 | 0.1780 |
| 23 | MLP | yes | no | retreat | 38.264 | 44.760 | 0.0727 | 0.1881 |

The independent audit `outputs/esn_fixed_reservoir_20261001/INDEPENDENT_AUDIT.json` has SHA256 `d82652a366c6f2d5cd6b3562c9b483ae298563f5a130955cf41aad3a8f6a2cb3`. All six rows have 550000 physical substeps and exact action replay; ESN reservoir-state replay maximum error is 0. ESN task success is 0/3 and strict success is 0/3. MLP task success is 3/3 but strict success is 0/3. The 73-file local receipt has SHA256 `eda963478fa3362d7ed4078bb6d6e9eb1bd500126310670eed8b83bfcbe54af6`.

This decomposition shows that fixing one reservoir does not make the low-scale ESN robust to readout seed. No formal `dt=5e-5` run is unlocked. Artifacts remain local and pending arm1/GitHub synchronization because both network paths were unavailable.
