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

The next smoke stage is a paired 100k-step run with identical seed and balanced
reward, followed by validation and targeted reward-profile checks.  Only after
these gates pass should multi-seed, multi-profile overnight training start.
