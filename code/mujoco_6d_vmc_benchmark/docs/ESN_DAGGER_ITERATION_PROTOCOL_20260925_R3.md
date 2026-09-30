# ESN DAgger iteration protocol r3 (2026-09-25)

This protocol is frozen before collection. It is a development-only closed-loop
iteration; no previously observed validation fixture is used for fitting or
selection.

## Development fixtures

| id | push angle (rad) | push height (m) | payload mass (kg) |
|---:|---:|---:|---:|
| 9320 | -0.080 | 0.575 | 0.090 |
| 9321 | 0.020 | 0.595 | 0.110 |
| 9322 | 0.120 | 0.615 | 0.130 |

The runner uses the unchanged 24 s loaded-lift scene, 50 microsecond MuJoCo
timestep, observation contract, safety filter, task logic, and strict maximum
external penetration gate of 0.2 mm. The stage-weighted r2 checkpoint is used
to collect all three student-on-policy trajectories. No trajectory is removed
because it fails or because its action error is large.

## Fitting rule

The final readout only is refit from the nine r1/r2 development trajectories
and the three r3 trajectories. Reservoir weights, leak, normalization, first
readout layer, action projection, safety filter, teacher configuration, and
task gates remain frozen. Every sample is retained. Stage 3 samples receive
weight 2.0; all other samples receive weight 1.0; proximal ridge is 0.01.
There is no beta scan and no validation trace is read by the fitter.

## Promotion rule

The resulting checkpoint is eligible for a separately frozen blind evaluation
only if all three r3 development fixtures satisfy task success and the strict
0.2 mm penetration gate. Otherwise the iteration is recorded as a negative
development result and no blind result is generated. A development result,
positive or negative, is not a real-robot readiness claim.
