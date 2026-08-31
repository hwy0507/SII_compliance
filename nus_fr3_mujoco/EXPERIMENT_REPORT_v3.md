# FR3 tabletop dynamic grasp benchmark: final collision-free validation

## Reproducibility

- Date: latest server validation (artifact suffix `20260901`)
- Scene: `fr3_office_v36_rgbd_proxy.xml`
- Runner: `nus_fr3_mujoco.tabletop_demo`
- Mode: wrist RGB-D nominal layer with dynamic obstacle and online horizon supervision
- Artifacts (server): `outputs/fr3_near_obstacle_final_20260901.gif`,
  `outputs/fr3_near_obstacle_final_20260901.json`

## Result

| Metric | latest |
|---|---:|
| Grasp success | `True` |
| Placement success | `True` |
| Placement error | `0.00756 m` |
| Receding-horizon checks | `93` |
| Plan switches | `1` |
| Active-view accepted | `7` |
| Active-view rejected | `0` |
| Dynamic-obstacle contact steps | `0` |
| Maximum dynamic-obstacle force | `0 N` |
| Illegal target-contact steps | `0` |
| Finite-state check | `True` |
| Swept-volume collision count | `0` |
| Swept-volume near-collision count | `0` |
| Swept-volume minimum clearance | `0.000 m` |

The selected route is `approach_center+place_left`. The approach is lifted in
front of the keyboard (`+Y=0.18`, `+Z=0.30`), settles at
`pre-grasp=target+[0,0.14,0.04]`, and closes at the validated side-grasp pose
`target+[0,0.105,0]`. The target is pinned to its initial desk-rest pose until
the closure window; this removes pre-contact sliding while preserving normal
MuJoCo contact dynamics during grasp and lift.

For visual evaluation, the dynamic box now crosses near the carry trajectory
at approximately `[x=0.78 -> 0.30, y=-0.10, z=1.28]` during `10.4--11.2 s`
and exits toward `[1.20, 0.80, 1.50]` by `13.0 s`. It is therefore visibly
close to the arm without remaining in the workspace during placement or
return-home.

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

The result remains a deterministic simulation proof-of-concept. The nominal
checker still uses a benchmark RGB-D prediction proxy and the grasp latch is a
validation aid; neither should be presented as the final contact-only,
uncertainty-robust real-robot method.
