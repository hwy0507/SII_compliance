# ESN proposed follow-up (2026-09-25)

## Frozen baseline

The frozen proprio48 ESN checkpoint is `outputs/teacher_history_diagnostic_20260923_r1_archive/frozen_models/esn.npz` (SHA256 `0f9d1c2970bbf9e35f9748eb68ae73c84340e6f4e193f3ee37e584970337975a`). Under the existing six-condition protocol it is task-success `1/6`, strict gate `0/6`. It is not evidence of real-world readiness.

## Physical evidence

All entries below use the existing panel geometry, unchanged task gate, unchanged safety filter, 24 s duration, and 480000 MuJoCo steps at 50 microseconds. The 9301 frozen/local rerun is a platform parity check; the new models are development diagnostics, not replacements for the frozen result.

| checkpoint / fixture | task | lift (m) | endpoint error (mm) | substep RMSE (mm) | peak torque (N m) | peak speed (m/s) |
|---|---:|---:|---:|---:|---:|---:|
| frozen ESN, 9301 local | 0 | 0.2138 | 45.5 | 131.8 | 36.94 | 0.1436 |
| history adapter, 9301 | 0 | 0.0042 | 272.8 | 232.1 | 38.65 | 0.1540 |
| on-policy readout, 9301 | 0 | 0.0317 | 225.9 | pending report | 41.13 | pending |
| beta=0.10 blend, 9300 | 0 | 0.2045 | 47.9 | 117.6 | 40.30 | 0.1391 |
| beta=0.10 blend, 9301 | 1 | 0.2463 | 6.3 | 152.1 | 36.56 | 0.1428 |
| beta=0.10 blend, 9302 | 0 | 0.1682 | 90.4 | 184.0 | 36.50 | 0.1503 |
| beta=0.20 blend, 9301 | 0 | 0.0319 | 226.1 | 215.0 | 41.12 | 0.1393 |

The beta=0.10 result is a fixed development blend of the frozen readout with one student-on-policy VMC relabel fit. It improves the selected 9301 fixture but remains `1/3` over the predeclared 9300/9301/9302 development set. Beta=0.20 fails on the same 9301 fixture. No failure was removed and no gate or threshold was changed.

## Interpretation

1. Offline teacher-history fitting alone is unsafe: the history adapter lowered action RMSE but made the physical rollout substantially worse.
2. One student-on-policy relabel pass can repair the fixture used for relabeling after a conservative beta=0.10 blend, but the cross-fixture result remains inconsistent. This is evidence for closed-loop distribution shift, not a completed ESN solution.
3. The next valid step is iterative student-on-policy collection across all three development fixtures, teacher relabeling with one frozen VMC configuration, and a predeclared beta/grid selected only on development data. Every iteration must be evaluated on untouched validation fixtures before any real-world claim.

## Artifacts

- `outputs/esn_history_adapter_20260925_r4/adapted.npz`, SHA256 `6cf764d9f881ac286a125e4ef4e8c0b2e15bf7ae073daff45c6217d080cb1f0f95`
- `outputs/esn_onpolicy_dagger_20260925_r1/onpolicy_adapted.npz`, SHA256 `47ccf3ab43d8afa3952b4420a233752012d5e57507b2350ec4c8290b21f225a6`
- `outputs/esn_onpolicy_blend_beta010_20260925/blended.npz`, SHA256 `018e9937d656c5c69608ad3b8db1acb8d7b4732b493a8e576908c27267ab3eab`
- `scripts/fit_esn_onpolicy_readout_20260925.py`
- `scripts/blend_esn_readout_20260925.py`
- `scripts/run_esn_development_fixture_20260925.py`

## Multi-trajectory DAgger physical rollout (2026-09-25)

The multi-trajectory readout checkpoint was physically evaluated before any
validation use.  The first launch with the system Python was retained as a
failed execution record (`ModuleNotFoundError: gymnasium`); the successful
reruns used the project `.venv-rl` interpreter and absolute checkpoint paths.
The simulation source and gates were unchanged.  Each run used 480,000
MuJoCo steps at 50 microseconds, the same 24 s loaded-lift fixture protocol,
and the same safety filter.

| seed | task | lift (m) | endpoint error (mm) | substep RMSE (mm) | peak torque (N m) | peak speed (m/s) | max penetration (mm) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 9300 | 0 | 0.12224 | 141.82 | 178.30 | 41.18 | 0.11882 | 0.20242 |
| 9301 | 0 | 0.12224 | 141.82 | 178.30 | 41.18 | 0.11882 | 0.20242 |
| 9302 | 0 | 0.12224 | 141.82 | 178.30 | 41.18 | 0.11882 | 0.20242 |

