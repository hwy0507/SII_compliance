# Published baseline learning diagnostics

The first sections preserve the early CHEQ snapshot; later sections record the
first complete condition cycle, numerical migration and contact audit.
The latest complete-cycle/mask-stratified and parameter-action findings are at the end. None is
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


## Complete LayerNorm cycle and bootstrap-mask correction

All four CHEQ LayerNorm learners finished cycle0 normally, each collecting41,250
new transitions (30 full55s episodes), in addition to imported replay. Mean
returns were -33.51545828 / -.55531106 / -12.11115782 / -4.58189673, with strict
success counts0/18/12/16, in Direct/Impedance/Admittance/VMC order. These are
changing-policy training trajectories. The unchanged success counts versus the
previous stage do not demonstrate learning improvement; network resets also
prevent treating cross-stage curves as uninterrupted convergence evidence.

An important diagnostic correction: CHEQ's fixed Bernoulli masks deliberately
exclude some transition/critic pairs from that critic's training loss. Earlier
terminal MAE pooled fitted and deliberately withheld predictions. That remains
a valid ensemble prediction error, but must not be described entirely as
training fit error. The new diagnostic preserves the pooled statistic and adds:

| Interface | Pooled terminal MAE | In-bag MAE (pairs) | Out-of-bag MAE (pairs) | Alpha |
|---|---:|---:|---:|---:|
| Direct |63.173968|19.598477 (315)|246.191030 (75)|.044302|
| Impedance |46.079629|30.806066 (322)|118.404441 (68)|.060335|
| Admittance |73.277604|49.906551 (324)|188.008229 (66)|.023673|
| VMC |185.050815|102.134920 (311)|511.466558 (79)|.142326|

Each snapshot has78 terminal rows and5 critics (390 pairs). In-bag errors remain
substantial. Out-of-bag means internal bootstrap withholding, **not unseen task
conditions**. Critic loss rises after its earlier decline; finite arithmetic
alone does not establish healthy optimization. Historical LayerNorm robustness
probe errors also pooled both mask groups; their improvement is an ensemble
prediction result, not a pure fitted-row calibration claim.

Terminal sample error is also not a stand-alone convergence threshold. The fixed
canonical observation does not explicitly contain remaining episode time, while
horizon endings remove bootstrap. Similar physical observations can therefore
have different time-dependent targets. The previous nearest-input search found
no exact duplicates; that neither establishes nor rules out approximate state
aliasing under the fixed inputs. Requiring every terminal prediction to equal
its sampled reward, or resetting a learner on this metric alone, is unjustified.
Assess repeated-cycle learning, finite/stable optimization and independent
policy outcomes together. No time/privileged field has been added to the actor
or critic, and no further learner reset is selected from this diagnostic.

Immutable snapshots, plot, full reward decomposition and corrected diagnostics:
`runs/diagnosis_cheq_layernorm_cycle00_masked/`. The original unstratified
`runs/diagnosis_cheq_layernorm_cycle00/` remains preserved.

## Finite fixed-label terminal fitting study

`runs/terminal_fitting_probe_v1` completed4 interfaces ×2 sampling variants,
5,000 critic-only updates per variant, batch16,384. Each variant restored the
same checkpoint and optimizer. Labels were computed once from frozen target
critics0/1 and one sampled next action per real replay row; terminal labels are
exactly unbootstrapped rewards. Actor, target networks and temperature remained
bit-identical, checked at each variant end. Original replay masks were retained.

| Interface | Terminal MAE: uniform → terminal10% | Ordinary fixed-label MAE: uniform → terminal10% |
|---|---:|---:|
| Direct |54.431763 →48.330021|.930202 →1.021440|
| Impedance |46.758320 →22.326107|1.329092 →1.505661|
| Admittance |67.700394 →34.211300|.976086 →1.601816|
| VMC |171.769775 →111.143280|3.003430 →3.915981|

This is evidence that weighting matters for these fixed labels; it is not proof
that oversampling improves online policy learning. Ordinary error increases,
and substantial terminal error remains. v1 reports pooled errors only: the mask
correction was discovered after its immutable source was launched. It saved no
final critic weights, so no mask-specific endpoint is claimed retrospectively.
Formal sampling, rewards and policies have not changed on this result.

A bounded replication is now running in `runs/terminal_fitting_replication_v2`:
two new seeds2026102511/2026102512, the same four checkpoints, two variants and
5,000 updates each. It checks robustness to minibatch/next-action label sampling,
adds mask-specific statistics, and saves auxiliary critic weights for analysis.
It shares the four GPUs and CPU54; its weights are explicitly excluded from
formal policy continuation. Completion/results must be checked in individual
FINISHED/FAILURE receipts. These are useful finite auxiliary jobs, not an
unbounded GPU occupancy loop or final baseline training.

## Parameter action effect and exact shield replay

`audit_published_parameter_cycle_20261025.py` independently replays saved virtual
storage inputs through the frozen parameter shield for all90 completed parameter
policy episodes. It checks exact journal/NPZ/trace action linkage, registered
bounds/log-rate and source hashes. All123,750 updates match with max error0.

| Interface | Updates | Rate-limited rows | Energy-limited rows | Non-nominal parameter rows |
|---|---:|---:|---:|---:|
| Impedance |41,250|22,222 (53.87%)|0|41,250|
| Admittance |41,250|28,969 (70.23%)|0|41,250|
| VMC |41,250|21,994 (53.32%)|0|41,250|

Mean absolute applied log-parameter ratios relative to the nominal center are
roughly .09–.11 by dimension. Changes are real; weak task improvement cannot
be explained by the energy tank suppressing every action in this dataset.
Impedance emits zero action7 intentionally while modifying its native Cartesian
torque-law gains; zero action7 does not mean its RL parameters are ignored.
Admittance/VMC emitted nonzero action7 on37,532/40,170 updates respectively.
The result does not establish that larger changes would help, justify relaxing
limits, reconstruct physical storage states, or prove global passivity.
Evidence: `runs/parameter_cycle_audit_v1/results/AUDIT.json`.

## Continuation and fixed-controller matrix status

CHEQ performance migration has completed with four genuinely updating replacements
in `runs/cheq_performance_seed20261025_v1` / `runtime/source_train06`. It preserved
network/optimizer/targets/alpha/RNG/replay including masks and complete cycle
history. Parent total steps were120444/121765/121820/122526, all at82,500 updates.
This is exact learner continuation at a complete-cycle boundary; the earlier
LayerNorm restart was not. Its cycle archiver is now active inside this run.
SAC remains in `sac_layernorm_seed20261025_v2`, draining cycle0 before its already
registered coordinator replaces each method. Do not launch duplicate learners.

`runs/nominal_four_interfaces_cohort30_v1` uses CPU52/53 for120 fixed-controller
cases (4 existing interfaces ×the same30 conditions). Zero normalized actions,
physical/source hashes, raw contact audit, public-filter replay and reward
reconstruction are checked per episode. Six cases had completed at this report
snapshot; the matrix is ongoing. All four methods fail the first passive case
at carry. On the first active-short case, fixed Direct and Impedance succeed
at24.52s/12.96s, peaks47.0487/45.3060Nm, with no human contact (ratio NA).
These partial results cannot define the final SPT reference or establish a
ranking, but reinforce that successful RL trajectories alone do not prove a
learning benefit. All task failures remain included.

The60s GPU window with v1 terminal probes measured means57.67/57.10/59.12/60.47%
and minima34/23/40/6%. A pure-online window after CHEQ migration but before these
probes measured48.22/39.35/35.90/39.67%. All-card mean50% was achieved with
auxiliary fitting in the measured window, not guaranteed for online training
alone or every instant. Raw measurements remain in the two corresponding
PERFORMANCE_*_GPU_60S_01.json files under `runs/`.

Small numerical evidence and source receipts are committed as
`code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_COMPLIANCE_CYCLE_MASK_AUDIT_20261025.json`.
No sufficient convergence, full fixed-policy comparison, final shared empirical
SPT reference or designated-ESN comparison is claimed.

Validation in this revision: all90 completed parameter episodes replayed with
zero error; a separately altered applied-parameter record was rejected. For
all four critics' reports, mask counts and weighted errors reconstruct the
original pooled390-pair statistic to1e-10. Four analysis/runner scripts parse,
and repository whitespace checks pass. Existing frozen physics runs and their
source snapshots were not edited by these checks.

A subsequent60s window during v2 replication measured54.30/55.47/57.35/49.10%
(mean), with minima16/33/21/21%. Thus even auxiliary-inclusive all-card50% is
not a persistent guarantee; GPU3 fell slightly below the requested average.
Evidence: `runs/PERFORMANCE_WITH_TERMINAL_REPLICATION_GPU_60S_01.json`.


## First additional fitting seed and queued torque projection audit

The four seed2026102511 jobs in `runs/terminal_fitting_replication_v2` have
completed, each with5,000 updates per variant. Seed2026102512 remains in flight.
The completed seed separates fitted and deliberately withheld critic-row pairs:

| Interface | In-bag terminal MAE: uniform → terminal10% | Out-of-bag terminal MAE: uniform → terminal10% | Ordinary MAE: uniform → terminal10% |
|---|---:|---:|---:|
| Direct |14.983403 →.288443|245.885208 →245.988007|.908590 →.969696|
| Impedance |34.059044 →3.451669|119.043900 →119.539452|1.313104 →1.534171|
| Admittance |43.703320 →2.576228|187.940735 →187.761276|.930885 →1.455883|
| VMC |97.979637 →8.315726|514.435852 →513.732239|2.983827 →3.834315|

Thus weighting changes fitted terminal predictions substantially, while held-out
predictions remain far from their sampled terminal rewards. Both the mask
interpretation and the finite-horizon/partial-observation caveat above still
apply. Ordinary error also increases. This does not show policy improvement or
justify modifying formal replay or resetting the online learners. Actor,
targets and alpha remained exact; auxiliary critic weights and receipt hashes
are archived. Small evidence:
`code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_TERMINAL_FITTING_MASKED_SEED11_20261025.json`.

The extended `audit_published_episode_20261025.py` now records the common velocity-servo
torque projection inputs/outputs. It binds before parameter controllers capture
the projection, so native impedance's generated equivalent command is observed
at the same shared safety boundary. It records original actuator limits and
checks that they do not change. The projection's returned object is passed
through unchanged. No training runtime or earlier audit snapshot is edited.

`replay_published_torque_audit_20261025.py` replays that frozen projection,
checks previous-output recurrence, amplitude/slew limits and per-call limits,
and links each output to the80 physical substeps in its4ms servo interval.
This is **not** reconstruction of native Cartesian reference, wrench, Jacobian
or posture/friction generation. A successful result will close the downstream
torque-projection scope only, not all native-controller implementation auditing.

Nine focused filter/torque tests pass, including exact observational outputs
and rejection of1e-12 output/previous-torque/physical-torque changes, clock
misalignment and changed actuator limits. Initial testing caught NumPy arrays
inside dataclass configuration comparison; this was fixed before any physical
launch. No production training process was affected.

The full55s transparency check is queued as
`runs/interim_impedance_torque_audited_v2`, using frozen `runtime/evaluation_audit_v6`.
It uses the exact42000-step Impedance checkpoint, original `source_train04`,
registered active-long case and `cuda:1` from the already passing public-filter
transparency pair. The coordinator waits for the four finite replication
process identities to exit successfully before taking CPU54. It then checks
full trajectory and contact-file equality, independent filter replay, torque
replay and physical metrics. Formal training keeps52 cores and the nominal
matrix keeps52/53. **No full-episode torque transparency result exists yet.**

The first queue registration (`interim_impedance_torque_audited_v1`, wrapperv5)
was cancelled while waiting, with no evaluation child or physical steps, to add
explicit immutable actuator-limit equality. Its source/registration and
CANCELLED_BEFORE_PHYSICS receipt are preserved. Only v2 is pending; it must not
be duplicated. `run_published_torque_transparency_20261025.py` records original
process start ticks, prerequisite completion, launch/failure and final receipts.

A read-only monitor in `runs/diagnosis_cycle01_dispatch_v1` is also waiting on
the four live CHEQ learner identities and their exact cycle1 archive files.
It will run the frozen masked diagnostic on CPU54 and retain matched-condition
cycle0/1 training-return changes. Output is
`runs/diagnosis_cheq_performance_cycle01`; until FINISHED exists this is pending,
not a second complete-cycle result. Analysis can temporarily share CPU54 with
the bounded auxiliary jobs; it creates no simulation or learner updates.


## Second full condition cycle, replication completion and actuator evidence

The four exact cycle1 checkpoints were archived without misses. Each interface
collected another41,250 real transitions and completed165,000 optimizer updates
since the LayerNorm restart. The retained transition totals below include
imported data. The performance migration preserved the full learner state.

| Interface | Retained transitions | Cycle0 return | Cycle1 return | Strict cycle0 → cycle1 |
|---|---:|---:|---:|---:|
| Direct |161694|-33.515458|-33.068692|0/30 →0/30|
| Impedance |163015|-.555311|-2.241907|18/30 →17/30|
| Admittance |163070|-12.111158|-10.476058|12/30 →13/30|
| VMC |163776|-4.581897|-4.648096|16/30 →16/30|

These are same-condition changing-policy trajectories, not paired frozen-policy
acceptance. They show mixed changes, not a consistent learning benefit. Direct
now fails at carry17/grasp5/lift8, with no approach-stage failures in this cycle;
that change is useful diagnostic information but still not task completion.

