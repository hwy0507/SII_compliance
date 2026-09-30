# ESN iterative DAgger protocol R5 (2026-09-26)

## Scope

R4 is a negative development result: its fitted checkpoint achieved task
success on only fixture 9330, missed the strict 0.2 mm penetration gate on
that fixture, and failed the task on 9331 and 9332. R5 is a new
development-only DAgger iteration. It does not read the historical validation
fixtures 9610--9612 or any future cross-condition fixture during fitting.

## Frozen fit

The base checkpoint is the R4 checkpoint with SHA256
`4dc980c03834020cbc651b3ed84a5b713f9c3cb619a682f867d06a9eb482e821`.
The only fitting trajectories are the three complete R4 closed-loop
trajectories 9330--9332. They are relabelled by the same fixed VMC teacher.
Every sample is retained. Stage 3 samples have weight 2.0, all other samples
have weight 1.0, and the proximal ridge around the R4 readout is 0.01.

Only the final readout is refit. The 48-D normalization, heterogeneous-leak
128-unit reservoir, first readout layer, action projection, safety filter,
MuJoCo runner, task gate, and strict maximum external penetration gate remain
frozen.

## Development replay gate

The fitted R5 checkpoint is evaluated exactly once on fixtures 9330--9332
with their already frozen geometry and payload parameters. R5 passes this
development replay gate only if all three fixtures pass both the unchanged
task gate and the strict maximum external penetration gate of 0.2 mm.

## Predeclared cross-condition set

Only a checkpoint that passes the development replay gate may be evaluated on
the following new set. These parameters are frozen before R5 fitting results
are inspected.

| id | push angle (rad) | push height (m) | payload mass (kg) |
|---:|---:|---:|---:|
| 9340 | -0.080 | 0.580 | 0.095 |
| 9341 | 0.000 | 0.610 | 0.125 |
| 9342 | 0.100 | 0.590 | 0.105 |
| 9343 | -0.160 | 0.615 | 0.130 |
| 9344 | 0.080 | 0.565 | 0.090 |
| 9345 | 0.180 | 0.630 | 0.140 |

Cross-condition robustness requires all six runs to pass task and strict gate
in one evaluation. Any failure is retained. A development or cross-condition
success is simulation evidence only and is not a real-robot deployment claim.
