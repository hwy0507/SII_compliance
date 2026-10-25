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
