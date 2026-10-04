# Proprioceptive reservoir control for disturbed pick-and-place: methods draft

Status: **working English manuscript material, not a submission-ready paper**.
Prepared on 2026-10-04 before final model selection and before opening the 24
held-out conditions. Equations below describe the implemented candidate family;
they do not assert that a particular variant has been selected or is superior.
This document changes no experiment, budget, environment, or success criterion.
Results, abstract claims, and the final contribution statement remain pending.

## Task and common execution system

We study simulated pick-and-place with a seven-joint arm and a frictional
parallel gripper. A common planner supplies the nominal route to a prescribed
table-corner destination. An edge omitted from the planner's map, a pillar,
a launched ball, a driven hand surrogate, and a driven rod introduce contact
along execution. There is no online obstacle sensing or replanning. The learned
compliance actor receives proprioceptive estimates and reference-relative
signals; it receives neither the map omission nor the disturbance schedule.
The common planner and task manager retain their existing reference and
transition logic. Prohibiting a task-stage input to the actor does not imply
that the entire robot execution system has no task manager.

The registered office-v6 geometry and materials are identical across methods.
MuJoCo 3.11.0 integrates at 50 microseconds; the low-level servo period is
4 milliseconds and the policy period is 40 milliseconds. Each evaluated
episode has a 55-second horizon, unless an unchanged numerical/physical abort
condition terminates it. Geometry, reference generation, actuator amplitude
and slew restrictions, and evaluation gates are frozen. Every completed or
aborted attempt is retained. Formal-resolution development rollouts are
development data, not held-out results merely because they use 50 microseconds.

The actuator interface records requested, clipped, and filtered actions and
actual execution separately. Imitation policies produce seven channels: a
bounded slowdown channel and six bounded compliance channels. Their deployment
uses the existing common action filter and WBC. A pure ESN means that no VMC
teacher is blended into its runtime actor; it does not mean removing the
common planner, observer, WBC, or actuator restrictions. Parameter-RL baselines
retain their distinct underlying classical control laws, described below.

## Proprioceptive multiscale reservoir

Let o_t denote the canonical 48-component observation. Indices in this paragraph
are zero-based and slice endpoints are excluded. The actor uses only 18
components. Its normalized estimated wrench and context are

\[
x_t=\operatorname{clip}(o_t[39:45]/[8,8,8,1,1,1],-12,12),
\]
\[
c_t=\operatorname{clip}([o_t[14:17]/0.06,\ o_t[26:29]/0.06,
o_t[45:48],\ o_t[20:23]/0.08],-4,4).
\]

The four context blocks are nominal linear velocity, linear velocity error,
path direction, and position error. Thus “proprioceptive” includes internally
available reference commands, not just raw physical measurements. Wrench is
observer-estimated, not the simulator's contact-force truth. Absolute time,
event time, stage labels, ball state, vision, and distance are not actor inputs.

With d_t=[x_t,|x_t|] and b_t=vec(d_t c_t^T), the 156-dimensional drive is
u_t=[d_t,b_t]. A 128-unit reservoir evolves as

\[
h_t=h_{t-1}+\alpha_t\odot
  [\tanh(W_{in}u_t+Wh_{t-1})-h_{t-1}],\qquad h_{-1}=0.
\]

The fixed random recurrent matrix has a Bernoulli sparsity mask with density
0.08 and is scaled to spectral radius 0.5 or 0.8. Input gains are selected
from 0.08, 0.25, and 0.6; the cross-feature columns of the random input matrix
are additionally divided by three. There are 32 units at each time constant
tau in {0.04, 0.12, 0.5, 2} seconds, with base leak
alpha_i=1-exp(-0.04/tau_i).

The registered contextual-leak variant uses a fixed Gaussian matrix G and

\[
\alpha_{t,i}=\min\{1,\alpha_i[0.05+1.95\sigma(
  \operatorname{clip}((Gc_t)_i+\log(0.95),-40,40))]\}.
\]

The ungated variant uses the base leak. In both variants all input, recurrent,
and gate matrices are fixed; only the final linear readout is fitted. Its
424 features are phi_t=[x_t,h_t,|x_t,h_t|,b_t,c_t]. The last 12, context-only
readout rows are identically zero, leaving 412×7=2,884 trainable coefficients.
The raw readout is phi_t^T B. Channel zero is clipped to [0,1], the other six
to [-1,1]. No learned hidden readout is included in this campaign's pure ESN.
Amendment 02, registered before fitting on 4 October at 04:20 UTC, adds a
separate ungated point-loss candidate with 128 fixed interaction features
`h_t * tanh(G_c c_t)`, where G_c has independent Gaussian entries with
standard deviation 1/sqrt(12), generated with seed+50000. These features
precede the zero context-only rows. The readout has 552 features, of which
540×7=3,780 coefficients are fitted. The 128 reservoir units, input fields,
and bounded action interface are unchanged. All 72 ESN/memoryless ridge
candidates passed an independent exact reconstruction of their fixed arrays.
This is a registered candidate, not yet the selected final method.

