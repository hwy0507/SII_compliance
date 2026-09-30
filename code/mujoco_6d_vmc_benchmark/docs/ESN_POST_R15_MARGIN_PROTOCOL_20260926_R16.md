# ESN post-R15 safety-margin protocol R16 (2026-09-26)

R15 offset -1 passed task+strict on all nine 9330--9345 development
conditions, then failed the original frozen blind set at fixture 9352 with
0.203829 mm maximum external penetration. Task success remained true. The
entire 9350--9357 set is development-exposed after that single evaluation and
will never again be described as blind.

Before inspecting or fitting to R15 blind trajectories, R16 freezes a new
eight-condition blind plan in `configs/esn_r16_blind_plan_20260926.json`.
Fixtures 9360--9367 remain unopened until one fixed R16 checkpoint passes
task+strict on every exposed 9330--9357 condition. The strict gate remains
task success, grasp/lift success, valid physics, and maximum external
penetration no greater than 0.2 mm. A preferred development engineering
margin of 0.195 mm is reported separately and is not substituted for the
original gate.

R16 may use all failures and successes from 9330--9357 for diagnosis and
training. Deployment inputs remain proprio48 only. Fixture ID, geometry,
stage, clock, and success labels may not enter the deployed policy. Physics,
environment geometry, task gate, penetration gate, and the existing safety
filter are frozen. No failed rollout may be removed.

The 9360--9367 plan may be run once only after complete development
qualification. Cross-condition simulation robustness requires task+strict
8/8 on that single run. These simulation results do not establish real-robot
readiness.
