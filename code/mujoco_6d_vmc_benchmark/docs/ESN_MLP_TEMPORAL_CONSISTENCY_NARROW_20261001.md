# ESN/MLP temporal consistency narrow follow-up

## Protocol

This development follow-up tested only the training loss coefficient
`delta_weight = 0.25` and `0.75`. The locked teacher manifest, 7/2 identity
split, canonical48D proprioceptive input, action7 output, width 128, and
`office-v5 combined-thick-corner-pillar-v4` scene were unchanged. Both methods
were trained from the same seven train identities and evaluated in the same
55 s development rollout at `dt=1e-4` (550000 physical substeps). The actor
received no contact truth, object or ball state, event time, task stage,
visual, or distance input. The only changed quantity was the weighted
consecutive-action delta term in the training objective.

Configuration SHA256: `4e6fd694756b73fd964f9f1fe1ab6e71eee98f4da165c06f5f79d48851eac886`.
Training source SHA256: `49a3b2bf3ad69889f07f8d8f42326d82cde686d0d3a60cb9e02b79eaf48bb4f5`.
The locked teacher manifest SHA256 remains
`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`.

## Closed-loop results

| delta | method | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | penetration mm | ball rebound | longest rod run s |
|---:|---|:---:|:---:|---|---:|---:|---:|---:|:---:|---:|
| 0.25 | ESN | no | no | retreat | 52.502 | 45.556 | 0.117007 | 0.146245 | yes | 0.7673 |
| 0.25 | MLP | yes | no | retreat | 44.193 | 44.268 | 0.093121 | 0.140633 | yes | 0.1243 |
| 0.75 | ESN | no | no | carry | 74.311 | 43.161 | 0.108427 | 0.136028 | yes | 0.0025 |
| 0.75 | MLP | yes | no | retreat | 45.095 | 45.203 | 0.074644 | 0.099006 | no | 0.0123 |

The `delta=0.25` ESN reached retreat and exhibited the longest continuous rod
contact in this narrow screen, but it did not complete placement. Both MLP
rows completed the task gate, but neither was strict: the `delta=0.25` row
failed required contact coverage, and the `delta=0.75` row additionally failed
ball rebound. No row passed strict, so the formal `dt=5e-5` rerun remains
locked. The result does not support an ESN advantage over MLP.

## Independent audit

The independent audit is
`outputs/esn_mlp_temporal_consistency_narrow_20261001/INDEPENDENT_AUDIT.json`
and its source SHA256 is
`c9639aecdcb26cce9bcfa394e471a1e2c953224456b77ab44dfec5c582e82c3f`.
For all four rows, canonical action replay maximum error and ESN reservoir
state replay maximum error were zero where applicable. The audit independently
recomputed the three physical substep metrics and verified exactly 550000
substeps over 55 s. Raw rollouts, checkpoints, MJB/XML files, evaluator JSON,
and failed rows remain in:

```text
outputs/esn_mlp_temporal_consistency_narrow_20261001_dw025/
outputs/esn_mlp_temporal_consistency_narrow_20261001_dw075/
```

These are development results only; no hardware or formal-step claim is made.

Correction (2026-10-01 integrity audit): no separate execution.json exists in
these directories. The configuration was committed after the runs, not as a
pre-run Git registration. The recent compiled model corresponds to MuJoCo
3.14.0; earlier frozen runs used 3.11.0. Do not pool them as algorithm-only
comparisons. See ESN_MLP_TEMPORAL_INTEGRITY_20261001.md for evidence and archive.
