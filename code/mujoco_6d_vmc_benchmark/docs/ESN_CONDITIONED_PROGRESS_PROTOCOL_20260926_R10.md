# ESN condition-separated progress protocol R10 (2026-09-26)

## Motivation and frozen evidence

R8 global progress shaping at gain 1.0 passed the original task gate on all
three development fixtures and passed the strict 0.2 mm penetration gate on
9331 and 9332. Fixture 9330 missed only the strict gate, at 0.204059 mm. R9
applied recovery shaping only to four 9332 failure histories; it regressed to
task 1/3, showing that sparse failure-only shaping is not sufficient.

R10 retains the broadly supported R8 recovery target on all cumulative
histories except the four archived 9330 histories. Those four histories use a
lower progress gain so the frozen reservoir can learn condition-separated
conservatism from proprioceptive history. Trajectory membership affects only
training labels. The deployed policy receives the unchanged 48-D input and no
fixture identifier, geometry, stage, clock, or privileged state.

## Fixed candidate budget

The base checkpoint is the R7 aggregate checkpoint, SHA256
`a122da8e677867bbc3b6c9c7ddfae7cf80c691ec329a745570b4f63812f18051`.
All 18 cumulative trajectories and all samples are retained. Default progress
gain is 1.0 per metre. Exactly three conservative gains are declared before
physical evaluation: 0.0, 0.25, and 0.50 per metre. Deadband is 0.012 m,
maximum progress action is 0.30, loaded-stage weight is 2.0, and proximal
ridge is 0.01.

The four conservative histories are the 9330 trajectories from R4 collection,
R4 evaluation, R5 replay, and R6 beta=0.50 replay. Only the final readout is
fit. Normalization, heterogeneous-leak reservoir, first readout layer, action
projection, safety filter, physics source, task gate, and strict penetration
gate remain frozen.

Each candidate is evaluated once on fixtures 9330--9332. Feasibility requires
task and strict penetration success on all three. Among feasible candidates,
select the lowest mean physical-substep RMSE, then peak torque, then peak
speed. If none is feasible, no candidate is promoted.

Only a feasible candidate may run the frozen 9340--9345 cross-condition plan.
All six fixtures must pass both gates before reporting simulation cross-
condition robustness. This is MuJoCo evidence and is not a real-robot claim.
