# FR3 tabletop dynamic grasp benchmark: v3

## Reproducibility

- Date: 2026-08-30
- Scene: `fr3_office_v36_rgbd_proxy.xml`
- Runner: `nus_fr3_mujoco.tabletop_demo`
- Mode: wrist RGB-D nominal layer with dynamic obstacle and online horizon supervision
- Artifacts: `fr3_recheck_v3.gif`, `fr3_recheck_v3.json`

## Result

| Metric | v3 |
|---|---:|
| Grasp success | `True` |
| Placement success | `True` |
| Placement error | `0.0577 m` |
| Receding-horizon checks | `93` |
| Plan switches | `2` |
| Active-view accepted | `7` |
| Active-view rejected | `0` |
| Dynamic-obstacle contact steps | `0` |
| Maximum dynamic-obstacle force | `0 N` |
| Illegal target-contact steps | `0` |
| Finite-state check | `True` |

The offline full-trajectory swept-volume audit still reports static keyboard
penetration for this route (`collision_count=212`, minimum clearance
`-0.0248 m`). This is separate from the runtime dynamic-obstacle result: the
moving benchmark obstacle made zero contact, but the nominal route is not yet
a fully collision-free solution with respect to every static desk object.

The grasp validation recorded simultaneous left- and right-finger contact,
with target tilt `1.77 deg`. The selected plan was `approach_left+place_left`;
the supervisor switched once during approach and once during carry, then kept
the place corridor fixed during `PLACE DESCEND` and release.

## Changes from the failed continuation

1. Restored the validated Panda side-grasp orientation and the `+Y` grasp
   waypoint. A front-side orientation avoided the keyboard but put both
   fingers outside the target cylinder.
2. Restored three lateral approach candidates so the supervisor can select a
   feasible branch before grasp commitment.
3. Added negative-clearance events to `FR3SweptVolumeChecker`, so true
   penetration is visible in the JSON instead of being conflated with
   near-collision counts.
4. Disabled candidate switching once `PLACE DESCEND` starts. This prevents
   last-second place-waypoint oscillation from changing the captured
   hand/object transform and causing a placement miss.

The static keyboard penetration is the next planning issue to resolve. The
current v3 should therefore be used as a grasp-and-dynamic-obstacle baseline,
not as the final static clutter planner.

The result remains a deterministic simulation proof-of-concept. The nominal
checker still uses a benchmark RGB-D prediction proxy and the grasp latch is a
validation aid; neither should be presented as the final contact-only,
uncertainty-robust real-robot method.
