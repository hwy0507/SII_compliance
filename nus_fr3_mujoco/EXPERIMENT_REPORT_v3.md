# FR3 tabletop dynamic grasp benchmark: final collision-free validation

## Reproducibility

- Date: latest server validation (artifact suffix `20260901`)
- Scene: `fr3_office_v36_rgbd_proxy.xml`
- Runner: `nus_fr3_mujoco.tabletop_demo`
- Mode: cooperative fixed-base + wrist RGB-D nominal layer with dynamic obstacle
  and online horizon supervision
- Artifacts (server): `outputs/fr3_dual_rgbd_motion_handoff_20260831.gif`,
  `outputs/fr3_dual_rgbd_motion_handoff_20260831.json`

## Result

| Metric | latest |
|---|---:|
| Grasp success | `True` |
| Placement success | `True` |
| Placement error | `0.03881 m` |
| Receding-horizon checks | `93` |
| Plan switches | `0` |
| Active-view accepted | `9` |
| Active-view rejected | `0` |
| Dynamic-obstacle contact steps | `0` |
| Maximum dynamic-obstacle force | `0 N` |
| Illegal target-contact steps | `0` |
| Finite-state check | `True` |
| Swept-volume collision count | `0` |
| Swept-volume near-collision count | `0` |
| Swept-volume minimum clearance | `0.000 m` |
| Observation-driven safety holds | `2` (`0.48 s` each) |
| Dynamic-obstacle minimum geometric clearance | `0.2004 m` |

The selected route is `approach_center+place_left`. The approach is lifted in
front of the keyboard (`+Y=0.18`, `+Z=0.30`), settles at
`pre-grasp=target+[0,0.14,0.04]`, and closes at the validated side-grasp pose
`target+[0,0.105,0]`. The target is pinned to its initial desk-rest pose until
the closure window; this removes pre-contact sliding while preserving normal
MuJoCo contact dynamics during grasp and lift.

For visual evaluation, the dynamic box now follows one continuous leftward
trajectory near the carry corridor: `[x=0.78 -> 0.30 -> -0.78, y=-0.45,
z=1.28]` during `10.4--13.0 s`. Both segments use the same X velocity
(`-0.60 m/s`), so the red box no longer reverses or jumps diagonally as if it
had been struck. The RGB-D tracker records the obstacle locally at
`t=11.04--11.28 s`; the safety shield inserts one `0.48 s` hold at `t=11.08 s`.
A direct per-cycle geometric audit finds the closest robot/obstacle pair at
`0.1880 m` for `fr3_right_finger_collision` at `t=11.28 s`, while runtime
contact remains zero.

The camera audit is based on the rendered wrist RGB-D pose. At the first
confirmed detection (`t=11.04 s`) the obstacle is within `39.9 deg` of the
optical axis; the camera keeps `PREDICTED_OBSTACLE` focus through the
`DYNAMIC SAFE HOLD`, reaching `33.6 deg` by `t=11.40 s`. Once the obstacle is
no longer visible and confidence decays, the controller returns to its normal
search focus.

The grasp validation recorded simultaneous left- and right-finger contact,
with target tilt `1.77 deg`. The selected plan was
`approach_center+place_left`; the smooth rerun completed without a plan switch,
then kept the place corridor fixed during `PLACE DESCEND` and release.

The dual-camera handoff is recorded in the metrics file: `base_rgbd` first
detects the obstacle at `t=0.00 s`, `wrist_rgbd` first detects it at
`t=11.04 s`, and the base camera reacquires it at `t=11.32 s` after brief arm
occlusion. The fused state triggers two safe holds while maintaining zero
contact.

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
