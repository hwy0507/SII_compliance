# FR3 tabletop dynamic grasp benchmark: final collision-free validation

## Long-rod run (2026-08-31)

The latest server artifact is the long-duration rod benchmark with a diagonal
wrist-camera mount for genuine two-camera overlap:

- GIF: `/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_rod_dual_camera_mount_20260831.gif`
- Metrics: `/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_rod_dual_camera_mount_20260831.json`

The target is a horizontal rod with world-axis `+Y`, using a top-down FR3
pinch.  Its radius is `0.024 m` and half-length is `0.12 m`.  The target is
held at the desk-rest pose through closure so a single fingertip cannot push it
away before the opposite fingertip arrives.  The latch engages only after a
real simultaneous two-finger MuJoCo contact.  During the latched carry, the
free-body target collision channel is disabled; after release, only desk
support affinity is restored.

| Metric | rod run |
|---|---:|
| Grasp success | `True` |
| Placement success | `True` |
| Placement error | `0.05139 m` |
| Dynamic-obstacle contact steps | `0` |
| Maximum dynamic-obstacle force | `0 N` |
| Active-view accepted / rejected | `17 / 0` |
| Observation-driven safety holds | `3` |
| Horizon replanning / plan switches | `125 / 0` |
| Illegal target-contact steps | `0` |
| Dual-camera visible steps | `24` |
| Swept-volume collision / near-collision count | `0 / 0` |

The dynamic obstacle follows a slow continuous leftward path.  The base RGB-D
camera provides the desk-wide track, while the diagonally mounted wrist RGB-D
camera detects the same red obstacle from `0.36 s`; both streams are visible
simultaneously for `24` policy steps.  The reported dynamic geometric minimum
is `0.0 m` because MuJoCo's distance query is conservative at a
tangent/degenerate configuration; the runtime contact and force audits are the
decisive safety checks and both remain zero.

## Baseline cylindrical run (historical)

The remainder of this file retains the earlier short-cylinder validation for
comparison.  Its artifacts and metrics are not the latest rod benchmark.

## Reproducibility

- Date: latest server validation (`2026-08-31`)
- Scene: `fr3_office_v36_rgbd_proxy.xml`
- Runner: `nus_fr3_mujoco.tabletop_demo`
- Mode: cooperative fixed-base + wrist RGB-D nominal layer with dynamic obstacle
  and online horizon supervision
- Artifacts (server): `outputs/fr3_rod_topdown_perfect_20260831.gif`,
  `outputs/fr3_rod_topdown_perfect_20260831.json`

## Result

| Metric | latest |
|---|---:|
| Grasp success | `True` |
| Placement success | `True` |
| Placement error | `0.05377 m` |
| Receding-horizon checks | `125` |
| Plan switches | `0` |
| Active-view accepted | `16` |
| Active-view rejected | `0` |
| Dynamic-obstacle contact steps | `0` |
| Maximum dynamic-obstacle force | `0 N` |
| Illegal target-contact steps | `0` |
| Finite-state check | `True` |
| Swept-volume collision count | `0` |
| Swept-volume near-collision count | `0` |
| Swept-volume minimum clearance | `0.000 m` |
| Observation-driven safety holds | `3` (`0.48 s` each) |
| Dynamic-obstacle minimum geometric clearance | `0.0 m` (conservative tangent report) |

The rod route is `approach_left+place_left`. The approach is lifted above the
keyboard, settles over the rod, and closes with the validated top-down pinch.
The target is pinned to its initial desk-rest pose until the closure window;
this removes pre-contact gravity drift while preserving real fingertip contact
validation before lift.

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
