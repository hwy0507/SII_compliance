# Online parameter RL on the four video-derived primitive scenes

This is a new development protocol added by the user during the existing five-hour
2026-10-02 session (07:36:31–12:36:31 UTC). It does not change the final environment
or WBC work owned by another agent. Computation and artifacts stay on Spark.

## What is implemented

A pinned official SimbaV2 actor-critic selects controller parameters at 25 Hz.
Observation stays canonical/proprioceptive 48D: joint position/velocity, nominal
twist, pose/twist error, estimated joint load/wrench and nominal path direction.
The policy receives no obstacle pose, contact truth, scene ID, stage or clock.
The policy has 7 actions for admittance, 5 for impedance, and 7 for VMC. These
are parameter requests; they are not the seven Cartesian residual action channels.

The existing controller families from main commit
`b75ef8e177a6bd149786b74279704ea8caaa0b92` are copied verbatim into the scoped vendor
directory with per-file hashes and provenance. Their helpers implement:

- Admittance: implicit virtual M-D-K dynamics and shifted Cartesian WBC reference.
- Impedance: bounded moving equilibrium driven by the shared nominal twist,
  with Cartesian spring/damper wrench mapped through J transpose and the
  original motor torque projection and slew limiter. Mass/inertia are fixed
  damping parameters, so there are five independent action axes.
- VMC: the existing saturated six-channel virtual dynamics and stable velocity/
  displacement readout; seven grouped stiffness, damping and readout axes.

The legacy table-corner source has a joint-waypoint nominal controller whose
command method ignores Cartesian target arguments. Its admittance compatibility
map therefore converts the virtual reference state into a twist residual:
`virtual_twist + diag(5,5,5,3,3,3) * offset`. It leaves the nominal controller
unchanged. Both fixed-prior and learned-parameter comparisons use this same map.
The first smoke snapshot predates this compatibility correction: its admittance
table-corner action was zero despite nonzero internal virtual displacement.
That failure is retained and excluded from final paired claims.

## Shared BO-derived prior

The user explicitly chose one scene-independent prior per controller, instead
of routing priors by scene category. We verified the historical locked bank:
`1cafd43556f754df0595027c6aa1a358520038bbd5a3f742b9ef3b2a2f287945`.
For each method, its three category-specific decoded vectors are aggregated by
componentwise geometric mean. All four scenes use this same vector.

This is a **transferred BO-derived prior**, not a newly optimized BO solution for
these four video scenes. The old three-domain BO performance is not pooled with
the present experiments. The original bank and exact decoded vectors are in
`BO_LOCKED_SOURCE.json` and `PRIORS.json`.

Each action requests `theta_target = theta_prior * exp(log(2) * action)`, clipped
to the original BO search bounds. The repository's `action_to_kappa` is reused
in padded six-vector blocks with a maximum log rate of 1.6/s (0.064 per 40 ms).
Padding is removed before execution; impedance still has exactly five policy
actions. Controller internal state is never reset on parameter updates.

## Energy budget and its limits

A controller-side tank begins at 0.8 J, with [0.08, 1.2] J limits. It debits
positive changes in the local stored-energy model caused by parameter changes.
A log-space line search contracts a request if insufficient energy is available.

Admittance storage uses the diagonal virtual kinetic plus spring energy.
Impedance uses its bounded local spring error (mass is not a physical inertia
state). VMC uses the potential corresponding to its saturated spring,
`sum(sigma^2 / K * log(cosh(K*x/sigma)))`, plus virtual kinetic energy.
A conservative fraction (0.2) of relative virtual damping power recharges the tank.
The entire energy ledger, accepted parameters, scale, virtual state and requests
are saved at each policy step.

This is an explicit local accounting safeguard, **not a global passivity,
Lyapunov or closed-loop stability certificate**. Moving nominal references,
VMC readout gain, saturation/discretization and robot execution are outside the
storage-change guarantee. The existing `EnergyBudgetSafety` constrains a
specific translational return-drive increment and was inspected, not misleadingly
reused as a general proof for all parameter actions. No paper-specific theorem
or CHEQ reproduction is claimed. The literature list provided by the user has
not yet been verified from full texts and is not cited as implemented evidence.

