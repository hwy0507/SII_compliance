# Temporal ESN/MLP integrity audit — 2026-10-01

The latest six development rollouts are retained negative results: ESN task
0/3, MLP task 3/3, strict 0/3 for each. These three settings include two loss
weights and a replication seed; they are not three independent identically
distributed seeds. No ESN advantage or formal success is established.

| delta / ESN seed | method | RMSE mm | peak torque Nm | peak speed m/s | task | strict |
|---|---|---:|---:|---:|---|---|
| .25 / 2026100150 | ESN | 52.502 | 45.556 | .117007 | false | false |
| .25 / 2026100150 | MLP | 44.193 | 44.268 | .093121 | true | false |
| .75 / 2026100150 | ESN | 74.311 | 43.161 | .108427 | false | false |
| .75 / 2026100150 | MLP | 45.095 | 45.203 | .074644 | true | false |
| .25 / 2026100152 | ESN | 72.223 | 44.403 | .125044 | false | false |
| .25 / 2026100152 | MLP | 46.980 | 45.918 | .070165 | true | false |

## Verified and limited claims

The strengthened audit verifies all six checkpoint hashes against both training
and evaluator metadata, MJB hashes against evaluator metadata, finite actor
inputs/actions/reservoir and physical arrays, 550000 positive 0.0001 s substeps,
three independently recomputed metrics, and exact action/reservoir replay.
Task diagnostics may contain NaN sentinels for events that never happened; they
are not actor inputs. The first all-fields finite check rejected task_carry_load;
the final check explicitly covers actor/state/physical arrays instead.

All six MJB SHA256 values equal
`4433c323e92084716b16b81cb9fd52a931d9f36b4e974e04790f561b402de374`.
The older frozen MJB is
`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`.
Read-only binary loading probes establish that .venv-rl currently uses MuJoCo
3.14.0 and loads the recent model but rejects the older model; .venv-canonical-rl
uses 3.11.0 and does the reverse. This confirms a runtime compatibility break;
it does not isolate its effect on task outcomes or prove physical equivalence.
The latest paired comparison is usable within its model/runtime; comparisons
with the earlier frozen batches must not be described as algorithm-only.

No new simulations were launched during this audit. These read-only audits ran
with systemd MemoryMax=3G and one BLAS/OpenMP thread. The recent historical runs
lack execution.json and evidence of enforced MemoryMax; those missing records
cannot be retrospectively fabricated. Evaluator JSON and TRAINING_COMPLETE.json
retain arguments, source/trace/checkpoint hashes and seed/split information.

## Config repair and next-run requirements

The original seed42 config path was overwritten by seed52 at 434e46f. It is now
restored byte-for-byte from 62f8c65; seed52 has a distinct narrow_rep_seed52 path.
The seed52 bytes and historical training records remain unchanged. Locally
writing a config before training and committing afterward is not precommitted
registration; prior narrow/seed52 wording is corrected here.

Before any further training/evaluation, freeze and record the actual interpreter,
MuJoCo version, model/source/config/checkpoint hashes, command and cgroup limits
in a new execution.json. Use .venv-canonical-rl (MuJoCo 3.11.0) for evaluations
that claim comparability with the original frozen campaign. A same-checkpoint
paired runtime diagnostic, retaining both failures, must precede attributing
cross-batch changes to learning. Do not alter gates or the scene to bridge this
difference. No formal dt=5e-5 evaluation is unlocked.

Only nine certified teacher trajectories exist (7 train / 2 validation);
sustained-push validation coverage remains absent. Repeated hyperparameter
screens cannot establish cross-condition generalization from this evidence.

## Synchronization

Live remote checks read main ba84ed8a39ed743f603aa5d60e901bdf87090e1d and baseline
699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0. The latter reports separate frozen RL
studies and a paused ball-replay investigation; it is not merged or restarted.
Earlier network failures were sandbox-dependent: authorized external Git/SSH
access succeeded this turn. The archive receipt below records verified paths;
historical statements about “only local” describe their earlier check time.

Verified archive:
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_integrity_20261001T1450Z/evidence.tar.gz`
(652346695 bytes; SHA256
`0d30662ae0479b5594f8240eb4f019f7e2f9ee7b76ad974b80b8fdd6216bd460`).
It includes all seven paired temporal run directories (delta0/.5/1, seed42,
narrow .25/.75, seed52), historical and strengthened audit outputs, and both
runtime probes. No original failures were removed.

Pre-correction source snapshot:
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/434e46fbedfc88df11d7ff8c44f2b3d064ebd217/repository.tar`
(65945600 bytes; SHA256
`d23b4c74298ff87b5079002f4e3bb246582f4db6447a97613eab7da1e88479b2`).
Updated audit code and small JSON evidence are versioned in this corrective
commit. Its source snapshot is separately archived on publication.
