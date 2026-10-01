# 2026-10-01 ESN reservoir time-scale screen

This screen tested a pure ESN algorithm change on the locked VMC teacher bank. The only ESN change was the fixed 128-unit reservoir leak vector, represented by three time constants repeated across the fast, middle and slow reservoir blocks. The paired MLP was retrained for each profile with the same 128-unit hidden width, teacher manifest, identity split, estimated-wrench training weight, and optimizer budget.

The frozen manifest is `outputs/teacher_bank_label_manifest_20260930_final_v1/manifest.json`, SHA256 `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`. The actor remained canonical48D to action7 with pure proprioception. Contact truth, object or ball state, event time, task stage, and visual or range fields were not read. The combined-thick-corner-pillar-v4 world, original gate, actuator amplitude and rate limits, seed `2026091751`, 55 s horizon, and development `dt=1e-4` (550000 physical substeps) were unchanged.

The pre-registration is [`configs/esn_tau_screen_20261001.json`](../configs/esn_tau_screen_20261001.json), SHA256 `cd21c44d4b0aa494f464d9aa450c9ff70b6d002361f924e19ae5c7a378d9a9d4`. The training and materialization source is [`tools/train_esn_mlp_tau_screen_20261001.py`](../tools/train_esn_mlp_tau_screen_20261001.py), SHA256 `510fd962ebcf96051f064e5a51bab6fa14a16af5afa9650babd52dd71be4fa09`.

| profile | reservoir time constants (s) | method | validation weighted MSE | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|
| fast | 0.04 / 0.16 / 0.64 | ESN | 4.189e-5 | no | no | lift | 182.592 | 55.548 | 0.1311 | 0.1669 |
| fast | 0.04 / 0.16 / 0.64 | MLP | 1.575e-5 | yes | no | retreat | 47.897 | 44.029 | 0.0719 | 0.1576 |
| baseline | 0.08 / 0.40 / 1.60 | ESN | 6.844e-5 | no | no | carry | 86.080 | 40.585 | 0.0862 | 0.1540 |
| baseline | 0.08 / 0.40 / 1.60 | MLP | 1.960e-5 | yes | no | retreat | 40.338 | 44.927 | 0.0693 | 0.1374 |
| slow | 0.16 / 0.80 / 3.20 | ESN | 4.278e-5 | no | no | lift | 717.503 | 58.190 | 0.5007 | 0.1732 |
| slow | 0.16 / 0.80 / 3.20 | MLP | 1.700e-5 | no | no | load_transfer | 49.954 | 45.175 | 0.0651 | 0.1122 |

The independent audit is `outputs/esn_mlp_tau_screen_20261001/INDEPENDENT_AUDIT.json`, SHA256 `a91a64417b99632005ac9ee7cb107a9522a0d942fdb329264d4e6ef50054746a`. All six rows have 55 s and 550000 physical substeps; every action replay has maximum absolute error 0. ESN reservoir-state replay also has maximum absolute error 0. The execution metadata and raw rollouts are retained in the three profile directories. The combined evidence receipt covers 70 files and has SHA256 `361116939aee2ef4b6bedbcba828b215a516de3158434c00161e7e9c4694eea0`.

No candidate passed the unchanged strict gate, so no formal `dt=5e-5` run was started. The baseline leak profile reduced ESN RMSE and peak speed relative to fast and slow, but still stopped in carry; this is an algorithmic negative screen, not evidence that ESN is superior to MLP or deployable in a real environment. The MLP controls completed task in two of three profiles but did not pass strict, so replay MSE and task completion remain separate from compliance success.

At this turn GitHub and `arm1@192.168.31.70` were unreachable (`Couldn't connect to server` / SSH operation not permitted). The screen is therefore **local and pending server synchronization**; the local raw artifacts and hashes are preserved and are not described as server-archived.
