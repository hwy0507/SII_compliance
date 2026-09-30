# ESN DAgger iteration protocol R4 (2026-09-25)

This is a new development-only collection after the R3 failure. It does not
reuse the previously observed validation fixtures `9610--9612` for fitting or
selection.

## Frozen data and new fixtures

The fit will use the six locally recoverable, hash-verified development
rollouts `9310--9312` and `9320--9322`, plus these three new fixtures:

| id | push angle (rad) | push height (m) | payload mass (kg) |
|---:|---:|---:|---:|
| 9330 | -0.120 | 0.570 | 0.085 |
| 9331 | 0.040 | 0.600 | 0.115 |
| 9332 | 0.140 | 0.620 | 0.135 |

The R2 readout checkpoint collects all three new student-on-policy trajectories
before fitting. The unchanged 24 s loaded-lift runner, 50 microsecond MuJoCo
timestep, observation contract, safety filter, task logic, and strict maximum
external penetration gate of 0.2 mm are retained. All supplied samples are
kept, including task and gate failures.

## Frozen fit

Only the final readout is refit. Reservoir weights, leak, normalization, first
readout layer, action projection, safety filter, teacher configuration, and
task gates remain frozen. Stage 3 samples have weight 2.0; all other samples
have weight 1.0; proximal ridge is 0.01. No validation trace is read.

## Promotion rule

The R4 checkpoint is eligible for a future blind protocol only if all three
new fixtures pass both task and strict gate in a single predeclared evaluation
of the fitted checkpoint. Otherwise it remains a negative development result;
no blind or real-environment claim follows.
