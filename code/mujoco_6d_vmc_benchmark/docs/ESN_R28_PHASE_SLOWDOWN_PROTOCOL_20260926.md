# ESN reservoir-phase slowdown protocol R28 (2026-09-26)

R25--R27 show that replacing or interpolating the six-dimensional yield
response can repair one condition while transferring penetration risk to
another.  Offline replay also shows that the eight screen conditions are
indistinguishable to the proprioceptive policy before contact, while the
reservoir reliably identifies the common pre-contact phase at control step 53.
R28 therefore uses the reservoir only as a temporal cue and leaves the full
R15 base logits and all six yield channels unchanged.  During one pre-contact
pulse it applies a lower bound only to action channel 0, the normalized WBC
slowdown request.

This protocol is frozen before reading the final R27 scale-0.75 result.  The
selector threshold is 0.5, confirmation is two 40 ms control steps, and pulse
length is 45 steps (1.8 s), long enough to cover the delayed first contact at
the strongest fixed slowdown.  Three candidates are fixed: slowdown floors
0.25, 0.50, and 0.75, corresponding to nominal WBC scales no greater than
0.80, 0.60, and 0.40 during the pulse under the unchanged minimum scale 0.20.
All three candidates run the same eight-condition exposed screen.  Every run,
including failures, is retained.  Eligibility requires task+strict 8/8; if
several qualify, the lowest floor is selected a priori as the smallest change
to R15.

The R15 base policy, reservoir, phase selector weights, six yield channels,
normalization, action filter, safety filter, physics, task gate, and 0.2 mm
penetration gate are frozen.  Deployment remains proprio48 plus policy-local
reservoir/counter state; stage, fixture identity, geometry, and clock are not
deployment inputs.  A selected candidate must pass all nine exposed remainder
conditions for a combined exposed result of 17/17 before the hash-frozen
9360--9367 blind plan is opened once.  Blind 8/8 task+strict is required for a
cross-condition simulation-robustness claim and does not establish real-robot
readiness.
