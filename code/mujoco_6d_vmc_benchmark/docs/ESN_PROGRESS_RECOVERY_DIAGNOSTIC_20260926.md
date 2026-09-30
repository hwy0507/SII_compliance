# ESN progress-recovery causal diagnostic (2026-09-26)

The cumulative R7 aggregate checkpoint passes task and strict gate on fixtures
9330 and 9331 but fails 9332. On 9332, the fixed VMC teacher and a zero-residual
fixed-WBC diagnostic also fail. Therefore pure teacher imitation cannot provide
a successful recovery label for this state distribution.

This diagnostic tests one causal hypothesis: loaded-lift failure is caused by
insufficient residual velocity along the commanded upward path. Starting from
the frozen R7 aggregate checkpoint, add a constant logit bias only to action
channel 3 (world-frame z yield) with exactly three predeclared deltas: 0.05,
0.10, and 0.20. Evaluate each once on fixture 9332. No task gate, penetration
gate, safety filter, geometry, or other action channel is changed.

These constant-bias checkpoints are diagnostics, not selectable policies and
cannot be promoted. If the hypothesis is supported, the next model must learn
a phase-conditional progress-recovery target from observable 48-D histories;
the heterogeneous-leak reservoir must encode persistence, while the deployed
policy receives no stage label, clock, or geometry input.
