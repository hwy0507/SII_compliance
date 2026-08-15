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

from rl_sixd_stiffness_env import Fixture, PandaSixDStiffnessEnv, default_fixtures
from stiffness_training_core import DRIVE_RESIDUAL_OBSERVATION_FIELDS, DriveResidualActionConfig, StiffnessActionConfig, training_contract


def load_fixture_manifest(path: Path, split: str) -> tuple[Fixture, ...]:
    """Load only a declared development split; V4 final manifests are rejected."""

    manifest = json.loads(path.read_text())
    if manifest.get("reference_source") != "fixed_panda_wbc" or "post_v4_development" not in path.as_posix():
        raise ValueError("Fan Ye RL requires the isolated post-V4 fixed_panda_wbc development manifest")
    rows = manifest.get("splits", {}).get(split, [])
    if split not in ("train", "validation") or not rows:
        raise ValueError("RL fixture split must be a non-empty development train or validation split")
    return tuple(Fixture(
        rod_stroke_m=float(row["rod_stroke_m"]), rod_height_m=float(row["rod_height_m"]), rod_start_time_s=float(row["rod_start_time_s"]),
        grasp_time_s=float(row["grasp_time_s"]), rod_approach_side=row["rod_approach_side"],
        rod_center_x_m=float(row["rod_center_x_m"]), rod_center_y_m=float(row["rod_center_y_m"]),
    ) for row in rows)