| Interface | In-bag terminal MAE | Out-of-bag terminal MAE | Alpha | Last1000-update mean critic loss |
|---|---:|---:|---:|---:|
| Direct |73.5462|902.2080|.140087|210.864|
| Impedance |487.2361|1714.3437|.508256|2996.435|
| Admittance |403.3215|942.0583|.181348|3744.422|
| VMC |1172.2398|3660.0721|1.074443|20072.472|

Each snapshot has108 terminal rows (not the previous78), so terminal error
changes are not a fixed-dataset paired test. The temporal plot nevertheless
shows substantial critic loss/value drift within this cycle. The mask and
partial-observation caveats still apply; finite arithmetic or nearly target
entropy cannot establish healthy convergence. The live learners continue with
unchanged reward/sampling settings. Evidence and inspected figure:
`runs/diagnosis_cheq_performance_cycle01/`; matched-condition changes:
`runs/diagnosis_cycle01_dispatch_v1/PAIRED_CYCLES.json`.

Both additional fitting seeds have now finished all4×2 variants successfully.
The second seed2026102512 reproduces the first seed's direction:

| Interface | In-bag MAE: uniform → terminal10% | Out-of-bag MAE: uniform → terminal10% | Ordinary MAE: uniform → terminal10% |
|---|---:|---:|---:|
| Direct |9.564847 →1.038683|245.844543 →245.891830|.912737 →.992618|
| Impedance |32.420273 →1.519159|118.788765 →119.127586|1.254683 →1.493922|
| Admittance |42.537090 →2.613943|187.976990 →189.029999|.949631 →1.544698|
| VMC |96.667976 →6.033612|515.230713 →514.104736|3.029513 →3.924508|

All actor/target/temperature invariants passed. Full summary and source/weight
receipts are in `runs/terminal_fitting_replication_v2/SUMMARY.json`. These jobs
have ended. No further terminal-oversampling replication is currently queued;
no formal replay distribution was changed from these offline results.

The full55s audit in `runs/interim_impedance_torque_audited_v2` also finished.
Original checkpoint/model/actor journal/physical trajectories and the raw contact
archive match exactly. All1,375 public-filter calls replay exactly;13,750 common
torque-projection calls match with max error0 and exact previous-output recurrence.
Their output equals the actual actuator torques in all1,100,000 physical
substeps. Maximum servo/substep clock mismatch is1.35e-13s (clock-only tolerance
1e-9s); torque equality is exact. Original limits, amplitude and slew checks pass.
The recorded projection scale stayed1 in this case, so active amplitude scaling
is covered by the focused synthetic test, not claimed as exercised here.
This closes the shared downstream projection scope for this one early case;
native reference/wrench/Jacobian/posture construction remains outside the replay.
It is not final acceptance of current trained policies. CPU54 has been released.

## Batch-size sensitivity registered after cycle1

The pinned author's `config/training/training.yaml` specifies batch[1,256];
`config/rl/ensemble_sac.yaml` specifies LR3e-4, gamma.99, five256×256 critics,
LayerNorm off and pink action noise. The current adapter explicitly differs:
batch16384, two updates per new transition, gamma.9995, registered critic
LayerNorm and white action noise. These are adaptations, not only a new reward.
The official asynchronous trainer schedules updates from episode-length
notifications, so its `[1,256]` setting alone is not a measured effective
wall-clock UTD. This report does not claim an exact measured128× upstream
training budget from multiplying batch and nominal UTD.

Given continued critic drift, `runs/batch_sensitivity_cycle01_v1` freezes the
four complete cycle1 checkpoints and compares batch256/16384 with2,000 full
learner updates per variant. Each variant restores the same network, optimizer,
target, alpha and RNG states; replay and masks remain fixed. This includes
moving Bellman targets and actor/temperature updates, unlike the earlier
critic-only fixed-label probe. Batch order is counterbalanced across interfaces;
wall timing under shared GPUs is not an isolated performance benchmark.
The four finite jobs share CPU54 and GPUs after the previous probes/audit ended.

This is equal-update sensitivity with unequal sampled-row budgets, no new
physical transitions and no online UTD comparison. Auxiliary learner states
cannot enter the formal comparison. Results are pending; the experiment does
not preselect a new formal batch size, reward, architecture or restart.
Tool: `probe_published_batch_sensitivity_20261025.py`.

The post-replication GPU window (online jobs plus the GPU1 deterministic audit)
measured22.80/25.18/15.93/14.82% while primary cycles drained to1–3 samplers.
This misses the requested50% target and does not describe full9-sampler operation.
Raw samples: `runs/ONLINE_AND_TORQUE_AUDIT_GPU_60S_01.json`.
Small combined evidence:
`code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_COMPLIANCE_CYCLE01_TORQUE_AUDIT_20261025.json`.

A later60s window after full sampling concurrency resumed, with the finite
batch probes active, measured50.20/50.03/50.92/55.85% (minima10/16/20/33%).
This meets the average target in that auxiliary-inclusive window only.
Raw samples: `runs/ONLINE_WITH_BATCH_PROBE_GPU_60S_01.json`.
SAC Direct's completed LayerNorm cycle0 had0/30 strict successes and mean
return-34.439232; it resumed from64,492 retained transitions and82,500 updates.
The other SAC interfaces are still completing their parent cycle at this snapshot.


## Completed batch sensitivity and started frozen-policy subset

All eight2,000-update variants completed without nonfinite failures, restored
initial diagnostic values exactly, and retained separate auxiliary states.
In-bag terminal MAE after batch256 / batch16384 was:

| Interface | Batch256 | Batch16384 |
|---|---:|---:|
| Direct |647.4896|68.2311|
| Impedance |1668.2537|457.5714|
| Admittance |880.7542|438.4452|
| VMC |3590.1152|1245.8142|

This short switch from a checkpoint already trained with a large batch does not
support reducing the live batch as a demonstrated fix. It does not establish
that256 is generally inferior, validate16384 as optimal, or reproduce fresh
upstream training. Equal2,000 optimizer updates sample64 times as many rows in
the16384 arm; ordinary replay Q/alpha also keep changing. Formal protocol stays
unchanged. Full results: `runs/batch_sensitivity_cycle01_v1/SUMMARY.json`;
small evidence: `PUBLISHED_BATCH_SENSITIVITY_CYCLE01_20261025.json` under the
benchmark evidence directory. These finite auxiliary processes have ended.

After their actual exit, `run_interim_published_matrix_20261025.py` started
`runs/interim_cheq_cycle01_representatives_v1` on CPU54. It freezes all four
exact cycle1 checkpoints and selects the lexicographically first registered
condition in each of passive_corner, active_short and active_long (all0000),
with the same selection for every interface. Each method uses its original
GPU for deterministic inference, with no updates. Twelve corresponding nominal
rows are copied immutably before the evaluation; all task failures are retained.

Each completed method's three episodes are independently checked for physical
metrics, public-filter replay and common torque projection/actual-actuator
linkage using frozen wrapperv6. The matrix reports learned and nominal rows
side by side, with no final SPT reference. This is an interim fixed-policy
check to distinguish actual learned behavior from changing-policy training
returns, not a full30-condition comparison or convergence proof. The first
Direct physical episode is running; no completed interim matrix is claimed.
Formal52-core training and the nominal matrix on52/53 continue independently.

After all batch probes ended, another60s window with online training and the
single GPU0 deterministic evaluation measured42.67/36.47/37.93/39.87%
(minima9/25/0/0%). The all-card50% target remains unmet without auxiliary fitting.
Initial/final sampler counts and raw samples are saved in
`runs/POST_PROBE_ONLINE_GPU_60S_01.json`; earlier auxiliary-inclusive measurements
must not be reported as the current online utilization.


## Read-only soft targets and actual CHEQ mixing

`runs/soft_target_mixing_cycle01_v1` completed all eight frozen snapshots (four
interfaces, complete cycles0/1), with zero optimizer updates or physics. Each
snapshot samples4096 nonterminal replay rows and includes all terminal rows.
All ten distinct critic pairs are averaged, matching the expectation of the
uniform pair selection. Network state remains exactly unchanged. Scalar checks
cover pair averaging, negative entropy sign, terminal masks and shape rejection.

At cycle1 the nonterminal mean target components were:

| Interface | Immediate reward | Discounted entropy contribution | Discounted target Q | Implied next mixing weight at0.2 |
|---|---:|---:|---:|---:|
| Direct |−0.004510|−0.999336|817.086768|100%|
| Impedance |−0.002890|−2.576078|1766.578687|100%|
| Admittance |−0.003790|−1.286649|715.970513|99.9756%|
| VMC |−0.003593|−7.373715|2467.243329|100%|

The entropy term is negative here. Large positive Q is not explained by a
positive entropy bonus in these samples. The target is dominated by predicted
future value. Policy-vs-replay action pair-minimum Q gaps average4.6955/8.0406/
9.0690/16.8825. These are predictions from the same critic, not measured action
advantages or proof of the cause of value drift. Terminal bootstrapping is
exactly zero. Different cycles contain different replay ages; this is not a
controlled experiment changing the discount or uncertainty threshold.

CHEQ retains the published absolute uncertainty bounds0.02/0.2. At these
snapshots ensemble disagreement almost always maps to the minimum RL authority
0.2. A separate captured last1000 online transitions per method likewise all
record context0.2. This confirms actual recent behavior, whereas the snapshot's
implied weights use sampled current-policy actions on historical replay states.
The deployed CHEQ action is therefore recently20% raw RL plus80% nominal action;
plain SAC is a separate unmixed control. No threshold has been changed. The
reward-scale sensitivity of these absolute thresholds now needs explicit
calibration evidence before another scientific adaptation. It is not sufficient
to label the near-minimum mixed policies as trained standalone RL controllers.

The full report, sample-index hashes and captured online contexts are under the
run above; committed evidence is `PUBLISHED_SOFT_TARGET_MIXING_20261025.json`.
The finite read-only job initially starved at nice19 on physics CPU54. A renice
request was denied and is recorded as unapplied; it completed at nice19 by
sharing idle time on SAC learner CPU10, with no formal affinity changed.

## CPU launch overhead and finite-check validation

A66.50s process sample measured primary learner CPU use98.92–99.50% of one core,
with GPU means42.13/47.35/37.87/39.71%. Existing SAC, nominal and interim jobs
were active; the read-only diagnosis could also perform brief inference.
`/proc` wait-channel values do not establish pipe-blocking time. This window
still misses all-card50% and is distinct from prior auxiliary-training windows.

`runs/learner_profile_cycle01_v1` completed64 finite auxiliary updates using a
copied VMC cycle1 state. Weights were discarded. In the32-update cProfile
segment, total time was1.839s; finite checks accounted for0.513s cumulative
(27.9%) and replay sampling0.268s (14.6%). A separate16-update Torch profile
recorded28,328 CUDA kernel launches and3,456 isfinite calls. Nested cumulative
times and CUDA annotation ranges overlap; summing them is not GPU utilization.
The low-priority shared-load profile identifies overhead, not an online speedup.
Small evidence: `PUBLISHED_LEARNER_PROFILE_20261025.json`.

The candidate finite check concatenates all parameters and existing gradients
by device/dtype, checks every element, and preserves the original first-failing
parameter name through a fallback. It does not omit target-critic gradients,
reduce check frequency, cast mixed dtypes or change the update. Five focused
tests pass, including NaN/Inf gradients, noncontiguous/mixed-dtype parameters,
values beyond float32 range, and rejection of reward/physics/protocol drift.

The first paired validator correctly rejected complete-state equality even
though network values and gradients matched: repeated optimizer loading had
aliased CPU step counters in the in-memory parent. Its failure remains in
`runs/concatenated_finite_check_validation_v1`. The corrected v2 deep-copies
each restore and verifies the original parent state remains unchanged. This is
a diagnostic harness defect; live continuation loads its parent once and was
not reset or changed by either validation arm.

The same missing defensive deepcopy was present in the earlier terminal-fitting
and batch-sensitivity auxiliary tools. Their source is corrected for future
runs, but old immutable runtimes/results are preserved. Withdraw the blanket
claim that every optimizer field was restored exactly between those old arms:
CPU step counters can carry over. Their measured outputs remain historical
observations, not fully verified optimizer-identical comparisons. No old
auxiliary weights entered formal training. The new paired validator checks all
network/target/optimizer/temperature/RNG/metric fields and gradients, rather
than relying only on final network hashes or matching initial predictions.


The corrected paired check completed256 updates per variant/interface. All
learner state fields and gradients match exactly, and each immutable parent
remains unchanged. Observed baseline/candidate elapsed-time ratios were1.5001,
1.4782,1.4149,1.5151 for Direct/Impedance/Admittance/VMC. These are single ordered
shared-load trials, not a promised online speedup or utilization improvement.
The2,048 auxiliary updates produced no formal weights and no new physics.

`runtime/source_train07` copies source_train06 with only the finite-check helper
changed. All other source/physics, controller parameter, official-code and robot
asset hashes match. `REGISTRATION_CHEQ_PERFORMANCE_V2.json` registers an exact
full-cycle continuation from the existing CHEQ performance run. The existing
coordinator implementation drains each old learner to its complete cycle before
resuming the same CPU/GPU/sampler allocation in
`runs/cheq_performance_seed20261025_v2`. Check migration receipts for actual
new-learner starts; registration itself does not mean migration has completed.
The separate SAC v1 migration continues independently and must not be duplicated.
Evidence: `PUBLISHED_CONCAT_FINITE_CHECK_20261025.json`.

The frozen cycle1 Direct interim evaluation has now completed its passive0000
and active_short0000 physical episodes: both full55s, Task/Strict false, ending
in lift. Active_long0000 is next/in progress; the three-case method-level
physical/filter/torque audits are written only after all three finish. Do not
confuse a completed raw episode with completed independent audit or final
acceptance. The nominal matrix had21/120 audited rows at this observation.


