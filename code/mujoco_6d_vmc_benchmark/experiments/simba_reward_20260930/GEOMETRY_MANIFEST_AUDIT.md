# Office reward study: geometry, manifests and adapter validation

Date: 2026-09-30. These are preflight and implementation checks, not trained-policy test results.

## Geometry exclusion discovered before launch

The current combined_thick_corner_pillar_v4 geometry translates the pillar by
0.018 m per integer variant. Initial model audit with no policy or physics rollout found:

| Variant | Initial geometry |
|---|---|
| -4, -3, -2, -1, 0, 1, 2 | Passed |
| 3 | Failed: pillar mount intersects target object by approximately 1.036 mm |
| 4, 5 | Failed: pillar mount intersects target object by approximately 1.000 mm |
| 6 | Failed: pillar mount intersects target object by approximately 0.954 mm |

Thus the inherited training variants (-2,-1,3,4) must not be reused unchanged.
Recommended legal training variants: (-4,-3,-2,-1).
The geometry was not moved to make this test pass; invalid variants were excluded
before training. Dynamic physical validity and required contact coverage are still
separate evaluation gates and are not established by this initial audit.

## Frozen manifests

- Validation: /home/arm1/vmc_mujoco_runtime/reward_study_20260930/validation_manifest.json
- Evaluation: /home/arm1/vmc_mujoco_runtime/reward_study_20260930/test_manifest.json

Every one of the 8 exact manifest conditions passed initial geometry audit,
using the specified seed and variant. No policy was evaluated in these checks.

Validation has two cases, variants 0 and 1, seeds 190100001 and 190100002,
dt=1e-4. Evaluation has six cases with dt=5e-5:
- Known development layouts 0/1/2, seeds 2026091751 / 2026091852 / 2026091953.
- New fixed physical parameter draws on layouts 0/1/2,
  seeds 190200001 / 190200002 / 190200003.

All use the current v4 scene and current 2s-ball/3s-person/7s-rod schedule.
Reusing historical layout seeds does not make old and new scene/protocol results
interchangeable. These layouts have already been inspected in development;
the last three cases are held-out parameter draws, not unseen Office geometries.
Test results must not select checkpoint, tune reward, or train normalizers.
The validation and test manifests themselves are independent conditions, although
some layout IDs are shared. Do not claim a strict layout-disjoint validation/test split.

## Real physics no-op regression

Script:
 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/test_hooks_invariance.py

Result:
 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/hooks_invariance_64s/VALIDATION.json

Ran 6.4 seconds, dt=5e-5, seed2026093007, variant0, all events.
Compared unmodified zero-residual path (no hooks, no policy) with queued zero
policy plus new runtime reward hooks. Max difference was exactly zero for
time/qpos/qvel/ctrl/hand/ball/ball_velocity/cup/stage/object_position.
Compiled model hashes and all three audited metrics matched exactly.
128000 physical substeps were recorded per rollout.
The 6.4-second regression includes ball/human motion but does not reach the
scheduled rod event or assess full placement.

## Trainer integration regression

Script:
 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/test_training_adapter.py

Result directory:
 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/fake_physics_trainer_5001_v2/

Real official actor/critic, normalizers, replay, trainer, checkpoint and reward
were exercised with fake physical stepping for 5001 transitions / 4 SAC updates.
This crossed the 5000-step warmup boundary and passed. Fixed one scalar logging
condition in train.py: nested official update metric dictionaries cannot be
passed to numpy.isfinite; np.isscalar is used before conversion.
This test says nothing about policy performance or simulated physics.

## Evaluation runner

 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/evaluate.py

Loads the saved official config and normalization state, calls the actor with
training=False, and requires unchanged normalizer/update counts throughout
evaluation. Metrics and strict task/physical gates are taken from raw validator
JSON; all physical substeps and requested actions are retained.
A zero-action mode is available. Underlying Office duration must be >=6.2s;
55s remains the complete evaluation duration. No 55s policy evaluation has been
run by this audit task.