def make_env(menagerie: Path, fixtures: tuple[Fixture, ...], rank: int, seed: int, enable_drive_residual: bool, enable_energy_safety: bool, recovery_gate_hold_s: float, recovery_gate_taper_s: float, recovery_error_weight: float, recovery_progress_reward: float, action_change_penalty: float, residual_magnitude_penalty: float, recovery_tube_time_penalty: float, recovery_tube_radius_m: float, contact_impulse_penalty: float, recovery_jerk_weight: float, jerk_reference_mps3: float, kappa_max_log_rate_per_s: float, drive_max_log_rate_per_s: float, reference_source: str, fan_ye_model_npz: Path | None, fan_ye_train_summary_json: Path | None):
    def _factory() -> PandaSixDStiffnessEnv:
        return PandaSixDStiffnessEnv(
            menagerie=menagerie, fixtures=fixtures, enable_drive_residual=enable_drive_residual, enable_energy_safety=enable_energy_safety,
            recovery_gate_hold_s=recovery_gate_hold_s, recovery_gate_taper_s=recovery_gate_taper_s, recovery_error_weight=recovery_error_weight,
            recovery_progress_reward=recovery_progress_reward, action_change_penalty=action_change_penalty,
            residual_magnitude_penalty=residual_magnitude_penalty, recovery_tube_time_penalty=recovery_tube_time_penalty,
            recovery_tube_radius_m=recovery_tube_radius_m,
            contact_impulse_penalty=contact_impulse_penalty,
            recovery_jerk_weight=recovery_jerk_weight, jerk_reference_mps3=jerk_reference_mps3,
            kappa_max_log_rate_per_s=kappa_max_log_rate_per_s, drive_max_log_rate_per_s=drive_max_log_rate_per_s,
            reference_source=reference_source, fan_ye_model_npz=fan_ye_model_npz,
            fan_ye_train_summary_json=fan_ye_train_summary_json, seed=seed + rank,
        )
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
    parser.add_argument(
        "--enable-drive-residual", action="store_true",
        help="Use a seventh policy action for virtual-carriage return drive; springs remain six channels.",
    )
    parser.add_argument(
        "--enable-energy-safety", action="store_true",
        help="Apply the causal energy-budget/direction-smoothing shield to the learned return-drive residual.",
    )
    parser.add_argument("--recovery-gate-hold-s", type=float, default=0.0, help="Causal error-triggered residual-hold duration.")
    parser.add_argument("--recovery-gate-taper-s", type=float, default=0.0, help="Optional causal smooth taper at the end of the held recovery gate; zero preserves the binary hold.")
    parser.add_argument("--recovery-error-weight", type=float, default=0.075)
    parser.add_argument("--recovery-progress-reward", type=float, default=0.040)
    parser.add_argument("--action-change-penalty", type=float, default=0.003)
    parser.add_argument("--residual-magnitude-penalty", type=float, default=0.0, help="Penalty on gated residual magnitude; default preserves prior protocol.")
    parser.add_argument("--recovery-tube-time-penalty", type=float, default=0.0, help="Post-release gated penalty per control step outside the rejoin tube.")
    parser.add_argument("--recovery-tube-radius-m", type=float, default=0.005)
    parser.add_argument("--contact-impulse-penalty", type=float, default=0.0, help="Training-only physical contact-impulse cost; actor never observes contact.")
    parser.add_argument("--recovery-jerk-weight", type=float, default=0.0)
    parser.add_argument("--jerk-reference-mps3", type=float, default=1200.0)
    parser.add_argument("--kappa-max-log-rate-per-s", type=float, default=1.6)
    parser.add_argument("--drive-max-log-rate-per-s", type=float, default=1.0)
    parser.add_argument("--resume", type=Path, default=None, help="Optional PPO zip checkpoint.")
    parser.add_argument("--fixture-manifest", type=Path, default=None, help="Isolated post-V4 WBC development manifest for Fan Ye RL.")
    parser.add_argument("--fixture-split", choices=("train", "validation"), default="train")
    parser.add_argument("--fan-ye-model-npz", type=Path, default=None)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, default=None)
    args = parser.parse_args()
    if args.total_timesteps < 1 or args.n_envs < 1:
        raise ValueError("timesteps and n-envs must be positive")
    if args.enable_energy_safety and not args.enable_drive_residual:
        raise ValueError("--enable-energy-safety requires --enable-drive-residual")
    fan_ye_enabled = args.fan_ye_model_npz is not None or args.fan_ye_train_summary_json is not None
    if fan_ye_enabled and (args.fan_ye_model_npz is None or args.fan_ye_train_summary_json is None or args.fixture_manifest is None or not args.enable_drive_residual):
        raise ValueError("Fan Ye WBC RL requires model, summary, post-V4 fixture manifest, and 7-D drive residual actions")
    fixtures = load_fixture_manifest(args.fixture_manifest, args.fixture_split) if args.fixture_manifest is not None else default_fixtures()
    reference_source = "fixed_panda_wbc" if fan_ye_enabled else "proxy"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MUJOCO_GL", "egl")
    torch.set_num_threads(1)
    env = SubprocVecEnv(
        [make_env(args.menagerie, fixtures, rank, args.seed, args.enable_drive_residual, args.enable_energy_safety, args.recovery_gate_hold_s, args.recovery_gate_taper_s, args.recovery_error_weight, args.recovery_progress_reward, args.action_change_penalty, args.residual_magnitude_penalty, args.recovery_tube_time_penalty, args.recovery_tube_radius_m, args.contact_impulse_penalty, args.recovery_jerk_weight, args.jerk_reference_mps3, args.kappa_max_log_rate_per_s, args.drive_max_log_rate_per_s, reference_source, args.fan_ye_model_npz, args.fan_ye_train_summary_json) for rank in range(args.n_envs)], start_method="spawn",
    )
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
        "policy_observation_contract": "Fan Ye normalized q/qdot/WBC twist (20) + fixed reservoir state (64)" if fan_ye_enabled else (DRIVE_RESIDUAL_OBSERVATION_FIELDS if args.enable_drive_residual else training_contract()["observation_fields"]),
        "policy_observation_dimension": 84 if fan_ye_enabled else (52 if args.enable_drive_residual else 51),
        "reference_source": reference_source,
        "fan_ye_fixed_reservoir": None if not fan_ye_enabled else {"model_npz": str(args.fan_ye_model_npz), "train_summary_json": str(args.fan_ye_train_summary_json), "reservoir_state_dimension": 64, "student_input": ["q(7)", "qdot(7)", "wbc_task_twist(6)"]},
        "enable_drive_residual": args.enable_drive_residual,
        "energy_budget_safety": {
            "enabled": args.enable_energy_safety,
            "placement": "after PPO's 25 Hz low-frequency residual action and before the 250 Hz virtual-carriage force application",
            "uses_contact_or_obstacle_information": False,
            "claim": "incremental return-drive energy budget and direction smoothing; not a global passivity proof for the moving-reference robot",
        },
        "recovery_gate": {
            "hold_s": args.recovery_gate_hold_s,
            "taper_s": args.recovery_gate_taper_s,
            "activation": "causal measured end-effector tracking-error gate, with optional held recovery window",
            "uses_contact_or_obstacle_information": False,
        },
        "reward_scales": {
            "recovery_error_weight": args.recovery_error_weight,
            "recovery_progress_reward": args.recovery_progress_reward,
            "action_change_penalty": args.action_change_penalty,
            "residual_magnitude_penalty": args.residual_magnitude_penalty,
            "recovery_tube_time_penalty": args.recovery_tube_time_penalty,
            "recovery_tube_radius_m": args.recovery_tube_radius_m,
            "contact_impulse_penalty": args.contact_impulse_penalty,
            "recovery_jerk_weight": args.recovery_jerk_weight,
            "jerk_reference_mps3": args.jerk_reference_mps3,
            "kappa_max_log_rate_per_s": args.kappa_max_log_rate_per_s,
            "drive_max_log_rate_per_s": args.drive_max_log_rate_per_s,
        },
        "drive_residual_action": None if not args.enable_drive_residual else {
            "dimension": 1,
            "meaning": "virtual-carriage return-drive residual; not a seventh spring",
            **DriveResidualActionConfig().__dict__,
            "activation": "smooth measured end-effector tracking-error gate; no contact, force, obstacle, or future-phase input",
        },
        "privileged_quantities_excluded": training_contract()["excluded_privileged_diagnostics"],
        "fixtures": [fixture.__dict__ for fixture in fixtures],
        "fixture_manifest": None if args.fixture_manifest is None else str(args.fixture_manifest),
        "fixture_split": args.fixture_split if args.fixture_manifest is not None else None,
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
