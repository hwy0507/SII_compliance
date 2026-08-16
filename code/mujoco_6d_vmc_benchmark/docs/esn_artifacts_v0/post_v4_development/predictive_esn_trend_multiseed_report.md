# Predictive ESN trend multi-seed reproduction

## Protocol

Three new paired development seeds (`20260972`--`20260974`) repeat the frozen
120-ms error-change predictor, 102,400 PPO steps, eight environments,
impulse-constrained reward, 38-D matched input dimension, shared safety layer,
and the separated post-V4 train/validation fixtures.  The learned comparator
is the 38-D kinematic-forecast MLP; the ESN lane replaces only its six
constant-twist trend channels with the fitted fixed-reservoir forecast.

The forecast readout itself is not retrained per seed and V4 final remains
unread.

## Forecast result is not the control result

On the held-out development-validation probe traces, the ESN predicted 120-ms
translation error change with `0.790 mm` RMSE, compared with `6.066 mm` for
the causal constant-twist extrapolation.  This is strong evidence that the
reservoir captures short-horizon WBC-error dynamics.  It is not by itself a
control-performance claim.

## Control reproduction

| seed | kinematic MLP gate | predictive ESN gate | reason when pair excluded |
|---:|---|---|---|
| 20260972 | fail | pass | MLP task success 8/9; ESN task success 9/9 |
| 20260973 | fail | pass | MLP task success 8/9; ESN task success 9/9 |
| 20260974 | pass | pass | eligible paired comparison |

The two invalid pairs cannot be included in a paired effect aggregate.  In the
one fully gated pair (`20260974`), predictive ESN minus the matched kinematic
MLP was:

| metric | effect |
|---|---:|
| recovery RMSE | +0.261 mm |
| rejoin latency | +31.1 ms |
| paired-offset RMSE | +0.029 mm |
| peak paired offset | +0.247 mm |
| contact impulse | +0.003 N s |
| peak torque | -0.046 Nm |
| peak jerk | -11.5 m/s^3 |

## Decision

Do not promote the predictive ESN trend feature as the proposed controller.
The original smoke seed showed a coherent recovery/impulse/torque/rejoin
benefit with a small jerk cost, but that direction did not reproduce in the
only fully valid multi-seed pair.  Conversely, the two baseline task failures
show the simple kinematic forecast is a weak and training-sensitive control
feature, not that the ESN has already achieved a robust task advantage.

The defensible conclusion is narrower: fixed Fan Ye reservoir memory provides
a highly accurate causal 120-ms WBC-error-change predictor, but the current
PPO residual interface does not yet reliably exploit it.  Keep this as a
representation/forecasting result and negative control-transfer result.  The
independent ESN-v2 remains the only controller with a three-seed repeatable
recovery and peak-torque advantage against the current-state MLP.
