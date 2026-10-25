# Published baseline learning diagnostics

The first sections preserve the early CHEQ snapshot; later sections record the
first complete condition cycle, numerical migration and contact audit. None is
a convergence claim. The early29000-step snapshot preceded a balanced30-condition
cycle and included approximately10000 recovered transitions per interface.

## Terminal value calibration

The diagnostic reads immutable copies of each atomic checkpoint, resolves the
actor/critic definitions from frozen `source_train04`, and performs no updates.
It separately reports terminal transitions, whose Bellman target is their reward
because the bootstrap mask is zero. This comparison does **not** confuse the
entropy-regularized nonterminal Q value with the ordinary episode return.

| Interface | Snapshot transitions | Terminal transitions | Mean terminal Q absolute error | Mean sampled TD absolute error | Alpha |
|---|---:|---:|---:|---:|---:|
| Direct | 29000 | 9 | 58.3913 | 0.4467 | 0.025961 |
| Impedance | 29000 | 9 | 63.5757 | 0.4039 | 0.017737 |
| Admittance | 29001 | 9 | 76.5813 | 0.4166 | 0.019023 |
| VMC | 29000 | 9 | 92.9193 | 0.4913 | 0.031695 |

Terminal errors average across nine observations and five critics. The sampled
TD diagnostic uses4096 replay rows and critics0/1 for its target; actual training
randomly chooses a critic pair. It is a fixed diagnostic, not the exact minibatch
loss logged during an optimizer update. Terminal rows comprise only about0.03%
of replay at these snapshots. Therefore a small mean replay error can coexist
with badly calibrated failure values.

The training plot also shows critic loss rising when the first complete55s
episodes enter replay. Before that point, low loss describes fitting mostly
nonterminal targets. Current computations are finite, but **critic health and
convergence are not established**. No new reward is selected from this early
snapshot. Later complete cycles must be checked for terminal calibration,
temperature/entropy stability, policy saturation, genuine paired-condition
reward improvement, and independent policy performance.

The diagnostic reconstructs every included ended episode return from logged
transitions and verifies that progress, occupancy, time, contact torque/force,
slew, penetration, peak torque, terminal outcome, failure tail and completion
bonus sum to that return. At this snapshot all nine episodes per method failed:
Direct ended in approach7/align1/grasp1; the parameter methods ended in carry9.
These are trajectories collected with changing training policies, not final
evaluation results or evidence that the task is impossible.

## Evidence and reproducibility