The authoritative peak torque for all three runs is 41.180027212549724 N m,
and the authoritative substep RMSE is 178.30347754653683 mm.  All three
reached `LOADED LIFT` and retained grasp/contact, but failed the task because
the final loaded-lift trajectory diverged (the same final state and raw
rollout hash were produced for all three seed values).  The strict 0.2 mm
penetration gate also failed at 0.202424746 mm.  These commands use the fixed
9301 loaded-lift scene protocol with the seed recorded in the scene metadata;
the identical adapted traces therefore must not be described as three
independent physical geometries.  The earlier beta=0.10 development outputs
remain the authoritative 9300/9301/9302 comparison set.

Outputs:

- `outputs/esn_onpolicy_dagger_multi_20260925_r1_9300_abs/`
- `outputs/esn_onpolicy_dagger_multi_20260925_r1_9301_abs/`
- `outputs/esn_onpolicy_dagger_multi_20260925_r1_9302_abs/`
- Adapted checkpoint SHA-256: `ade53e8a06b306c60519b900eb5f4e8a86d212cf20e8a1c2069bba4800e35f2e`
- Each `rollout.npz` SHA-256: `285c0a67f19f1fb70c76ff04486cfe94bbf6b7a24bd13eefdce46dda232ba010`
- Each metrics manifest records the frozen runner hashes and 480,000 finite
  samples.  The failed system-Python launch is preserved in
  `outputs/esn_onpolicy_dagger_multi_20260925_r1_9300/` with status 1.

This is a negative closed-loop result: teacher relabeling reduced the
development action RMSE (`0.08118 -> 0.02097`) but the adapted readout did not
complete any of the three development rollouts.  Therefore it is not eligible
for validation selection, real-environment claims, or replacement of the
frozen proposed checkpoint.  The next useful experiment is causal inspection
of this common failure state (readout output, projected action, and safety
intervention history), followed by a predeclared new on-policy iteration only
if the failure mechanism is understood; repeatedly scanning beta or filtering
until a success would be selection on the same development fixtures.

## Translation-only causal diagnostic (2026-09-25)

To test whether the full-readout regression was caused by changing slowdown and
rotational channels, a second development checkpoint adapted only action
channels 1--3 (translational yield).  Channels 0 and 4--6 were copied from the
beta=0.10 base checkpoint without modification.  Offline relabel RMSE changed
from `0.0811843` to `0.0603012`; checkpoint SHA-256 is
`06cdee0788188da935fd0359c65afe06559ad5d41d45098e5dbd658f5ccbc3e4`.

The physical result was still negative and identical for the fixed loaded-lift
scene replayed with seed values 9300/9301/9302: task `0`, endpoint error
18.008 mm, lift 0.25048 m, substep RMSE 162.047 mm, peak torque 37.894 Nm,
substep peak speed 0.12316 m/s, and maximum penetration 0.21034 mm.  The
checkpoint reached LOADED LIFT and retained grasp/contact, but failed the
unchanged 0.2 mm penetration gate.  The three raw rollouts are byte-identical
(`e5851f813cdb5ebd79ed9ebf08a98c9187530b3ad95e95423cdcc9ffc73d588`), as
expected from the deterministic fixed-scene runner; they are not independent
random geometries.

Artifacts: `scripts/fit_esn_onpolicy_translation_only_20260925.py`,
`outputs/esn_onpolicy_translation_only_20260925_r2/`, and
`outputs/esn_onpolicy_translation_only_20260925_r2_9300_abs/` (with the
9301/9302 deterministic replays).  This rules out the simple explanation that
only the non-translational channels caused the multi-readout failure.  It also
does not justify more same-scene coefficient scanning or any validation/real-
environment claim.

## Offline causal and coverage audit (2026-09-25)

The causal replay and state-coverage audits were run without MuJoCo and without
changing any checkpoint, safety filter, task gate, or threshold. The exact
checkpoint/trace inputs and hashes are recorded in
`outputs/esn_dagger_causal_audit_20260925_r2/audit.json` and
`outputs/esn_state_coverage_audit_20260925_r3/audit.json`.

