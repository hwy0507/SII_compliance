# ESN phase-pulse amplitude protocol R27 (2026-09-26)

R15 (pulse scale 0) preserves most exposed conditions but misses 9352/9355.
R25 (scale 1 for 30 steps) fixes 9352 but transfers safety risk to 9340,
9344, and 9355. R26 shows that simply ending the full-amplitude pulse before
contact is not monotonic and already fails 9330. R27 therefore fixes the R25
trigger and 30-step window and varies only the interpolation amplitude between
the complete R15 base logits and the frozen 1.10 margin-expert logits.

Before the remaining R26 results are read, three candidates are fixed:
`pulse_scale` 0.25, 0.50, and 0.75. All use threshold 0.5, confirmation 2,
and pulse length 30. Each must run the unchanged eight-condition screen with
all results retained. Eligibility requires task+strict 8/8; if multiple
qualify, the lowest scale is selected a priori because it is the smallest
deviation from R15. No other scale enters R27.

Only the branch interpolation scalar changes. R15, the margin expert,
reservoir, normalization, selector weights, physics, action/safety filters,
task gate, and 0.2 mm penetration gate remain frozen. Deployment remains
proprio48 plus policy-local reservoir/counter state. A selected candidate must
pass the nine-condition exposed remainder before the precommitted 9360--9367
blind plan is opened once.