## Budget and comparisons

Registered parameter experiment: three controller families, seed 75001, metric
reward, target 60,000 interactions each, UTD 2, 5,000-step near-prior warmup,
gamma 0.9995. Same official observation/reward normalization and 4-scene balanced
replay as the directly acting SimbaV2 campaign. Training ends by 11:40 UTC,
finishing its current finite episode. The common completed periodic checkpoint
is selected by available step budget, never by validation/test score.

Reward physical/error/task terms are unchanged. Its smoothness term sees the
actual executed Cartesian action7 after the parameter controller; impedance
has zero Cartesian action7 and acts through torque. Thus reward values are not
used to rank controller families; physical outcomes and raw metrics are reported.

The scope addition reduced the preregistered heldout test to indices 0,1,2 per
scene, twelve physical conditions per model, before any test was run. The
amendment is saved on Spark and is based on the added work/time budget.
Every learned parameter controller is paired with its own fixed-prior controller
using identical code, tank, physics, initialization, task gates and actuator limits.
The earlier six-candidate classical search is a separate controller implementation,
not silently relabeled as the fixed BO-derived comparator.

Task, physical numeric check, intended-contact exposure, their conjunction,
RMSE, peak actual torque, peak end-effector speed and duration are retained
including failures. The physical numeric check means <=0.2 mm external
penetration and finite peak torque; it is not a full contact-validity certificate.
The four source scenes retain their original dt (ball/corner 1e-4, push 5e-5,
legacy table 2.5e-4), task supervisor and safety configuration. These are mixed
development fixtures, not a new uniform formal-dt result.

## Artifact pointers

All paths below are on `arm1@192.168.31.70`.

- Experiment root: `/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/`
- Immutable controller/trainer: `.../parameter_rl/frozen_train01/`
- Initial controller compatibility checks: `.../parameter_rl/fixed_prior_smoke01/`
- Corrected interface/zero-action check: `.../parameter_rl/interface_smoke02/`
- Adversarial shield check: `.../parameter_rl/SHIELD_AUDIT.json`
- Original videos/fixture definitions/source snapshots: parent study root.
- Exact original/amended budgets: parent `BUDGET.json`,
  `FINAL_EVALUATION_PROTOCOL.json`, `EVALUATION_BUDGET_AMENDMENT01.json`.

At this documentation checkpoint, interface validation is in progress.
Do not interpret registered budgets or source code as completed training.
Final outcome tables and checkpoint identities will be added after actual runs.

## Latest implementation check (2026-10-02 09 UTC)

User explicitly selected one shared BO-derived prior per controller across four scenes. The current immutable snapshot is parameter_rl/frozen_train02. A 5D impedance pilot completed 750 real interactions and 1470 gradient updates; its requested 64-step threshold finished the current episode by design. The first main admittance run (seed75001, target60000) is running. The failed first pilot rejected an extra config metadata key before simulation. The corrected wrapper retains action dimension in checkpoint metadata and excludes it from upstream SimbaV2Config.

Original direct RL hit a CLI parsing failure at step21525: a negative scientific-notation scalar was mistaken for an option. Adapter02 uses --key=value. Recovery02 restores checkpoint20000/replay/RNG, skips the unfinished episode and explicitly is not exact environment-state resumption. Both rewards are again advancing. All provenance is under /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002.

Main7cd5f4b was reviewed after the user supplied the final environment. The separate office_baseline_bridge_20261002/evaluate.py compiles four checked policy seams against that immutable main source, consumes its exact canonical48 and records the executed evaluator hash. Only import/compile was checked so far; no office transfer or physical equivalence is claimed. The comparison proposal is docs/FINAL_ENV_BASELINE_PROTOCOL_20261002.md.
