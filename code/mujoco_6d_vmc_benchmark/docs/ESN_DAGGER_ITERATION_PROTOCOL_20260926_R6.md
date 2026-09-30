# ESN cumulative-reservoir DAgger protocol R6 (2026-09-26)

## Motivation and scope

R5 fitted only the newest three trajectories and regressed on fixtures 9331
and 9332. R6 tests the predeclared hypothesis that retaining the full set of
reservoir histories prevents this catastrophic forgetting. This remains a
development-only selection protocol.

## Frozen data and fit

The aggregate fit uses all 15 complete student-on-policy trajectories from
three successive collections: the original nine trajectories 9310--9332, the
three R4 evaluation trajectories 9330--9332, and the three R5 replay
trajectories 9330--9332. No historical validation trace or future
cross-condition trace is read.

The base checkpoint is R4 (SHA256
`4dc980c03834020cbc651b3ed84a5b713f9c3cb619a682f867d06a9eb482e821`).
Only its final readout is refit. Every sample is retained, stage 3 has weight
2.0, other stages weight 1.0, and proximal ridge is 0.01. The normalization,
heterogeneous-leak 128-unit reservoir, first readout layer, action projection,
safety filter, runner, task gate, and strict 0.2 mm penetration gate remain
unchanged.

## Fixed candidate budget

Five candidates are evaluated on the same Spark source snapshot and the same
three fixtures 9330--9332:

1. unchanged R4 base;
2. 0.25 interpolation from R4 toward the aggregate fit;
3. 0.50 interpolation;
4. 0.75 interpolation;
5. the unblended aggregate fit.

No additional interpolation coefficient is added after results are observed.
All failures remain in the report. A candidate is feasible only if all three
fixtures pass both task and strict gate. Among feasible candidates, selection
minimizes mean physical-substep position RMSE, then peak torque, then peak
speed. If none is feasible, no checkpoint is promoted; for the sole purpose
of another DAgger collection, the diagnostic leader is ranked by task count,
then strict count, then mean endpoint error.

## Cross-condition gate

Only a feasible selected candidate may be evaluated once on the already
frozen 9340--9345 plan in
`configs/esn_r5_cross_condition_plan_20260926.json`. Robustness requires task
and strict-gate success on all six fixtures. This is simulation evidence, not
a real-robot readiness claim.
