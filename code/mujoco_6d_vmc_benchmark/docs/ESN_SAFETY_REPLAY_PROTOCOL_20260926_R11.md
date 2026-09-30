# ESN cumulative safety-replay protocol R11 (2026-09-26)

## Evidence and status change

R10 conservative-gain 0.50 is the first checkpoint to pass task and the
strict 0.2 mm penetration gate on development fixtures 9330--9332. On the
previously unseen 9340--9345 set it passed task 6/6 but strict 4/6: 9340 was
0.201385 mm and 9344 was 0.206054 mm. Those six fixtures are therefore now
development evidence and may not be described as held-out again.

R11 appends all six R10 cross-condition trajectories to the exact 18-trajectory
R8/R10 cumulative set. The four archived 9330 histories retain gain 0.50. The
new unsafe 9340 and 9344 histories use the unchanged VMC label (progress gain
0.0); all other histories use gain 1.0. This partition is used only to build
training targets. Deployment still receives only the frozen 48-D proprioceptive
input and no fixture ID, geometry, stage, clock, or privileged state.

## Fixed budget and gates

The base is R10 conservative-gain 0.50, SHA256
`2ce4e13d01c205965a9ccd2148acec869ad296915140c336a90751740b2cd3dc`.
All 24 trajectories and all samples are retained. Loaded-stage weight is 2.0,
proximal ridge is 0.05, deadband is 0.012 m, and maximum progress action is
0.30. The fixed candidate budget is exactly three safety replay multipliers:
1, 2, and 4. Only the final readout is fit; normalization, reservoir, first
readout layer, action projection, safety filter, runner, task gate, and strict
penetration gate are frozen.

Candidates are screened once on 9330, 9332, 9340, 9344, and 9345. A screen
candidate must pass task and strict gate on all five; a preferred engineering
margin is maximum penetration at or below 0.195 mm. Among feasible candidates,
rank by margin status, mean physical-substep RMSE, peak torque, then peak
speed. The winner is then run once on the remaining 9331, 9341, 9342, and 9343.
All nine development conditions must pass both original gates before blind
evaluation.

The 9350--9357 plan is frozen before any R11 physical rollout. It is the new
blind cross-condition set. All eight must pass task and strict penetration
gate; any failure prevents a cross-condition robustness claim. This remains
MuJoCo evidence, not real-robot validation.
