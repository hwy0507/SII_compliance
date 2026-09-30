# ESN DAgger iteration protocol (2026-09-25)

This protocol is frozen before the next physical collection. It is a
development-only expansion intended to test angular and payload coverage. The
existing validation fixtures `9610/9611/9612` are not used for fitting or
selection.

## New development fixtures

| id | push angle (rad) | push height (m) | payload mass (kg) |
|---:|---:|---:|---:|
| 9310 | -0.100 | 0.570 | 0.090 |
| 9311 | 0.000 | 0.590 | 0.110 |
| 9312 | 0.100 | 0.610 | 0.130 |

The fixed loaded-lift runner, 24 s duration, 50 microsecond MuJoCo timestep,
unchanged observation contract, safety filter, task logic, and `0.2 mm`
penetration gate are retained. All three new trajectories are collected with
the current stage-weighted checkpoint. They are then appended to the six
previous development trajectories without success filtering.

## Fixed fitting rule

Only the final readout is refit. Reservoir weights, leak, normalization,
first readout layer, action projection, safety filter, and task gates remain
frozen. Every sample is retained. Stage `3` samples receive weight `2.0`; all
other samples receive weight `1.0`; proximal ridge is `0.01`. No validation
trace is read by the fitter.

The resulting checkpoint is evaluated once on all three new development
fixtures and once on the untouched validation fixtures `9610/9611/9612`.
Failures, strict-gate failures, raw traces, hashes, and finite-sample checks
are retained. A development improvement does not establish real-environment
readiness.
