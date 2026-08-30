# FR3 Fixed-Base Dynamic Replanning Benchmark v29

## Scope

This experiment is the first reportable normal-operation result for the
fixed-base FR3 tabletop platform. It retains the NUS paper's closed-loop
structure as a system inspiration:

```text
observe -> maintain scene state -> plan -> execute -> short-horizon check
        -> switch compatible candidate when a future collision is predicted
```

The experiment is not a line-by-line Fetch/ManiSkill port. The arm is a fixed
FR3 in a cluttered office desk scene with a Panda hand, wrist RGB-D camera,
and native MuJoCo joint-space torque control.

## Compared Conditions

| Condition | Scene | Short-horizon replanning | Dynamic obstacle contact | Task result |
| --- | --- | ---: | ---: | --- |
| Static baseline | office clutter only | 0 switches | 0 steps | grasp + placement success |
| Predictable dynamic | same scene + mocap crossing box | 2 switches | 0 steps | grasp + placement success |

Controller settings:

- policy period: `0.04 s`;
- supervisor period: `0.20 s`;
- prediction horizon: `0.60 s`;
- horizon sample interval: `0.06 s`;
- candidates: three approach corridors x three placement corridors;
- phase constraint: approach can change before pre-grasp; after commitment,
  only the same approach family is allowed; release and return are locked.

## Main Result

The predictable dynamic obstacle enters the planned carry corridor. The
supervisor detects future geometric penetration before the robot reaches the
obstacle and switches plans:

```text
7.00 s: approach_left+place_left   -> approach_left+place_center
8.00 s: approach_left+place_center -> approach_left+place_right
```

The executed dynamic-obstacle contact count is zero and the maximum measured
dynamic-obstacle contact force is `0 N`. The robot completes the grasp, carry,
release, retract, and return-home phases. Placement error at the release
instant is below the current `0.06 m` acceptance tolerance in both conditions.

## Metrics

### Static baseline

- total time: `15.20 s`;
- grasp success: `true`;
- placement success: `true`;
- placement error at release: `0.0386 m`;
- plan switches: `0`;
- predicted collision-triggered checks: `0`;
- dynamic obstacle contacts: `0`;
- nominal swept-volume penetrations: `0`.

### Predictable dynamic obstacle

- total time: `15.20 s`;
- grasp success: `true`;
- placement success: `true`;
- placement error at release: `0.0415 m`;
- plan switches: `2`;
- collision-triggered horizon checks: `12`;
- dynamic obstacle contacts: `0`;
- maximum dynamic-obstacle contact force: `0 N`;
- nominal swept-volume penetrations: `0`.

## Interpretation for the Group Meeting

The result supports the following claim only:

> A fixed-base FR3 can execute the cluttered tabletop pick-and-place task,
> and a NUS-inspired short-horizon closed loop can detect a predictable moving
> obstacle and switch among phase-compatible candidate trajectories without
> dynamic-obstacle contact.

It does not yet support the stronger compliance claim. The current dynamic
obstacle is kinematic and predictable, the target attachment still uses the
deterministic `MuJoCoGraspLatch`, and the nominal checker receives obstacle
state directly from the scripted benchmark. The next research step is to
replace this privileged predictor with RGB-D belief updates and then generate
teacher trajectories/contact labels for the encoder-only student compliance
policy.

## Files

- `fr3_office_v29_static.gif`
- `fr3_office_v29_static.json`
- `fr3_office_v29_dynamic.gif`
- `fr3_office_v29_dynamic.json`
- `scenes/fr3_office_v28_dynamic_predictable.xml` on the experiment server