## Third complete CHEQ cycle and completed performance migration

All four cycle2 checkpoints are archived without misses. The v1 learners ended
normally and all four source_train07 learners in
`runs/cheq_performance_seed20261025_v2` have produced new transitions and updates.
Networks, targets, optimizer/temperature/RNG, replay/masks and cycle history are
retained. Migration is complete, not merely registered; the new archiver is live.

| Interface | Cycle0 Strict /30 | Cycle1 Strict /30 | Cycle2 Task /30 | Cycle2 Strict /30 | Cycle2 mean reward |
|---|---:|---:|---:|---:|---:|
| Direct |0|0|3|3|−27.827238|
| Impedance |18|17|17|16|−4.276838|
| Admittance |12|13|12|11|−13.776704|
| VMC |16|16|17|17|−2.803664|

Each cycle contains the same30 conditions. Direct's first strict successes were
active_short0000 at54.72s, active_short0500 at52.72s and active_long0900 at45.60s.
Its mean reward improved by5.24145 from cycle1, while Impedance/Admittance
worsened. All four still have0/10 passive strict successes. These changing-policy
training episodes are not frozen-policy acceptance or a convergence claim.

Impedance active_long0000 stopped after581 transitions because the original
`global_penetration_exceeded_2mm` gate triggered. It remains a failed case in the
30-case denominator. Consequently this cycle added40,456 transitions, versus
41,250 for each other interface; the step-count difference is not a lost sample
or migration defect. The complete category/failure-stage and paired-condition
record is `runs/cycle02_complete_comparison_v1/SUMMARY.json`.

Read-only exact-cycle2 diagnostics also completed, with138 terminal rows each:

| Interface | In-bag terminal MAE | Out-of-bag terminal MAE | Mean sampled Q | Alpha | Last1000 mean critic loss |
|---|---:|---:|---:|---:|---:|
| Direct |183.39|2319.47|2288.15|0.50395|2145.53|
| Impedance |613.80|2365.26|2583.02|0.80294|15308.55|
| Admittance |4940.98|10631.12|6855.98|0.87315|490399.56|
| VMC |4035.78|10618.07|7755.93|2.41286|172394.44|

The plotted Q/loss growth is substantial, particularly for Admittance and VMC.
Actual Direct successes do not establish healthy optimization. Withheld-mask
errors, hidden finite-horizon time and moving replay distributions retain their
previous caveats; a single terminal MAE threshold is not a convergence gate.
Results and original plot: `runs/diagnosis_cheq_cycle02_v1/results/`.

## Frozen cycle1 Direct: three independently audited cases

The interim Direct subset finished all three55s episodes and physical, public
filter and torque-projection/actual-actuator audits. No filter/projection
mismatch or machine safety violation was found. The fixed checkpoint failed
all three at lift; its later cycle2 stochastic successes must not be conflated
with this earlier frozen policy.

| Condition0000 | Learned Task/Strict | Nominal Task/Strict | Learned peak Nm | Nominal peak Nm | Learned contact-only ratio |
|---|---|---|---:|---:|---:|
| Passive |false/false|false/false|39.9144|38.5957|NA (0s contact)|
| Active-short |false/false|true/true|40.3015|47.0487|NA (0s contact)|
| Active-long |false/false|true/true|43.5290|46.6169|99.9684% (6.32655/6.32855s)|

Nominal active-short/long completion times are24.52/28.80s. The active-long
nominal contact ratio is100% over6.81705s. Lower learned peak torque and a near
100% contact ratio do not compensate for task failure. The failed learned
cases have SPT0 for any valid eventual reference; no final common reference is
selected from this interim subset. The matrix now evaluates Impedance on CPU54;
nominal evaluations continue on52/53 (26/120 at the latest recorded count).

## Finite discount sensitivity and its limitations

`runs/discount_sensitivity_cycle01_v1` finished four interfaces ×two discounts
×2,000 full learner updates, with fixed cycle1 replay/batch16384/masks. Each arm
deep-copies the same complete learner state, verifies all initial state fields
match, and confirms the original parent state remains unchanged. Method order
alternates which discount runs first. These16,000 auxiliary updates remain
separate, with ineligible auxiliary weights clearly labeled by their actual
Bellman discount. They do not modify any formal run.

| Interface | Final replay Q mean, gamma.99 | Final replay Q mean, gamma.9995 | In-bag terminal MAE .99 / .9995 |
|---|---:|---:|---:|
| Direct |751.69|834.20|67.43 /69.75|
| Impedance |1591.93|1766.43|385.77 /412.31|
| Admittance |654.44|724.24|372.07 /419.24|
| VMC |2271.38|2510.02|1106.64 /1274.98|

Lower gamma reduces predicted values but does not eliminate calibration errors.
Critically, this changes only the auxiliary Bellman discount: stored rewards
still contain shaping built with gamma.9995. It is a target-sensitivity test,
not a consistent alternate shaped-objective reproduction, a fresh-network
experiment, or a valid online policy ranking. Terminal credit1374 steps earlier
is approximately0.503 with.9995 but1.006e-6 with.99. A lower loss alone cannot
justify that change for the55s task. Formal gamma, shaping and CHEQ uncertainty
thresholds remain unchanged.

After all discount auxiliary processes ended, a new60-sample GPU window with
source_train07 CHEQ, SAC and one GPU1 fixed-policy evaluator measured means
38.33/30.98/30.08/32.22% (minima12/0/12/0). This still misses all-card50%; reduced
validation overhead is not evidence of meeting utilization. Full context and
counters are `runs/SOURCE07_ONLINE_GPU_60S_01.json`. A CPU-only diagnostic was
also active. Do not mix this window with the preceding auxiliary training.

Combined small evidence: `PUBLISHED_CYCLE02_AND_INTERIM_20261025.json` under the
benchmark evidence directory. No convergence, final SPT reference or ESN
comparison is claimed.

## First complete SAC cycle and all four continuations

All four source_train05 SAC parents completed their30-condition cycle and
resumed under the already-running source_train06 coordinator in
`runs/sac_performance_seed20261025_v1`. Every new learner has produced real
transitions and updates, with exact parent checkpoint receipts and a live cycle
archiver. Do not restart the old parent jobs or launch another coordinator.

| Interface | Retained transitions | Strict /30 | Mean reward | Terminal Q MAE | Alpha |
|---|---:|---:|---:|---:|---:|
| Direct |64492|0|−34.439232|56.1847|0.24225|
| Impedance |63528|16|−4.173868|13.8829|0.05103|
| Admittance |61765|12|−11.900917|106.3742|0.46815|
| VMC |62259|15|−6.343414|53.6897|0.27477|

Each parent has82,500 updates and41,250 newly collected transitions, with
different imported replay counts. This first SAC cycle cannot be ranked against
CHEQ's third cycle as equal training exposure. Read-only diagnostics and evidence
are `runs/diagnosis_sac_cycle00_v1/results/` and
`PUBLISHED_SAC_CYCLE00_20261025.json`.

The diagnostic plot previously left a blank next-target-Q panel because the
upstream plain SAC does not log that quantity. The renderer now plots the mean
of its two logged replay-Q predictions and labels it explicitly, rather than
implying a zero or inventing a target trace. Revised figures are in each
CHEQ diagnostic run's `plot_revision_v1/` and SAC run's `plot_revision_v2/`,
with source receipts (SAC v2 shortens a clipped title); original
figures and numerical diagnostics remain preserved. CHEQ retains its actual
logged next-target-Q trace. Both plots were visually reviewed.

## Shared-state action preferences: disagreement is not just an offset

`runs/action_value_cycle12_v1` completed a read-only comparison of all four
interfaces' exact cycle1/2 checkpoints. Each uses1,024 nonterminal states from
the earlier checkpoint's most recent complete cycle, with the replay prefix
verified exactly against the later checkpoint. Both checkpoints evaluate the
same12 candidates per state: stored action, zero nominal residual, each policy's
deterministic action, and four stochastic actions from each policy. Inputs
retain the recorded CHEQ context; these are raw-action value predictions.
Both online and target ensembles are evaluated. No optimizer or physics runs.

For critic i, state s and candidate a, decompose Q_i(s,a) into its candidate
mean b_i(s) and centered value c_i(s,a). With equal candidate weights,
mean_a Var_i(Q) = Var_i(b) + mean_a Var_i(c). The tool checks this identity in
float64 and reports both components. Synthetic checks cover pure offsets,
zero-mean action differences, offset invariance and invalid dimensions. This
does not change CHEQ's uncertainty rule or calibrate an alternative rule.

| Interface | Cycle2 offset fraction of total variance | Centered uncertainty mean cycle1 →2 | Cycle2 centered uncertainty ≥0.2 |
|---|---:|---:|---:|
| Direct |12.24%|6.407→17.844|100%|
| Impedance |32.72%|11.897→21.932|100%|
| Admittance |17.83%|14.143→96.485|100%|
| VMC |28.74%|25.963→45.840|100%|

These are online-ensemble statistics; target-ensemble results agree in direction
and are retained in the JSON. Thus action-dependent disagreements account for
most sampled variance; simply removing per-critic action-mean offsets would
still leave the registered0.2 threshold exceeded. This rejects an offset-only
explanation in the sampled cohort. It neither proves ground-truth action error
nor justifies a new threshold. Candidate-set selection affects this decomposition.

The cycle2 deterministic policy's predicted advantage over stored actions rises
from−0.630/1.321/2.282/9.536 under cycle1 critics to19.249/24.032/70.222/59.540 under
cycle2 critics. These are model predictions on the same candidates and states,
not measured return improvement. The earlier policy and critic preferentially
agree too; this cannot establish which policy actually performs better.
All network tensors remain exact, with0 gradients/updates. The25.8s diagnostic
finished; it is not persistent auxiliary training. Formal reward/gamma/mixing
and all protected control/physics settings remain unchanged.

## Fixed-cycle1 Impedance: audited efficiency/contact tradeoff

The three registered Impedance representative cases are complete, bringing
the interim matrix to6/12. All run the55s audit horizon, with exact filter replay
(1,375 calls), exact common torque-projection replay (13,750 calls), and agreement
with1,100,000 physical substeps per case. `PHYSICAL_AUDIT.json` alone explicitly
does not certify filter replay; the separate FILTER/TORQUE audit receipts do.

| Condition0000 | Learned / nominal strict success | Completion s learned / nominal | Peak Nm learned / nominal | Contact-only ratio learned / nominal |
|---|---|---:|---:|---:|
| Passive |false / false|NA / NA|41.3342 /40.5833|NA / NA|
| Active-short |true / true|12.92 /12.96|45.9904 /45.3060|NA / NA|
| Active-long |true / true|52.40 /20.52|51.5369 /52.2561|74.48% /24.07%|

Passive fails at carry. In active-long, learned compliant contact time is
5.89935 of7.92035s; nominal is1.87035 of7.76920s. This improvement in contact
threshold compliance comes with much slower completion, not a general method
win. The engineering comfort thresholds are below actuator safety limits;
strict success is the original gate, not a claim of100% comfort compliance.
No machine safety violation is reported in these three learned cases. No human
contact occurred in passive or active-short, so their ratio remainsNA.

CPU54 now evaluates Admittance; the120-case nominal matrix has31 audited rows
and continues on52/53. Neither is the complete final comparison, and no common
final SPT reference is selected. All eight formal learners continue; at the
evidence capture CHEQ retained230,334/235,815/233,756/238,563 transitions in cycle3,
and SAC101,749/71,389/67,144/68,174 in cycle1, respectively. These counters include
registered imported replay and must not be described as all-new experience.

Immutable source is `runtime/action_value_diagnostic_v1`; registration, reports
and comparison snapshot are under `runs/action_value_cycle12_v1` at the existing
SSD base. Small repository evidence is
`PUBLISHED_ACTION_VALUES_AND_IMPEDANCE_20261025.json`. No convergence, all-GPU50%
utilization, complete SPT result or designated-ESN comparison is claimed.

## Exact device replay cache and boundary continuation

Earlier profiling attributed14.6% of learner call time to CPU replay sampling.
`published_replay_device_cache_20261025.py` mirrors the authoritative CPU replay
on GPU. CPU insertion, NumPy sampling RNG, mask generation/rejection and saved
replay format remain unchanged. Each accepted index vector gathers contiguous
device samples; synchronous row copies keep the mirror current. It adds
432–448MB per learner (about0.40–0.42GiB), without increasing batch or UTD.
All state changes must go through add/load; direct external array mutation is
not supported by this cache.

Two finite paired validations use immutable complete-cycle CHEQ and SAC states,
all four interfaces, batch16384, and one copied replay-row insertion per two
updates to exercise online cache maintenance. These inserted rows are test
inputs, not new physical experience. Each arm deep-copies the full parent state,
clears prior gradients and verifies parent immutability. The first trial uses
128 updates/arm, the second256 with reversed order, totaling6,144 auxiliary
updates. Every pair has identical full learner state, optimizer/target/alpha/
RNG, replay and gradients. Auxiliary weights are discarded; all workers ended.
Validation uses source_train07's learner implementation for both algorithms;
the SAC continuation retains source_train06's older finite-check implementation,
which is untouched by the cache and does not change the learning arithmetic.

| Interface | CHEQ speedup trial1 / trial2 | SAC speedup trial1 / trial2 |
|---|---:|---:|
| Direct |1.580 /1.207|1.332 /1.211|
| Impedance |1.020 /1.443|1.275 /1.285|
| Admittance |1.560 /1.117|1.249 /1.255|
| VMC |1.044 /1.452|1.292 /1.250|

