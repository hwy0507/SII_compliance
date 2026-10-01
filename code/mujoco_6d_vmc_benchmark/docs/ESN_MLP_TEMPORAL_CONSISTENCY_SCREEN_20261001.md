# ESN/MLP temporal-consistency loss screen

## Frozen protocol

This registered screen used the locked nine-trajectory teacher manifest (SHA256 `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`), the fixed 7-train/2-validation identity split, canonical 48D proprioception, action7, and width 128 for both students. The environment was frozen `office-v5 combined-thick-corner-pillar-v4` with the original gate and actuator amplitude/rate limits. The actor received no contact truth, object or ball state, event time, task stage, visual, or distance input. Only the training objective changed: weighted action MSE plus `delta_weight` times weighted consecutive-action delta MSE. The runtime policy and environment were unchanged.

Source/config hashes:

| item | SHA256 |
|---|---|
| `configs/esn_mlp_temporal_consistency_screen_20261001.json` | `34cd86834ec9348bfb5a0f41602ed5ae09e47a58f199a66d50ab44d6719670a3` |
| `tools/train_esn_mlp_temporal_consistency_screen_20261001.py` | `49a3b2bf3ad69889f07f8d8f42326d82cde686d0d3a60cb9e02b79eaf48bb4f5` |
| audit tool | `2297f8f4267e6efeaee5afc6e6d910caa37b10d34b92e06e0a12fcc589588104` |

Training used ESN seed `2026100140` and MLP seed `2026100141`. Every closed-loop row is a development result at `dt=1e-4`, 55 s and 550000 physical substeps. No row passed strict, so formal `dt=5e-5` was not run.

## Results

| delta weight | method | validation weighted action MSE | checkpoint SHA256 | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | external penetration mm |
|---:|---|---:|---|:---:|:---:|---|---:|---:|---:|
| 0.0 | ESN | 9.0916e-5 | `e2e5c4f1cf141e3c2c0943dec14bc077da2a7db9315da1c449dc60c6875f0bd2` | no | no | carry | 137.286 | 46.639 | 0.0962 | 0.1500 |
| 0.0 | MLP | 3.4258e-5 | `315e69ce3296b249e488bb5f69749ed6e169d77411a4bbde60bc548f434e5794` | no | no | load_transfer | 53.349 | 44.491 | 0.0778 | 0.1122 |
| 0.5 | ESN | 6.5165e-5 | `9d9ab4eecda0178859f1aad72c344396a47a0559673c87b54ea8ef40b13e8a23` | no | no | carry | 161.839 | 48.398 | 0.1293 | 0.1424 |
| 0.5 | MLP | 5.3885e-5 | `83fd01808d3a5dbeb9d3a55093fc0c5f782a51303169476d21d75d2778e36216` | yes | no | retreat | 35.511 | 44.256 | 0.0665 | 0.1108 |
| 1.0 | ESN | 7.4083e-5 | `66e6d6785a84e4732312ed1d65838736e95c8be1d0bb9e1af6619e0c97ed2dd7` | no | no | load_transfer | 40.378 | 48.034 | 0.1207 | 0.1321 |
| 1.0 | MLP | 5.6804e-5 | `23f099a41396c5ce9f29d44e5d1945a54643402fbf4adbc0361cfacdef576550` | yes | no | retreat | 43.874 | 44.601 | 0.1114 | 0.0947 |

The strongest ESN row by task progress was `delta_weight=1.0`: it reached `load_transfer` and had RMSE 40.378 mm, but did not complete placement and therefore was not a task or strict success. The `delta_weight=0.5` MLP completed task, but strict remained false because required contact coverage was invalid. No candidate supports an ESN advantage.

## Independent audit and retained evidence

All six rows passed the independent audit. Action replay maximum error was 0 for every row; ESN reservoir replay maximum error was 0; MLP reservoir replay is null because MLP has no reservoir. Each row has 550000 physical substeps and 55 s physical duration, and the three reported physical metrics were recomputed from substep records. Raw rollouts, MJBs, checkpoints, training metadata, and failure reasons remain in:

```text
outputs/esn_mlp_temporal_consistency_20261001_dw0/
outputs/esn_mlp_temporal_consistency_20261001_dw05/
outputs/esn_mlp_temporal_consistency_20261001_dw1/
```

The campaign did not alter the scene, gate, actor inputs, or actuator limits. GitHub and `arm1@192.168.31.70` were unreachable during this round; these large outputs are local only and pending synchronization.
