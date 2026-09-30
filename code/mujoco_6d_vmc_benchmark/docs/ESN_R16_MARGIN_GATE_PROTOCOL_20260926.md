# ESN R16 margin-gate protocol (2026-09-26)

R16 combines the frozen R11 weight-2 yield expert with the feasible
residual-logit-scale 1.10 margin expert. Both share the identical proprio48
normalization, heterogeneous-leak reservoir, and first readout layer. A
16-unit tanh gate reads only the resulting 128-D hidden state. Deployment does
not receive stage, fixture ID, geometry, clock, success, or penetration.

The cumulative fit contains all 24 R14/R15 historical gate trajectories, all
17 R15 offset -1 development/blind trajectories, and both successful 1.10
margin-expert trajectories: 43 trajectories total. Positive trajectories are
R10 9344, R15 9344, R15 9352/9355, and margin-expert 9352/9355. Only samples
with offline stage >= 3 in those six trajectories receive a positive label;
all other samples are negative. No failed trajectory is removed.

Training remains deterministic full-batch Adam: 16 hidden units, 6000 steps,
learning rate 0.01, L2 1e-4, seed 20260926. Before fitting, gate offsets 0,
-1, and -2 are fixed. Offline admission requires TPR >= 0.95, FPR <= 0.01,
positive probability p05 > 0.5, and negative probability p95 < 0.5. Every
admitted candidate enters the same exposed-condition screen; no candidate is
selected from a favorable single fixture.

The first physical screen is fixed to 9330, 9332, 9340, 9342, 9344, 9352,
9355, and 9357, covering prior task failure, yield/clearance conflicts, the
two R15 blind failures, and two narrow-margin passes. Feasibility requires
task+strict 8/8. A feasible checkpoint must then pass task+strict across all
remaining exposed 9330--9357 conditions before the frozen 9360--9367 blind
plan may run once. Physics, environment, safety filter, task gate, and 0.2 mm
penetration gate are unchanged.
