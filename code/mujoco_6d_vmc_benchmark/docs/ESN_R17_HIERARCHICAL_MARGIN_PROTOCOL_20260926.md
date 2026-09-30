# ESN hierarchical margin protocol R17 (2026-09-26)

R16 proved that its 1.10 margin expert repairs exposed failures 9352 and 9355,
but replacing R15's clearance expert transfers risk to 9330, 9340, 9342, and
9344. R17 therefore freezes the complete R15 offset -1 gated policy as its
base. A second 16-unit tanh selector, driven only by the same reservoir-derived
128-D hidden state, blends that base policy with the frozen 1.10 margin expert.
When the selector is zero, R17 is exactly the already validated R15 policy.

The cumulative selector fit contains the 43 trajectories used by R16 plus all
16 R16 screen trajectories, for 59 trajectories total. Positive trajectories
are R15 9352/9355, margin-expert 9352/9355, and both R16 candidate trajectories
for 9352/9355 (eight total). Only their offline stage >= 3 samples are positive.
All other samples, including every 9344, 9340, and 9342 trajectory, are
negative. No failure or unfavorable rollout is removed.

Training is fixed before fitting: deterministic full-batch Adam, 16 hidden
units, 6000 steps, learning rate 0.01, L2 1e-4, seed 20260926, and selector
offsets 0, -1, and -2. Offline admission requires TPR >= 0.95, FPR <= 0.01,
positive p05 > 0.5, and negative p95 < 0.5. Every admitted candidate runs the
same eight-condition exposed screen (9330, 9332, 9340, 9342, 9344, 9352, 9355,
9357); feasibility requires task+strict 8/8.

A screen winner must also pass task+strict on the other nine exposed
conditions, giving 17/17 over 9330--9357, before the already hash-frozen
9360--9367 blind plan may run once. Deployment remains proprio48-only. Physics,
environment, action filter, task gate, and the 0.2 mm penetration gate are
unchanged. Simulation success does not imply real-robot readiness.
