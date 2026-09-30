# ESN reservoir-state gated readout protocol R14 (2026-09-26)

R10--R13 show that a single linear final readout cannot express both the yield
response required by 9340 and the rapid-clearance response required by 9344
without transferring penetration risk to 9332. R14 changes readout capacity,
not observations, physics, safety filtering, or gates.

The yield expert is the R11 weight-2 checkpoint (SHA256
`0650269e221b702257486c5a2c86cec1d70fce9af011e8bc9e0847d572d70b4f`).
It passes task 5/5 and strict 4/5 on the safety screen, including 9340. The
clearance expert is the frozen R8 global gain-1.5 checkpoint (SHA256
`705237c205391871c7254286d30ecc1575ed82310a2d7a4c508efa3004536abf`).
It passes the targeted 9344 diagnostic at 0.198888 mm.

A logistic gate reads only the common 128-D hidden state derived from the
frozen heterogeneous-leak reservoir and frozen first readout layer. Positive
training labels are loaded-stage samples from the archived R10 9344 rollout;
all other samples in the same 24-trajectory cumulative set are negative.
Stage and trajectory identity construct offline labels only and are absent at
deployment. Both experts and every upstream component are frozen.

Before physical evaluation, gate separability must have true-positive rate at
least 0.95, false-positive rate at most 0.01, positive p05 probability above
0.5, and negative p95 below 0.5. The fixed physical candidate budget is gate
offsets 0, -1, and -2 with L2=0.1. Each candidate runs once on the five-condition
R11 safety screen. Feasibility requires task+strict 5/5. A feasible winner must
then pass the four-condition development remainder before the already frozen
9350--9357 blind plan runs. No gate, threshold, fixture, or safety filter is
changed.
