# Combined thick-corner + single-pillar ESN audit (2026-09-29)

This is an independent **development** fixture. It is not the frozen baseline
world, and all results below use `dt=1e-4`, not formal `dt=5e-5`. The actor is
canonical48D/action7, pure ESN (`hybrid_vmc_blend=0`); the safety threshold is
unchanged at 0.2 mm external penetration. Ball launch at 2 s is an opt-in
presentation condition, not the original t=0 formal condition.

## Geometry provenance

The flag `--combined-thick-corner-pillar-v1` was used while pillar geometry was
being developed. It **does not uniquely identify a world**. Compare archived
`rollout.mjb`/`rollout.xml` and source hashes, not the flag name alone.

| archived result | pillar center (m) | radius / half-height (mm) | MJB SHA256 prefix | task / strict |
|---|---|---|---|---|
| `combined_thick_corner_pillar_v1_esn_ridge_v1_dt1e4_20260929` | (.619,-.270,.710) | 4 / 10 | `8c2b0f81aea` | true / false |
| `combined_thick_corner_pillar_v1_teacher_v8_dt1e4_20260929` | (.619,-.270,.710) | 4 / 10 | `8c2b0f81aea` | false / false |
| `combined_thick_corner_pillar_v1_esn_ridge_v3_dt1e4_20260929` | (.600,-.360,.750) | 2 / 3 | `9280daf61d4e` | false / false |

The archived `v1` 2 mm candidate used scene-source SHA256
`11b41fee578603f40bf744da35b77605da5b8d64c29ad2de68090c63db366a8c`).
The archived 2 mm run used earlier source SHA256
`a85a1d9db689c01a7582340d7fb384bad64dd3af25eef50baa64016c5b175e3f`;
its archived MJB remains the physics authority. The evaluator now adds
diagnostic contact logging only; old results retain their original source hashes.
The later `v4` source and MJB are independently hashed below; the former
`v1` flag cannot stand in for either later world.

## Closed-loop evidence

`ridge_v1` (model SHA256 `1b1a58fec824cc1fa2d0b2a72d6b97f806ea913042ba74e2663d4a1e89d9433d`)
completed placement and retreat, but failed safety: external penetration
`0.943513 mm`, pillar contact `19.4125 s`. Independent physical-substep
recalculation gives 3-D position RMSE `43.9415 mm`, peak generalized actuator
torque `58.8085 Nm`, and peak end-effector linear speed `0.245539 m/s`.
All 1375 saved actions and 128-D reservoir states replay exactly (max error 0).

The same readout in the archived 2 mm world (`ridge_v3`) had external penetration
`0.125156 mm`, but stopped at `load_transfer`; pillar contact was only `0.0264 s`
and placement did not occur. Physical-substep recomputation gives RMSE
`46.4174 mm`, torque `58.3713 Nm`, speed `0.238788 m/s`. The teacher on the old
4 mm world also stopped at `load_transfer`, with `0.152511 mm` penetration and
`0.2465 s` pillar contact. Failed trajectories are retained, not excluded.

## Contact interpretation

For `ridge_v1`, rod force-bearing contact totals `1.0262 s` over physics
substeps, first/last at about `8.0724/13.9017 s`. Saved 25 Hz control bins have
a longest consecutive run with nonzero prior rod impulse from `8.12` to `10.36 s`;
the hand moved `48.5 mm` in x during those bins. This supports motion while the
rod was interacting, but **does not prove uninterrupted substep contact or
tangential slip**. The new evaluator diagnostic records the longest continuous
physical-substep run and hand displacement for future rollouts.

An XML/saved-state contact snapshot scan of `ridge_v1` first finds the payload
touching `office_v5_corner_top` at `10.48 s`, stage `carry`, after lift began at
`1.92 s` and carry began at `10.08 s`. Snapshot replay is not a force-bearing
substep audit, but it already rules out presenting this run as an observed
lift-phase corner impact. The new evaluator separately records force-bearing
payload/corner contact duration and peak by task stage. `rod_geom` also contacts
the corner slab at reset; it is a scene-prop contact, not evidence of robot
compliance or a satisfied target/corner interaction.

## Status

## Independently versioned v2 negative probe

The `--combined-thick-corner-pillar-v2` experiment is a separate world, not a
correction to v1. Its 15 s pure-ESN, `dt=1e-4` short probe is archived in
`outputs/combined_thick_corner_pillar_v2_probe15_dt1e4_20260929/` with raw
NPZ, XML/MJB, substep metrics, source/checkpoint hashes and the original failed
rollout. MJB SHA256 is
`f1fe21a8e05f2643f18384aa23553fc6adf3298b9a154463ac3456621e40dd7d`;
the ESN checkpoint SHA256 remains
`1b1a58fec824cc1fa2d0b2a72d6b97f806ea913042ba74e2663d4a1e89d9433d`.
The probe kept the 2 s ball launch and unchanged actuator/safety thresholds.

