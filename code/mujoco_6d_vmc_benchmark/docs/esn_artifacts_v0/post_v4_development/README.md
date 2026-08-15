# Post-V4 jerk-aware ESN/RL development pool

## Purpose and boundary

This is a new physical MuJoCo development pool created **after** the frozen
Fan Ye ESN-VMC V4 result was recorded. It is the only pool permitted for the
next jerk-aware residual / RL development stage. The completed V4 final
holdout must not be reread for hyperparameter selection, reward selection,
early stopping, or controller changes.

The pool uses the same fixed-Panda-WBC physical rod scene and validity gates,
but four timing realizations that do not overlap prior ESN train/validation,
V4 development pilot, or V4 final test:

| split | fresh rod start times (s) | effective fixtures |
|---|---|---:|
| development train | 0.965, 1.165 | 9 |
| development validation | 0.970, 1.175 | 9 |
| final test | none | 0 |

The resulting set is not a new final benchmark. It is development data only.

## Physical-screening result

All candidates were screened with a frozen six-dimensional `vmc_gated`
selector, `reference_source=fixed_panda_wbc`, physical rod-hand contact,
matched no-rod task, stable 5 mm / 80 ms rejoin, lift/hold success and no hard
torque limit.

- candidates attempted: 20
- effective development fixtures: 18
- train / validation: 9 / 9
- effective approach-side counts: `negative_x=4`, `positive_x=2`,
  `negative_y=4`, `positive_y=4`, `negative_z=4`

Both `positive_x_c1_t1` candidates are retained as invalid calibration records:
they missed rod-hand contact and therefore also failed effective force,
impulse, and stable-rejoin gates. They are excluded from the effective splits,
not silently resampled or relabelled as controller failures.

## Next development protocol

The next controller must keep the deployed-information and safety boundary:

```text
WBC / proprioceptive history → Fan Ye ESN state → bounded 6-spring + return-drive residual
                             → positive/rate-limited projection
                             → torque feasibility scaling + slew limiter
```

It may optimize a jerk-aware reward on the 9 development-train fixtures, but
selection must occur only on the 9 development-validation fixtures. It may not
observe rod contact, force, obstacle state/geometry, collision normal, future
release time, fixture ID, or V4 outcomes. Any RL result must be compared to a
zero-residual / frozen analytic-teacher control under the same physical
fixtures before being called an improvement.

## Artifact

- [screening manifest](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/post_v4_development/esn_post_v4_development_manifest.json)
- [Fan Ye ESN 84-D WBC actor-interface smoke](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/post_v4_development/fan_ye_esn_rl_interface_smoke.json)
- [online WBC-aware Gym zero-residual smoke](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark/docs/esn_artifacts_v0/post_v4_development/fan_ye_esn_wbc_rl_rollout_smoke.json)