These are shared-load timing ratios, not isolated throughput guarantees. The
order dependence prompted the second trial; both show a reduction in measured
update time, but cannot establish all-card50% online utilization. Six protocol/
finite-check tests, two CPU/CUDA replay tests (wraparound, restoration, mask
rejection and RNG equivalence), and one migration-archive handoff test pass.

Immutable source_train08 retains source_train07 and source_train09 retains
source_train06. Each changes exactly two source files: the trainer and new cache.
Parameter, robot assets, published learner, physics/controller/reward sources
remain identical to its own parent. Registrations are
`REGISTRATION_CHEQ_PERFORMANCE_V3.json` and `REGISTRATION_SAC_PERFORMANCE_V2.json`
under runs/cohort30_v2. Coordinators preserve full states at complete-cycle
boundaries, using the existing52-core allocation and same four GPUs.

The first coordinator commands referenced a file absent from the inherited
runtime. Both interpreters exited before any STOP request or child process;
the failed launch/log receipts remain. After verifying the original learners
were still live and untouched, dispatch was frozen separately in
runtime/device_replay_dispatch_v1 and restarted with new retry receipts.
At the evidence capture, VMC/Impedance had really resumed CHEQ cycle4 with cache
enabled; Direct/Admittance and all SAC learners were still draining. Never
restart these parents or dispatch another migration from an observation delay.

Because siblings can migrate far apart in time, a new migration-only archive
mode follows the growing LAUNCH list and preserves early complete boundaries.
It exits after the coordinator starts its normal archive and writes
MIGRATION_FINISHED. Its separate early_cycle_archive directory preserves this
coverage without modifying learners or colliding with the normal archiver.
Current fourth-cycle CHEQ Task/Strict counts are18/17 for Impedance and17/17 for
VMC, with mean returns−2.247359/−2.810630; other interfaces are not complete yet.
The previous VMC mean−2.803664 and17/30 strict count are similar, which alone
does not establish stable optimization or sufficiently learned convergence.

## SAC Direct's second complete cycle does not show learning success

The exact cycle1 checkpoint has105,470 retained transitions, including40,978
new transitions this cycle. All30 cases fail at approach. Two original2mm
penetration aborts are retained: passive_corner0100 at1,282 steps and
active_short0100 at1,196 steps. They explain the272-transition shortfall from
30 full1,375-step episodes; this is not lost training data.

Mean return worsens from−34.439232 to−35.575272. Sampled replay-Q mean grows
from716.39 to3,401.98; terminal MAE from56.18 to329.77; last1,000-update mean
critic loss from44.66 to624.17. Alpha grows from0.24225 to0.56530. These
diagnostics sample each checkpoint's own replay (47 versus77 terminal rows),
not an identical-state calibration comparison. The smooth decline in actor
loss accompanies growing Q and failed tasks; it is not evidence of healthy
convergence. The diagnostic plot was visually checked, including its explicit
SAC replay-Q label.

`runs/diagnosis_sac_direct_cycle01_v1` has completed0 updates/0physics. The other
SAC cycle1 checkpoints were absent at capture and are marked missing, never
substituted with another cycle. Latest intermediate evaluation remains6/12,
with Admittance on CPU54; nominal has35/120. The shared SPT reference and ESN
comparison remain incomplete. Small evidence is
`PUBLISHED_DEVICE_REPLAY_CONTINUATION_20261025.json`; detailed validation is in
runs/device_replay_validation_v1 and v2. No formal scientific setting changed.

## Fourth CHEQ cycle completed; all four cache learners now updating

Later in the same work period, all four parents completed cycle3 and their exact
boundaries were archived with no misses. All four new source_train08 learners
have real new transitions and updates. The coordinator finished, its normal
archive started, and the migration-only archive exited normally without misses.
SAC migration remains in progress, with no replacement learner yet at capture.

| Interface | Task / Strict out of30 | Mean return cycle2 →3 | Passive / short / long strict counts, each /10 |
|---|---:|---:|---:|
| Direct |6 /6|−27.82724→−22.61414|1 /5 /0|
| Impedance |18 /17|−4.27684→−2.24736|0 /9 /8|
| Admittance |13 /13|−13.77670→−10.43662|0 /9 /4|
| VMC |17 /17|−2.80366→−2.81063|0 /10 /7|

Each cycle3 contributes41,250 new transitions; retained totals are244,194 /
244,721 /245,570 /246,276. Direct's first passive success is useful changing-policy
training evidence, not proof of a fixed successful policy or generalization.
The parameter methods still have no passive strict success. The full late
snapshot preserves all30 episode rows per method, not only successful cases.

After all cache learners updated, the first60-sample online window (67.65s wall
time) measured GPU means40.90/33.22/40.12/32.10%, minima0/0/8/0. No auxiliary
updates were running. Old SAC learners and one GPU2 fixed-policy evaluator were
active. The subsequent CPU-only cycle3 critic diagnosis started after this
window. Cache timing gains therefore still do not establish the requested
all-card50% utilization; this first post-migration window is not an isolated
steady-state benchmark. Raw samples are `runs/SOURCE08_ONLINE_GPU_60S_01.json`.

The exact cycle3 CPU-only critic diagnosis subsequently completed in
`runs/diagnosis_cheq_cycle03_v1`, with0 optimizer updates and0 new physical steps.
All168 terminal replay rows per method are included, with bootstrap masks
separating trained from withheld critic/row pairs. The plot was visually checked.

| Interface | In-bag terminal MAE | Out-of-bag terminal MAE | Sampled replay Q mean | Last1,000 updates mean critic loss |
|---|---:|---:|---:|---:|
| Direct |358.05|4530.54|4607.57|7676.61|
| Impedance |1063.08|3084.58|3691.79|43584.80|
| Admittance |21892.57|43966.29|32102.17|6642665.41|
| VMC |8474.15|22293.34|18220.59|783913.95|

These continue to worsen despite some task-success improvements. Out-of-bag
means bootstrap withholding, not unseen tasks. Actor-loss descent largely
tracks the growing Q scale, and finite losses do not establish stability.
The next scientific priority is value-learning stability, not declaring a
plateau sufficient or merely accumulating more transitions. No new scientific
repair, reward/discount change or privileged critic input has been selected.


## Fifth CHEQ cycle: Direct regression and continued optimization concerns

All four cycle4 boundaries (the fifth complete cycle) are archived without
misses in `runs/cheq_performance_seed20261025_v3/cycle_archive`. Every method adds
41,250 new transitions this cycle; retained totals include earlier imported data.

| Interface | Retained transitions | Task / Strict, each /30 | Mean reward | Passive / short / long strict, each /10 |
|---|---:|---:|---:|---:|
| Direct |285444|0 /0|−32.889049|0 /0 /0|
| Impedance |285971|17 /16|−4.035049|0 /9 /7|
| Admittance |286820|15 /14|−8.756420|0 /9 /5|
| VMC |287526|17 /17|−2.836609|0 /10 /7|

Direct regressed from6 strict successes in cycle3 to0. The parameter methods'
results fluctuate or remain similar; this is not learned convergence. All
four were subsequently verified collecting cycle5 transitions. The complete
120 episode summaries, cycle history and archive snapshot are in
`PUBLISHED_VALUE_BOUND_AND_FEEDBACK_20261025.json`.

## Necessary upper bound: current positive values are not calibrated soft returns

`runs/value_bound_cycle03_v1` audits all120 cycle3 episodes, reconstructs every
reward term and the discounted shaping telescope, and aligns rewards/dones with
the immutable replay. For fixed checkpoint policy and fixed current alpha,
all running costs are nonpositive, shaping telescopes to −5 phi(initial), and
the sole terminal plus efficiency reward is at most30. Differential entropy is
at most log(V), where V is the action-space volume. A relaxed, time-independent
necessary bound on Q is therefore:

`Q <= 30 + alpha * log(V) * sum(gamma**k for k in 1..1374)`.

Using the full horizon rather than hidden remaining time makes this a valid
upper bound even for a critic averaging over an unobserved episode clock.
Direct has log(V)=6 log(2), Impedance5 log(2), Admittance/VMC7 log(2).
The analysis is about the frozen-policy/current-alpha return, not a future
changing temperature schedule. All network tensors remain unchanged;0 updates
and0 physics. Four mathematical regression tests pass.

| Interface | Conservative global upper bound | Sampled online critic values above bound |
|---|---:|---:|
| Direct |3404.053884|99.4873%|
| Impedance |3654.932061|51.0498%|
| Admittance |15887.996124|57.6416%|
| VMC |18637.881140|62.7881%|

Fractions use5 critics times4096 sampled rows, with0.01 numerical tolerance;
they are not a whole-population estimate. A violation establishes failure to
represent the corresponding soft return, not a specific software bug or its
repair. Values below the bound are not automatically correct. The separately
computed remaining-time threshold is only contextual: an aliased critic can
legitimately exceed a particular hidden-time value. Likewise, raw terminal
MAE is a useful diagnostic but cannot be required to vanish when the critic
cannot distinguish a terminal-time observation from similar earlier states.

## Actor and temperature feedback: finite controlled intervention

`runs/policy_feedback_cycle03_v1` restores identical full cycle3 state for three
arms, each1000 updates: ordinary full learning; moving actor with fixed alpha;
and frozen actor/alpha with moving critics and targets. All use the same replay
sampling stream. Per-update NumPy/CUDA reseeding couples critic pairs and next
policy standard-normal samples; it intentionally differs from the formal RNG
stream. Actor/optimizer and alpha/optimizer invariance are checked for frozen
arms; critic updates and immutable parents are checked for all arms. All12,000
auxiliary updates completed, and weights were discarded.

| Interface | Initial Q mean | Full final | Moving actor, fixed alpha | Frozen actor and alpha |
|---|---:|---:|---:|---:|
| Direct |4769.2334|4778.0337|4777.3706|4770.4580|
| Impedance |3455.6023|3482.2039|3481.1443|3479.1492|
| Admittance |33116.6094|33576.2891|33556.2266|33533.4219|
| VMC |17964.0820|18083.9727|18084.2793|17967.6582|

Fixing the actor reduces short-window growth strongly for Direct/VMC; it does
not eliminate growth for Impedance/Admittance. Fixing alpha alone is insufficient.
This does not identify a unique cause or prove long-run online improvement.
Initial actual optimizer rows also have negative target means in all four
methods; do not assert they all began with positive entropy-driven targets.

## Fresh-critic fixed-policy evaluation and a separate online repair trial

`runs/fresh_critic_evaluation_cycle03_v2` completed24,000 auxiliary updates:
four interfaces, batch16384 versus256,3000 updates each. Actor, alpha and their
optimizers remain fixed at the same cycle3 checkpoint. Both arms start with
identical fresh critics, matching targets and empty critic Adam state. Replay,
reward, gamma and masks stay unchanged. This is equal updates, not equal sampled
rows (a64-fold difference); it cannot rank online batch settings. All protected
state assertions pass and auxiliary weights are discarded.

| Interface | Q mean at3000 updates, batch16384 /256 | In-bag terminal MAE,16384 /256 |
|---|---:|---:|
| Direct |−124.2667 /−119.8012|87.1947 /82.0219|
| Impedance |−87.7786 /−84.2734|89.0208 /79.4748|
| Admittance |−170.9697 /−173.5242|294.6170 /290.5739|
| VMC |−253.0531 /−249.8849|312.8596 /309.8316|

No sampled Q exceeds the positive global bound, but values are still moving
and terminal errors remain. Starting near zero also reduces value magnitude
mechanically; this is not a convergence or repair claim. The failedv1 run is
retained: its actor-invariance assertion compared CPU and CUDA tensors directly
and exited before any optimizer updates or physics. v2 compares on CPU.

A separate bounded online critic-reset trial is now registered in
`runs/cohort30_v2/REGISTRATION_CHEQ_CRITIC_RESTART_V1.json`. It isolates critic
initialization: published learner updates, batch16384, UTD2, gamma, actor,
alpha, their optimizers, replay/masks, RNG and all physical contracts remain.
Fresh critics/targets and a new empty critic optimizer are created from the
registered seed2026102528 at a complete parent-cycle boundary. No auxiliary
weights are imported. The CHEQ uncertainty/mixing output can change as a
consequence of changing critics; the mixing rule and actor inputs stay fixed.

The new stage runs exactly two complete30-condition cycles per interface for
review; that budget is not a convergence criterion or a cap on the overall Goal.
Original checkpoints and their cycle histories are preserved. New-stage plateau
detection starts with an empty history, so it cannot combine pre-reset and
post-reset cycles. Real-network tests verify actor/alpha/optimizer/RNG preservation,
empty critic optimizer, target equality, restoration, parent immutability and
rejection of unintended optimizer/target changes. Runtime source_train08 is
unchanged; preparation/dispatch code is separately frozen in
`runtime/critic_restart_dispatch_v1`. Consult dispatch receipts for actual launch
state; registration alone does not establish that a new learner has updated.

## All12 fixed-cycle1 representatives completed; cycle3 comparison started

`runs/interim_cheq_cycle01_representatives_v1/FINISHED.json` confirms12/12 audited
cases. All four passive cases fail; Direct also fails both active cases.
Impedance, Admittance and VMC pass both active cases. Original55s audit horizon,
physical substeps, public filter and common torque projection checks pass;
no machine safety violations are reported. This is three cases per method,
not the full30-condition final comparison.

The additional completed Admittance/VMC rows are:

