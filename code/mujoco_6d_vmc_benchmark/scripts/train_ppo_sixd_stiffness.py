#!/usr/bin/env python3
"""Train state-feedback PPO for the physical six-spring MuJoCo benchmark."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.vec_env import SubprocVecEnv, VecMonitor, VecNormalize

from rl_sixd_stiffness_env import PandaSixDStiffnessEnv, default_fixtures
from stiffness_training_core import StiffnessActionConfig, training_contract


def make_env(menagerie: Path, rank: int, seed: int):
    def _factory() -> PandaSixDStiffnessEnv:
        return PandaSixDStiffnessEnv(menagerie=menagerie, fixtures=default_fixtures(), seed=seed + rank)
    return _factory


def linear_learning_rate(initial: float, final: float):
    """SB3 schedule from a conservative early rate to a stable late rate."""

    def schedule(progress_remaining: float) -> float:
        return final + (initial - final) * progress_remaining
    return schedule


class PairedPolicyCheckpointCallback(BaseCallback):
    """Save PPO weights and matching observation-normalization state together."""

    def __init__(self, save_freq: int, save_dir: Path) -> None:
        super().__init__()
        self.save_freq = save_freq
        self.save_dir = save_dir

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq != 0:
            return True
        self.save_dir.mkdir(parents=True, exist_ok=True)
        step = self.num_timesteps
        self.model.save(self.save_dir / f"ppo_sixd_{step}_steps")
        environment = self.model.get_env()
        if not isinstance(environment, VecNormalize):
            raise RuntimeError("PPO checkpoint environment is expected to be VecNormalize")
        environment.save(self.save_dir / f"ppo_sixd_{step}_steps_vecnormalize.pkl")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--total-timesteps", type=int, default=1_000_000)
    parser.add_argument("--n-envs", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--resume", type=Path, default=None, help="Optional PPO zip checkpoint.")
    args = parser.parse_args()
    if args.total_timesteps < 1 or args.n_envs < 1:
        raise ValueError("timesteps and n-envs must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MUJOCO_GL", "egl")
    torch.set_num_threads(1)
    env = SubprocVecEnv([make_env(args.menagerie, rank, args.seed) for rank in range(args.n_envs)], start_method="spawn")
    env = VecMonitor(env, filename=str(args.output_dir / "monitor.csv"))
    env = VecNormalize(env, norm_obs=True, norm_reward=False, clip_obs=10.0)
    batch_size = 256
    if args.resume is not None:
        model = PPO.load(args.resume, env=env, device=args.device)
    else:
        model = PPO(
            "MlpPolicy", env, verbose=1, seed=args.seed, device=args.device,
            n_steps=512, batch_size=batch_size, n_epochs=5,
            learning_rate=linear_learning_rate(2e-4, 5e-5),
            gamma=0.995, gae_lambda=0.95, clip_range=0.15, target_kl=0.015, ent_coef=0.003,
            vf_coef=0.5, max_grad_norm=0.5,
            policy_kwargs={"net_arch": [256, 256]},
            tensorboard_log=str(args.output_dir / "tensorboard"),
        )
    checkpoint = PairedPolicyCheckpointCallback(save_freq=max(1, 100_000 // args.n_envs), save_dir=args.output_dir / "checkpoints")
    metadata = {
        "algorithm": "PPO state-feedback; not CEM or a timed schedule",
        "total_timesteps_requested": args.total_timesteps,
        "n_envs": args.n_envs,
        "seed": args.seed,
        "action_config": training_contract(StiffnessActionConfig(base_kappa=(27.579838, 52.550787, 48.699427, 35.859580, 40.719830, 34.766858)))["action"],
        "policy_observation_contract": training_contract()["observation_fields"],
        "privileged_quantities_excluded": training_contract()["excluded_privileged_diagnostics"],
        "fixtures": [fixture.__dict__ for fixture in default_fixtures()],
        "optimization_changes_vs_run_003": {
            "n_epochs": "10 -> 5",
            "learning_rate": "constant 3e-4 -> linear 2e-4 to 5e-5",
            "clip_range": "0.20 -> 0.15",
            "target_kl": 0.015,
            "reward": "loading/recovery-aware internal reward; no privileged policy observation",
            "residual_gate": "smooth deployable position-error gate: 0 below 3 mm, full by 12 mm",
        },
    }
    (args.output_dir / "training_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    try:
        model.learn(total_timesteps=args.total_timesteps, callback=checkpoint, progress_bar=False, reset_num_timesteps=args.resume is None)
        model.save(args.output_dir / "ppo_sixd_final")
        env.save(args.output_dir / "vecnormalize.pkl")
    finally:
        env.close()


if __name__ == "__main__":
    main()