Current server base:
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`.

- Tool: `code/mujoco_6d_vmc_benchmark/tools/diagnose_published_training_20261025.py`.
- Immutable checkpoint copies, full reward decomposition, original diagnostic
  source and plot: `runs/diagnosis_cheq_v3_early01/`.
- Small committed numerical evidence:
  `code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_COMPLIANCE_EARLY_DIAGNOSIS_20261025.json`.
- Figure: `runs/diagnosis_cheq_v3_early01/training_diagnostics.png`.

The tool ran on CPU54 with CUDA hidden and one numerical thread. Four primary
learners and four separate plain-SAC online ablations remain independent of this
analysis. Training source snapshots, replay contents and optimizer states were
not changed by the diagnostic.

## Independent contact-metric audit

The initial episode adapter saved coincident contact/torque integrals per actor
interval, but its original physical substep archive omitted human contact force.
That was insufficient to independently recompute contact-only compliance from
raw saved substeps. `audit_published_episode_20261025.py` adds one recorder call
after the existing reward-telemetry sample, preserving the frozen base adapter.
The recorder writes timestep, seven actuator torques, actual human contact force,
external penetration and simulation time; none of these enter the actor.

The independent evaluator's optional `--audit-substeps` mode records the wrapper
source hash alongside the frozen actor, model and reference hashes.
`summarize_published_episode_audit_20261025.py` recomputes the physical metrics,
checks original substep clock/torque alignment, compares actor/action journals,
and emits a comparison row including failure and no-contact semantics. It
explicitly does **not** claim independent filter replay verification.

A paired transparency check completed as
`runs/interim_direct_deterministic_audited_v2`, using the same21000-step Direct
checkpoint and first passive condition as `interim_direct_deterministic_v1`.
The model, actor journal and terminal record are byte-identical. Physical state,
observations, actions and physical substep torque arrays match exactly. Original
`task_carry_load` has an intentional NaN sentinel outside its applicable gate;
that identical mask was checked separately, with no allowance for nonfinite
state/action/torque. The initial naive comparison that treated equal NaN masks
as inequality is retained as `TRANSPARENCY.json`; the corrected scoped check is
`TRANSPARENCY_VERIFIED.json`, produced by the portable comparison tool.

The independent audit covers1100000 physical substeps/55s. Peak torque is
51.505995Nm, no machine safety violation, Task/Strict false, final stage approach.
Actual human contact duration is0, so the compliance ratio isNA. Actor/action
trace alignment and the original torque/clock archive passed; this still does
not replace an independent filter replay. A second instrumented episode subsequently completed in `runs/interim_impedance_human_audited_v1` on the first registered
active-long person condition, selected before its evaluation result. Its
purpose is checking actual-contact metric coverage, not a final policy ranking.

The audit source was frozen separately in `runtime/evaluation_audit_v2`; training
then used `source_train04`. The current migration uses `source_train05`.

## Joint GPU use and first positive terminal signals

After all four plain-SAC ablations began actual updates, the last60 samples of a
180s monitor window averaged69.48/61.25/63.03/59.57% GPU utilization. The minima
were42/42/40/44%; this demonstrates four-card **mean** utilization above50% for
that window, not an invariant instantaneous utilization. Raw samples include
SAC update counters. These are online physics learners, not dummy GPU load.

Later than the29000-step diagnostic snapshot, the first active-short training
conditions supplied strict successes: Impedance8, Admittance8 and VMC7 at that
check. There were no Direct successes. These are partial-cycle counts from
changing policies; neither a success-rate estimate over the complete cohort nor
proof of improvement. Rewards from different task categories must not be
mistaken for a learning trend. Positive terminal signals are now present and
will be checked in subsequent full-cycle calibration.

Small evidence for utilization, transparency and physical metric reconstruction:
`code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_COMPLIANCE_AUDIT_20261025.json`.

## First full cycle and numerical health

The old CHEQ v3 completed one balanced30-condition cycle before migration.
Exact cycle checkpoints and SHA receipts are in `runs/cheq_cycle_archive_v1`;
`FIRST_CYCLE_SUMMARY.json` retains all30 results per interface. These are online
training episodes with changing policies, not a frozen-policy success rate.

| Interface | Passive strict | Active-short strict | Active-long strict | Task total | Strict total | Mean return |
|---|---:|---:|---:|---:|---:|---:|
| Direct |0/10|0/10|0/10|0/30|0/30|-33.960537|
| Impedance |0/10|10/10|8/10|18/30|18/30|-0.463638|
| Admittance |0/10|9/10|3/10|12/30|12/30|-12.051560|
| VMC |0/10|9/10|7/10|17/30|16/30|-4.572615|

At these exact checkpoints, terminal Q mean absolute errors were
108.377/31.061/49.421/58.528, respectively, over30 terminal observations and5
critics per interface. Direct was deteriorating. In the separate old SAC Direct
run, critic loss reached roughly6e7 and alpha roughly109–120; it was stopped
with23242 transitions and a saved checkpoint. Finite arithmetic did not imply
healthy learning. Files `NUMERICAL_STOP_REQUEST.json` and later migration-stop
receipts distinguish these decisions from autonomous training completion.

The checkpoint saturation audit found SAC Direct's largest absolute mean about
22.96, but only0.000279 of sampled tanh outputs exactly saturated; examined CHEQ
Direct outputs had no exact saturation. Therefore saturation is not established
as the general cause of divergence.

A controlled fresh-SAC offline study used one immutable22000-transition real
Direct replay, seed2026102507 and3000 updates per variant. All other core
hyperparameters matched (gamma.9995, LR3e-4, initial alpha1).

| Variant | Batch | Critic LayerNorm | Final terminal Q MAE |
|---|---:|---|---:|
| Original numerical implementation |16384|off|41.56265|
| Amended numerics |256|off|52.51827|
| Amended numerics |256|on|50.62701|
| Amended numerics |16384|off|41.66969|
| Amended numerics |16384|on|5.20190|

Actual CHEQ49-D replay from the first Direct cycle confirmed the direction:
with amended numerics/batch16384/3000 updates, terminal Q MAE was56.22633 without
critic LayerNorm and27.49647 with it. These finite fitting studies justify
trying the authors' existing option; they do not establish closed-loop success
or a universally superior hyperparameter. A broader4-interface×2-seed paired
replication is now registered separately, with no policy weights fed into the
online learners.

The first offline-probe launch failed before updates because optional Gym/OpenCV
imports changed resolution of `utils`. Pinning the published source after
importing Spaces fixed module resolution; no display library/driver was changed.
Three numerical regression tests passed: stable Jacobian equals the exact
unsaturated density, preserves finite ±2 gradients at inputs ±20, and column
actor Q preserves the original broadcast-mean scalar/gradients. The author's
original files are unchanged and hash-verified; amendment hashes are recorded.

## Actual contact comparison with fixed nominal impedance

The early42000-step CHEQ Impedance and zero-parameter fixed Impedance were run
on the identical registered `active_long_train_0000` model and nominal plan.
Both completed all55s and passed Task/Strict. Independently recomputed metrics:

| Policy | Stable-placement completion | Peak torque | Actual human contact | All joints below engineering thresholds during contact |
|---|---:|---:|---:|---:|
| Early CHEQ Impedance |20.480s|51.571922Nm|7.750350s|0.422450s / 5.450722%|
| Fixed nominal Impedance |20.520s|52.256104Nm|7.769200s|1.870350s / 24.073907%|

Both had no recorded machine safety violation. The thresholds were43.5Nm for
joints1–4 and6Nm for joints5–7; human contact required summed force>0.05N.
They are engineering references, not validated human comfort limits. Raw torque,
clock, human force and contact denominators were checked over1100000 substeps
per run. Independent filter replay is still outstanding and explicitly false
in these audit receipts.

This one case shows that success cannot yet be attributed to learning, and that
the early RL policy had worse contact-only threshold compliance despite slightly
faster completion/lower peak. It is neither a final ranking nor the final SPT
reference. The first-cycle stochastic training episode on this condition had
success bonus25 and completion bonus3.1745, versus contact torque penalty about
-0.0641 and contact-force penalty-0.0871. The reward proxy does not directly
optimize the final contact compliance fraction. This mismatch remains a design
diagnostic; no reward was changed during the numerical migration.

Evidence directories (under the server base above):

- `runs/diagnosis_cheq_v3_cycle00/`, `runs/numerical_stability_audit01/`.
- `runs/numerical_stability_probe_v2/`, `runs/cheq_numerical_stability_probe_v1/`.
- `runs/interim_impedance_human_audited_v1/PHYSICAL_AUDIT.json`.
- `runs/NOMINAL_IMPEDANCE_HUMAN_PHYSICAL_AUDIT.json`.
- `runtime/source_train05/PHYSICS_SOURCE_EQUIVALENCE.json` and
  `LEARNER_RESTART_VALIDATION.json`.
- Small committed evidence: `PUBLISHED_COMPLIANCE_LAYERNORM_20261025.json` in
  `code/mujoco_6d_vmc_benchmark/docs/evidence/`.

Still required: adequate paired-cycle improvement and stability, healthy terminal
values/entropy, frozen-policy common-condition evaluation, full filter audit,
final shared SPT_empirical reference, and the designated ESN checkpoint. Early
successes, offline fitting, finite losses and low GPU idle time cannot replace
these requirements.

## Early migrated learners and GPU observation

An immutable early snapshot of the new LayerNorm CHEQ stage is in
`runs/diagnosis_cheq_layernorm_early01`. At89194/90515/90570/91276 total retained
transitions, terminal Q MAE was20.77/17.86/22.37/31.70 and alpha was
0.00418/0.01107/0.01003/0.01268. Each snapshot had48 terminal rows inherited from
the prior data. These are different data/training ages from the old first-cycle
snapshot; this is not a paired claim of online improvement. The upper error tail
remains large, and the new stage had not completed a full condition cycle.

With the finite auxiliary probes active, another60s monitor window measured
GPU means67.67/58.35/60.52/58.05% and minima49/28/16/30%. All four means exceeded
50% in that window. These measurements include auxiliary fitting, so they do
not describe online training alone or guarantee future/instantaneous load.
Raw samples: `runs/LAYERNORM_WITH_PROBES_GPU_60S_01.json`.

An extended observational wrapper records the actual public-filter inputs,
configuration, initial state and returned outputs/flags without replacing its
numerical implementation. `replay_published_filter_audit_20261025.py` independently
replays that saved sequence from frozen source and checks linkage to the actor
journal and physical trace. Three tests pass: transparent stateful recording,
rejection of a1e-12 filtered-command change, and rejection of journal mismatch.
A full55s paired transparency evaluation is running as
`runs/interim_impedance_filter_audited_v1`, using the identical42000-step
Impedance snapshot and active-long condition. Its code is independently frozen
in `runtime/evaluation_audit_v3`; it does not mutate a training runtime.
Completion and exact trajectory comparison remain to be checked. Even a passing
public-filter replay does not imply native torque-controller or actuator-layer
replay, which are distinct scopes.

The broader LayerNorm replication has now completed all16 finite probes without
failures (2 seeds ×4 interfaces ×2 configurations,3000 updates each). Paired
terminal Q MAE (without → with LayerNorm) was:

| Interface | Seed2026102508 | Seed2026102509 |
|---|---:|---:|
| Direct |56.076 →28.452|56.165 →30.488|
| Impedance |25.064 →19.231|24.912 →16.840|
| Admittance |45.939 →26.756|46.118 →22.627|
| VMC |39.691 →31.322|39.773 →32.147|

Every paired terminal-error comparison improved, but substantial errors remain.
These are offline fitting results from first-cycle replay, with no new physics
or downstream policy evaluation. The auxiliary processes have ended; their GPU
utilization measurement must not be presented as a permanent running load.
Full table and receipt hashes: `runs/cheq_layernorm_robustness_probe_v1/SUMMARY.json`.

## Filter transparency completed; performance continuation registered

The first extended-filter run used CPU inference accidentally, whereas the
original42000-step evaluation used `cuda:1`. Its first actor action already
showed floating-point differences and the full transparency comparison failed;
that failure is preserved in `interim_impedance_filter_audited_v1`. The evaluator
now explicitly records the inference device. Rerunning with the original
`cuda:1` in `interim_impedance_filter_audited_v2` passed all comparisons:
checkpoint/model/journal/terminal files match, all physical arrays match exactly,
and the double-precision human-contact/torque audit substep file hash matches.
The1,375 public-filter decisions replay exactly, including input linkage and
saturation/slew flags. No tolerance was relaxed. This is one Impedance case;
its native torque-controller and downstream actuator layer were not replayed,
and the other final policies still require their own audits.

Pure online training after auxiliary probes finished measured another60s GPU
mean51.83/40.78/44.20/41.33%, so the all-card50% target is still unresolved.
Profiling identified a performance opportunity: batching the finite-check flags
into one host transfer retains every parameter/gradient check. Across1,000
paired real-replay updates per interface, final network hashes and log-alpha
were exactly equal. Observed ordered/shared-GPU speedups were1.89/1.68/1.70/1.69
for Direct/Impedance/Admittance/VMC; these are not isolated throughput benchmarks.
The first profiling launch failed before updates because `profile.py` shadowed
Python's standard-library module during Torch import; v2 uses an unambiguous name.

`runtime/source_train06` freezes this performance-only change. Four tests cover
finite checks, invalid parameters/gradients, rejection of reward/physics drift,
and unregistered parents. Both actual continuation registrations passed
scientific-contract and protected-source checks. The new trainer permits an
explicitly registered parent only when all scientific settings and protected
sources match. It records parent/checkpoint hashes and restores optimizers,
replay masks/RNG, temperature, target critics, cycle history and learner RNG.

Two coordinators are draining complete cycles in the current CHEQ and SAC runs,
then will resume each controller in `runs/cheq_performance_seed20261025_v1` and
`runs/sac_performance_seed20261025_v1`. Parent checkpoints are copied immutably;
CPU/GPU/worker allocations remain identical. `MIGRATION_PROGRESS.json` currently
has no launched replacements: this is a registered pending continuation, not a
claim of completed migration or higher production utilization. Inspect these
coordinators and their failures before launching anything again. Full-cycle
checkpoint archivers are created after all replacement learners actually update.

A separate read-only nearest-input check on the early saved replay found no
exact terminal/nonterminal observation-action duplicates. It therefore does not
establish irreducible observation aliasing as the cause of the remaining value
error; no actor or critic information fields were changed on this hypothesis.
Evidence stays in `runs/terminal_input_neighborhood_audit_v1`.
