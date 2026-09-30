# ESN short pre-contact pulse protocol R26 (2026-09-26)

R25's fixed 30-step pulse improved exposed fixtures 9330 and 9342 but moved
9340 from 0.198769 mm to 0.201319 mm. This result rules out a pulse that
continues through the contact-force peak for every condition. The R25
selector itself consistently starts at control step 52 and the observed
force peaks begin at step 71, so R26 fixes a small two-candidate duration
ablation before reading the remaining R25 results:

- confirm 2, pulse 8 steps (0.32 s; ends at the offline stage-2 boundary);
- confirm 2, pulse 16 steps (0.64 s; ends before the earliest observed peak).

Both candidates use exactly the frozen R25 phase selector, R15 base, 1.10
margin expert, reservoir, normalization, physics, action/safety filters, task
gate, and 0.2 mm penetration gate. Both must run the same eight-condition
screen with all failures retained. A candidate is eligible only at task+strict
8/8; if both qualify, the shorter pulse is selected a priori. No other pulse
length enters R26. The selected model must then pass the nine-condition
exposed remainder before the precommitted 9360--9367 blind plan is opened
once. Deployment remains proprio48 plus policy-local reservoir/counter state.
