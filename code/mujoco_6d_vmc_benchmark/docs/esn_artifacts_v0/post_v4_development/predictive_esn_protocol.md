# Predictive ESN protocol

## Method change

The rejected action-context ESN was allowed to remember its own past residual
command.  That lowered impulse but encouraged excessive residual authority.
The predictive ESN instead estimates a physical state quantity: the WBC pose
tracking error 120 ms in the future.  It does not receive residual-action
history.

```text
current deployable WBC state/error history
  -> fixed fast/slow Fan Ye reservoirs
  -> ridge future-pose-error readout (120 ms)
  -> PPO residual policy
  -> unchanged shared safety adapter
```

## Information contract

Predictor input at time `t` is exactly:

`q(7), qdot(7), WBC task twist(6), WBC pose error(6), WBC twist error(6)`.

Its training target is pose error at `t + 120 ms`.  Future state is used only
as an offline supervised label; it is never provided to the online actor.
Contact, force, rod state, obstacle geometry, future release, fixture ID, and
reward are excluded from both predictor and actor input.  The V4 final holdout
is excluded completely.

## Fair baseline

The predictive ESN output contains 6 forecast channels.  Therefore it is not
compared to the 32-D current-state MLP directly in its first smoke test.  The
paired learned baseline receives the same 6 forecast channels from a causal
constant-twist extrapolation of current WBC pose/twist error.  Both actors are
38-D and use the same PPO, action, safety, fixture, seed, and reward contracts.
The claimed difference is ESN dynamic prediction versus a simple causal
kinematic prediction, not extra feature dimension.

## Pre-PPO forecast gate

Development-train probe traces fit the fixed-reservoir ridge readout and the
separate development-validation probes evaluate it.  Promotion requires finite
outputs and validation error materially below the matched kinematic forecast.
Only after that gate does a 102,400-step paired PPO smoke begin.  Task success,
no-rod success, effective collision, and torque gates precede all recovery,
impulse, jerk, and torque comparisons.
