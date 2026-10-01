# Low-scale ESN/MLP weight-decay screen

## Scope and frozen contract

This screen kept the locked teacher bank and the frozen `office-v5 combined-thick-corner-pillar-v4` evaluation unchanged. The students used canonical 48D proprioception, action7, width 128, the fixed 7-train/2-validation identity split, and no contact truth, object state, event time, task stage, visual, or distance input. The original gate and actuator amplitude/rate limits were unchanged. Only the AdamW `weight_decay` value was varied; the ESN input scale was fixed at `0.25` for this screen.

The teacher manifest is `outputs/teacher_bank_label_manifest_20260930_final_v1/manifest.json` with SHA256 `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`. The training source and configuration hashes are:

| item | SHA256 |
|---|---|
| `configs/esn_mlp_low_scale_weight_decay_screen_20261001.json` | `f2249f5ada52ed12058432f985cf6aabafed7f1f024821405b13a2e48eddb83d` |
| `tools/train_esn_mlp_low_scale_weight_decay_20261001.py` | `6b6f45c55ca3fded968c7b0bba52d586b602267c7255c89dcab51aaea99f0fe8` |
| `tools/audit_single_office_esn_rollout_20260929.py` | `2297f8f4267e6efeaee5afc6e6d910caa37b10d34b92e06e0a12fcc589588104` |

All closed-loop rows are development results: `dt=1e-4`, 55 s, 550000 physical substeps, evaluation seed `2026091751`. The formal `dt=5e-5` run remains locked because no unchanged strict pass exists.

## Training and closed-loop results

Training used ESN seed `2026100130` and MLP seed `2026100131`. The checkpoint hashes are recorded in each `TRAINING_COMPLETE.json` and are repeated here for review.

| weight decay | method | validation weighted MSE | checkpoint SHA256 | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | external penetration mm |
|---:|---|---:|---|:---:|:---:|---|---:|---:|---:|---:|
| 1e-5 | ESN | 5.0491e-5 | `85c0595c...079b48f` | no | no | lift | 77.173 | 42.170 | 0.1106 | 0.1635 |
| 1e-5 | MLP | 1.7024e-5 | `ce01d0db...3b90cfb` | yes | no | retreat | 48.442 | 44.781 | 0.0662 | 0.1106 |
| 1e-4 | ESN | 5.0839e-5 | `d89867e2...418e9f` | no | no | lift | 75.485 | 42.723 | 0.1078 | 0.0997 |
| 1e-4 | MLP | 1.8082e-5 | `3cb4410c...302a45d9` | yes | no | retreat | 60.176 | 45.249 | 0.1172 | 0.1323 |
| 1e-3 | ESN | 5.0284e-5 | `6bd28d37...7b37e4c` | no | no | lift | 73.093 | 41.235 | 0.1134 | 0.0919 |
| 1e-3 | MLP | 1.7160e-5 | `abc09521...8686ac` | yes | no | retreat | 47.831 | 44.426 | 0.0702 | 0.1666 |

The MLP task successes still failed the unchanged strict gate because combined contact coverage was invalid (including the required pillar/contact conditions and, depending on the row, the ball rebound condition). ESN rows did not complete the task and stopped at `lift`; lower torque or penetration did not compensate for loss of task progress. These results do not support an ESN advantage.

## Audit and failure accounting

All six rows completed the full 55 s horizon and passed the independent action/physics audit. Action replay maximum error was `0`; ESN reservoir replay maximum error was `0`; MLP reservoir replay is `null` because MLP has no reservoir. Each audit reports 550000 physical substeps and 55 s physical duration, and recomputes RMSE, peak torque, and peak speed from the substep record. Raw rollouts, execution metadata, checkpoints, MJBs, and failure rows remain in:

```text
outputs/esn_mlp_low_scale_weight_decay_20261001_wd1e-5/
outputs/esn_mlp_low_scale_weight_decay_20261001_wd1e-4/
outputs/esn_mlp_low_scale_weight_decay_20261001_wd1e-3/
```

Two early command/setup failures occurred before any MuJoCo rollout: one used an invalid hash-variable path in the launcher, and one passed the repository root instead of the teacher-bank root. They are retained as setup failures and are not counted as experimental episodes. No gate, environment, actor input, or actuator constraint was changed to obtain the reported rows.

The current local source is complete for this screen, but GitHub and `arm1@192.168.31.70` were unreachable during this handoff. Therefore these large outputs are **local only and pending server synchronization**; the report does not claim a remote archive. The experiment is suitable for comparison as a development screen, not as a formal-step or real-hardware result.
