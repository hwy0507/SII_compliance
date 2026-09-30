# Reward interface audit — 2026-09-30

Scope: read-only inspection of existing runtime; new pure reward module and tests only.
Original running trainer and environment files were not edited. This report belongs
to the baseline branch change batch managed by the parent agent.

## Relevant server paths

- Existing continuation trainer:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/train_official_simba_v2_office_resume_20260929.py
- Existing queue environment and obsolete reward:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/train_simba_v2_office_20260927.py
- Validator:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/validate_office_apparatus_v5_20260917.py
- Physics executor:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/audited_velocity_env.py
- Task definition:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/office_task_v4_20260917.py
- Runtime task patch:
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/office_recovery_scene_v4_20260918.py
  /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/office_recovery_scene_v5_20260918.py
- New reward:
  /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/rewards.py
- Tests:
  /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/test_rewards.py

## Findings requiring correction

1. The old reward's torque proxy is NOT actual motor torque.
   obs[32:39] contains JointLoadObserver.filtered, an external joint-load estimate.
   Correct signal for the new peak reward is d.qfrc_actuator[:7], after mj_step.
   The validator already tracks this in world_step. Use env.torque_limits,
   not a duplicated array: nominal hardware limits are [87,87,87,87,12,12,12] Nm.

2. The reference is a stage waypoint, not a time-indexed continuous trajectory.
   PickPlaceTask.sample returns goals[index], a constant pose, plus zero feedforward.
   ScaledReferenceWBC creates the bounded feedback velocity. The old reward's sigma
   counter does not move this reference. Do not claim sigma-based trajectory
   following or compare these errors with a different continuous reference.

3. Timing is 25 Hz RL, 250 Hz torque controller, and much faster MuJoCo physics.
   RL_DT=0.04 s; CONTROL_DT=0.004 s. Physics steps are explicit model.opt.timestep.
   audited_velocity_env.py calls substep_observer immediately after each mj_step
   and internal contact audit. Aggregate actual error dt, force, peak torque,
   and speed there; avoid reading only the final 25 Hz sample.

4. The old queue final next_obs repeats the preceding observation.
   OfficeDirectActionEnv.step assigns next_obs=self.obs when terminal is published.
   The new queue should publish a genuine final observation plus final interval
   aggregates, so terminal error/replay state are not stale.

5. Current terminal conditions are fixed duration and penetration >2 mm.
   Strict physical acceptance remains penetration <0.2 mm. A result can complete
   the simulation yet be physically invalid. Do not equate stage retreat with
   task success.

6. Existing strict_placement_success combines placement_complete, physical_valid,
   cup_valid, and release_supported. placement_complete additionally requires
   stable tabletop support >=0.5 s, supported release, lift >0.1 m, final hand
   position <15 mm from retreat goal, and open fingers >75 mm total. Task stages
   have separate position/orientation/speed/0.2s-hold gates. Preserve their actual
   implementation; no success inferred solely from the stage name.

7. Actor is causal observation48: q7, dq7, nominal twist6, pose error6,
   twist error6, external joint load7, estimated tool wrench6, path direction3.
   World/task reward metadata must travel separately, not in the observation.
   The old policy mapped tanh speed to [0.2,1], then to slowdown. The NEW root
   adapter instead uses the canonical shared slowdown + six residual interface
   directly, exactly matching the common ESN/VMC executor. Keep original tanh
   action in replay; do not retain the old RL-specific 0.30 authority gate.

## Recommended potential

Use a bounded [0,1] function of the existing ordered task route:
sum of completed segment/milestone weights plus fractional progress on the
current segment. Use fixed route geometry/weights from episode initialization,
not the reference change itself as a separately rewarded event. Duplicate
waypoints (grasp and release) require explicit milestone weights; they must not
divide by zero. Stage index is monotonic. Intermediate progress may decrease
when the arm moves back, so no clipped positive-only differences.

Use r_progress = gamma * Phi_next - Phi_current with the SAME gamma as the
learner; Phi_next=0 at every true terminal including finite-horizon timeout.
The discounted sum then telescopes to -Phi_initial, independently of repeated
approaches, waypoint switches, or loop motions, for complete episodes.
Do not reset the potential on a nonterminal waypoint change.

## New module semantics

OfficeReward accepts caller-supplied physical interval aggregates.
error_cost must be the unbounded sum of physical dt/T * (position_error/e_scale)^2.
There is no contact gate or error clipping. Peak torque uses the actual
normalized interval peak, updating an episode maximum. The squared increments
telescope only without discount. Both facts are deliberately explicit.

requested_action must be the normalized action7 BEFORE common safety/filter.
Default previous action on reset is zero7 (canonical zero slowdown and zero
residual). The smooth cost is the squared difference; no dt factor. Common
filter before/after arrays must additionally be logged by the environment.

Modes:
- office_task: PRIMARY task-centric baseline, strict success +20/failure -20,
  dense global potential (5), and elapsed time (1). It is an explicit Office
  adaptation, not a reward invented by the SimbaV2 paper.
- metric: the SAME task terms plus integral error (4), peak actual torque (8),
  and weak requested-action smoothing (0.005).
- task_only: sparse task-only diagnostic; NOT the main baseline because its
  exploration signal can be unnecessarily weak. No causal progress information
  is withheld from office_task merely to make metric look better.
Weights are serialized through RewardConfig.to_dict and should be frozen in
the experiment protocol or tuned only on training/development conditions.

## Early-failure anti-evasion

