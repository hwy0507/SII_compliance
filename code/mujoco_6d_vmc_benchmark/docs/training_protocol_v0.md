# Six-Dimensional Stiffness Training Protocol v0

## Scope and sequence

This protocol prepares an RL-ready controller interface, but does **not** yet
claim a trained policy. The required sequence is:

1. evaluate the deterministic Latin-hypercube static design;
2. remove candidates failing the physical-task and safety gate;
3. use the resulting valid Pareto region to set the RL action envelope;
4. train a low-rate stiffness scheduler only after the static gate is passed;
5. evaluate frozen policies on held-out collision seeds and baseline ladder
   fixtures, never on the training fixture alone.

The fixed reference is still the reachable moving-reference proxy. Nothing in
this protocol makes a live WBC or real-robot claim.

## Policy interface

The policy action is a six-vector in channel order:

```text
a = [a_x, a_y, a_z, a_roll, a_pitch, a_yaw],  a_i ∈ [-1, 1]
```

It is updated at `25 Hz`, not each MuJoCo control step. Its commanded target
is mapped in log space:

```text
kappa_target = clip(kappa_base * exp(0.8 * a), kappa_min, kappa_max)
```

The controller applies a non-learned log-rate safety shield of
`1.6 s⁻¹`. Damping is recomputed from the fixed damping ratio as each channel
stiffness changes. The initial envelope is `kappa ∈ [8, 70]^6`, based on the
validated hard-fixture search; it is a starting safety envelope, not an
optimized claim.

## Deployment observation: 51 dimensions

Only signals plausibly available on the robot are allowed:

| Signal | Dimensions |
|---|---:|
| world-frame position error | 3 |
| world-frame orientation error | 3 |
| twist error | 6 |
| joint position / velocity | 14 |
| virtual-carriage displacement / velocity | 12 |
| applied torque ratio | 7 |
| previous policy action | 6 |
| **Total** | **51** |

The following simulation-only truth is excluded from the final policy
observation: rod contact boolean, rod force, contact penetration, rod command
or position, obstacle geometry/pose, and future collision phase. It may be
logged for diagnostics, validity gates, or privileged teacher experiments only.

## Curriculum and splits

`prepare_stiffness_training.py` creates a deterministic Latin-hypercube
manifest with train / validation / test partitions. The first-stage fixture
range intentionally stays near calibrated valid contact geometry:

| Variable | Range |
|---|---:|
| rod stroke | 0.155–0.180 m |
| rod height | 0.538–0.542 m |
| rod start time | 1.040–1.120 s |
| closure time | 2.40 s |

Rod direction, rod mass, contact solver, reference trajectory and torque
limits are held constant in the first stage. Direction/mass/contact variation
belongs to held-out robustness evaluation after a policy proves task-valid on
this stage.

## Validity gate and optimization rule

An episode is invalid if any of the following is false:

1. simulation stays finite;
2. rod physically contacts Panda `hand_collision`;
3. released end effector stably rejoins the `5 mm / 80 ms` trajectory tube;
4. the target is lifted and held at the end;
5. no arm joint reaches a hard torque limit; and
6. the matched no-rod episode passes the same task gate.

For training eligibility, a geometrical contact is not enough: retain only an
**effective collision** with peak rod--hand force at least `15 N` and impulse
at least `0.45 Ns`. This prevents the optimizer from obtaining a deceptively
small tracking error by selecting grazing or near-miss geometry.

For valid runs, do not collapse research conclusions to a single scalar
reward. Preserve a Pareto front minimizing paired rod offset, recovery RMSE,
rejoin latency, torque burden and jerk. A temporary scalar screening score may
accelerate search, but it cannot replace the multi-metric report.

## Reproducible preparation command

```bash
python scripts/prepare_stiffness_training.py \
  --output-dir outputs/training_prep_v0 \
  --train-samples 32 --validation-samples 8 --test-samples 8 \
  --seed 20260814
```

The generated manifest is an experiment plan, not a trained checkpoint. It
must be archived beside subsequent static-search and RL results.

To execute a resumable pilot of the first four samples on the server:

```bash
MUJOCO_GL=egl python scripts/run_static_stiffness_manifest.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --manifest docs/training_artifacts_v0/stiffness_training_manifest.json \
  --output-dir outputs/static_manifest_pilot --splits train --max-samples 4
```