| Interface / condition0000 | Learned / nominal completion s | Learned / nominal peak Nm | Contact-only compliance |
|---|---:|---:|---:|
| Admittance passive |fail /fail|40.5852 /40.7253|NA /NA|
| Admittance short |46.40 /45.28|52.4769 /53.9337|NA /NA|
| Admittance long |40.08 /42.48|50.7246 /54.1645|100% /100%|
| VMC passive |fail /fail|38.2458 /38.2857|NA /NA|
| VMC short |27.28 /27.44|47.2052 /47.2274|NA /NA|
| VMC long |31.64 /31.88|46.6635 /46.6593|100% /100%|

Admittance long contact duration is5.07970s versus5.20980s; VMC6.64985s versus
6.64235s. The previously reported Impedance long comfort/efficiency tradeoff
remains:52.40s versus20.52s,74.48% versus24.07% contact compliance. A favorable
single row does not establish a method winner.

The independent cycle3 matrix uses the same12 prespecified cases and the same
copied nominal rows, exact archived cycle3 checkpoints, source_train07 and
wrapperv6. Its coordinator is frozen in `runtime/interim_matrix_cycle03_v1`,
with an explicit `cheq_cycle03_` label prefix. Registration hashes checkpoints,
runtime, training protocol, audit helpers and nominal snapshot. It is running
on CPU54, not an extra full-cohort final test. The nominal matrix has47/120
completed rows at this evidence capture and continues on CPUs52/53. No final
common empirical SPT reference or designated-ESN comparison is available yet.


At the later dispatch check, the critic-reset coordinator PID429389 and its
migration-period archiver PID500618 are live; all four parent stop requests
refer to this registered boundary handoff. No replacement learner has launched
yet, and there is no migration failure. SAC's existing cache migration also
still has no replacement at this capture. The original learners continue
collecting real transitions. The nominal matrix has subsequently reached49/120.

After all finite auxiliary updates ended, a new60-sample window spanning66.75s
measured GPU means34.43/38.67/34.88/39.22%, with at least one0% instantaneous
sample on each card. It includes formal CHEQ/SAC and fixed-policy GPU0 inference;
the new restart coordinator is only waiting/preparing on CPU. This again falls
short of sustained all-card50%. Raw samples are
`runs/SOURCE08_ONLINE_GPU_60S_02.json`; do not count completed probes as current
GPU load. New stages must be judged by real learning and evaluation, not load.


## Critic restart is producing real transitions; first partial health snapshots

The registered coordinator has now actually restarted Impedance, VMC and
Admittance; Direct was still completing its original cycle5 at this capture.
No duplicate learner or migration failure was found. Each replacement uses
source_train08 and its own parent/restart checkpoint receipts. SAC Direct has
also completed its separate cache migration and is updating source_train09;
other SAC parents still drain through the existing coordinator.

`runs/critic_restart_early_health_v1` completed a CPU-only, zero-update diagnosis
of the two replacement snapshots available when it began. Their network tensors
are unchanged, and the plot was visually checked. These partial snapshots have
unequal new-transition counts and no completed new episode, so no new success
rate or reward-plateau conclusion is available yet.

| Interface | New transitions since reset | New optimizer updates | Sampled Q mean | Current-alpha global upper bound | Above-bound fraction | Alpha |
|---|---:|---:|---:|---:|---:|---:|
| Impedance |6000|12000|32.0672|120.6412|0%|0.0263244|
| VMC |4000|8000|447.2673|4709.8162|0%|0.970808|

In-bag terminal MAE is32.30/440.51 respectively, on retained parent terminal
rows only (228 rows/interface); there are no new terminal rows yet. The VMC
curve still shows growing Q and a critic-loss rebound after its initial drop.
The reset has changed value scale; this does not demonstrate calibration or
healthy convergence. Temperature changes also change the appropriate soft-value
bound. The current success criterion is not merely being below that bound.

The read-only diagnostic now verifies the exact audited reward/efficiency
sources before applying the bound, verifies unchanged network tensors, and
reports retained versus newly collected terminal errors when the replay has
not wrapped. It explicitly warns that missing episode time can produce terminal
aliasing. `runs/critic_restart_stage_audit_v1`, frozen in
`runtime/critic_restart_audit_v1`, waits for exact parent cycle5 and new cycles6/7
archives, then produces separate full reports and curves. It performs0 training
updates/physics, has a three-hour observer deadline, and never substitutes a
partial checkpoint for a complete cycle. The observer deadline does not stop
training or cap the overall Goal; reports still require scientific review.

## Live learner sampling identifies waiting and update overhead

A separately installed py-spy0.4.1 binary under `sii_rl/tools/py_spy_0_4_1`
sampled the live Direct parent for60 seconds at50Hz with idle stacks included.
The training Python environment was not modified. There were14,995 samples and
0 sampling errors:11,996 had empty Python stacks; the2,999 identifiable Python
stacks predominantly had the trainer module as root, with an additional partial
stack rooted in PyTorch named-members iteration. Percentages below condition on
identifiable Python stacks, not on all native threads or GPU execution time.

| Identifiable Python-stack category | Samples | Fraction |
|---|---:|---:|
| Published learner update |1809|60.32%|
| Waiting for sampler events |756|25.21%|
| Replay sampling |188|6.27%|
| Checkpoint preparation/save |96|3.20%|
| Actor inference/mixing |90|3.00%|
| Other |60|2.00%|

Checkpoint saving is not the largest observed bottleneck. Sampler waiting and
update overhead both matter; late cycles also have fewer live physics samplers.
This is one shared-load Direct window, not isolated CPU/CUDA kernel attribution
or a demonstrated four-GPU utilization fix. Original raw stacks and profiler
hash are in `runs/live_learner_profile_v1`.

## Exact-state candidate: suppress unused target-parameter gradients

The published CHEQ actor loss differentiates through target critics. Its target
weights update through Polyak averaging, so their accumulated parameter gradients
are unused. Freezing those parameter gradients still permits gradients through
the critic's action input into the actor; it must not use no_grad or detach on
the actor-loss forward path.

`published_target_gradients_20261025.py` is a candidate helper, not deployed in
the active science trial. `runs/target_gradient_validation_v1` completed two
reverse-order trials for all four interfaces,256 updates/arm,4096 auxiliary
updates total. Full learner/network/optimizer/alpha/RNG state, sampling RNG and
all non-target gradients match exactly. Only the intentionally unused target
parameter gradients differ. Parent checkpoints/replay are unchanged; auxiliary
weights were discarded and every validation worker exited.

| Interface | Observed speedup, first / reversed trial |
|---|---:|
| Direct |1.197 /1.044|
| Impedance |1.144 /1.015|
| Admittance |1.190 /1.066|
| VMC |1.144 /1.009|

The order dependence and shared GPU load limit timing conclusions. Exact used-
state equivalence is supported; sustained online speedup or50% GPU utilization
is not yet demonstrated. No active runtime or scientific setting was changed
by this candidate validation.

## Fixed-cycle3 Direct still fails all three representatives

The cycle3 Direct cases are now independently audited (3/12 matrix complete).
All run the full55s horizon, have Task/Strict false, fail at carry, and have no
machine safety violation. Physical, public-filter and torque-projection audit
receipts pass. The cycle1 counterpart failed at lift; reaching another stage
still does not constitute task completion or prove convergence.

| Condition0000 | Learned peak Nm | Nominal peak Nm | Learned / nominal contact compliance |
|---|---:|---:|---:|
| Passive |39.1198|38.5957|NA /NA|
| Active-short |39.2055|47.0487|NA /NA|
| Active-long |40.5029|46.6169|100% /100%|

Active-long contact duration is6.76980s versus6.81705s. Nominal succeeds in both
active cases (24.52s and28.80s), whereas the learned policy does not. Lower peak
loads and100% contact threshold compliance cannot replace task completion;
failed-case SPT remains0 regardless of the eventual shared reference. The
matrix now evaluates Impedance on CPU54. Nominal is55/120 at capture. No final
shared SPT reference, ESN comparison or convergence result is claimed.

Compact evidence and source hashes are in
`PUBLISHED_RESTART_HEALTH_AND_PROFILE_20261025.json`.


## All four critic-reset learners resumed; exact parent cycle5 audit completed

The coordinator now finished normally, all four replacements have real new
transitions/updates, and normal archiver PID1477077 has taken over. The early
archiver exited without misses. All four parent cycle5 checkpoints are archived,
and original learners ended normally. The current replacement handles are
Direct1471404, Impedance981510, Admittance1373289, VMC1099359; always revalidate
identity before acting. The stage-audit observer has completed the parent report
and now waits for full new cycle6 archives, then cycle7.

| Interface | Parent retained transitions | Parent cycle5 Task / Strict, each /30 | Mean reward |
|---|---:|---:|---:|
| Direct |326694|0 /0|-32.951656|
| Impedance |327221|18 /17|−2.258570|
| Admittance |328070|13 /13|−10.366395|
| VMC |328776|17 /17|−2.809056|

The exact parent diagnosis performs0 updates/physics, verifies network tensors
unchanged and reconstructs complete episode rewards. Its plot was visually
checked. It shows continued growth before the registered reset:

| Interface | Sampled Q mean | Above current-alpha global bound | In-bag terminal MAE | Last1000 updates mean critic loss |
|---|---:|---:|---:|---:|
| Direct |10913.10|84.45%|1289.43|81750.75|
| Impedance |6996.29|59.34%|1822.38|132180.51|
| Admittance |122751.82|57.81%|84910.74|90082761.25|
| VMC |68614.76|41.67%|34594.98|12246919.20|

These are parent snapshots, not evidence that the new trial has converged or
already failed. New-stage performance needs complete episodes and cycles.
The initial two-snapshot health report above is retained at its original
capture; later-arriving methods are not silently inserted into it.


The subsequent60-sample window after all four replacements started spans66.81s:
GPU means57.17/47.87/28.50/33.22%, minima2/0/0/0. Auxiliary updates and profiling
had ended; formal learners and the GPU1 fixed-policy evaluator were active.
This is still below the sustained all-card50% target. Raw samples are
`runs/RESTART_ONLINE_GPU_60S_01.json`; exact SAC Impedance startup-receipt timing
relative to the window is separately recorded in the compact evidence, so the
window is not assumed to have an isolated stationary background. At the latest
check both SAC Direct and Impedance had genuinely resumed source_train09,
while Admittance/VMC still drained. Nominal reached57/120. No final SPT/ESN
comparison or convergence claim is available.

The SAC Impedance startup receipt precedes that GPU window by43.15s. The raw
file's context text described only Direct as migrated; the evidence records
this correction explicitly. Raw utilization samples are unchanged.


## Actual target-gradient runtime validation and prepared continuation

`runs/target_gradient_validation_v2` tested the actual source_train08 and
source_train10 adapters, using immutable parent cycle5 checkpoints. Four
interfaces × two reverse-order trials × two arms ×256 updates produced4096
finite auxiliary updates and0 physics transitions. Full learner state,
optimizers, temperature, RNG, replay sampling RNG and all non-target gradients
matched exactly. The constructors were separately checked: original targets
trainable, candidate targets frozen. Actor gradients still pass through target
Q to the action input. No auxiliary weights were saved/promoted; all four
validation processes exited.

| Interface | Shared-load speedup, first / reversed order |
|---|---:|
| Direct |1.1574 /1.2932|
| Impedance |1.1159 /1.0489|
| Admittance |1.0683 /0.9723|
| VMC |1.2629 /1.0463|

These are finite equivalence and timing results, not guaranteed online speedup
or GPU utilization. One Admittance arm is slightly slower under shared load.

The first real registration check rejected source_train10 before launch:
the parent umbrella registration lists both CHEQ and SAC, whereas the initial
guard incorrectly required the entire algorithm list to equal CHEQ only.
`PREPARATION_V1_FAILURE.json` preserves this failure, and the original candidate
runtime/registration remain unchanged. The corrected code scopes the amendment
to CHEQ separately and rejects SAC execution of this continuation. Eight
software tests passed, including preservation of actor gradients, Polyak
updates, umbrella registration and rejection of protected-contract changes.

`runtime/source_train11` is a new frozen candidate: its learner/helper are
byte-identical to the validated source_train10; only its trainer scope guard
changes. All source hashes and protected manifest bytes were checked, and the
actual continuation protocol validated successfully. The registration is
`runs/cohort30_v2/REGISTRATION_CHEQ_TARGET_GRADIENT_PREPARED_V2.json`, with receipt
`runs/target_gradient_validation_v2/PREPARATION_V2.json`. **Prepared only: no
STOP request, coordinator or replacement training was launched.** Keep the
source_train08 critic-reset trial running its two complete cycles6/7, review
its scientific results, then decide continuation. Do not deploy the old
performance coordinator early because it would request a cycle-boundary stop
before that trial has finished. All learning states would be preserved; the
performance candidate does not perform another critic reset.

## Cycle3 Impedance representative evaluation completed

The frozen matrix reached6/12 audited cases and now evaluates Admittance.
Impedance uses the same three prespecified conditions and nominal rows as the
cycle1 evaluation. Every case completes55s; public-filter replay and torque
projection/physical linkage checks pass, with no machine safety violation.

| Condition0000 | Learned / nominal Task and Strict | Completion s | Peak Nm | Actual-human-contact threshold ratio |
|---|---|---:|---:|---:|
| Passive |failed /failed|NA /NA|40.9212 /40.5833|NA /NA|
| Active-short |passed /passed|12.84 /12.96|45.5225 /45.3060|NA /NA|
| Active-long |passed /passed|20.64 /20.52|51.6602 /52.2561|37.27% /24.07%|

