# Fixed-Base FR3 Tabletop Environment

## Purpose

Establish the normal-operation baseline before introducing compliance. The
robot must use an external RGB-D observation to plan and execute pick-and-place
motions in a cluttered tabletop scene. The robot base remains fixed.

## Scene v0: deterministic development scene

Use this scene first so failures are attributable to code rather than random
asset placement:

- tabletop: 1.20 m x 0.80 m, top height 0.70 m;
- FR3 base: fixed at the front-center of the table workspace;
- target object: one graspable box or YCB-like primitive;
- static clutter: 5--8 boxes/cylinders with partial occlusions;
- no dynamic obstacle in the first smoke benchmark;
- one fixed RGB-D camera and one optional wrist camera;
- collision geometry separated from visual geometry.

The initial object set should use simple primitives. YCB meshes can be added
after the perception/planning loop is stable.

## Scene v1: static clutter generalization

Randomize independently:

- target position and yaw;
- clutter object count, shape, size, and pose;
- target visibility ratio;
- camera pose and depth noise;
- table-side and backstop geometry;
- initial FR3 configuration.

The train/test split must hold out object arrangements, not only random seeds.

## Scene v2: dynamic obstacle challenge

Add one obstacle that is not part of the initial static map:

- slow predictable crossing;
- delayed appearance from behind clutter;
- random-acceleration motion;
- high-speed crossing;
- sudden stop or direction change.

The nominal controller is allowed to use the RGB-D scene observation. The
later student policy is not allowed to use obstacle geometry or contact truth.

## NUS-inspired closed loop

```text
observe -> maintain scene belief -> choose target grasp pose
        -> plan -> execute -> monitor
        -> if scene/task invalid: observe -> replan
```

For the fixed-base arm, navigation and base prepose are removed. The planning
problem is instead:

```text
q_start -> pre-grasp -> grasp -> lift -> carry -> place
```

Every candidate trajectory is checked against all FR3 links and the gripper.
The first implementation may use an offline collision-free trajectory; the
second implementation should replan during execution when a new obstacle is
observed.

## Recommended milestones

1. Known target, empty table, fixed grasp pose.
2. Known target, static clutter, collision-free planning.
3. Random target/clutter, grasp-pose generation.
4. Occlusion and scene refresh, execution-time replanning.
5. Dynamic obstacle, nominal perception-based avoidance.
6. Same scenes with perception delayed or disabled for the compliance study.

## Evaluation contract

Report separately:

- perception success;
- valid grasp-pose generation;
- collision-free planning success;
- execution success;
- object grasp success;
- object placement success;
- collision rate by FR3 link;
- replanning count and latency;
- minimum clearance;
- path length and task time.

Do not combine a planning failure, a perception failure, and a collision into
one generic failure category. The purpose of this environment is to show where
the normal NUS-inspired loop succeeds before compliance is evaluated.