When wrench input is zero and the initial state is zero, arbitrary context
cannot generate an action. This equilibrium does not imply immediate zero
output after a loaded history. The tanh update with leaks in (0,1] keeps
reservoir components in [-1,1] from the zero initialization. Neither this
boundedness nor the selected spectral radius establishes the echo-state
property, passivity, or closed-loop physical safety.

## Demonstrations and fitting

Conditions have separate training, imitation-validation, development, and
final-test roles. An episode qualifies as a positive demonstration only if
it physically executes the full horizon and passes the unchanged task and
strict gates. All rejected executions remain in the collection ledger and
are charged to data-collection cost. Complete condition identities, rather
than adjacent frames, define the fitting/validation split. ESN, MLP, and RNN
receive the same qualifying trajectories within a learning cohort.

The first cohort used 18 training and 6 validation identities. After selection
of teacher09 on public development conditions, all 40 training/validation
identities were physically recollected. The unchanged eligibility rule yielded
20 training and 5 validation histories (34,375 frames), shared by all six
imitation families in Amendment 02. Each of three seeds contributes one
ESN, memoryless, matched MLP/RNN and ordinary MLP/RNN refit; all 18 enter the
same eight development conditions. Existing candidates remain eligible under
the original aggregate-seed selection rule. The new cohort changes both data
and features, so differences from earlier cohorts do not isolate the feature
mechanism. Teacher validation strict success decreased from 6/8 to 5/8 despite
placement increasing from 7/8 to 8/8; this is not uniformly better data.

The refit adds 12 ridge candidates per ESN/memoryless seed and one 4,000-update
point-loss fit per neural family/seed at the previously selected learning rate.
Cumulative ESN and memoryless counts are 60 and 36 candidates per seed;
pooling ordinary and matched networks gives 16 fits per MLP/RNN type per seed.
These are unequal computation costs, disclosed separately from shared teacher
collection, development simulation and RL interaction. No additional gate,
learning-rate or temporal-loss search is included in this amendment.

Labels are requested teacher actions from actual executed histories. Requested,
clipped, filtered, and executed quantities are retained for provenance and
replay; requesting an action does not imply that exactly that quantity reached
the robot. No counterfactual relabeling or development trajectory is silently
substituted for an executed training demonstration.

For each reservoir candidate, training features are divided by their
training-only standard deviations, floored at 0.005. Weighted ridge regression
fits the raw requested-action readout, with ridge strength 0.001 or 0.1.
Validation compares the bounded exported actor against requested labels.
The six radius/gain combinations and two ridge strengths give 12 candidates
per loss/seed. Independent histories reset the reservoir; validation does not
alter the fitted coefficients or training statistics.

The point-loss version minimizes weighted squared action error plus ridge
regularization. The temporal version also penalizes first differences of
action error (weight 0.25) and 16-step integrated action error (weight 0.1),
without crossing history boundaries. The integrated proxy uses per-channel
scales [0,0.64,0.64,0.64,0.48,0.48,0.48]; temporal terms are normalized by
their valid pair/window weight mass. It compares errors to the teacher, rather
than penalizing intentional teacher yielding. This supervised proxy is not
actual closed-loop position RMSE, contact impulse, energy, or a safety proof.

The memoryless control resets its reservoir before every observation and
refits its readout on the same data. It is not merely a test-time reset of a
model trained to rely on history. An isolated memory claim requires matching
the loss and feature/gate variant; independently selected family winners
with different variants support a method comparison, not that causal claim.

## Comparator construction and selection

All learned imitation architectures have hidden/reservoir width 128. Ordinary
bias-free MLP and Elman RNN controls learn their input and output matrices;
the RNN also learns its recurrence. They use the same 18 observation fields
with signed/absolute inputs, but not the engineered outer-product features.
Their bounded residual output uses tanh, whereas ESN and feature-matched
networks use clipped linear readouts. These are disclosed architectural
differences, not a parameter-matched comparison.

Feature-matched MLP/RNN controls share the reservoir family's input transforms,
time constants, and fixed contextual gate when present. They are initialized
from same-seed memoryless/ESN parents and learn the input and readout matrices;
the RNN additionally learns recurrence. Parent fitting costs are disclosed.
Each fit receives 4,000 gradient updates, with recurrent backpropagation
truncated to 64 steps. Update zero remains eligible for validation selection.
Smaller learning rates were registered after initial matched RNN fits selected
their unchanged parents. These follow-up closed-loop evaluations are still
pending completion. Neural point versions retain a first-difference weight
of 0.25, unlike the point ESN. Consequently these loss labels are not an
exact single-factor cross-architecture experiment.

