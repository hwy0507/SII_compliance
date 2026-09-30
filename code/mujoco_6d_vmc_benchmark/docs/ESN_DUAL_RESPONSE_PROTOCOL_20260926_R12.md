# ESN dual yield/clearance replay protocol R12 (2026-09-26)

R11 kept task success on all five safety-screen fixtures but never passed the
strict gate on 9344. Increasing the weight of a zero-progress target improved
9340 while worsening 9344. A pre-R12 information-gain diagnostic with the
already frozen R8 gain-1.5 model reduced 9344 penetration to 0.198888 mm and
contact duration to 0.29295 s while retaining task success. This supports two
opposite, history-conditioned responses: yield for 9340 and rapid clearance
for the lower 9344 obstruction.

R12 uses the same 24 cumulative trajectories as R11. The four archived 9330
histories retain progress gain 0.5. The R10 9340 trajectory uses yield gain
0.0 with weight multiplier 2. The R10 9344 trajectory uses a clearance gain
from the fixed predeclared set 1.25, 1.50, and 1.75 with weight multiplier 2.
All other histories use gain 1.0. Loaded weight is 2.0, proximal ridge is 0.05,
deadband is 0.012 m, and maximum progress action is 0.30.

Only the final readout is fit. The deployed policy receives the original 48-D
proprioceptive input and no trajectory group, fixture ID, geometry, stage,
clock, or privileged state. Reservoir, normalization, first readout layer,
action projection, safety filter, physics source, task gate, and strict 0.2 mm
penetration gate remain frozen.

The three candidates are evaluated once on the frozen R11 safety screen. A
candidate is feasible only at task+strict 5/5. Feasible candidates are ranked
by whether maximum penetration is at most 0.195 mm, then mean physical-substep
RMSE, peak torque, and peak speed. The winner must pass the remaining four
development conditions before the already frozen 9350--9357 blind plan runs.
All eight blind conditions must pass both original gates. The 9340--9345 set
is development evidence and is not relabeled as blind.