Active-long human contact lasts7.7182s versus7.7692s. These are engineering
thresholds, not validated human-comfort limits. This single condition shows a
small time/torque tradeoff; it does not establish overall superiority or
convergence. The failed passive case remains in the denominator and hasSPT0;
no final shared SPT reference has been selected. Nominal is59/120 at capture.
Current training has not produced a complete post-reset cycle yet, so partial
condition mixes are not compared as whole-cohort success rates. The Goal and
ESN comparison remain unfinished; the designated ESN checkpoint is still
unavailable. Compact evidence: `PUBLISHED_TARGET_RUNTIME_VALIDATION_20261025.json`.


After auxiliary workers exited, a new60-sample/67.64s online window measured
GPU means50.48/23.65/31.15/43.10%, minima13/0/0/0. This includes the existing
CHEQ/SAC learners and GPU2 Admittance fixed-policy inference; source11 is not
running. Four-card sustained50% remains unmet. Raw samples are
`runs/RESTART_ONLINE_GPU_60S_02.json`; this window is preserved separately from
the earlier57.17/47.87/28.50/33.22% window. No claim of prevented shutdown is
made from utilization samples alone.


## First full post-reset Impedance cycle: unchanged success, slower completion

Impedance completed cycle6 at368471 retained transitions, with41250 new physical
transitions. Its immutable archive SHA256 is
`eaa586e539bbc7807b3cc8c2952d31599fdc7381646b6c3f8a9e21c80eee041c`.
The existing learner entered cycle7, the second registered repair-trial cycle.
All30 episode rewards were reconstructed from41250 logged transition components
and checked against the archive receipt. This is a complete single-interface
training cohort, not a frozen-policy test or the all-interface critic report.

| Metric | Parent cycle5 | Post-reset cycle6 |
|---|---:|---:|
| Task success /30 |18|18|
| Strict success /30 |17|17|
| Mean reward |−2.25856995697|−2.41004915544|
| Passive strict /10 |0|0|
| Active-short strict /10 |9|9|
| Active-long strict /10 |8|8|
| Mean completion over the same17 strict successes, s |16.6517647071|19.3788235307|

There are no gained or lost strict-success conditions. All failed passive
conditions still end at carry. The paired reward change is−0.15147919846;
−0.14048484848 comes from reduced completion-efficiency bonus. The same17
successful conditions finish2.72705882353s later on average. This conditional
time statistic does not remove failures from success/reward denominators.
The first new cycle does not support a task-performance benefit from the reset;
the second cycle and full critic-health audit remain necessary. No convergence
or repair-success claim is made. Evidence:
`PUBLISHED_RESTART_FIRST_CYCLE_20261025.json`.

A new read-only paired-review tool validates complete condition membership,
category identity, reward reconstruction, immutable-cycle boundary and explicit
network-invariance evidence before comparing reports. It reports gained/lost
successes, category summaries, reward component deltas and separate before/after
critic diagnostics; it does not concatenate training across the reset or decide
convergence automatically. Four software tests passed. Actual parent cycle5
self-comparison was a schema/integration check only, not scientific evidence.
An attempted historical cycle3→5 comparison was correctly rejected because
that older report lacks explicit `network_state_unchanged` evidence; its log
is retained, no guard was relaxed and no old diagnostics were rewritten.
The initial ad-hoc aggregation used system Python without NumPy and exited at
import before output; rerunning with the registered project Python completed.

`runs/CRITIC_RESTART_PAIRED_REVIEW_V1.json` registers a finite observer
PID2655393, frozen under `runtime/critic_restart_paired_review_v1`. It verifies
the existing stage-auditor PID900989 and process start ticks while waiting, then
checks finished report hashes and compares5→6,5→7 and6→7. It adds0 physics and0
optimizer updates, does not stop/restart learners, and leaves training unchanged
if the auditor disappears or its observation deadline expires. Check actual
process identity before acting. At this capture it waits for complete cycle6
reports across all four methods; no comparison plots from those stages exist yet.

SAC VMC has also completed its existing cache handoff and is really updating
source_train09 as PID2397784. Direct/Impedance are already there; Admittance still
drains source_train06 under the original coordinator. Do not launch a duplicate
migration. The prepared source_train11 target-gradient optimization remains
undeployed. Physics, actor contract, gates, filter, actuator limits and dt remain
unchanged; the persistent training/convergence/ESN-comparison Goal remains active.


Subsequent live verification: SAC Admittance also completed its boundary handoff
and now updates source_train09 as PID2758791. `MIGRATION_FINISHED.json` confirms
all four replacements have updated, and normal archiver PID2767227 has taken
over. The coordinator has finished; no old SAC process or migration should be
restarted. The exact receipt and current progress are appended to the compact
evidence above, preserving the earlier VMC-only capture.


## All-interface SAC second-cycle audit: value growth is not CHEQ-specific

All four SAC cycle1 checkpoints are now immutable in
`runs/sac_performance_seed20261025_v1/cycle_archive`. A registered read-only audit
under `runs/SAC_CYCLE01_ALL_AUDIT_V1.json` reused the frozen auditor and produced
`runs/diagnosis_sac_cycle01_all_v1/sac_cycle01/results/DIAGNOSIS.json` plus its
training plot. The auditor exited normally; all report/checkpoint registration,
reward reconstruction and network-invariance checks passed, with0 optimizer
updates and0 new physics. The plot was visually reviewed.

| Interface | Retained steps | Task / Strict, each /30 | Mean reward | Replay Q mean | Last1000 mean critic loss |
|---|---:|---:|---:|---:|---:|
| Direct |105470|0 /0|−35.575272|3401.98|624.17|
| Impedance |104778|17 /16|−4.133093|858.16|401.61|
| Admittance |103015|14 /13|−10.352139|5430.80|10654.33|
| VMC |103509|18 /18|−1.172646|4105.49|14230.63|

Every interface still has0/10 passive strict success. Direct aborted two
conditions at the unchanged2mm global-penetration limit; failures remain in the
denominator. The three parameter interfaces' short/long strict counts are
9/7,7/6,10/8. This is the second full SAC cycle, not matched exposure to the
later CHEQ cycles; do not rank the two algorithms from these rows.

Cycle0 replay-Q means were716.39/113.58/1166.50/420.92; the corresponding last1000
critic losses were44.66/2.06/248.40/29.70. All four increased substantially.
The plots show sustained positive Q growth and worsening losses, despite entropy
remaining near its dimensional target. Actor loss decreases together with the
rising Q baseline; it is not a reliable improvement signal in this state.
The fixed-policy/current-alpha conservative global-bound violation fractions
are99.85%/0%/0.55%/0%. Direct is inconsistent with that necessary bound; satisfying
the bound in the other methods does not prove value calibration. Terminal MAE
is329.77/160.22/1124.75/1210.30, with the previously documented hidden-clock
aliasing limitation.

Value drift therefore also occurs without CHEQ's ensemble/context/mixing. This
observation does not isolate a shared cause or establish a remedy. No reward,
gamma, learning-rate, physics or mixing change was made by this audit. Compact
evidence: `PUBLISHED_SAC_SECOND_CYCLE_20261025.json`. Existing SAC learners keep
training under their registered source_train09 protocol; source_train11 remains
prepared only, and the CHEQ two-cycle critic-reset trial continues.


After all SAC cache handoffs,60 samples spanning67.98s measured mean GPU usage
39.28/32.17/10.87/28.77%, minima12/0/0/0. No auxiliary GPU updates were running;
this window includes CHEQ cycle6→7 transitions and GPU2 fixed Admittance
inference. It is not stationary isolated throughput, and remains below the
all-card50% target. Raw data: `runs/ALL_SAC_CACHE_GPU_60S_01.json`. Existing
training remains live; the low window is not evidence that learners stopped.


## All four first post-reset cycles completed and paired review verified

All cycle6 checkpoints are archived without misses; the existing four learners
entered cycle7. The stage auditor completed network-invariance and full reward
reconstruction checks, then the paired-review observer completed5→6. Both wait
for cycle7 now. The diagnosis and paired plots were visually checked. There
were0 diagnostic optimizer updates and0 new diagnostic physics transitions.

| Interface | Retained transitions | Task / Strict, each /30 | Mean reward | Strict change vs parent5 |
|---|---:|---:|---:|---:|
| Direct |367944|1 /1|−31.484336|0→1|
| Impedance |368471|18 /17|−2.410049|17→17|
| Admittance |369320|16 /16|−5.367201|13→16|
| VMC |370026|17 /16|−4.586778|17→16|

Every method still has0/10 passive strict success. Direct gains
`active_long_train_0500`; Admittance gains active-long0300/0500/0600 with no
lost successes. Impedance's success set is unchanged. VMC loses strict success
on `active_short_train_0600`. Improvements therefore remain mixed and must not
be summarized as four converged policies or a uniformly successful repair.

| Interface | Replay Q mean | Current-alpha global bound | Sampled Q above bound | Last1000 mean critic loss | In-bag terminal MAE |
|---|---:|---:|---:|---:|---:|
| Direct |133.87|207.96|0%|25.13|44.42|
| Impedance |123.41|129.56|37.95%|66.92|49.98|
| Admittance |326.08|147.17|99.50%|105.29|115.70|
| VMC |1384.20|2797.16|0%|7189.25|1080.71|

Lower magnitudes than parent5 do not establish calibration. Impedance and
Admittance already violate a necessary fixed-policy/current-alpha bound on
many samples. VMC's critic loss and Q grow throughout the cycle; Direct's
smaller loss and one successful episode are insufficient convergence evidence.
The30 newly collected terminal rows per method separately have in-bag MAE
86.30/59.61/135.87/1563.21. Hidden-clock observation aliasing still limits terminal
error interpretation; neither zero terminal error nor mere bound satisfaction
is asserted as a convergence criterion. The within-cycle reward trace also
changes with condition category, so its rise is not itself learning evidence.

Evidence is `PUBLISHED_RESTART_CYCLE06_REVIEW_20261025.json`, with original reports
under `runs/critic_restart_stage_audit_v1/restart_cycle06` and
`runs/critic_restart_paired_review_v1/parent05_to_restart06`. The registered
second cycle remains live; source_train11 is not deployed, and no further
scientific setting is silently selected from this single-cycle result.


The separate frozen cycle3 matrix now has9/12 audited cases and evaluates VMC
on CPU54 (evaluator PID3248872; verify identity). Admittance's three completed
representatives pass physical, public-filter and torque-linkage audits, with
no machine safety violation. These are older cycle3 policies, not the current
critic-reset cycle6 checkpoints:

| Admittance condition0000 | Learned / nominal Task and Strict | Completion s | Peak Nm | Human-contact threshold ratio |
|---|---|---:|---:|---:|
| Passive |failed /failed|NA /NA|40.9741 /40.7253|NA /NA|
| Active-short |failed /passed|NA /45.28|40.9232 /53.9337|NA /NA|
| Active-long |passed /passed|42.88 /42.48|49.9474 /54.1645|100% /100%|

Active-long contact duration is5.6033s versus5.2098s. Active-short's lower torque
is accompanied by failure and SPT0, so it is not a successful compliance result.
Nominal matrix progress is64/120. No final shared SPT reference or ESN comparison
has been produced. Rows and audit hashes are included as a separate section in
`PUBLISHED_RESTART_CYCLE06_REVIEW_20261025.json`.


## Finite reward-unit study, original versus reciprocal success bonus

The registered `runs/reward_units_fresh_cycle06_v1` study completed four
interfaces × two scales × 2500 updates = 20,000 auxiliary updates. Both arms
start from the same entirely fresh actor, critics, targets, optimizers,
alpha and RNG (seed2026102530), sampling the same immutable cycle6 replay.
Only sampled reward tensors are multiplied by1 or0.04; stored replay,
terminal masks and historical context remain unchanged. The scale0.04 was
chosen before outcomes as the reciprocal of the existing success bonus25.
Batch16384, gamma0.9995, architecture and initial alpha1 are unchanged.
Consequently this deliberately changes relative entropy pressure; it is not
a change of units applied consistently to the entire soft objective.

| Interface | Q mean, scale1 /0.04 | In-bag terminal MAE, scale1 /0.04 | Alpha, scale1 /0.04 |
|---|---:|---:|---:|
| Direct |36.6076 /926.2000|60.5542 /942.2123|0.46953 /11.73734|
| Impedance |31.1527 /781.8120|29.2920 /778.4697|0.46967 /11.74141|
| Admittance |43.8050 /1099.0005|49.1348 /1099.0662|0.46970 /11.74252|
| VMC |43.8375 /1097.7887|43.8139 /1092.9542|0.46969 /11.74229|

All table values are converted to original reward units, including alpha.
Raw Q magnitudes remain similar, so lower reward units alone do not establish
better value calibration. Temperature is still adapting. All sampled Q are
below the current-alpha conservative bound at these short fresh states;
this is not calibration or convergence. Implied minimum-authority fractions
are6.0791%/1.0498%,0.8545%/0.0732%,0.7812%/0.0732%,0.5127%/0.0488%
respectively, with unchanged absolute CHEQ uncertainty thresholds. These are
frozen-data diagnostics, not observed online task or safety outcomes.

