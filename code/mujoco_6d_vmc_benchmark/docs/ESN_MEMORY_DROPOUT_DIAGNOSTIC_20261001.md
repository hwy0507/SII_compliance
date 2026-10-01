# Memory and sequence-consistent dropout diagnostic

The dropout ESN advances from lift to load_transfer, but still does not place
the object. Both MLP controls complete the task. All five new evaluations fail
unchanged strict success; none unlocks formal dt=5e-5. This is a diagnostic
result from one seed pair, not a generalization or superiority claim.

| setting | method | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | penetration mm |
|---|---|---|---|---|---:|---:|---:|---:|
| reset history every observation | ESN | false | false | align | 25.213 | 34.820 | .076344 | .171339 |
| dropout 0 | ESN | false | false | lift | 48.971 | 43.600 | .116950 | .131457 |
| dropout 0 | MLP | true | false | retreat | 46.908 | 45.907 | .070165 | .151728 |
| dropout .1 | ESN | false | false | load_transfer | 44.666 | 47.458 | .094228 | .122975 |
| dropout .1 | MLP | true | false | retreat | 46.587 | 44.587 | .073259 | .160285 |

Resetting history prevents even grasping in this checkpoint. Its smaller
errors/torques occur on a different task trajectory and are not an improvement.
It also loses ball rebound and has no continuous rod contact. The result does
not establish that all recurrent memory is harmful: resetting changes the
state-feature distribution on which the readout was trained.

Dropout reduces ESN RMSE by 4.305 mm and peak speed by .022722 m/s, but increases
peak torque by 3.858 Nm; task failure remains. MLP still completes placement in
both conditions. Do not select only the favorable ESN metrics or claim that its
better stage or lower replay error proves task success.

## Fixed learning and evaluation protocol

Memory intervention was committed before running at 078446e; dropout at
f4422c9. The two dropout arms use the same nine certified teacher trajectories,
7/2 identity split, seeds 2026100152/153, 160 epochs and 1120 optimization steps
per method. The only new learning parameter is dropout probability 0 versus .1.
One inverted Bernoulli mask on 128 features is held fixed for an entire training
trajectory; new masks are drawn across trajectories/epochs. ESN masks its
standardized reservoir features; MLP masks its first hidden-layer output.
This matches probability, dimensionality and optimization budget, but the
representations have different meanings, so it is not an equivalent structural
intervention. No dropout is used during validation or deployment.

Both retain canonical48D/action7, 128+128 computational units, fixed ESN
reservoir, identical teacher labels and original actor-input contract. Trainable
parameter counts remain ESN23559 versus MLP23687; do not call them exactly
parameter-matched. No contact truth, object state, event time, task stage or
vision/range is an actor input. This is pure learned inference with the same
existing actuator adapter, without a runtime VMC mixture.

Each full evaluation is 55s/550000 physical substeps/dt1e-4 at scene seed2026091751
under MuJoCo3.11.0. Every MJB is the frozen 5eaee4aa model. The local services
used one simulator, one thread and verified cgroup memory.max=3221225472.
Raw failures, execution records, source/config/teacher/checkpoint hashes and
training histories are retained. Independent audits replay actions and ESN
states exactly, recompute three physical metrics, and check finite arrays,
duration, metadata and matched training data/normalization/reservoir.

The dropout0 checkpoint AND raw rollout hashes match the previous frozen
seed52 reference byte-for-byte for both methods, confirming reproducibility.
Export parity passes; the matched reservoir/normalization checks pass.
Validation action MSE alone is not used as a task outcome.

## Budget correction and closeout

The automation was created at 05:48:54.070 UTC; creation plus eight hours is
13:48:54.070. Its scheduled wakeup end was 16:20, which the recent scripts
mistakenly used as a dispatch cutoff. There is no separately pinned authorized
start that establishes this extension. Conservatively, these late diagnostics
must not be reported as occurring inside the original eight-hour window.

Once the conflict was recognized, no additional campaign was dispatched.
The already-started last episode (15:38:42–15:40:30) completed, followed only by
read-only audits and archiving. The heartbeat is PAUSED. AGENTS.md now requires
an explicit budget origin/deadline and prohibits treating the automation
schedule as budget authorization. Historical execution/config files remain
unchanged; BUDGET_RECONCILIATION.json is an explicitly retrospective sidecar.
Further experiments require a fresh budget with a recorded start and deadline.

Completed: memory intervention, two matched dropout arms, all five raw audits,
and reproducibility verification. Running: no simulations. Unfinished: ESN
placement, strict success, multiple-seed/condition validation, and formal steps.
The next hypothesis is history-robust readout learning, not another gate or
environment change; this experiment has not yet validated that solution.

Evidence: docs/evidence/temporal_memory_dropout_20261001/FINAL_AUDIT.json.
Verified archive:
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_memory_dropout_20261001_v1/evidence.tar.gz`
(232570508 bytes; SHA256
`4ed503552bea79609578040aa4cff344a790bf75051313a183764b8e53820bf5`).
It retains all five rollouts, both training arms, execution logs/hashes, audits
and the retrospective budget-correction sidecar.
Registered source snapshots are at
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/078446e00aa5470ad1bb68caaa1932d35d802c00/repository.tar`
and
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f4422c9b56ef97d1889b774c8d843a1526d4905d/repository.tar`;
their verified SHA256 receipts are in UPDATE_LOG.
