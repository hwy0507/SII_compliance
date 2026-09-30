# ESN nonlinear reservoir-state gate protocol R15 (2026-09-26)

R14 demonstrated that a linear gate contains useful signal but cannot meet the
predeclared TPR/FPR requirements. R15 retains the same frozen R11 weight-2
yield expert, frozen R8 gain-1.5 clearance expert, cumulative 24 trajectories,
and positive/negative labels. It replaces only the logistic gate with a
16-unit tanh MLP driven by the same 128-D reservoir-derived hidden state.

Training is deterministic full-batch Adam for 6000 steps, learning rate 0.01,
L2 1e-4, seed 20260926. The fixed candidate offsets are 0, -1, and -2. Stage
and trajectory identity construct offline labels only; deployment inputs remain
proprio48. A candidate may run physically only if TPR >= 0.95, FPR <= 0.01,
positive p05 > 0.5, and negative p95 < 0.5.

Qualifying candidates run once on the frozen five-condition safety screen.
Feasibility requires task+strict 5/5. A winner must then pass the four-condition
development remainder before the already frozen 9350--9357 blind plan runs.
Physics, task gate, 0.2 mm penetration gate, and safety filter are unchanged.