This window does not justify applying reward-only rescaling as a repair;
it does not show that reward scaling is generally harmful. No formal reward
or training state changed, no physics ran, and no auxiliary weights were
saved or promoted. All four auxiliary processes exited. Two focused tests
passed (reward-copy/mask preservation and entropy-temperature bound units);
the registered reporter completed and its plot was visually checked.
Evidence, source/registration/report/plot hashes and limitations are in
`PUBLISHED_REWARD_UNITS_PROBE_20261025.json`. Full artifacts remain at
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/reward_units_fresh_cycle06_v1`.

After auxiliary exit, a60-sample window over67.96s measured GPU means
38.97/43.38/27.17/34.73%, with instantaneous minima0/0/0/0. This includes
four CHEQsource08 cycle7 learners, four SACsource09 learners and fixed VMC
inference onGPU3; it is a shared online window, not isolated throughput.
The requested four-card50% target remains unmet. Raw measurements are
`runs/CYCLE07_POST_PROBE_GPU_60S_01.json`; source_train11 remains prepared only.
The original two-cycle critic-reset study must finish and be reviewed before
any scientific continuation. No early STOP or replacement learner was added.


## Fresh consistent-discount probe and observed passive-task regression

The earlier discount probe changed only the Bellman discount on inherited
learner states, leaving stored PBRS at0.9995. A new registered finite study,
`runs/consistent_discount_fresh_cycle06_v1`, removes those two limitations.
Four interfaces × two arms ×5000 updates =40,000 auxiliary updates completed.
Each arm resets the same entire fresh actor/critics/targets/optimizers/alpha/RNG
(seed2026102531). A separate copy contains all41,250 transitions from the30
full55s cycle6 episodes, paired with their original reward logs. This subset
is different from the whole-replay reward-unit probe; do not rank across them.

Both Bellman gamma and PBRS gamma are0.99 or0.9995. The helper reconstructs
`5*(gamma*phi_next-phi)` with terminal phi_next0, checks original reward/log
alignment and discounted telescoping, and rejects incomplete/early-abort
inputs rather than silently retaining inconsistent failure-tail rewards. All
30 conditions are full-horizon here; no failed conditions were discarded.
Stored formal replay, masks, historical context and physical data are unchanged.
Same batch16384, sampling streams, architecture, alpha initialization, and CHEQ
uncertainty thresholds. Two focused tests and real all-condition reconstruction
passed. The report completed and its plot was visually reviewed.

| Interface | Q mean .99 /.9995 | In-bag terminal MAE .99 /.9995 | Last recorded critic loss .99 /.9995 |
|---|---:|---:|---:|
| Direct |44.1622 /52.2408|1.1394 /2.6338|1.8924 /1.7124|
| Impedance |37.0254 /44.1145|11.2235 /15.3930|0.6161 /0.8008|
| Admittance |52.4948 /62.2985|11.4927 /14.2350|1.0940 /1.2390|
| VMC |51.8829 /61.5495|22.4809 /29.0146|2.4717 /3.2600|

Alpha is approximately0.222 in all arms and is still changing. All sampled Q
lie below the current-alpha conservative bound, but Q still grows in both
arms. These short fresh states do not establish long-run calibration or online
task quality. Low discount attenuates terminal credit1374 steps earlier to
about1e-6 versus0.503 with0.9995; smaller Q alone cannot justify adopting it for
this55s task. No formal gamma/reward change was made. All auxiliary workers
exited, with no physics and no saved/promoted auxiliary weights.

A separate read-only analysis examines the one observed Direct passive0900
success from cycle3 against the same condition in cycles5/6/7. All four MJB,
nominal-plan and physical-fixture hashes are identical; dt5e-5 and canonical48
are verified. Reward components reconstruct, and each episode has1375 decisions.

| Training cycle | Task/Strict | Completion s | Final stage | First align /lift /carry time s | Final placement XY error mm |
|---|---|---:|---|---|---:|
|3|true/true|37.32|release|0.16 /1.80 /3.68|4.26|
|5|false/false|NA|carry|0.16 /1.92 /4.92|95.59|
|6|false/false|NA|lift|9.16 /27.84 /not reached|177.41|
|7|false/false|NA|lift|29.72 /36.52 /not reached|148.61|

Cycle3/5 mixing context is always0.2; cycle6/7 means are0.23889/0.21098,
maxima0.95991/0.85208. The commanded residuals also change. Later regression
already affects early approach/grasp, so failure cannot be described only as
getting stuck in late carry. However this is one selected condition, with
changing policies and stochastic actions. It does not isolate causality,
prove a fixed successful checkpoint, or replace independent safety acceptance.
The isolated success is not generalized to the passive cohort.

Case returns are19.77413,−31.92895,−31.67844,−31.52589. In the last two failures,
slightly higher total reward coexists with much later first alignment; reduced
penetration cost and changed undiscounted PBRS sums contribute. Episode return
alone therefore does not certify task improvement. The PBRS term must also be
interpreted with its discount, not as an undiscounted progress score.

Compact evidence is `PUBLISHED_CONSISTENT_DISCOUNT_AND_PASSIVE_20261025.json`.
Full artifacts are under
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/consistent_discount_fresh_cycle06_v1`
and `runs/passive0900_training_regression_v1`. No additional physics or
training-state changes were made by the analyses. Formal source08 cycle7 and
source09 SAC continue; source11 remains prepared only pending complete review.

The60-sample/67.81s shared GPU window measured50.28/12.17/36.73/21.85% means,
minima11/0/0/0. Auxiliary workers finish during/before this window; per-sample
process presence is recorded. It is not formal-only throughput and still does
not meet four-card50%. Original `runs/CONSISTENT_DISCOUNT_SHARED_GPU_60S_01.json`.

Later boundary update: Impedance cycle7 completed at409721 retained transitions,
with Task18/30, Strict17/30 (passive0, short9, long8), mean reward−2.30143463
versus−2.41004916 in cycle6. The registered two-cycle learner exited normally
and its exact cycle7 state is archived. Do not restart that old PID. The other
three CHEQ learners still finish their original stage; SAC remains live. Existing
auditor/reviewer wait for the full group. This boundary alone is not the
scientific review required before choosing continuation or deploying source11.


## Completed critic-reset trial and registered actor learning-rate continuation

All four original source08 learners completed their two registered cycles6/7,
saved exact complete-cycle archives and exited normally. The existing read-only
auditor and paired reviewer finished, verified reward reconstruction/network
invariance, and produced5→7 and6→7 comparisons. All three figures were visually
reviewed. This is the scientific review required before any further stage.

| Interface | Cycle7 transitions | Task /Strict out of30 | Mean reward | Strict cycle5 →6 →7 |
|---|---:|---:|---:|---|
| Direct |409194|0 /0|−32.911626|0 →1 →0|
| Impedance |409721|18 /17|−2.301435|17 →17 →17|
| Admittance |410570|14 /12|−11.980507|13 →16 →12|
| VMC |411276|17 /17|−2.837811|17 →16 →17|

Every passive cohort remains0/10 strict. Direct loses active-long0500 versus6;
Admittance loses active-long0500 and active-short0000/0600/0900 versus6. VMC
regains active-short0600; Impedance's strict-success set is unchanged. Direct's
failures now include16lift,2align,3approach,6carry and3load-transfer cases.
These outcomes do not establish sustained task improvement from critic reset.

| Interface | Cycle7 Q mean | Current-alpha bound | Samples above bound | Last1000 mean critic loss | In-bag terminal MAE |
|---|---:|---:|---:|---:|---:|
| Direct |381.25|613.43|3.24%|194.85|92.56|
| Impedance |514.69|434.52|43.72%|1216.17|152.52|
| Admittance |382.32|254.47|76.33%|1083.08|343.23|
| VMC |4230.62|6139.30|27.28%|57826.03|2677.72|

All four late critic losses grow. Lower values than the very large pre-reset
cycle5 do not establish calibration. The two-cycle intervention did not fix
optimizer health or deliver four converged controllers. The fixed-current-alpha
bound is necessary, not sufficient; hidden-clock aliasing still limits terminal
error interpretation. No new critic reset was selected.

A finite actor-rate probe followed the earlier frozen-actor feedback evidence:
`runs/actor_lr_cycle06_v1`, four methods ×two factors ×10,000updates=80,000
auxiliary updates. Both arms restore the same full cycle6 learner/optimizer/RNG
and replay sampling stream. Only actor Adam LR changes3e-4→3e-5; all moments,
critic/alpha settings and rewards stay unchanged initially. The four processes
exited; no physics, auxiliary weights saved, or weight promotion. Two focused
actor-LR tests passed, and the report/plot were checked.

| Interface | Q mean original /0.1LR | In-bag terminal MAE original /0.1LR |
|---|---:|---:|
| Direct |140.04 /137.14|38.53 /37.22|
| Impedance |166.34 /162.45|63.99 /62.26|
| Admittance |321.68 /317.11|133.70 /121.28|
| VMC |1738.80 /1722.66|1277.43 /1259.54|

These modest reductions do not remove drift; VMC keeps growing, and bound
violations are not uniformly reduced because alpha also evolves. A slower actor
can delay useful learning. This evidence supports only a bounded online
sensitivity trial, not a proven repair or guaranteed convergence.

The explicit decision receipt `runs/CRITIC_RESTART_FINAL_SCIENTIFIC_REVIEW_V1.json`
and registration `runs/cohort30_v2/REGISTRATION_CHEQ_ACTOR_LR_CONTINUATION_V1.json`
therefore select two new full cycles8/9 with actor LR3e-5 for all four methods.
All weights, critic/target/alpha, Adam moments, RNG, replay/masks, gamma0.9995,
batch16384/UTD2 and physical/control contracts are retained. The stage's old
cycle-summary list is cleared to avoid pooling unlike optimizer stages; prior
logs/checkpoints remain archived. The inherited `critic_restart` registration
field is provenance only and does not trigger another reset.

New frozen source_train12 keeps the previously validated source11 learner and
unused-target-gradient optimization. Its trainer adds explicit reviewed-stage,
parent-boundary, stage-budget and actual-actor-LR checks and execution receipts.
The new completed-stage dispatcher validates all four finished archived parents
and the full scientific-review hashes before launching; it issues no STOP
requests and never reuses the live-parent-only migration coordinator. Three
new stage tests and all eight existing performance-contract tests passed.
Real complete Impedance checkpoint preparation verified exact preservation of
all non-LR/history fields, and both protocol branches passed. Actual launch
then verified this invariant separately for all four parents.

`runs/actor_lr_online_seed20261025_v1` is genuinely updating cycle8 on GPUs0–3,
with9samplers per interface and the original CPU allocation. Learner PIDs are
919723/923788/927495/932939 (reverify before action). Startup coordinator911732
finished normally; archive941236 tracks boundaries. No auxiliary weights were
imported. Four SACsource09 learners continue independently. Source11 remains
an unused preparation; source12 is the actually deployed continuation.

Read-only auditor969396 and reviewer969397 now wait for complete cycles8/9,
using `ACTOR_LR_STAGE_AUDIT_V1.json` and `ACTOR_LR_PAIRED_REVIEW_V1.json`. The
review compares7→8,7→9 and8→9, reusing the completed cycle7 report. Their3h
observation deadline does not stop training. No conclusion is automated from
a stage ending. Evidence and provenance are in
`PUBLISHED_ACTOR_LR_CONTINUATION_20261025.json`; server base remains
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`.

## Frozen cycle3 representative matrix completed; cycle7 matrix started

The older cycle3 matrix finished12/12 registered representatives. All physical,
public-filter and actuator-torque projection audits passed; no machine safety
violation was recorded. Strict successes are Direct0/3, Impedance2/3,
Admittance1/3 and VMC2/3. All four passive representatives fail. These are
three prespecified cases per method, not the full30-condition final comparison.

The newly completed VMC rows are:

| Case0000 | Learned /nominal Task and Strict | Completion s learned /nominal | Peak Nm learned /nominal | Contact threshold ratio |
|---|---|---:|---:|---|
| Passive |fail /fail|NA /NA|38.0997 /38.2857|NA /NA|
| Active-short |pass /pass|27.40 /27.44|47.2304 /47.2274|NA /NA|
| Active-long |pass /pass|31.64 /31.88|46.7528 /46.6593|100% /100%|

Active-long human contact is6.6629s/6.64235s. Small timing differences are not
an overall superiority claim. Failed cases remain in the denominator and
haveSPT0; no final shared empirical T_ref is selected from this interim matrix.
Compact all12-row/audit evidence is `PUBLISHED_FIXED_CYCLE03_COMPLETE_20261025.json`.
The nominal full matrix has75/120 completed at capture, still on CPUs52/53.

After all exact cycle7 archives became available and the previous matrix
processes exited, `runs/interim_cheq_cycle07_representatives_v1` was registered
for the same12 cases and same frozen nominal rows. Its coordinator803220 and
Direct evaluator804667 are live on CPU54/GPU0 inference (reverify). It uses
source08 policies from cycle7, not the new actor-LR learners. No duplicate
cycle3 evaluation, final SPT selection, or designated ESN comparison occurred.

After actor-LR startup,60samples over67.60s measured GPU means42.22/30.42/31.08/31.48%,
minima5/9/0/0. Four source12 CHEQ and four source09 SAC learners plus frozen
cycle7 Direct inference were active; all auxiliary workers had exited. This
shared window still fails the requested four-card50% target and is not an
isolated speedup measurement. Raw `runs/ACTOR_LR_ONLINE_GPU_60S_01.json`.


## Prepared unchanged-LR continuation after the current scientific trial

A read-only follow-up found a future handoff limitation in source12: the
unchanged-rate branch expected3e-4 unconditionally. It would reject a legitimate
later continuation retaining the current3e-5, despite the checkpoint preparer
already preserving the lower rate and history. This does not affect the live
first LR-intervention stage8/9.

The candidate source13 trainer now validates an explicitly registered list of
parent actor learning rates. The dispatcher checks those rates against every
reviewed parent checkpoint before launching any learner. With factorNone, the
full optimizer state and cycle history remain exact; with the first0.1 factor,
backward compatibility with the original3e-4→3e-5 trial is retained. Repeated
compounding of the0.1 intervention is rejected. Boundary/budget, malformed or
nonfinite rates, mismatched optimizer-group count, protected source/objective,
and unlike-stage history checks remain enforced. Plateau criteria are unchanged.

Five completed-stage tests and all eight existing performance-contract tests
passed. Preparation against all four actual immutable lower-LR checkpoint
states retained every field exactly, including weights, moments, RNG, replay
and history. These are real archived preparation states from cycle7, not
invented future cycle9 archives. The separately checked future protocol is
only a structural candidate with an intentionally absent scientific review;
it does not select or dispatch a new stage. No weights were saved or promoted,
no optimizer updates or physics ran, and no STOP/continuation process started.

`runtime/source_train13` and `runtime/completed_stage_dispatch_v2` are frozen
candidates only. The sole source change relative to source12 is the trainer;
learner, robot assets, parameter adapter and published implementation manifests
are identical. Current four source12 learners and four SACsource09 learners
remain live. They must finish and review the registered cycles8/9 before any
new continuation decision. This preparation does not imply that their learning
has converged. Evidence: `PUBLISHED_UNCHANGED_LR_PREPARATION_20261025.json`;
full receipts under
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/unchanged_actor_lr_preparation_v1`.