The module charges a conservative discounted bound on ALL remaining avoidable
negative costs at an early failed terminal: error, elapsed time, smoothness,
and remaining peak-torque budget. It uses the geometric sum of future gamma
powers, including a possible fractional last policy interval. At horizon
timeout the remaining-horizon charge is exactly zero.

The bound assumes position error <=3 m, normalized actuator torque <=1, and
normalized requested actions in [-1,1]^7. These must be checked against the
physical model and executed signals before formal training. The implementation
raises a contract error when measured support is violated; it never silently
clips the true error. The position bound must be justified from robot reach and
waypoint workspace, not chosen from test results. This conservative penalty is
an explicit reward-design choice and can be large for very early failure.
It is not the exact unknown counterfactual return.

Under those support bounds and a complete terminal-zero potential, failing
early cannot produce a higher return merely by skipping future bounded costs
than continuing to an eventual failed terminal. It does not mean every
successful policy has positive return or guarantee easy exploration.

## Validation

Command:
cd /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src
python3 -m unittest test_rewards -v

15 tests passed:
actual torque peaks/reset, physical partition independence, uncapped squared
error, discounted potential telescoping with waypoint-like changes, worst-case
and randomized early-failure dominance, explicit strict-success labels,
no post-success actions, normalized requested-action smoothing, timeout
continuation zero, declared support checks, fractional-horizon accounting, office_task dense progress/no metric terms,
office_task early-failure time-cost anti-evasion, and stopping only the time
term after verified placement while retaining final strict-success evaluation.

The pure-module tests do not validate simulator integration; a short full
substep rollout must confirm action conversion, interval boundaries, stage
transition timing, exact elapsed-time sums, final observation freshness, and
agreement between logged raw peak torque and the reward accumulator.

## Integration update

The parent selected current /home/arm1/SII_compliance_baseline code for the new
adapter, preserving its current strict_success gate including required contact
and bounce validity, rather than silently using the older runtime gate above.
Report strict_success AND physical task placement success separately. The old
runtime findings above document the historical implementation, not proof that
all old behavior is retained in the new protocol. Record final commit hashes.

## Physical integration validation completed

Command:
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/arm1/vmc_mujoco_runtime/simba_v2_venv/bin/python /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/test_interval.py --output /home/arm1/vmc_mujoco_runtime/reward_study_20260930/reward_interval_smoke_64s

Zero canonical action; variant -2; seed 2026093001; all events; 6.4 s smoke,
not a task-performance trial. No policy updates. 160 RL intervals / 64000 physics
substeps. Error integral = 0.24821362940844335; independently reconstructed
from evaluator RMSE = 0.24821362947257858 (relative difference 2.58e-10).
All per-joint actual torque peaks agree within float32 logging precision.
Largest torque = 33.1948 Nm; sum of peak-square increments and final normalized
peak square both 0.20293901847420812. Final observation finite, changed from
previous observation by norm 0.04457 (not stale). No simulator abort.

Machine-readable result:
/home/arm1/vmc_mujoco_runtime/reward_study_20260930/reward_interval_smoke_64s/VALIDATION.json

The reward now accepts task_complete_before_interval. When true, ONLY the time
cost stops; error, torque, smoothing and progress remain active. The root adapter
must populate it from existing strict object-placement/safety gates at the prior
boundary, not merely the stage label. Final success still uses the complete
fixed-horizon evaluator's strict gate.

Trainer review: normalizers consume each preceding transition once; raw replay
is preserved and copied before wrapper normalization. Pending last transition
is saved in runner_state and exact episode-boundary resume has now been tested
with the real official agent and deterministic fake dynamics (details below). Main comparisons must use equal transition/update budgets, with wall
time and physical simulated seconds also reported. A common wall-time cutoff
alone can give different sample budgets when rewards cause different early
failure rates. Official running reward normalization changes scale during
training, so raw-reward potential/peak algebra must not be advertised as exact
identities for the changing normalized training return.

## Exact episode-boundary resume implementation and validation

train.py now accepts --resume CHECKPOINT and keeps --steps as the ORIGINAL
total budget; extending it implicitly would alter the original learning-rate
schedule and is rejected. Use a new --output directory. Resume checks seed,
reward config, UTD, timestep, warmup, fixture cycle and runtime source hashes.

Restores network/optimizer states, both official normalizers, JAX RNG, replay
data/ring count/sampling RNG, exploration RNG, episode fixture index, and the
pending terminal transition exactly once. Reward state resets at the next
episode as in uninterrupted execution. Mid-episode checkpoints are explicitly
rejected because the live MuJoCo state was not saved. They remain usable for
evaluation, but cannot be silently reset and called exact continuation.

Existing fixed-step checkpoints remain. New checkpoint_boundary_N checkpoints
are saved at the first episode end at or beyond each checkpoint interval.
The optional --stop-after-step records an early checkpoint without changing
the planned total-step learning-rate schedule.

Test source:
/home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/test_resume.py

A real official agent, including actual optimizer updates, ran 4 uninterrupted
steps versus 2 steps + save/reload + 2 steps in deterministic fake dynamics.
All 111 parameter/optimizer leaves are elementwise identical. Actions, rewards,
replay, normalizers and RNGs match; pending terminal consumed once; attempting
mid-episode resume raises the intended error. This validates software state,
not physical MuJoCo bitwise reproducibility across device/runtime changes.

Results:
/home/arm1/vmc_mujoco_runtime/reward_study_20260930/resume_invariant_01/VALIDATION.json

The parent subsequently corrected training fixture variants to [-4,-3,-2,-1]
after initial-geometry audit rejected old variants 3/4. Both fixture generator,
PROTOCOL and resume run_definition record the corrected list.
