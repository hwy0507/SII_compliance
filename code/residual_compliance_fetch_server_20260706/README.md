# Residual Compliance Fetch - Clean Server Package

This is the clean server package for the current Fetch arm residual-compliance
project. It keeps only the latest code, docs, and the current BC warm-start
checkpoint. Old failed visualizations, old `outputs/`, and old datasets are not
included.

Current task definition:

```text
The upper-level planner provides the next nominal arm target/trajectory.
The low-level controller tracks that trajectory.
An obstacle may be unseen before contact.
The controller reacts only after contact / force-like feedback.
The arm should soften tracking, retreat/slide, then recover the nominal path.
```

Current scope:

```text
ManiSkill/SAPIEN Fetch simulation
fixed base
fixed torso
fixed head
7D arm joint velocity control only
one dynamic crossing obstacle
baseline vs analytic contact_compliance vs BC warm-start policy
```

Non-arm joints are locked after every physics step:

```text
root_x_axis_joint
root_y_axis_joint
root_z_rotation_joint
torso_lift_joint
head_pan_joint
head_tilt_joint
```

This fixes the earlier misleading visual issue where the robot body/torso
appeared to squat after impact.

## Included

```text
src/residual_compliance_fetch/      core controller and rollout code
scripts/                           eval / visualization / BC / PPO entry scripts
configs/default.yaml
docs/progress.md                   detailed experiment history and conclusions
runs/bc_body_locked_unfiltered_policy.pt
runs/bc_body_locked_unfiltered_policy.history.json
SERVER_README.md                   server run notes
```

Excluded on purpose:

```text
outputs/
data/*.npz
old GIFs
old failed visualizations
__pycache__/
```

## Environment

Use the same conda environment as the local reproduction if possible:

```bash
conda activate mobile_grasping_in_dynamic
cd residual_compliance_fetch_server_20260706
```

Check imports and CUDA:

```bash
python - <<'PY'
import torch
import mani_skill
import sapien
import gymnasium
import numpy
print("imports ok")
print("cuda available:", torch.cuda.is_available())
PY
```

## Smoke Test

Run a small body-locked strict-threshold evaluation:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 3 \
  --sampler contact_heavy \
  --render-mode none \
  --allowed-penetration 0.010 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --output-dir outputs/server_smoke_3
```

Expected modes:

```text
baseline
contact_compliance
bc_policy
```

## Current Empirical Status

The meaningful strict safety threshold is:

```text
allowed_penetration = 0.010 m
```

Under this 1 cm threshold, the latest local 100-episode result was:

```text
baseline:
  success_rate = 0.82
  collision_rate = 0.18
  mean_score = 73.895

contact_compliance:
  success_rate = 0.80
  collision_rate = 0.20
  mean_score = 72.072

bc_body_locked_unfiltered_policy:
  success_rate = 0.80
  collision_rate = 0.20
  mean_score = 72.065
```

Interpretation:

```text
The analytic controller is not a perfect teacher.
The BC policy mainly imitates the analytic controller.
BC is only a PPO warm start, not the final controller.
PPO should directly optimize the strict 1 cm contact-safety objective.
```

## PPO Next Step

Important: `scripts/train_ppo_residual.py` is currently a placeholder entry
point. Before long server training, implement it as a Gymnasium-compatible PPO
environment around the existing ManiSkill rollout logic.

Confirmed PPO setup:

```text
algorithm: PPO
policy action: 7D residual arm joint velocity
base command: qdot_cmd = nominal_tracker(q_arm) + gated_residual
warm start: runs/bc_body_locked_unfiltered_policy.pt
no contact / no force memory: residual is forced to 0
contact released: residual decays during recovery
non-arm joints remain locked
collision threshold: max_penetration > 0.010 m
```

Recommended observation:

```text
q_arm
q_target
q_target - q_arm
qdot_nominal
previous_residual
contact flag / contact memory
contact depth or penetration proxy
force proxy level
qvel tracking error
active contact link one-hot
```

Recommended reward:

```text
large penalty if max_penetration > 0.010 m
penalty for penetration depth
penalty for contact duration
penalty for residual magnitude
penalty for action jerk / abrupt changes
penalty for final arm tracking error
bonus for reaching target without severe collision
bonus for reducing collision cases relative to baseline
```

Before implementing PPO, verify the warm start on the server:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 100 \
  --sampler contact_heavy \
  --render-mode none \
  --allowed-penetration 0.010 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --output-dir outputs/server_bc_strict_pen_100
```

See `SERVER_README.md` and `docs/progress.md` for more detailed notes.
