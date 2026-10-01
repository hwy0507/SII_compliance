# 2026-10-01 ESN recurrent spectral-radius screen

This is a second pure ESN algorithm screen on the locked VMC teacher bank. The only ESN change was the fixed recurrent spectral radius (`0.60`, `0.90`, or `1.10`) of the 128-unit reservoir. Each profile has a paired 128-unit MLP control trained from the same seven teacher identities and evaluated with the same two held-out identities. The manifest, canonical48D/action7 contract, prohibited input list, combined-thick-corner-pillar-v4 world, original gates, actuator limits, seed `2026091751`, 55 s horizon, and development `dt=1e-4` were unchanged.

The pre-registration is [`configs/esn_spectral_screen_20261001.json`](../configs/esn_spectral_screen_20261001.json), SHA256 `e96a9880d607d77390b062542e25dab677880587a2483aeb3dcfc4e9b48f0c17`; the training source is [`tools/train_esn_mlp_spectral_screen_20261001.py`](../tools/train_esn_mlp_spectral_screen_20261001.py), SHA256 `9381becd58ce6c750672e6184f4a452004990bec5e98dd989ba8eab97fab5e5c`.

| profile | spectral radius | method | validation weighted MSE | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | external penetration (mm) |
|---|---:|---|---:|---:|---:|---|---:|---:|---:|---:|
| low | 0.60 | ESN | 5.033e-5 | no | no | lift | 934.262 | 53.141 | 0.2172 | 0.1127 |
| low | 0.60 | MLP | 2.135e-5 | no | no | load_transfer | 49.318 | 44.387 | 0.0829 | 0.1891 |
| baseline | 0.90 | ESN | 7.012e-5 | no | no | lift | 144.160 | 50.655 | 0.2157 | 1.5602 |
| baseline | 0.90 | MLP | 1.954e-5 | yes | no | retreat | 64.162 | 44.255 | 0.1179 | 0.1432 |
| high | 1.10 | ESN | 6.244e-5 | no | no | carry | 224.085 | 45.164 | 0.2020 | 0.1049 |
| high | 1.10 | MLP | 1.828e-5 | no | no | lift | 50.577 | 35.428 | 0.0707 | 0.1432 |

The independent audit is `outputs/esn_mlp_spectral_screen_20261001/INDEPENDENT_AUDIT.json`, SHA256 `ee3d2ed86240f4a3c0ae753779c1a56e9719e03fa636b9ac46987ae3cbae2fb5`. All six rows have 550000 physical substeps and exact action replay; ESN reservoir-state replay maximum error is 0. No row passed strict, so no formal `dt=5e-5` run was unlocked. The 0.90 ESN exceeded the unchanged external penetration limit, which is retained as a failure rather than filtered out. The 73-file local evidence receipt is SHA256 `6505943bf8a8711fb03a2e48a86545cc1937e77b8f1e64c5e9459179a182ae0a`.

This screen provides no ESN task or strict success. The high-radius ESN reached carry with lower torque than some candidates, but did not complete placement. MLP task completion in one profile does not imply strict compliance or ESN superiority. The artifacts are local and pending arm1 synchronization because SSH remained unreachable during this turn.
