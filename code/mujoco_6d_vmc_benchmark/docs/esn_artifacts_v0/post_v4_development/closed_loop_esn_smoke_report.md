# Closed-loop ESN-v3 smoke report

## Question

Can a Fan Ye fast/slow ESN improve the residual controller by remembering the
previous safety-filtered slowdown/yield command as well as WBC state and error?

## Fair paired protocol

The current-state MLP and `fan_ye_closed_loop_esn` each received 102,400 PPO
steps at seed `20260961`, 8 parallel environments, the same post-V4
development-train fixtures, frozen `impulse_constrained` reward, PPO
hyperparameters, action contract, and safety adapter.  Validation used the
separate 9 development-validation fixtures.  V4 final was not accessed.

Only the ESN has fixed reservoir memory.  Its extra recurrence input is the
previous physical residual after safety filtering; it receives no raw action,
force, contact signal, rod state, obstacle geometry, future release, phase
label, fixture ID, reward, or evaluation diagnostic.

## Validity gates

| lane | task | no-rod | effective collision | hard torque limit |
|---|---:|---:|---:|---:|
| MLP | 9/9 | 9/9 | 8/9 | 0/9 |
| closed-loop ESN | 9/9 | 9/9 | 8/9 | 0/9 |

## Result

Values below are closed-loop ESN minus MLP; negative is favorable for all
listed physical metrics.

| metric | paired effect | interpretation |
|---|---:|---|
| recovery RMSE | +0.187 mm | worse |
| paired-offset RMSE | +1.193 mm | worse |
| peak paired offset | +1.862 mm | worse |
| rejoin latency | -8.9 ms | better |
| contact impulse | -0.294 N s | better |
| peak torque | +4.207 Nm | worse |
| peak jerk | +9.1 m/s^3 | worse |

This is not a promotion result.  The most likely mechanism is over-authority:
the ESN used a mean yield twist of `0.0602 m/s` versus MLP's `0.0166 m/s`,
which reduced impulse but amplified deviation and motor demand.  Retain it as
the negative `action-context ESN` ablation.  The current main candidate remains
ESN-v2, whose three independent seeds consistently improved recovery RMSE,
rejoin latency, and peak torque but did not yet establish full dominance in
impulse or jerk.
