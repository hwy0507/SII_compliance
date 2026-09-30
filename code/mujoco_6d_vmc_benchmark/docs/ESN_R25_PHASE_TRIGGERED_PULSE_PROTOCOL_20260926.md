# ESN phase-triggered margin pulse protocol R25 (2026-09-26)

R20/R21 showed that the original risk selector activates after the peak has
already formed. R23/R24 then showed that pre-peak proprio48 reservoir states
reliably encode the contact-approach phase but do not reliably identify which
fixture will later exceed 0.2 mm. Therefore R25 does not attempt a
condition-specific prediction.

R25 trains a 16-unit selector to identify offline stage 2 on all 59 exposed
trajectories. Stage is used only as an offline label. Deployment input remains
proprio48 and the frozen reservoir state. On all eight exposed R15 screen
trajectories, the zero-offset selector produces a single sustained run that
starts at control step 52 and lasts through step 72 or 73. The observed
high-contact force peaks occur at steps 71--79. R25 fixes two consecutive
positive decisions as the trigger and a one-shot 30-step (1.2 s) margin pulse,
which begins at step 53 and covers the entire observed peak window. The pulse
then returns to the complete R15 base and cannot retrigger during that episode.

The selector, confirmation length, and pulse length are fixed before physical
launch. All policy weights, the 1.10 margin expert, reservoir, normalization,
downstream action/safety filtering, physics, task gate, and 0.2 mm penetration
gate remain unchanged. R25 must pass task+strict 8/8 on the unchanged exposed
screen and 9/9 on the remainder before the hash-frozen 9360--9367 blind plan
is opened once. All failed rounds remain in the report.
