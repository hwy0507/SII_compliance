# Independent ESN-v2 Smoke Results

Date: 2026-08-16

## Scope

Both experiments use only the isolated post-V4 development manifest. Each lane
uses eight parallel environments and reaches 102,400 PPO steps after rollout
alignment. These are single-seed smoke results, not final multi-seed evidence.
The V4 final holdout is not used.

MLP and ESN-v2 share the 32-D deployable WBC/current-error input, action space,
PPO budget, fixture manifest, and safety adapter. ESN-v2 additionally receives
fixed 64-D fast and 64-D slow Fan Ye reservoir states selected from a
development-train-only 32-D CR/ESPI screen.

## Balanced Smoke

With seed `20260850`, both MLP and ESN-v2 pass 9/9 task success, 9/9 matched
no-rod success, 8/9 effective collisions, and zero hard torque limits.

| Mean over nine validation fixtures | MLP | ESN-v2 | ESN-v2 minus MLP |
|---|---:|---:|---:|
| Recovery RMSE | 4.226 mm | 2.821 mm | -1.405 mm |
| Rejoin latency | 174 ms | 28 ms | -147 ms |
| Contact impulse | 3.440 N s | 3.958 N s | +0.518 N s |
| Peak jerk | 955.7 m/s^3 | 962.6 m/s^3 | +7.0 m/s^3 |
| Peak torque | 31.700 Nm | 32.070 Nm | +0.371 Nm |

ESN-v2 lowers recovery RMSE in 9/9 fixtures and does not worsen rejoin latency
in any fixture. The recovery mechanism is therefore a genuine candidate, but the
contact-impulse increase prevents a universal safety claim.

## Phase Analysis

Offline phase analysis uses rod timing only after rollout. No policy input uses
rod timing, contact, force, obstacle state, or future release. ESN-v2 minus MLP
tracking RMSE is zero before authority opens, -1.79 mm during loading, and
-1.40 mm during recovery. This rejects a pre-contact trajectory-bias
explanation. The post-grasp interval is unfavorable, so a separately labelled
frozen WBC-only lift/carry wrapper is retained as a deployment safety variant.

## Rejected Deployment Projection

A causal WBC-error directional half-space projection was evaluated on the frozen
balanced ESN-v2 model. It lowered impulse to 2.974 N s, but task success fell to
6/9 and recovery RMSE worsened to 8.473 mm. The hard projection is rejected as
a main controller and is retained only as a negative ablation.

## Impulse-Constrained Smoke

The next profile increases only the training-time contact impulse cost while
keeping post-release error and recovery-progress terms. With new seed
`20260851`, both lanes again pass the same task, no-rod, collision, and torque
gates.

| Mean over nine validation fixtures | MLP | ESN-v2 | ESN-v2 minus MLP |
|---|---:|---:|---:|
| Recovery RMSE | 5.437 mm | 2.802 mm | -2.635 mm |
| Rejoin latency | 339 ms | 28 ms | -311 ms |
| Contact impulse | 3.660 N s | 3.820 N s | +0.160 N s |
| Peak jerk | 962.6 m/s^3 | 976.3 m/s^3 | +13.7 m/s^3 |
| Peak torque | 31.820 Nm | 32.266 Nm | +0.446 Nm |

The impulse penalty does not yet make ESN-v2 lower-impulse than MLP, but it
substantially narrows the cost relative to the balanced smoke while preserving
a large recovery advantage. The next step is a paired multi-seed reproduction,
not further reward tuning based on one seed.