## Live physical-worker profile (read-only, 2026-10-25)

A 60-second, 100 Hz py-spy sample of the existing source12 Direct active-short0600 worker produced 4,895 stacks and zero errors; PID/start ticks matched before and after. Observer-inclusive samples were 2,619 (53.50%); the mj_step call-site leaf had 921 (18.82%). These are recorded-stack shares, with idle threads excluded, no native unwinding, and one condition under shared load. They are neither all-system CPU shares nor evidence of a measured GPU speedup.

Contact traversal and per-substep telemetry warrant further profiling. They implement frozen contact/safety/reward evidence and must retain every substep and numerical operation order. No optimization was deployed, no frozen runtime edited, no additional simulation process or auxiliary learner update started. The actor-LR trial continues its original cycles8/9; source13 is only prepared. Full receipt, source hashes, frame tables and live progress: PUBLISHED_PHYSICAL_WORKER_PROFILE_20261025.json; raw artifacts: /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/physical_worker_profile_v1.

## Contact-access microbenchmark (not deployed, 2026-10-25)

Following the live worker profile, two finite probes reconstructed five prescribed saved configurations (1/8/18/35/50s) for each of the three cycle3 Direct representative cases. Original contact indexing, held-container indexing, and bulk geom-ID arrays returned exactly the same IDs/order. Distance/frame views were byte-identical, and mjSTATE_INTEGRATION before/after reads was byte-identical. Both processes exited; total30 mj_forward reconstructions, zero mj_step, physical transitions or learner updates. Frozen models/runtimes were unchanged.

v1 shared-CPU wall times had scheduling outliers. v2 retained the same arms/inputs and added process CPU timing: original/bulk-ID extraction ratios2.325–4.658, median4.547. This is an extraction microbenchmark, not a whole-loop or simulation speedup. The saved states do not reconstruct all historical warmstart fields, so no historical solved-force equivalence is claimed. A full-loop and physical trajectory/reward equivalence study remains necessary before considering deployment; no source12 change or new training dispatch was made. Evidence: PUBLISHED_CONTACT_ACCESS_PROFILE_20261025.json; raw runs contact_access_profile_v1/v2.

## Full contact-access candidate validation started (2026-10-25)

The isolated contact_candidate_v2 runtime changes only per-substep contact field access in audited_velocity_env.py and the evaluator, plus the matching episode-adapter source seam. Views are reacquired after each physics step; no contact order, force call, arithmetic sequence, telemetry or control contract is removed. It copies source07, whose three original worker files match live source12; parameter and robot manifests also match. Candidate v1 remains unused; v2 avoids redundant float conversions. No live runtime is edited.

Two software tests verify strict array comparison and rejection of missing seams, and a real complete archive self-comparison passed for1,100,000 substeps. A finite validator now replays twelve immutable cycle3 action tapes (four interfaces × three scenarios,55s each) through the candidate using the same frozen observational wrapper. It checks canonical48/reward telemetry before every action, then exact MJB/journal/terminal/substeps and all rollout/filter/torque NPZ arrays, and full result JSON except specifically registered source hashes and output prefixes. On observation timeout it polls the same live handle; only an actual mismatch/error stops its own child.

Coordinator2014112 and first child2019617 were verified live. The first156 complete actor intervals/124,800 physical substeps matched byte-for-byte, including reward journal prefixes. This is only an early prefix, not full equivalence, task improvement or measured online speedup. CPU10/nice10, one physics worker, no learner or optimizer updates. Current formal source12 cycles8/9 and source09 SAC continue unchanged. Evidence PUBLISHED_CONTACT_CANDIDATE_VALIDATION_20261025.json; raw runs/contact_candidate_validation_v1.

## Frozen cycle7 Direct representative results (2026-10-25)

The first3/12 frozen cycle7 representative evaluations completed all55s. Direct failed Task/Strict in passive, active-short and active-long; final stages were lift/lift/release. Peaks35.9494/37.9550/51.2366Nm; nominal peers38.5957/47.0487/46.6169Nm. Nominal active-short and active-long succeeded at24.52/28.80s, while passive nominal also failed. Learned long human contact6.1773s and100% engineering-threshold compliance do not replace task success; the other two contact ratios are NA. All physical alignment/filter/torque audits passed, no machine safety violation. This is cycle7, not current actorLR source12, and only three representative cases. Evaluator804667 finished normally; coordinator803220 continues with Impedance1952370. No final shared Tref or overall ranking. Evidence PUBLISHED_FIXED_CYCLE07_DIRECT_20261025.json.

## Direct actor-LR cycle8 improves training success; frozen comparison explains older stalls

Direct completed cycle8 at450,444 steps, with an immutable archive SHA256 8ca70658b93fd85999ef9723b8e231a8a9191413f9c3d737837cf2a08f424ffa. All30 registered conditions and terminal/model receipts were checked. Task14/30 and Strict13/30: passive3/10, active-short6/10, active-long4/10 strict. Short0600 has Task true but physical/Strict false and remains a strict failure. Mean return−10.163688 versus parent7−32.911626. Original cycle9 continues; no new intervention or early stop.

The82,500 new optimizer updates have first/last1000 q_loss means211.680/231.426 and logged next_q_values380.305/527.141; alpha means.14285/.06864. These logged quantities do not establish calibrated Q or healthy convergence. Full immutable-stage diagnosis awaits the remaining cycle8 archives. Training outcomes are from changing policies, not fixed-checkpoint acceptance or causal evidence for lower actorLR.

A separate0-update/0-physics analysis of nine archived fixed Direct trajectories (cycle3/7 and nominal across the same three prespecified cases) completed; report and plot inspected. Model/plan/fixture pairing and identical reward sources were checked, and nominal returns independently matched REWARD_AUDIT. Active nominal successes return+18.260/+20.365 (discounted+7.435/+9.592), versus cycle7 failures−34.221/−32.544 (discounted−19.118/−17.287). Thus reward favors these observed successful trajectories, without proving effective learning credit. Passive cycle7 has slightly better return than3 while placement error worsens87.63→198.01mm.

Cycle7 early public-filter Y residual means25–29mm/s and WBC scales~.91 accompany changed behavior; they do not isolate its cause. Last logged hand errors23.39/23.16/34.12mm exceed the12mm readiness condition in lift/release, despite maximum payload lift>0.14m. These pre-step diagnostics are necessary stage-readiness context, not a substitute for the independent final physical placement/release gate. No gate/filter/action changes are proposed or applied by this report. Evidence PUBLISHED_FIXED_DIRECT_AND_CYCLE08_20261025.json; raw fixed_direct_regression_v1 and DIRECT_CYCLE08_FIRST_REVIEW.json.

## Contact candidate first complete physical pass; comparator set-order correction

The first Direct passive55s replay completed all1,100,000 substeps with exact MJB, actor journal, terminal, trajectory, public filter, torque projection and substep arrays. Validator v1 then rejected full result JSON: its only additional difference was reversed hand/fr3_link7 ordering in stats.events.office_v5_corner_face.robot_parts, created as a Python set by the original evaluator. Both v1 processes exited and FAILURE.json is preserved.

The comparator now sorts only that documented set-valued field and rejects duplicates/non-string members; all other ordered lists and exact numeric checks remain. Four tests cover the boundary, including changed membership and task-event order. A read-only re-review passed the entire first episode. New contact_candidate_validation_v2 reuses that immutable episode and starts only the remaining11, using the same candidate runtime; coordinator2530701/first remaining child2535538, identities rechecked. No training deployment, learner updates or aggregate speedup claim. Evidence PUBLISHED_CONTACT_VALIDATION_RESUME_20261025.json.

Impedance also finished actorLR cycle8 at450,971 steps, Task17/30 Strict16/30 (passive0, short9, long7), versus parent7 Strict17/30. It continues original cycle9. This tempers Direct-only improvement; full all-interface cycle8 audit remains pending.

## All four actor-LR cycle8 archives complete

Four immutable checkpoints at450444/450971/451820/452526 steps were hash-verified, along with the full120 condition/terminal/model receipts. Task/Strict counts are14/13,17/16,15/15,17/16 out of30; returns−10.16369,−4.07799,−7.03086,−4.60589. Strict passive/short/long counts are3/6/4,0/9/7,0/10/5,0/9/7 (ten per category). Parent7 strict0/17/12/17 becomes13/16/15/16: improvement is heterogeneous. All four continue the already registered cycle9; original auditor969396 launched diagnosis child2614571, paired reviewer969397 awaits its output. This is training evidence, not healthy convergence or fixed-policy acceptance. Evidence PUBLISHED_ACTOR_LR_CYCLE08_TRAINING_20261025.json.

## Full cycle8 diagnostic and7→8 review complete

The original auditor and paired reviewer completed their reports and figures, now waiting for cycle9. Figures were visually inspected; all four networks remained unchanged and episode reward reconstruction passed. No diagnostic optimizer updates or physics were performed. Sampled Q means527.54/2091.51/775.46/8027.20 exceed the frozen-current-alpha bound in99.91/42.74/28.93/35.59% of samples. In-bag terminal MAE119.15/788.86/1402.85/6031.61; last1000 critic losses231.43/37502.40/19218.17/309861.91, all larger than cycle7. Direct task gains coexist with uncalibrated value estimates; parameter critics continue growing. Impedance loses long0000, VMC short0600; Admittance gains short0000/0600/0900. No health/convergence or causal actorLR conclusion. Continue original cycle9, no new intervention. The bound is specific to fixed policy/current alpha; terminal error can include hidden-clock aliasing. Compact evidence PUBLISHED_ACTOR_LR_CYCLE08_REVIEW_20261025.json.


## Cycle7/8 soft-target decomposition after actor-LR continuation

The finite read-only study `runs/soft_target_mixing_actor_lr_cycle08_v1` has finished and its process has exited. It reuses the validated soft-target diagnostic without modifying its source, on eight immutable complete-cycle checkpoints. This updates the earlier cycle0/1 evidence after the critic reset and actor-LR intervention; it performs zero optimizer updates and zero physics. Each snapshot samples4096 nonterminal replay rows plus all terminal rows and averages all ten distinct critic pairs. Network equality and exact zero terminal bootstrap passed for all eight snapshots.

| Interface | Discounted successor-Q mean,7→8 | Discounted entropy mean,7→8 | Predicted policy−replay pair-min Q,7→8 | Implied minimum RL weight fraction,8 |
|---|---:|---:|---:|---:|
| Direct | 378.905→528.135 | -1.005→-0.473 | 3.437→1.189 | 99.9268% |
| Impedance | 521.628→2070.421 | -0.593→-1.745 | 5.250→20.803 | 99.9756% |
| Admittance | 384.057→780.208 | -0.329→-0.787 | 2.447→4.638 | 100.0000% |
| Vmc | 4245.475→8046.319 | -8.942→-17.083 | 29.402→52.664 | 100.0000% |

Immediate nonterminal mean rewards remain negative, about−0.0035 to−0.0045. Positive targets are dominated by successor value estimates, not positive mean entropy bonuses. Policy/replay gaps are predictions from the same critics, not measured advantages or causal evidence of extrapolation. Different replay ages and separately sampled states prevent a controlled actorLR conclusion. No new implementation defect was established by rereading the published update and current trainer.

All four separately captured latest1000 cycle9 behavior transitions record mixing context0.2 exactly. This is actual recent behavior, distinct from implied weights computed on frozen historical replay. The CHEQ baseline remains20% raw RL plus80% nominal at these decisions; report it as a hybrid controller and keep plain SAC separate. Do not interpret training successes as learned standalone RL or healthy convergence. No uncertainty threshold was changed.

The contact-reading candidate now passes2/12 full55s trajectories (Direct passive and short), each1,100,000 substeps: model, journal, terminal, trajectory/filter/torque arrays and full result comparison pass the registered checks. The original v2 coordinator has advanced to Direct long; the candidate remains undeployed. All eight formal learners and original cycle9 observers continue. Current trial must finish and be reviewed before another intervention.

Compact evidence: `docs/PUBLISHED_ACTOR_LR_SOFT_TARGETS_20261025.json`; full registration, immutable source, eight reports and actual context captures are on the cluster at `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/soft_target_mixing_actor_lr_cycle08_v1`. GPU≥50% remains unproven, final convergence/SPT/ESN comparison incomplete.
