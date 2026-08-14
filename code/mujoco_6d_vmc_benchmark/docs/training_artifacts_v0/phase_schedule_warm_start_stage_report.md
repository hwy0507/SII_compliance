# Phase-Scheduled Six-Dimensional Stiffness Warm-Start: Stage Result

## What was trained

A Cross-Entropy Method (CEM) optimized a two-phase 12-D schedule:

```text
kappa_contact  = [x, y, z, roll, pitch, yaw]
kappa_recovery = [x, y, z, roll, pitch, yaw]
```

Training used four high-force train scenes selected from the completed static
manifest (`peak rod--hand force >= 15 N`) and retained the full paired
rod/no-rod task, effective-collision, stable-rejoin, lift/hold, and no-hard-
torque-limit gates. It is a dynamic parameter warm-start, **not** an online
state-feedback RL policy.

The first CEM run revealed a weak-collision scene (peak force `7.61 N`) in the
scene selector; its candidates were correctly rejected as `3/4` valid. The
selector was then corrected to use only effective static collisions.

## Frozen schedule selected after constrained CEM

The final run constrained each recovery stiffness to be no lower than its
corresponding contact-stage stiffness. Its train result was `4/4` valid.

| Channel | x | y | z | roll | pitch | yaw |
|---|---:|---:|---:|---:|---:|---:|
| Contact kappa | 27.58 | 52.55 | 48.70 | 35.86 | 40.72 | 34.77 |
| Recovery kappa | 45.60 | 55.61 | 48.70 | 54.66 | 62.54 | 61.58 |

This is physically interpretable: the selected schedule permits more x-axis
yield at contact, keeps y/z support, and tightens several translational and
rotational channels after physical release.

## Held-out validation

The frozen schedule was evaluated on four **validation** scenes that were not
used by CEM. All baseline and schedule runs passed task and effective-collision
gates (`4/4`). The baseline was constant six-channel `kappa=[35]*6`.

| Metric, validation mean | Constant kappa | Phase schedule | Change |
|---|---:|---:|---:|
| Valid tasks | 4 / 4 | 4 / 4 | — |
| Peak paired offset | 23.19 mm | 22.68 mm | **-2.2%** |
| Recovery RMSE | 2.62 mm | 2.68 mm | +2.2% |
| Release-to-rejoin latency | 0.390 s | 0.395 s | +1.3% |
| Peak applied torque | 30.21 Nm | 30.23 Nm | +0.04% |
| Peak physical contact force | 57.50 N | 57.82 N | +0.6% |

The contact-force levels (`46.8–78.7 N`) confirm that the small offset change
is not caused by selecting grazing contacts.

## Stage conclusion

This is a valid but **not yet performance-positive** warm-start result. The
phase schedule preserves task success and makes a small paired-offset
improvement, but it does not improve recovery RMSE, rejoin latency, or torque.
It therefore must not be reported as a VMC improvement over constant kappa.

The result is still useful: it isolates the limitation of a schedule that only
knows a predeclared release time. Further progress requires a low-rate,
state-feedback policy whose 51-D observation uses end-effector error/twist,
joint state, carriage state, torque ratio, and prior action, while excluding
MuJoCo-only rod/contact truth. The CEM elite distribution provides the safe
initial action/stiffness region for that next RL stage.
