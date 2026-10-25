# Published baseline learning diagnostics

This is an early snapshot of the ongoing CHEQ adaptation, not a convergence
claim. The four policies have not yet completed the first balanced30-condition
cycle. Logged steps include approximately10000 recovered real transitions each;
optimizers restarted after the documented first-attempt failure.

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
not replace an independent filter replay. A second instrumented episode is
running in `runs/interim_impedance_human_audited_v1` on the first registered
active-long person condition, selected before its evaluation result. Its
purpose is checking actual-contact metric coverage, not a final policy ranking.

Source is frozen separately in `runtime/evaluation_audit_v2`; the running
training runtime remains `source_train04`.

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
