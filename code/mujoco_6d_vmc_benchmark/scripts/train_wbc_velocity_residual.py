#!/usr/bin/env python3
"""Train matched current-state MLP or Fan Ye ESN WBC-residual actors."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, replace
from pathlib import Path

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize

from wbc_velocity_residual_env import (
    PandaWBCVelocityResidualEnv,
    VelocityResidualFixture,
    VelocityResidualRewardConfig,
)
from wbc_velocity_residual_core import VelocityResidualSafetyConfig


def load_development_fixtures(path: Path, split: str) -> tuple[VelocityResidualFixture, ...]:
    """Load only post-V4 development data; the frozen final holdout is rejected."""

    manifest = json.loads(path.read_text())
    if manifest.get("reference_source") != "fixed_panda_wbc" or "post_v4_development" not in path.as_posix():
        raise ValueError("direct ESN training requires the isolated post-V4 fixed-WBC development manifest")
    rows = manifest.get("splits", {}).get(split, [])
    if split not in ("train", "validation") or not rows:
        raise ValueError("training fixture split must be non-empty train or validation")
    return tuple(VelocityResidualFixture(
        rod_stroke_m=float(row["rod_stroke_m"]),
        rod_height_m=float(row["rod_height_m"]),
        rod_start_time_s=float(row["rod_start_time_s"]),
        grasp_time_s=float(row.get("grasp_time_s", 2.40)),
        rod_approach_side=row.get("rod_approach_side", "negative_y"),
        rod_center_x_m=float(row.get("rod_center_x_m", 0.55)),
        rod_center_y_m=float(row.get("rod_center_y_m", 0.0)),
    ) for row in rows)


def reward_profile(name: str) -> VelocityResidualRewardConfig:
    base = VelocityResidualRewardConfig()
    if name == "balanced":
        return base
    if name == "contact_safe":
        return replace(
            base,
            position_error_weight=0.035,
            slowdown_weight=0.004,
            yield_magnitude_weight=0.003,
            contact_impulse_weight=0.100,
            post_release_error_weight=0.085,
        )
    if name == "recovery_priority":
        return replace(
            base,
            contact_impulse_weight=0.035,
            post_release_error_weight=0.160,
            recovery_progress_weight=0.080,
            recovery_jerk_weight=0.003,
        )
    if name == "impulse_constrained":
        # Preserve the ESN-v2 rejoin objective while making loading impulse a
        # stronger training cost.  Unlike the earlier contact_safe profile, the
        # post-release/recovery terms remain active so safety is not obtained by
        # simply giving up the recovery task.
        return replace(
            base,
            contact_impulse_weight=0.090,
            post_release_error_weight=0.120,
            recovery_progress_weight=0.075,
            recovery_jerk_weight=0.003,
            slowdown_weight=0.004,
            yield_magnitude_weight=0.003,
        )
    raise ValueError(f"unknown reward profile: {name}")


def make_env(
    *,
    menagerie: Path,
    fixtures: tuple[VelocityResidualFixture, ...],
    model_npz: Path,
    summary_json: Path,
    observation_mode: str,
    reward_config: VelocityResidualRewardConfig,
    rank: int,
    seed: int,
    no_rod_every: int,
    residual_window_end_at_grasp: bool,
    directional_phase_projection: bool,
):
    def factory() -> PandaWBCVelocityResidualEnv:
        rod_enabled = no_rod_every <= 0 or rank % no_rod_every != 0
        return PandaWBCVelocityResidualEnv(
            menagerie=menagerie,
            fan_ye_model_npz=model_npz,
            fan_ye_train_summary_json=summary_json,
            observation_mode=observation_mode,
            fixtures=fixtures,
            rod_enabled=rod_enabled,
            safety_config=VelocityResidualSafetyConfig(directional_phase_projection=directional_phase_projection),
            reward_config=reward_config,
            residual_window_end_at_grasp=residual_window_end_at_grasp,
            seed=seed + rank,
        )
    return factory


def linear_learning_rate(initial: float, final: float):
    def schedule(progress_remaining: float) -> float:
        return final + (initial - final) * progress_remaining
    return schedule


class ResidualCheckpointCallback(BaseCallback):
    """Atomically pair PPO weights with their observation-normalization state."""

    def __init__(self, save_freq: int, save_dir: Path) -> None:
        super().__init__()
        self.save_freq = int(save_freq)
        self.save_dir = save_dir

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq != 0:
            return True
        self.save_dir.mkdir(parents=True, exist_ok=True)
        stem = f"ppo_wbc_residual_{self.num_timesteps}_steps"
        self.model.save(self.save_dir / stem)
        environment = self.model.get_env()
        if not isinstance(environment, VecNormalize):
            raise RuntimeError("WBC residual checkpoint environment must be VecNormalize")
        environment.save(self.save_dir / f"{stem}_vecnormalize.pkl")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fixture-split", choices=("train", "validation"), default="train")
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--observation-mode", choices=PandaWBCVelocityResidualEnv.observation_modes, required=True)
    parser.add_argument("--reward-profile", choices=("balanced", "contact_safe", "recovery_priority", "impulse_constrained"), default="balanced")
    parser.add_argument("--total-timesteps", type=int, default=1_000_000)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260820)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--no-rod-every", type=int, default=4, help="Make every Nth environment a matched no-rod task; <=0 disables.")
    parser.add_argument("--checkpoint-interval", type=int, default=100_000)
    parser.add_argument("--residual-window-end-at-grasp", action="store_true", help="Return residual authority to fixed WBC from gripper-close onward.")
    parser.add_argument("--directional-phase-projection", action="store_true", help="Constrain yield/rejoin velocity to the causal WBC-error half-space.")
    parser.add_argument("--resume", type=Path, default=None)
    args = parser.parse_args()
    if args.total_timesteps < 1 or args.n_envs < 1 or args.checkpoint_interval < 1:
        raise ValueError("timesteps, n-envs, and checkpoint interval must be positive")
    fixtures = load_development_fixtures(args.fixture_manifest, args.fixture_split)
    rewards = reward_profile(args.reward_profile)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MUJOCO_GL", "egl")
    torch.set_num_threads(1)
    factories = [make_env(
        menagerie=args.menagerie,
        fixtures=fixtures,
        model_npz=args.fan_ye_model_npz,
        summary_json=args.fan_ye_train_summary_json,
        observation_mode=args.observation_mode,
        reward_config=rewards,
        rank=rank,
        seed=args.seed,
        no_rod_every=args.no_rod_every,
        residual_window_end_at_grasp=args.residual_window_end_at_grasp,
        directional_phase_projection=args.directional_phase_projection,
    ) for rank in range(args.n_envs)]
    env = SubprocVecEnv(factories, start_method="spawn")
    env = VecMonitor(env, filename=str(args.output_dir / "monitor.csv"))
    env = VecNormalize(env, norm_obs=True, norm_reward=False, clip_obs=10.0)
    if args.resume is None:
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            seed=args.seed,
            device=args.device,
            n_steps=512,
            batch_size=256,
            n_epochs=5,
            learning_rate=linear_learning_rate(2e-4, 5e-5),
            gamma=0.995,
            gae_lambda=0.95,
            clip_range=0.15,
            target_kl=0.015,
            ent_coef=0.003,
            vf_coef=0.5,
            max_grad_norm=0.5,
            policy_kwargs={"net_arch": [256, 256]},
            tensorboard_log=str(args.output_dir / "tensorboard"),
        )
    else:
        model = PPO.load(args.resume, env=env, device=args.device)
    metadata = {
        "algorithm": {
            "current_mlp": "PPO readout over deployable current WBC state and tracking errors",
            "fan_ye_esn": "PPO readout over deployable current WBC state/errors plus frozen Fan Ye v1 reservoir state",
            "fan_ye_multiscale_esn": "PPO readout over deployable current WBC state/errors plus fixed fast/slow Fan Ye reservoir states",
        }[args.observation_mode],
        "controller_family": "independent_wbc_velocity_residual",
        "uses_vmc": False,
        "action_contract": {
            "policy_dimension": 7,
            "policy_action": "neutral-zero slowdown request plus normalized 6-D Cartesian yield velocity",
            "physical_action": "WBC velocity scale in [0.2,1.0] plus bounded world-frame Cartesian yield twist",
            "shared_safety": asdict(VelocityResidualSafetyConfig()),
        },
        "observation_contract": {
            "mode": args.observation_mode,
            "dimension": {"current_mlp": 32, "fan_ye_esn": 96, "fan_ye_multiscale_esn": 160}[args.observation_mode],
            "current_input": ["q(7)", "qdot(7)", "fixed_WBC_task_twist(6)", "measured_WBC_pose_error(6)", "measured_WBC_twist_error(6)"],
            "reservoir_state_dimension": {"current_mlp": 0, "fan_ye_esn": 64, "fan_ye_multiscale_esn": 128}[args.observation_mode],
            "reservoir_time_constants_s": None if args.observation_mode != "fan_ye_multiscale_esn" else [0.04253725603074088, 0.14001593770536352],
            "excluded": ["contact", "force", "rod state", "obstacle geometry", "future release", "fixture id"],
        },
        "fairness_contract": "Compared modes use the same deployable current state/errors, action, safety layer, PPO network, reward, fixtures, seed, and step budget; ESN variants differ only by fixed reservoir memory.",
        "residual_window_end_at_grasp": args.residual_window_end_at_grasp,
        "directional_phase_projection": args.directional_phase_projection,
        "reward_profile": args.reward_profile,
        "reward_config": asdict(rewards),
        "total_timesteps_requested": args.total_timesteps,
        "n_envs": args.n_envs,
        "seed": args.seed,
        "no_rod_every": args.no_rod_every,
        "fixture_manifest": str(args.fixture_manifest),
        "fixture_split": args.fixture_split,
        "fixtures": [asdict(fixture) for fixture in fixtures],
        "fan_ye_fixed_reservoir": {
            "model_npz": str(args.fan_ye_model_npz),
            "train_summary_json": str(args.fan_ye_train_summary_json),
        },
        "holdout_policy": "V4 final is frozen and excluded from training/model selection.",
    }
    (args.output_dir / "training_metadata.json").write_text(json.dumps(metadata, indent=2, default=lambda value: value.tolist()) + "\n")
    callback = ResidualCheckpointCallback(
        save_freq=max(1, args.checkpoint_interval // args.n_envs),
        save_dir=args.output_dir / "checkpoints",
    )
    try:
        model.learn(
            total_timesteps=args.total_timesteps,
            callback=callback,
            progress_bar=False,
            reset_num_timesteps=args.resume is None,
        )
        model.save(args.output_dir / "ppo_wbc_residual_final")
        env.save(args.output_dir / "vecnormalize.pkl")
    finally:
        env.close()


if __name__ == "__main__":
    main()