The 15 mm-radius pillar at `(.600,-.340,.700)` did not solve the full scene.
Moving the thick corner x from `.650` to `.640` caused force-bearing
corner/robot-hand contact from `0.7306 s`, before the payload was grasped.
The task remained in `align` at 15 s, with no payload/corner contact in lift.
The longest continuous physics-substep rod-contact run lasted `0.2371 s`,
but hand planar displacement was only `1.80 mm`; this does not demonstrate
a substantial rub while the rod remains engaged. External penetration was
`0.063049 mm`, but this short probe was not a task or strict success. Initial
reset geometry audit is retained in
`outputs/combined_thick_corner_pillar_v2_initial_audit_20260929.json`.
The result rules out simply translating the entire corner slab toward the
approach path; the next geometry must leave grasp/align clearance.

## v4 full-horizon development result

The separately flagged `--combined-thick-corner-pillar-v4` world preserved the
2 s ball-to-robot path and created force-bearing payload/corner contact during
lift. Its archived MJB SHA256 is
`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`.
The same pure-ESN ridge checkpoint as above was used (SHA256
`1b1a58fec824cc1fa2d0b2a72d6b97f806ea913042ba74e2663d4a1e89d9433d`),
with `hybrid_vmc_blend=0`, canonical48D/action7, seed `2026091751`, 55 s,
and development `dt=1e-4`. The exact evaluator arguments, source hashes and
unfiltered failed result are in
`outputs/combined_thick_corner_pillar_v4_full55_dt1e4_20260929/rollout.json`;
the raw trajectory, XML, MJB and 550,000 physical-substep samples are beside it.
Raw rollout JSON/NPZ SHA256 are respectively
`666dd558513748b6b84e8aa77ac5bd640175da05dc5f3415222af8fe8837dcf3`
and `d7ab26ee742f49bc2ea3c9ce0fa085593c3bc5f0a1db25a3c6217834b0bc50b3`.

Task and strict both failed; final stage was `load_transfer` with no placement.
The ball hit FR3 link6 at `2.0939 s` and rebounded. The longest uninterrupted
force-bearing rod contact was only `0.0349 s`, with `0.122 mm` hand planar
motion; the `0.8703 s` total rod contact is fragmented and does not demonstrate
continuous rubbing. Pillar contact was `0.0375 s`, below the original `0.4 s`
exposure requirement. Payload/corner force-bearing contact during lift totaled
`0.2080 s`; this does establish the requested lift-phase interaction, but not
completion or compliance success. External penetration peaked at `0.394114 mm`
on pillar/FR3 link6, above the unchanged `0.2 mm` limit. In load transfer the
best position error was `16.798 mm`, above the original `12 mm` stage gate,
so the robot never released the block. The three independently recomputed
physical-substep metrics were 3-D RMSE `47.0526 mm`, peak generalized torque
`58.0678 Nm`, and peak end-effector speed `0.272753 m/s`. All 1375 actions and
128-D reservoir states replayed with zero maximum difference.

This is a complete **negative development result**, not formal `dt=5e-5` evidence.
The next experiment must change only the pure-ESN policy on this archived world;
no geometry, gate, actor input, actuator limit or failed episode is discarded.

## Same-world pure-ESN output-gain ablation

The one-candidate gain `0.8` ablation was registered before execution in
`configs/esn_combined_thick_corner_pillar_v4_gain08_plan_20260929.json`.
It changed only the checkpoint's output gain from 1.0 to 0.8. The 55 s
`dt=1e-4` result is archived at
`outputs/combined_thick_corner_pillar_v4_gain08_full55_dt1e4_20260929/`.
The world MJB SHA256 was **identical** to the gain-1 run, and the candidate
checkpoint SHA256 was
`a31c9b92039a6e08850084500d981be70efec9cee629c0feebdfd5d6a5acf8d9`.
An independent audit in that directory replayed 1375 actions and reservoir
states with zero error and recomputed all three metrics from 550,000 physical
substeps. Raw rollout JSON/NPZ SHA256 were
`33a8443eb9dcd714cec46bfe433876f394d057cae4ad068a1b5c0924d4f7c9dd`
and `6f19eb830b0468734d35d6ffac75a0d828fb0eac1d9d5e2dc7f186f88a52cd50`.

| gain | task / strict | 3-D RMSE mm | peak torque Nm | peak speed m/s | external penetration mm | pillar contact s |
|---:|---|---:|---:|---:|---:|---:|
| 1.0 | false / false | 47.0526 | 58.0678 | 0.272753 | 0.394114 | 0.0375 |
| 0.8 | false / false | 43.1634 | 53.3077 | 0.096728 | 0.136818 | 0 |

The 0.8 run still rebounded the ball at `2.0929 s` and had lift-phase
payload/corner force-bearing contact (`5.6438 s`). Rod contact totaled
`2.5698 s`, but its longest uninterrupted physical-substep run was only
`0.0683 s` with `0.059 mm` hand planar motion, so the sustained rub objective
still lacks evidence. Load transfer never became ready: its best saved
position error was `14.986 mm` versus the unchanged `12 mm` gate, and no block
release occurred. The gain reduction trades away even the brief pillar
interaction; lower penetration alone does not establish obstacle robustness.
This is another negative development result. Formal evaluation remains locked.

## v3 closed-loop probe and a confounded ball path

