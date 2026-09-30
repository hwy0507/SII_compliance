# ESN post-grasp reservoir-phase vertical protocol R30 (2026-09-26)

R29 established two facts on the complete exposed screen.  A +z floor of 0.65
nearly eliminated external penetration on five conditions, but the stage-2
trigger at 2.16 s disrupted grasp/stage advancement and produced task 0/8.
Floors 0.35 and 0.50 retained task 8/8 but transferred penetration risk.
R30 therefore changes timing rather than searching another amplitude: it fits
a universal reservoir-state detector for stage 3 (loaded lift), with stage 2
as an explicitly equal-weighted hard-negative class.  Offline stage labels are
used only for fitting and auditing; deployment still receives only proprio48
and policy-local reservoir/counter state.

The selector is fit once on all eight retained R29 floor-0.35 exposed
trajectories.  All trajectories are positive only at stage >= 3; all stage-2
samples are hard negatives.  Training is deterministic full-batch Adam with
16 hidden units, 6000 steps, learning rate 0.01, L2 1e-4, and seed 20260926.
The sole physical candidate uses threshold 0.5, two-step confirmation, a
20-step (0.8 s) pulse, and +z floor 0.65.  Admission requires offline stage-2
false-positive rate 0, stage-3 true-positive rate >= 0.99, and replay trigger
strictly after each archived stage-3 transition.  No amplitude or duration
alternative is admitted in R30.

If admitted, the candidate runs the unchanged eight-condition exposed screen.
It is eligible only at task+strict 8/8, then must pass the nine-condition
exposed remainder for 17/17 before the frozen 9360--9367 blind plan is opened
once.  The R15 base readout, all non-z action channels, action/safety filters,
physics, task gate, and 0.2 mm penetration gate remain unchanged.  Blind 8/8
task+strict is required for a cross-condition simulation-robustness claim;
real-robot readiness requires separate hardware validation.