The adapted multi-readout checkpoint replays the recorded physical action to
machine precision (RMSE `1.46e-16`, max absolute error `9.16e-16`). Thus the
negative rollout is not a loader or checkpoint mismatch. In loaded-lift, the
safety slew filter is active on `76.95%` of adapted samples (`82.71%` for
frozen ESN), with no amplitude clipping. The observation contract was checked
against source: `observation[39:45]` is the encoder-derived 6-D wrench used by
`SixDVirtualDynamics`; this is not a simple 3-D wrench slice error.

The state-coverage audit compares six frozen training traces, six held-out
traces, and the three deterministic student replays descriptively; held-out
statistics were not used for selection. Aggregate normalized feature RMS /
p95 / max is `1.1616 / 2.2608 / 16.5491` for training, `1.2481 / 2.3876 /
17.7513` for held-out, and `1.6732 / 3.2289 / 18.4573` for the student.
Reservoir-state norm RMS / p95 / max is `4.0185 / 4.9418 / 5.5450`,
`4.2028 / 5.2225 / 6.2039`, and `4.9492 / 6.1052 / 7.3301`, respectively.
The student reaches stage 3 at about `2.52 s` in all three deterministic
replays. This supports closed-loop distribution/history shift as the leading
working hypothesis, not a causal proof.

Artifacts:

- `tools/audit_esn_dagger_causal_20260925.py`, causal audit JSON SHA256
  `8e0213064aea52684919ca98c3be86ca290e75e8c1753a63a3bde73444c6d508`.
- `tools/audit_esn_state_coverage_20260925.py`, coverage audit JSON SHA256
  `16be8f58e9cf5f97cf42b206ff27b4b4dd05faef46c2472ccbc209f2256a995f`.

The next scientifically useful step is a predeclared iterative on-policy
collection/relabel pass across all development fixtures, followed by an
untouched validation evaluation. Repeated same-scene beta/filter scans are
not justified, and no real-environment readiness claim is made.

## R3 development collection and workspace audit (2026-09-25)

The frozen R3 protocol is in `ESN_DAGGER_ITERATION_PROTOCOL_20260925_R3.md`.
The new fixtures were run with the R2 checkpoint without changing the
observation contract, safety filter, physical timestep, task logic, or gate.

| fixture | task | lift (m) | endpoint error (mm) | peak torque (N m) | speed P95 (m/s) | max penetration (mm) | strict gate |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 9320 | 1 | 0.24424 | 8.53 | 37.49 | 0.06790 | 0.20770 | 0 |
| 9321 | 1 | 0.24535 | 7.13 | 35.65 | 0.06353 | 0.11417 | 1 |
| 9322 | 0 | 0.03250 | 221.56 | 35.67 | 0.05865 | 0.03480 | 0 |

R3 therefore has task success `2/3` and strict gate success `1/3`. It is not
eligible for blind evaluation or any real-environment claim. The raw rollout
SHA256 values are `b5cbb8aa8d76c23f4b47c652a75c0928b77a39fb688682c2acfe51028db90123`
(`9320`), `02c9c8c9fd6cffb5c335163143a6249ff3cef77070bad752a1aa6963a40240d0`
(`9321`), and `3d832aa83f0eb561e9242c605dfd080bb345ac8f925e44dbf462c1fa9a6f839`
(`9322`). All three output directories contain the finite rollout, physics,
contact, metrics, MJB, log, and status artifacts.

The R2 report references nine fitting rollouts, but only the three `9310--9312`
raw files can currently be recovered by exact SHA256 from the local output
tree; the other six referenced raw files are absent. The R3 protocol's planned
12-trajectory refit is therefore intentionally not run. Reconstructing missing
raw trajectories would change the fitting data and is not equivalent to
recovering the original experiment. A new fitting protocol must be frozen only
after the complete input set is restored or a new collection is explicitly
declared.

The apparent workspace loss during the run was a command working-directory
mapping error: the repository is mounted and writable at
`/home/airpig/桌面/hwy/compliance_control`, while commands launched from the
parent repository used relative `code/...` paths and saw no such directory.
Subsequent checks use the absolute repository path and verified the mount and
output files. No existing rollout was overwritten or deleted.
# 2026-09-26 safety/robustness continuation

R8--R13 are summarized in `docs/ESN_SAFETY_ROBUSTNESS_REPORT_20260926.md`.
The formal R10 checkpoint passes task+strict 3/3 on 9330--9332 and task 6/6,
strict 4/6 on 9340--9345. It solves 9332 where the VMC teacher and neutral WBC
both fail. Later safety replay retains task success but does not close the
strict gate on all development conditions, so the predeclared 9350--9357 blind
set was not run and no real-robot or cross-condition safety claim is made.
