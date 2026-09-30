# ESN strengthened clearance replay protocol R13 (2026-09-26)

R12 kept task success on all five safety-screen fixtures and made 9344
penetration decrease monotonically from 0.217119 mm at clearance gain 1.25 to
0.209774 mm at gain 1.75. The other four fixtures passed the strict gate at
gain 1.75. The previously frozen global gain-1.5 diagnostic passed 9344 at
0.198888 mm, so the remaining deficit is attributed to insufficient influence
of the single condition-specific clearance history rather than a reversed
response direction.

R13 retains the R12 data, group partition, base checkpoint, gain 0.0 yield for
9340, gain 0.5 moderate response for historical 9330, and all frozen runtime
components. Clearance replay weight is increased from 2 to 4. Exactly three
clearance gains are declared before evaluation: 2.0, 2.5, and 3.0. Loaded
weight remains 2.0, yield multiplier 2.0, proximal ridge 0.05, deadband
0.012 m, and maximum progress action 0.30.

Only the final readout is fit. Deployment remains original proprio48 without
fixture ID, group label, geometry, stage, clock, or privileged state. The same
five-condition R11 screen is run once per candidate. Feasibility requires
task+strict 5/5. Feasible candidates are ranked by maximum penetration at or
below 0.195 mm, then mean physical-substep RMSE, peak torque, and peak speed.
The selected model must pass the four-condition development remainder before
the already frozen 9350--9357 blind plan runs. Any blind failure prevents a
cross-condition robustness claim.
