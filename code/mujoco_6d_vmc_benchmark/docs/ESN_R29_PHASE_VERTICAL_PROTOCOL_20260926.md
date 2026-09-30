# ESN reservoir-phase vertical-clearance protocol R29 (2026-09-26)

R28 floor 0.25 showed that WBC slowdown did not delay the moving rod's first
contact: first contact remained near 2.84--2.90 s, while the hand was about
5 mm lower at contact than under the R27 trajectory.  Thus slowdown attacks
the robot's nominal motion but not the externally driven rod velocity.  Before
reading the R28 floor-0.50 and floor-0.75 results, R29 fixes a mechanistically
different intervention: use the reservoir only to identify the shared
pre-contact phase, retain the complete R15 base readout, and apply a lower
bound only to action channel 3, the normalized +z translational yield.

R29 is run only if no R28 candidate reaches task+strict 8/8.  Its selector
threshold is 0.5, confirmation is two 40 ms steps, and the pulse lasts 30
steps (1.2 s), covering the nominal first-contact interval and early response.
Three candidates are fixed: +z floors 0.35, 0.50, and 0.65.  They correspond
to 0.056, 0.080, and 0.104 m/s minimum requested upward yield under the
unchanged 0.16 m/s translational action scale.  All three run the same eight
exposed screen conditions, all failures are retained, and eligibility requires
task+strict 8/8.  If several qualify, the lowest floor is selected a priori.

The R15 base policy, reservoir, phase selector, slowdown channel, the other
five yield channels, normalization, action filter, safety filter, physics,
task gate, and 0.2 mm penetration gate remain frozen.  Deployment remains
proprio48 plus policy-local reservoir/counter state.  A selected candidate
must pass the nine-condition exposed remainder for 17/17 before the frozen
9360--9367 blind set is opened once; blind 8/8 task+strict is required for a
cross-condition simulation-robustness claim.  No simulation result establishes
real-robot readiness.
