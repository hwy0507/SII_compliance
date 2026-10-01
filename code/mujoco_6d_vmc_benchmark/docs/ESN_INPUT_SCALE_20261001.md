# 2026-10-01 ESN input-weight scale screen and replication

This screen changed only the fixed ESN input weight scale while retaining the 128-unit reservoir leak, spectral radius, teacher labels, identity split, MLP control, frozen office-v5 combined-thick-corner-pillar-v4 world, gates, actor input contract and actuator limits. The three registered scales were `0.25`, `0.45`, and `0.80`; all rows used development `dt=1e-4`, 55 s, and 550000 physical substeps.

The manifest SHA256 remained `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`. The screen configuration [`configs/esn_input_scale_screen_20261001.json`](../configs/esn_input_scale_screen_20261001.json) has SHA256 `1197d1739ae0e2f1af9671cf4dbabbd1350bb4ab589ef7b951708fd5bd87deff`; the trainer [`tools/train_esn_mlp_input_scale_screen_20261001.py`](../tools/train_esn_mlp_input_scale_screen_20261001.py) has SHA256 `881d670a56f1723576534020ef4baebddd0ed29e5e0f7bb2f7a4ffc9e0db77c6`.

| input scale | method | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---:|---|---:|---:|---|---:|---:|---:|---:|
| 0.25 | ESN | yes | no | retreat | 68.471 | 48.004 | 0.1164 | 0.1499 |
| 0.25 | MLP | yes | no | retreat | 47.291 | 44.395 | 0.0906 | 0.1487 |
| 0.45 | ESN | no | no | carry | 48.304 | 45.226 | 0.1562 | 0.7154 |
| 0.45 | MLP | yes | no | retreat | 40.385 | 45.813 | 0.0720 | 0.1410 |
| 0.80 | ESN | no | no | load_transfer | 81.255 | 48.469 | 0.1142 | 0.1502 |
| 0.80 | MLP | yes | no | retreat | 56.117 | 44.347 | 0.1149 | 0.1225 |

The low-scale ESN row is the first task-completing ESN in this campaign, but it did not pass the sustained-contact strict gate. Its independent audit (`outputs/esn_mlp_input_screen_20261001/INDEPENDENT_AUDIT.json`, SHA256 `6ac8981698d3709adabd3ef1c7d766b8007cf3b7453d199079aad444e663404b`) reports exact action and reservoir replay and 550000 physical substeps for every row. It therefore did not unlock formal `dt=5e-5`.

To test whether the task success was a seed artifact, a pre-registered replication fixed input scale `0.25` and trained seeds `2026100118/19/20`. The replication configuration [`configs/esn_input_scale_replication_20261001.json`](../configs/esn_input_scale_replication_20261001.json) has SHA256 `b2e8136c131a2bead55386c6e9c11c89f3bafc92fa3d927c3b6220be78076f2`; its audit is `outputs/esn_input_replication_20261001/INDEPENDENT_AUDIT.json`, SHA256 `0bc7fe3f45124f21fab715ab49b30b369e87e104d987021da55e716b28305ba4`.

| seed | method | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---:|---|---:|---:|---|---:|---:|---:|---:|
| 18 | ESN | no | no | lift | 68.033 | 37.055 | 0.1168 | 0.1817 |
| 19 | ESN | no | no | lift | 156.774 | 48.296 | 0.0785 | 0.1237 |
| 20 | ESN | no | no | lift | 805.775 | 57.725 | 0.1716 | 0.1889 |

The low-scale ESN replication rate was 0/3 task success and 0/3 strict success. The single task-completing seed is therefore not evidence of a robust ESN structure. The three MLP replication rows had task success 0/3, 1/3, and 1/3 respectively, all strict=false. The 73-file replication receipt SHA256 is `688ae6b3556023d64eb1c68ba2d84cde0b6ca461892240cbe9f8a83666b484f2`.

All artifacts are local and pending arm1 synchronization; GitHub and SSH were unreachable during this turn. No environment, gate, forbidden input, or formal-step rule was relaxed.