The comparison also includes an enhanced VMC teacher, tuned admittance,
impedance and VMC controllers, and a zero-compliance-action nominal planner/WBC
reference. The latter still has feedback control and is not an open-loop robot.
Controller selection uses 12 candidates per family, a common two-condition
screen, and eight-condition confirmation of two finalists per family. The
two screening identities recur during confirmation and are not independent
additional test identities.

Five RL families are included: parameter adaptation of admittance, impedance,
and VMC, and direct policies with metric-based and task-based rewards. Their
office adaptation is distinct from historical primitive-to-office transfer.
The original RL checkpoint lineage, reward definitions, source revisions,
normalizers, and actual adaptation budgets accompany the results. Parameter
actions have dimensions 7, 5, and 7 for admittance, impedance, and VMC,
respectively. A shared recorded action7 does not erase this difference:
impedance parameters affect a separate Cartesian torque law and its common
residual-action record can be zero while the parameter policy still acts.

Before any learner reached the 49,500-step round, a common final boundary was
registered on 2026-10-04 at 03:24 UTC for all fifteen RL models. This time-capacity
amendment preserves the complete held-out comparison; it is independent of rewards
and task outcomes. Each finalist must use the naturally completed 49,500-stage
checkpoint (48,126–49,500 actual steps because a full episode is reserved before
dispatch). The original 80,000-step optimizer schedule remains unchanged. Immutable
coordinators may collect at most two additional episodes during graceful closure;
these later weights are ineligible, and their interactions are reported separately
as unused post-selection cost. Actual closure and all fifteen boundary receipts
are mandatory before freezing. This is a prospective policy, not a claim that
training or final evaluation has finished; see RESEARCH72_RL_FINAL_BOUNDARY_20261004.

For each imitation family, selection aggregates every registered training
seed and all eight development conditions. The frozen ranking prioritizes
strict count, task count, full horizons, worst penetration, mean stage-goal
RMSE, mean peak torque, and a deterministic lexical tie-break. Learning-rate
selection uses whole-identity validation before closed-loop selection.
There is no speed-maximization criterion or success eligibility filter that
removes unsuccessful baseline families. Equal width is not equal parameter
count, simulation exposure, gradient work, or computation. Those costs must
be reported separately, including failed teacher collection and parent fits.

## Evaluation protocol and exact outcome definitions

The public split has 32 training, 8 imitation-validation, and 8 development
conditions. A separate 24-condition final set remains sealed until all models,
evaluation source, and amendments are locked. Conditions vary ball speed
(1.305–1.595 m/s), hand start (3.5–4.5 s), rod start (12.5–13.5 s), hand stroke
(0.18–0.22 m), and rod stroke (0.2115–0.2585 m). Ball launch stays at 2 s.
Rod onset is at least one second after the hand's planned seven-second
press/hold/retract cycle. This is scheduled separation, not a guarantee that
physical contact with the hand has ended. Training seeds are 2026100301,
2026100302, and 2026100303.

The final plan contains 18 imitation policies (six families × three seeds),
15 RL policies (five families × three seeds), and five deterministic
controllers: 38 models × 24 conditions = 912 episodes. This is a planned
matrix, not a count of completed final results. Deterministic controllers
are not replicated as fake independent seed samples.

For the frozen planned-corner task, task success requires a completed full
horizon, lift exceeding 0.1 m, and the released payload remaining supported
at the destination at the end. At each 25 Hz check, XY error must be below
25 mm, vertical error below 15 mm, linear speed below 15 mm/s, and angular
speed below 0.15 rad/s. Finger opening must exceed 75 mm in total and no
force-bearing robot support may remain. All these placement predicates must
hold consecutively for at least 0.5 s as accumulated in 40 ms increments.
They are discrete placement checks, not continuous substep certification.

Strict success additionally requires no abort, maximum external penetration
at most 0.2 mm, and maximum unexpected-edge penetration at most 0.2 mm.
The original global-penetration abort at greater than 2 mm remains active.
Contact coverage and ball rebound are diagnostic in this planned-corner
protocol; they are not extra conjuncts in its strict-success definition.
Actuator amplitude/slew compliance is independently audited and reported;
we do not silently add a new gate to the existing strict label.

Strict success is the primary registered outcome, with task success, failure
stage, early termination, and unexecuted episodes reported beside it. To
characterize compliance, each of ball, hand, rod, pillar, and unknown edge
has contact exposure, contact P95 and peak force, force-magnitude time
integral, and contact duration. The force-magnitude integral is not signed net
impulse. Missing exposure is NA, not evidence of zero-force compliance.
Recovery uses the existing settled-rejoin diagnostic: error below 25 mm,
speed below 25 mm/s for 0.5 s, and subsequent path progress. Observation
windows and unrecovered, right-censored events are explicit. Neither rapid
motion nor a brief loss of contact alone proves recovery or successful yielding.

