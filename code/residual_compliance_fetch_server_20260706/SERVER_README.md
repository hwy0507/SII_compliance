# Residual Compliance Fetch - Server Run Notes

This package is the clean server version of the latest arm-only residual
compliance project.

It intentionally excludes old `outputs/`, old GIFs, old debug records, and old
datasets. The included checkpoint is only a PPO warm start:

```text
runs/bc_body_locked_unfiltered_policy.pt
```

## Current Scope

The current task is contact-only residual compliance for the Fetch arm:

```text
upper-level nominal arm trajectory
  -> 7D arm joint velocity tracker
  -> contact/force feedback gate
  -> residual policy or analytic residual
  -> body-locked ManiSkill Fetch simulation
```

The simulator now locks non-arm joints after every physics step:

```text
root_x_axis_joint
root_y_axis_joint
root_z_rotation_joint
torso_lift_joint
head_pan_joint
head_tilt_joint
```

Only the 7D arm is allowed to move. This fixes the earlier misleading visual
behavior where the Fetch body/torso appeared to squat under impact.

## Included Files

```text
src/residual_compliance_fetch/      core controller and ManiSkill rollout code
scripts/                           dataset / BC / eval / PPO entry scripts
configs/default.yaml               current config placeholder
docs/progress.md                   full experiment history and conclusions
runs/bc_body_locked_unfiltered_policy.pt
README.md
SERVER_README.md
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

Use the same environment as the original local project if possible:

```bash
conda activate mobile_grasping_in_dynamic
```

The code expects at least:

```text
python 3.9
mani_skill
sapien
gymnasium
numpy
torch
Pillow / imageio / matplotlib for visualization
```

Before long runs, verify imports:

```bash
cd residual_compliance_fetch_server_20260706

python - <<'PY'
import torch
import mani_skill
import sapien
import gymnasium
import numpy
print("imports ok", "cuda", torch.cuda.is_available())
PY
```

## Quick Smoke Test

Run a small body-locked evaluation:

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

The important safety threshold is currently:

```text
allowed_penetration = 0.010 m
```

This means penetration over 1 cm is counted as collision.

## Current Empirical Status

Under the stricter 1 cm threshold, baseline is no longer trivially successful:

```text
baseline, 100 episodes:
  success_rate = 0.82
  collision_rate = 0.18
```

The analytic teacher and BC warm start are not final solutions:

```text
contact_compliance:
  success_rate = 0.80
  collision_rate = 0.20

bc_body_locked_unfiltered_policy:
  success_rate = 0.80
  collision_rate = 0.20
```

Interpretation:

```text
BC is only a warm start.
PPO should optimize the 1 cm safety objective directly.
Do not treat the analytic teacher as a perfect expert.
```

## Recommended Next Step On Server

The placeholder PPO entry point has been replaced by a real Gymnasium/SB3 PPO
pipeline:

```text
scripts/train_ppo_residual.py
scripts/evaluate_ppo_residual.py
src/residual_compliance_fetch/ppo_env.py
```

Run this package in a directory and conda environment that are separate from the
grasp-overlap project, for example:

```bash
mkdir -p /root/residual_compliance_fetch_ppo_20260706
conda create -n residual_fetch_ppo python=3.10 -y
conda activate residual_fetch_ppo
```

The PPO environment reuses the same ManiSkill rollout components as the analytic
demo: fixed Fetch body joints, 7D arm velocity control, dynamic crossing sphere,
contact/force proxy feedback, strict 1 cm collision threshold, metrics, and GIF
camera. PPO controls only a gated 7D residual arm velocity.

Recommended PPO design:

```text
policy action:
  7D residual joint velocity

base command:
  qdot_cmd = nominal_tracker(q_arm) + gated_residual

hard gates:
  no contact/force feedback -> residual forced to 0
  contact released -> residual decays with recovery_decay
  base/torso/head joints remain locked
```

Recommended observation:

```text
q_arm
q_target
q_target - q_arm
qdot_nominal
previous_residual
contact_depth
force_proxy_level
qvel_tracking_error
contact_level
active_link one-hot
```

Recommended reward:

```text
large penalty if max_penetration > 0.010 m
penalty for penetration depth
penalty for contact_steps
penalty for residual magnitude
penalty for jerk / action change
penalty for final arm error
bonus for reaching target without collision
bonus for reducing collision cases relative to baseline
```

Start PPO from:

```text
runs/bc_body_locked_unfiltered_policy.pt
```

Install SB3 if the server image does not already include it:

```bash
pip install "stable-baselines3[extra]>=2.3"
```

Small smoke train:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/train_ppo_residual.py \
  --total-timesteps 2048 \
  --n-envs 1 \
  --n-steps 128 \
  --batch-size 64 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --allowed-penetration 0.010 \
  --output-dir runs/ppo_smoke_contact_heavy
```

First real run:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/train_ppo_residual.py \
  --total-timesteps 300000 \
  --n-envs 1 \
  --n-steps 512 \
  --batch-size 256 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --allowed-penetration 0.010 \
  --sampler contact_heavy \
  --output-dir runs/ppo_residual_contact_heavy
```

Evaluate and render one complete execution GIF:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_ppo_residual.py \
  --model runs/ppo_residual_contact_heavy/ppo_residual_final.zip \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --episodes 20 \
  --deterministic \
  --record-gif \
  --include-records \
  --allowed-penetration 0.010 \
  --output-dir outputs/ppo_residual_eval
```

If PPO code is not implemented yet, first verify the current BC warm start:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 100 \
  --sampler contact_heavy \
  --render-mode none \
  --allowed-penetration 0.010 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --output-dir outputs/server_bc_strict_pen_100
```

## Useful Commands

Generate new body-locked expert records:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 500 \
  --sampler contact_heavy \
  --render-mode none \
  --include-records \
  --output-dir outputs/contact_heavy_body_locked_500
```

Build an unfiltered BC dataset:

```bash
python scripts/build_bc_dataset.py \
  --summary outputs/contact_heavy_body_locked_500/randomized_summary.json \
  --mode contact_compliance \
  --output data/contact_heavy_body_locked_500_unfiltered_bc.npz
```

Train BC:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/train_bc_policy.py \
  --data data/contact_heavy_body_locked_500_unfiltered_bc.npz \
  --epochs 80 \
  --output runs/bc_body_locked_unfiltered_policy.pt
```

Run strict evaluation with BC:

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 100 \
  --sampler contact_heavy \
  --render-mode none \
  --allowed-penetration 0.010 \
  --bc-checkpoint runs/bc_body_locked_unfiltered_policy.pt \
  --output-dir outputs/bc_body_locked_unfiltered_strict_pen_100
```

## Notes

The old filtered BC checkpoint performed worse than expected because hard
filtering removed many difficult contact cases. Prefer unfiltered BC as the PPO
warm start, then let PPO optimize the strict safety reward.
