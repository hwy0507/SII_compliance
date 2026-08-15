# Independent ESN / VMC controller protocol

Date: 2026-08-15

## Decision

The main method is **not ESN+VMC**.  VMC and ESN are separate controller
families.  Previously completed experiments in which an ESN/PPO actor adjusted
VMC spring or return-drive parameters remain reproducible exploratory negative
results, but they are not the proposed method and are excluded from the new
overnight campaign.

## Controller ladder

| Method | Command path | Role |
|---|---|---|
| fixed VMC | fixed WBC -> six virtual springs/carriage -> Panda torque | independent physics baseline |
| current-state MLP | fixed WBC -> 20-D current input -> bounded velocity residual -> shared safety -> Panda torque | memory-free learned baseline |
| Fan Ye ESN | fixed WBC -> 20-D input + fixed 64-D reservoir -> bounded velocity residual -> shared safety -> Panda torque | proposed temporal controller |

The learned action is

\[
a_t=[s_t,\Delta \dot{x}^{yield}_t],
\]

where the applied WBC scale is bounded to \([0.2,1]\) and the six-dimensional
Cartesian yield twist is amplitude- and slew-limited before damped-pseudoinverse
mapping.  Joint velocity, joint acceleration, torque feasibility, torque
amplitude, and torque slew are then enforced by the same adapter for MLP and
ESN.  The all-zero policy action is exactly the unmodified fixed-WBC command.

The direct controller contains no `SixDVirtualCarriage`, `kappa`, spring force,
virtual-carriage state, or return-drive state.  It therefore cannot silently
fall back to VMC.

## Fairness contract

MLP and ESN must share:

- Panda model, MuJoCo scene, rod fixtures, fixed WBC, torque backend, and safety
  bounds;
- seven-dimensional output space and action filter;
- PPO network, reward profile, seed, rollout length, and training budget;
- matched rod/no-rod validation and failure gates.

They differ only in whether the policy receives the fixed Fan Ye reservoir
state.  The deployment input remains `q(7), qdot(7), WBC task twist(6)`; contact,
force, rod state, obstacle geometry, future release time, and fixture identity
are excluded.  Physical contact and release labels may be used only in the
training reward and offline evaluation.

The V4 final holdout remains frozen and is not used for training, reward tuning,
checkpoint selection, or the present smoke tests.

## First server smoke tests

Server environment:

- 20 logical CPUs;
- `/home/arm1/vmc_mujoco_runtime/.venv/bin/python`;
- official MuJoCo Menagerie Franka Panda model;
- post-V4 development validation split, nine fixtures.

### Neutral fixed-WBC execution

The all-zero direct action completed 9/9 rod tasks and 9/9 matched no-rod tasks,
with no torque hard-limit event.  Eight of nine fixtures met the pre-registered
effective-collision force/impulse gate.

| Metric | Neutral fixed WBC |
|---|---:|
| recovery RMSE | 8.570 mm |
| rejoin latency | 0.619 s |
| contact impulse | 3.081 N s |
| peak contact force | 37.149 N |
| peak jerk | 950.257 m/s^3 |
| peak torque | 31.409 Nm |

### 8,192-step paired PPO interface smoke

This run is a pipeline test, not a scientific convergence result.

| Metric | Current MLP | Fan Ye ESN |
|---|---:|---:|
| rod task success | 9/9 | 8/9 |
| matched no-rod success | 9/9 | 9/9 |
| effective collision | 8/9 | 6/9 |
| recovery RMSE | 7.754 mm | 10.087 mm |
| rejoin latency | 1.268 s | 0.837 s |
| contact impulse | 2.633 N s | 2.461 N s |
| peak jerk | 1004.407 m/s^3 | 997.378 m/s^3 |
| torque hard limit | 0/9 | 0/9 |

Both observation contracts, parallel training, checkpoint creation,
VecNormalize save/load, deterministic policy reload, matched evaluation JSON,
and finite-state safety gates ran successfully.  The short ESN run is not yet
competitive and must not be reported as a positive result.

## Smoke gate before overnight training

Before an overnight run is accepted, both MLP and ESN lanes must pass:

1. finite observations, actions, MuJoCo state, rewards, and torque commands;
2. zero torque hard-limit events in validation;
3. checkpoint/normalizer save-load-resume integrity;
4. complete matched rod/no-rod evaluation JSON;
5. no use of VMC objects in the direct execution path;
6. identical paired configurations except observation memory mode;
7. no access to the frozen V4 final holdout.

## Authority-gated 25k paired smoke

The first 100k smoke without an authority gate was rejected: both learned
actors could spend residual authority before contact and reduce the measured
collision below the effective-collision gate.  The corrected safety layer
smoothly opens residual authority from 0 to 1 as the measured WBC Cartesian
tracking departure grows from 4 mm to 12 mm.  The gate is a deployable safety
filter, not a collision or phase oracle, and is applied identically to MLP and
ESN.

With the same seed (20260831), reward, eight-environment budget, and train
fixtures, the 25k paired smoke produced:

| Metric | Neutral WBC | Current MLP | Fan Ye ESN |
|---|---:|---:|---:|
| rod task success | 9/9 | 9/9 | 9/9 |
| matched no-rod success | 9/9 | 9/9 | 9/9 |
| effective collision | 8/9 | 8/9 | 8/9 |
| recovery RMSE | 8.570 mm | 7.775 mm | **5.973 mm** |
| rejoin latency | 0.619 s | 0.623 s | **0.406 s** |
| contact impulse | 3.081 N s | 3.038 N s | **2.969 N s** |
| peak jerk | 950.3 m/s^3 | 951.9 m/s^3 | 972.2 m/s^3 |
| peak torque | 31.41 Nm | 31.64 Nm | 32.46 Nm |
| torque hard limit | 0/9 | 0/9 | 0/9 |

The ESN improvement over neutral WBC is 30.3% lower recovery RMSE, 34.5%
shorter rejoin latency, and 3.7% lower impulse.  Relative to the matched MLP,
the ESN is 23.2% lower in recovery RMSE and 34.9% faster to rejoin.  Jerk and
peak torque are slightly higher, so this is a Pareto improvement in recovery
and impulse, not an all-metric domination claim.  The complete JSON artifacts
are kept next to this protocol note.

The next smoke stage is a paired 100k-step run with the authority gate and
identical seed, followed by at least five independent seeds.  Only after those
gates pass should multi-profile overnight training start.

## Resumable overnight campaign

`scripts/run_independent_esn_overnight.py` launches a paired current-MLP and
Fan-Ye-ESN lane, each using eight environments and a dedicated ten-CPU set.  It
records an immutable artifact-hash manifest before training, pairs every seed
and reward profile, saves model/normalizer checkpoints every 100k steps, runs
the matched validation after each pair, and resumes safely by skipping only
fully evaluated pairs.

The planned first overnight pass is six seeds × three reward profiles × two
million PPO steps per lane.  The measured server throughput (about 0.85--0.90k
vector steps/s per lane) yields roughly 12 hours of paired training plus short
validation intervals.  Each result is accepted only when both controllers
retain all task/no-rod successes, at least eight valid collisions under the
predeclared fixture gate, and zero torque hard-limit events.  Pareto selection
then uses recovery RMSE, rejoin latency, impulse, jerk, and torque; no single
late checkpoint is assumed to be universally best.