Stage-goal RMSE is the square root of the time-weighted mean squared
end-effector position error to the active task-stage goal at each physical
substep. Different methods switch stages at different times, so this is not
tracking error to one common clock-indexed trajectory. Task stalling can
produce a deceptively small value. Actual actuator peak torque and slew,
end-effector peak speed, and mechanical work are secondary motion/effort
measures. Short episodes are not pooled into full-55-second integral/RMSE
summaries without identifying their shorter exposure.

Paired differences use the common condition identities. The registered
exploratory uncertainty calculation independently resamples condition and
training-seed axes with 10,000 crossed-bootstrap replicates, analysis seed
2026100373, and 95% percentile intervals. Three seeds give limited evidence
about training variability. Multiple intervals are not multiplicity-adjusted;
we do not interpret them as simultaneous proof of superiority to every method.
Constant empirical intervals do not establish certainty on new conditions.
Strictly successful, jointly exposed pairs may support conditional contact
comparisons, but this outcome-conditioned subset cannot replace full-cohort
failures, missing outcomes, and exposure coverage. No post-hoc weighted
aggregate score selects a winner.

## Reproducibility and scope

Native Spark physics is preserved because local numerical-library changes
were observed to alter trajectories. Local fitting and the actual interpreter,
NumPy/PyTorch/JAX/MuJoCo versions are recorded independently. Immutable source,
configuration, condition, model, checkpoint, raw trace, and audit hashes link
each result. Independent physical-substep recomputation and actor/state replay
are required. RL replay must reload the frozen policy independently and cover
failures as well as successful episodes. A saved-state consistency check alone
does not establish resumed training or final actor parity.

The apparatus audit identifies a 1 kg, radius-60-mm ball, an 80 g freely moving
payload, a driven finite-mass hand surrogate, and a 0.65 kg rail-mounted rod.
The pillar is a particular low-friction small geometry. Drive-force caps
are not contact-force caps. The model also retains off-scene legacy mocap
objects. This experiment does not validate human biomechanics, hardware
collision safety, broad office-layout generalization, or real-world deployment.
At the current step size, an existing short numerical diagnostic found that
ball force peaks were not converged. Existing public trajectories also place
the first ball peak before the first available post-impact policy call.
Consequently that peak cannot be attributed solely to instantaneous ESN
feedback; common servo behavior and contact physics contribute.

Final videos will use the lexicographically first final condition for every
locked method and seed, three camera views, and the full actual duration,
with failures and short episodes labelled. Selection is not based on visual
success. The result section, complete cost table, final checkpoint identities,
statistical comparisons, and those actual videos remain to be produced.

## Evidence and source map for manuscript editing

The verified predecessor source snapshot is at
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f6d22ffffa74e33e1e28dc8e49695cd22c3a7262/`.
Source paths below are relative to its `code/mujoco_6d_vmc_benchmark/` directory.
The runtime-specific archived sources and hashes in each execution record,
rather than a later checkout, remain authoritative for past experiments.

| Manuscript content | Implementation or evidence |
|---|---|
| Reservoir, features, gate, bounded readout | `scripts/office_vmc_memory_esn_20260927.py`; `tools/train_paper_context_esn_20261003.py` |
| Ordinary and matched controls | `scripts/office_mlp_rnn_20261002.py`; `tools/train_office_mlp_rnn_20261002.py`; `tools/train_paper_feature_matched_network_20261003.py` |
| Data identity, candidate budgets and selection | `tools/research72_protocol_20261003.py`; `tools/research72_build_demonstrations_20261003.py`; `tools/research72_train_models_20261003.py`; `tools/research72_select_learning_20261003.py`; `tools/research72_select_controllers_20261003.py` |
| Actual task/strict definitions | `scripts/validate_office_apparatus_v5_20260917.py`, placement checks and final planned-corner/edge result branches |
| Apparatus, statistics, limits | `docs/RESEARCH72_APPARATUS_SCOPE_20261004.md`; `docs/RESEARCH72_ANALYSIS_PLAN_20261003.md`; `docs/RESEARCH72_NUMERICAL_DIAGNOSTIC_20261003.md`; `docs/RESEARCH72_IMPACT_TIMING_20261003.md` |
| Prior work and claim restrictions | `docs/RESEARCH72_METHOD_POSITIONING_20261003.md`, including actual reading scope rather than invented citations |

The experiment evidence root is
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`.
Protocol SHA256: `5457d85726e2a88067e153464b7e50dbc9fcd173b89a9fc5da2da096c0891732`.
Formal MJB SHA256: `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`.
The draft must be reconciled with the final lock and complete evidence before
it can be used as submitted manuscript text. An ESN advantage or a new method
contribution cannot be inferred from the presence of this draft.