`--combined-thick-corner-pillar-v3` kept the support slab at the v1 location,
and added a short inner corner face plus a connected bridge on the measured
payload lift path. A read-only replay of the *old* v1 state trajectory found
no pre-lift contact, but predicted payload/bridge contact during lift from
`2.68 s` and payload/face contact from `4.60 s`. This was only a geometric
screen, not closed-loop evidence.

The actual 15 s pure-ESN v3 probe is retained under
`outputs/combined_thick_corner_pillar_v3_probe15_dt1e4_20260929/`.
It diverged from the replay: bridge/robot contact began at `1.0963 s`,
top/robot contact at `2.2900 s`, and the policy remained in `align`. There
was no payload/corner contact by stage, no lift, and no task or strict pass.
External penetration peaked at `0.067802 mm`; RMSE/peak torque/peak speed
were `34.129 mm / 41.896 Nm / 0.097900 m/s` over this *short probe only*.
The longest continuous rod contact lasted `0.0170 s` with `0.037 mm`
hand motion. MJB SHA256 is
`1ac3312081d08c3c3ccd4e5f7d067a5ccafbf56d5108b9958bb06c1cb7019882`;
the raw rollout NPZ SHA256 is
`58fe683c6c304a8246347745a8d147a7bede494383813af7ab2745f2a30c8c4f`.
Source, actor checkpoint, parameters and seed are recorded in `rollout.json`.
The reset audit (`outputs/combined_thick_corner_pillar_v3_initial_audit_20260929.json`)
found no initial overlap, but could not predict this dynamic blockage.

Crucially, the 15 mm post used in v2/v3 also intersects the ball lane. At
`2.04 s` the v2/v3 ball was already at about `(.569,-.401,.643)` with velocity
`(-.557,-.264,-.608) m/s`, and neither probe recorded a ball/robot event.
The older 4 mm-post v1 rollout instead recorded a ball/FR3-link6 impact at
`2.0939 s`. Thus a v2/v3 low penetration number cannot be interpreted as
successful ESN response to the requested ball impact. These are failed,
confounded development fixtures; the next version must first preserve an
unobstructed ball-to-robot path and pre-grasp clearance, then demonstrate
dynamic lift contact. No formal `dt=5e-5` evaluation is unlocked.

- **Done:** original raw trajectories, world/model hashes, action/reservoir replay,
  and the three independent physical-substep metrics for the task-completing run.
- **In progress:** substep-level contact diagnostics for future runs on a single
  explicitly hashed world; the current 2 mm post is too small to serve as a
  convincing visible obstacle without a separately versioned fixture decision.
- **Not done:** one pure-ESN run simultaneously meeting task, strict safety,
  sustained rod rub, visibly meaningful pillar interaction, and lift-phase
  thick-corner contact. No formal rerun or cross-condition generalization claim
  is unlocked.

## Gain 0.95 follow-up

The pre-registered 0.95 output-gain candidate used the identical v4 MJB and
was run for the same 55 s at `dt=1e-4`; provenance is in
`configs/esn_combined_thick_corner_pillar_v4_gain095_plan_20260929.json` and
`outputs/combined_thick_corner_pillar_v4_gain095_full55_dt1e4_20260929/`.
The model SHA256 is
`dadd414bd35e3d9979d8f40f6b07fa288122eee833e842aed78933b8d6478c27` and the
world SHA256 remains `5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`.
Independent action/reservoir replay and substep recomputation passed.

Task/strict were false/false and the run remained in `lift` for the full
horizon. It rebounded the ball at `2.0945 s`; external penetration was only
`0.120669 mm`, RMSE `28.5777 mm`, peak torque `39.3901 Nm`, and peak speed
`0.083917 m/s`. Rod contact totaled `1.2963 s` but the longest continuous run
was `0.0218 s` with `0.024 mm` hand motion. No pillar or lift-phase corner
target contact was recorded, and the best lift position error was `13.716 mm`,
still above the unchanged 12 mm stage gate. The intermediate gain therefore
reduces physical excursions but loses task progression and provides no
continuous rubbing evidence. It is retained as a negative algorithm-only
screen; formal evaluation remains locked.

## Gain 0.98 follow-up

The pre-registered 0.98 output-gain candidate used the identical v4 MJB and
55 s `dt=1e-4` horizon. Model SHA256 is
`0471703cd9fec5a3ba0ef9fb7496953ca85eb8065e80af478ab259a93daac68c` and the
world SHA256 is unchanged. Independent action/reservoir replay and all
550,000-substep metric checks passed.

Task/strict were false/false and the run remained in `lift`. Ball rebound was
observed at `2.0945 s`; penetration was `0.173824 mm`, RMSE `32.2391 mm`,
peak torque `43.0499 Nm`, and peak speed `0.088481 m/s`. Lift had only
`0.0023 s` of corner-target contact; no pillar contact was recorded. Rod
contact totaled `0.4961 s`, with a longest continuous run of `0.0361 s` and
`0.105 mm` hand motion. Best lift position error was `14.228 mm`, above the
unchanged 12 mm gate. This intermediate point does not recover task progress
or sustained rubbing and remains a negative development result.
