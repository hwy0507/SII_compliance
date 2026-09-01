# NUS-Inspired FR3 Tabletop Benchmark

This directory defines a clean fixed-base FR3 benchmark inspired by the
closed-loop mechanism of the NUS `Visibility-Awared-Mobile-Grasping` project.
It is not intended to be a line-by-line port of the Fetch/ManiSkill code.

## Current branch result: v7 long-transfer rod task (2026-09-01)

`tabletop_demo.py --rod-task --dynamic-obstacle` now validates the current
long-transfer scenario: the rod is acquired from the three-camera RGB-D search,
carried from `[0.1821, -0.2834, 0.747]` to the blue-holder side target
`[0.54, -0.10, 0.747]` (a planned distance of `0.40214 m`), and finally rests
at `[0.5697, -0.0986, 0.7423]`. The blue `pen_holder` is a known scene
landmark, not an RGB-D-detected destination; the rod, in contrast, is detected
and axis-estimated before grasping from the RGB-D search.

The v7 metrics are: `grasp_success=True`, `placement_success=True`, final
placement error `0.03012 m`, dynamic-obstacle contacts `0`, non-positive
dynamic-clearance samples `0`, minimum physical dynamic clearance `0.01333 m`,
one RGB-D-triggered hold, one smooth recovery, and a selected
`LATERAL_WITH_LOW_CLEARANCE` displacement of `0.09588 m`.

The controller pauses its nominal pick/carry/place time during an active
avoidance episode. That detail is essential: it prevents an obstacle response
from consuming the nominal carry time and making the arm jump directly to a
late phase after recovery. A recovery begins only after two consecutive
collision-gated checks; stale RGB-D tracks are removed from the prediction
proxy when the obstacle is no longer visible.

Large v7 GIF/JSON artifacts remain server-only:

```text
/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/
  fr3_rod_long_transfer_blue_holder_dynamic_v7_20260901.gif
  fr3_rod_long_transfer_blue_holder_dynamic_v7_20260901.json
```

The following v17/v18d sections are retained as prior experiment history.

## Latest validated result: buffered conditional active avoidance (2026-09-01)

The current implementation has been re-run on the MuJoCo office tabletop
scene with fixed base RGB-D, root-mounted active-base RGB-D, wrist RGB-D, a
moving obstacle, and a receding-horizon supervisor. The nominal rod task has
no unconditional lift; the only avoidance action is created when fused RGB-D predicts a
blocked carry horizon:

| Metric | Result |
| --- | ---: |
| Two-finger grasp success | `True` |
| Placement success | `True` |
| Placement error | 0.00267 m |
| Dynamic-obstacle contact steps | 0 |
| Maximum dynamic-obstacle contact force | 0 N |
| Receding-horizon checks | 118 |
| Plan switches | 4 |
| Active-view accepted / rejected | 0 / 0 |
| Illegal target-contact steps | 0 |
| Finite-state check | `True` |
| Conditional obstacle avoidance actions | 1 |
| Three-camera visible steps | 23 |
| Nominal carry maximum hand height | 0.91594 m |
| Selected avoidance | 0.11687 m lateral |

The selected route uses three lateral approach candidates and preserves the
validated rod-task top-down pinch orientation. Once `PLACE DESCEND` begins, the
place candidate is locked to prevent release-time oscillation. The complete
metrics are stored on the server at
`outputs/fr3_rod_balanced_clearance_v17_20260901.json`; the matching
589-frame GIF is next to it. The conditional action record is explicitly tagged
`trigger=rgbd_predicted_carry_blockage`. The online search compares hold,
lateral, lower, away, and raise candidates in ascending displacement order.
It selected `0.11687 m` laterally with a vertical component of only
`-0.00060 m`; the final dynamic-contact audit remained `0 steps / 0 N`.

Earlier GIFs retained a conspicuous upright pose because carry IK was solved
from an unused high `q_lift` seed. Although the `LIFT` execution segment had
been deleted, interpolation to that opposite elbow branch recreated the same
large Cartesian arc. The current code removes the hidden seed, uses two low
carry waypoints on the grasp branch, and limits place goals to the continuous
top-down-pinch workspace. The physical carry maximum is now `0.92967 m`
instead of roughly `1.40 m` in the previous run.

This is a deterministic simulation proof-of-concept, not the final planner.
The current static swept-volume audit reports zero collisions and zero
near-collisions, while the independent dynamic-obstacle audit reports zero
contact steps and zero measured force.

## Simulator decision

Use native MuJoCo 3.x with the official-style `franka_fr3/fr3.xml` model
already installed on the experiment server. The reason is methodological: the
paper's new variable is whole-arm contact response, so the simulator must make
joint-level control, contact impulses, solver settings, and repeatable
high-rate rollouts easy to inspect. The existing project already has a tested
MuJoCo FR3 WBC/residual stack; duplicating the robot in ManiSkill would create
two contact models and make the sim-to-real story harder to audit.

## Research interpretation

The NUS paper is used as a system-design inspiration:

- maintain a scene belief from RGB-D observations;
- generate task-relevant grasp/pre-grasp poses;
- plan collision-free arm motion;
- execute while monitoring the scene and task state;
- re-observe and replan when the nominal plan becomes invalid.

Fetch-specific implementation choices are deliberately removed. The first
FR3 paper should establish that this closed-loop idea works on a fixed-base
arm before adding the encoder-only compliance student.

## First milestone

The first milestone is a standalone cluttered-tabletop manipulation benchmark:

```text
RGB-D scene observation
  -> object/obstacle scene representation
  -> target grasp pose generation
  -> fixed-base FR3 collision-free planning
  -> nominal trajectory tracking
  -> execution monitoring
  -> re-observation/replanning when needed
```

The compliance student is intentionally absent from this milestone. Its later
role is to handle the residual cases where external perception is delayed,
occluded, or unable to predict a fast obstacle.

## Wrist-camera migration

The first active-perception migration attaches a Panda-compatible RGB-D
camera to `fr3_hand`. The camera pose is therefore generated by the FR3 hand
pose rather than by a fixed world camera. The demo exposes both the wrist RGB
image and metric depth image, and labels the current observation target as
`TARGET` during grasp acquisition or `SWEPT_VOLUME` during lift/transport.

The demo now uses a damped 6D hand-pose IK for the waypoint set. This is an
important change from position-only IK: each waypoint specifies both where the
hand should go and which direction the wrist camera should face. The current
implementation is a migration probe, not the final NUS-style joint
viewpoint-and-motion optimizer. The next planner must select camera-aware
observation waypoints using visibility, occlusion, and predicted FR3 swept
volume, then replan from the updated RGB-D scene belief.

## Scripted grasp validation

The office demo uses a small target cylinder sized for the Panda finger gap.
During the close-to-lift transition, `MuJoCoGraspLatch` captures the measured
hand/object transform and updates the target freejoint with that transform at
each policy step. This makes the pick, lift, carry, and release behavior
visible and deterministic while the scene is being validated. It is not yet a
contact-only grasp-success model; the research benchmark should later replace
the latch with finger contact, friction, force, and object-retention checks.

## What is retained from NUS

Keep the scientific ideas that are useful for this paper:

- scene/task stages: observe, pre-grasp, grasp, lift, place;
- visibility-aware or observation-aware replanning;
- dynamic-obstacle benchmark protocol;
- collision checks over every FR3 link;
- the distinction between nominal planning and low-level recovery.

Replace Fetch-specific components as follows:

| NUS/Fetch concept | Fixed-base FR3 replacement |
| --- | --- |
| Fetch + torso + mobile base | fixed FR3 7-DoF arm |
| ManiSkill velocity controller | native MuJoCo nominal velocity servo |
| Fetch/VAMP whole-body state | FR3 joint state + MuJoCo FK/Jacobians |
| Fetch IKFast/TRAC-IK path | FR3-specific IK and collision filtering |
| SAPIEN contacts | MuJoCo contact constraints and `mj_contactForce` |
| Fetch capability/reachability maps | FR3 workspace/reachability sampling |
| ROS trajectory action | direct MuJoCo nominal trajectory execution |

## Future student deployment contract

The student receives no image, point cloud, obstacle pose, obstacle velocity,
distance field, contact truth, or simulator contact force. Its deployment
observation is causal and proprioceptive:

```text
q, qdot, commanded qdot, WBC pose/twist error, short temporal history
```

The teacher may use obstacle geometry, velocities, contact force, and future
rollout labels only during offline training. The student should output a
bounded joint-velocity residual and a compliance/authority scale; a shared
safety adapter enforces joint, acceleration, torque, and slew-rate limits.

## Server layout

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
/home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3/fr3.xml
/home/arm1/vmc_mujoco_runtime/.venv/bin/python
```

The contract and trajectory layers are intentionally dependency-light, so they
can be smoke-tested locally. MuJoCo experiments run on the server through the
independent migration directory and the FR3 Menagerie model.

## Latest continuation (2026-08-30)

The continuation work keeps the validated Panda side-grasp geometry and adds
three safeguards:

1. Candidate switching is frozen once the robot commits to pre-grasp,
   descent, closure, or lift. This prevents an online place-candidate switch
   from replaying an earlier grasp stage and invalidating the latch. Place
   alternatives remain available during the carry corridor.
2. The predictable crossing obstacle is scheduled for the carry interval
   (`enter=10.4 s`, `contact=11.2 s`, `exit=13.0 s`) so RGB-D active-view
   behaviour is exercised while the object is being transported.

Large GIF outputs and server-side run logs stay on the runtime host and are not
part of the Git working tree. Before claiming a final collision-free result,
rerun the full-resolution server experiment and check both
`swept_volume_report.collision_count` and the dynamic contact metrics in the
generated JSON.

The latest server recheck moved the three placement candidates to the open
front area of the desk (`y=-0.30 m`) and raised the dynamic crossing profile to
`z=1.70 m`. This preserved successful grasp/release and reduced the static
keyboard collision count from 212 to 58 while reducing dynamic-obstacle robot
contacts to zero. The remaining 58 static samples are concentrated in the
original pre-grasp transition and still require a geometry-preserving bypass.


## Buffered safety-gate validation (v17)

The dynamic-obstacle execution checker now rejects zero-distance proxy or obstacle-boundary candidates. The prediction proxy is inflated by 0.030 m and the selected escape must keep an additional 0.020 m positive proxy clearance. In the 2026-09-01 server run, the RGB-D prediction triggered one `CONDITIONAL_OBSTACLE_AVOIDANCE`, selected a 0.11687 m lateral offset, and retained 0.02868 m proxy clearance; the independent dynamic contact audit remained 0 steps / 0 N.
