#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.bc_policy import ResidualMLP
from residual_compliance_fetch.controllers import ContactComplianceConfig
from residual_compliance_fetch.maniskill_demo import CommandConfig, DemoConfig
from residual_compliance_fetch.ppo_env import (
    PPOEnvConfig,
    PPORewardConfig,
    ResidualComplianceFetchPPOEnv,
    load_bc_metadata,
)
from residual_compliance_fetch.utils import ensure_conda_lib_path, ensure_dir


def _resolve(path: str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    return str(p if p.is_absolute() else PROJECT_ROOT / p)


def _make_env_factory(
    *,
    rank: int,
    seed: int,
    env_config: PPOEnvConfig,
    bc_meta: dict[str, Any],
):
    def _factory():
        from stable_baselines3.common.monitor import Monitor

        env = ResidualComplianceFetchPPOEnv(
            env_config=env_config,
            seed=int(seed) + int(rank) * 1009,
            link_vocab=bc_meta.get("link_vocab"),
            obs_mean=bc_meta.get("obs_mean"),
            obs_std=bc_meta.get("obs_std"),
            record_gif=False,
        )
        return Monitor(env)

    return _factory


def _copy_linear(src: nn.Linear, dst: nn.Linear) -> bool:
    if src.weight.shape != dst.weight.shape or src.bias.shape != dst.bias.shape:
        return False
    with torch.no_grad():
        dst.weight.copy_(src.weight.to(dst.weight.device))
        dst.bias.copy_(src.bias.to(dst.bias.device))
    return True


def warm_start_actor_from_bc(model, checkpoint_path: str | None) -> dict[str, Any]:
    if checkpoint_path is None:
        return {"enabled": False, "reason": "no_bc_checkpoint"}
    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"BC checkpoint not found: {path}")

    ckpt = torch.load(path, map_location=model.device, weights_only=False)
    bc_model = ResidualMLP(
        obs_dim=int(ckpt["obs_dim"]),
        action_dim=int(ckpt["action_dim"]),
        hidden_sizes=tuple(int(x) for x in ckpt["hidden_sizes"]),
    ).to(model.device)
    bc_model.load_state_dict(ckpt["model_state_dict"])
    bc_model.eval()

    bc_linear = [m for m in bc_model.net if isinstance(m, nn.Linear)]
    pi_linear = [
        m for m in model.policy.mlp_extractor.policy_net if isinstance(m, nn.Linear)
    ]
    copied_hidden = 0
    for src, dst in zip(bc_linear[:-1], pi_linear):
        copied_hidden += int(_copy_linear(src, dst))
    copied_action = False
    if bc_linear:
        copied_action = _copy_linear(bc_linear[-1], model.policy.action_net)
    return {
        "enabled": True,
        "checkpoint": str(path),
        "bc_linear_layers": len(bc_linear),
        "ppo_policy_linear_layers": len(pi_linear),
        "copied_hidden_layers": copied_hidden,
        "copied_action_layer": bool(copied_action),
        "note": "LayerNorm layers from BC are not copied into SB3 MlpPolicy.",
    }


def build_env_config(args: argparse.Namespace) -> PPOEnvConfig:
    demo = DemoConfig(
        env_id=args.env_id,
        render_mode="none",
        render_backend=str(args.render_backend),
        collision_only_visuals=bool(args.collision_only_visuals),
        seed=int(args.seed),
        dt=float(args.dt),
        max_steps=int(args.max_steps),
        no_early_stop=False,
        lock_non_arm_joints=not bool(args.allow_body_motion),
        record_gif=False,
        camera_view=str(args.camera_view),
        allowed_penetration=float(args.allowed_penetration),
        trajectory=args.trajectory,
        output_dir=str(args.output_dir),
    )
    command = CommandConfig(
        nominal_kp=float(args.nominal_kp),
        nominal_max_qdot=float(args.nominal_max_qdot),
        waypoint_tolerance=float(args.waypoint_tolerance),
        command_max_qdot=float(args.command_max_qdot),
        command_max_accel=float(args.command_max_accel),
        command_lowpass_alpha=float(args.command_lowpass_alpha),
    )
    compliance = ContactComplianceConfig(
        contact_trigger_clearance=float(args.contact_trigger_clearance),
        normal_gain=float(args.normal_gain),
        tangential_gain=float(args.tangential_gain),
        nominal_soften_gain=float(args.nominal_soften_gain),
        force_proxy_threshold=float(args.force_proxy_threshold),
        force_proxy_scale=float(args.force_proxy_scale),
        force_proxy_max_clearance=float(args.force_proxy_max_clearance),
        max_residual_qdot=float(args.max_residual_qdot),
        recovery_decay=float(args.recovery_decay),
    )
    reward = PPORewardConfig(
        alive_penalty=float(args.alive_penalty),
        progress_scale=float(args.progress_scale),
        success_bonus=float(args.success_bonus),
        collision_penalty=float(args.collision_penalty),
        penetration_scale=float(args.penetration_scale),
        contact_step_penalty=float(args.contact_step_penalty),
        residual_penalty=float(args.residual_penalty),
        jerk_penalty=float(args.jerk_penalty),
        final_error_penalty=float(args.final_error_penalty),
        ignored_action_penalty=float(args.ignored_action_penalty),
    )
    return PPOEnvConfig(
        demo=demo,
        command=command,
        compliance=compliance,
        reward=reward,
        obstacle_sampler=str(args.sampler),
        action_scale=float(args.action_scale),
        use_nominal_softening=not bool(args.no_nominal_softening),
    )


def train(args: argparse.Namespace) -> dict[str, Any]:
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import CheckpointCallback
    from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    output_dir = ensure_dir(_resolve(args.output_dir) or PROJECT_ROOT / "runs/ppo_residual")
    bc_checkpoint = _resolve(args.bc_checkpoint)
    bc_meta = load_bc_metadata(bc_checkpoint) if bc_checkpoint else {}
    env_config = build_env_config(args)

    factories = [
        _make_env_factory(
            rank=i,
            seed=int(args.seed),
            env_config=env_config,
            bc_meta=bc_meta,
        )
        for i in range(int(args.n_envs))
    ]
    if args.vec_env == "subproc" and int(args.n_envs) > 1:
        vec_env = SubprocVecEnv(factories, start_method="spawn")
    else:
        vec_env = DummyVecEnv(factories)

    hidden_sizes = tuple(
        int(x)
        for x in str(args.hidden_sizes or ",".join(map(str, bc_meta.get("hidden_sizes", (256, 256))))).split(",")
        if x.strip()
    )
    policy_kwargs = {
        "activation_fn": nn.Tanh,
        "net_arch": {"pi": list(hidden_sizes), "vf": list(hidden_sizes)},
    }
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=float(args.learning_rate),
        n_steps=int(args.n_steps),
        batch_size=int(args.batch_size),
        n_epochs=int(args.n_epochs),
        gamma=float(args.gamma),
        gae_lambda=float(args.gae_lambda),
        clip_range=float(args.clip_range),
        ent_coef=float(args.ent_coef),
        vf_coef=float(args.vf_coef),
        max_grad_norm=float(args.max_grad_norm),
        target_kl=None if args.target_kl is None else float(args.target_kl),
        policy_kwargs=policy_kwargs,
        tensorboard_log=str(output_dir / "tb"),
        seed=int(args.seed),
        device=args.device,
        verbose=1,
    )
    warm_start = warm_start_actor_from_bc(model, bc_checkpoint)

    checkpoint_callback = CheckpointCallback(
        save_freq=max(1, int(args.save_freq) // max(1, int(args.n_envs))),
        save_path=str(output_dir / "checkpoints"),
        name_prefix="ppo_residual",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )
    config_path = output_dir / "ppo_train_config.json"
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "args": vars(args),
                "bc_checkpoint": bc_checkpoint,
                "bc_meta": {
                    k: (v.tolist() if isinstance(v, np.ndarray) else v)
                    for k, v in bc_meta.items()
                    if k in {"obs_mean", "obs_std", "link_vocab", "hidden_sizes", "obs_dim", "action_dim"}
                },
                "warm_start": warm_start,
                "policy_kwargs": {
                    "activation_fn": "Tanh",
                    "net_arch": {"pi": list(hidden_sizes), "vf": list(hidden_sizes)},
                },
            },
            f,
            indent=2,
        )

    print(json.dumps({"output_dir": str(output_dir), "warm_start": warm_start}, indent=2))
    model.learn(
        total_timesteps=int(args.total_timesteps),
        callback=checkpoint_callback,
        progress_bar=bool(args.progress_bar),
        tb_log_name="ppo_residual_contact",
    )
    final_model = output_dir / "ppo_residual_final.zip"
    model.save(str(final_model))
    vec_env.close()

    summary = {
        "output_dir": str(output_dir),
        "final_model": str(final_model),
        "config": str(config_path),
        "warm_start": warm_start,
        "total_timesteps": int(args.total_timesteps),
    }
    summary_path = output_dir / "ppo_train_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def main() -> None:
    ensure_conda_lib_path()
    parser = argparse.ArgumentParser(description="Train PPO residual compliance policy.")

    parser.add_argument("--total-timesteps", type=int, default=300_000)
    parser.add_argument("--bc-checkpoint", default="runs/bc_body_locked_unfiltered_policy.pt")
    parser.add_argument("--output-dir", default="runs/ppo_residual_contact_heavy")
    parser.add_argument("--env-id", default="Empty-v1")
    parser.add_argument("--render-backend", default="cpu")
    parser.add_argument("--collision-only-visuals", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--trajectory", default=None)
    parser.add_argument("--sampler", default="contact_heavy", choices=["contact_heavy", "broad"])
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--vec-env", default="dummy", choices=["dummy", "subproc"])
    parser.add_argument("--device", default="auto")

    parser.add_argument("--max-steps", type=int, default=420)
    parser.add_argument("--dt", type=float, default=1.0 / 30.0)
    parser.add_argument("--allowed-penetration", type=float, default=0.010)
    parser.add_argument("--camera-view", default="close")
    parser.add_argument("--allow-body-motion", action="store_true")

    parser.add_argument("--nominal-kp", type=float, default=1.8)
    parser.add_argument("--nominal-max-qdot", type=float, default=0.75)
    parser.add_argument("--waypoint-tolerance", type=float, default=0.07)
    parser.add_argument("--command-max-qdot", type=float, default=0.90)
    parser.add_argument("--command-max-accel", type=float, default=3.20)
    parser.add_argument("--command-lowpass-alpha", type=float, default=0.30)

    parser.add_argument("--contact-trigger-clearance", type=float, default=0.0)
    parser.add_argument("--normal-gain", type=float, default=1.50)
    parser.add_argument("--tangential-gain", type=float, default=0.30)
    parser.add_argument("--nominal-soften-gain", type=float, default=1.00)
    parser.add_argument("--force-proxy-threshold", type=float, default=0.35)
    parser.add_argument("--force-proxy-scale", type=float, default=0.45)
    parser.add_argument("--force-proxy-max-clearance", type=float, default=0.035)
    parser.add_argument("--max-residual-qdot", type=float, default=0.90)
    parser.add_argument("--recovery-decay", type=float, default=0.82)
    parser.add_argument("--action-scale", type=float, default=0.90)
    parser.add_argument("--no-nominal-softening", action="store_true")

    parser.add_argument("--learning-rate", type=float, default=2.5e-4)
    parser.add_argument("--n-steps", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--n-epochs", type=int, default=6)
    parser.add_argument("--gamma", type=float, default=0.985)
    parser.add_argument("--gae-lambda", type=float, default=0.92)
    parser.add_argument("--clip-range", type=float, default=0.15)
    parser.add_argument("--ent-coef", type=float, default=0.003)
    parser.add_argument("--vf-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--target-kl", type=float, default=0.03)
    parser.add_argument("--hidden-sizes", default=None)
    parser.add_argument("--save-freq", type=int, default=25_000)
    parser.add_argument("--progress-bar", action="store_true")

    parser.add_argument("--alive-penalty", type=float, default=0.01)
    parser.add_argument("--progress-scale", type=float, default=8.0)
    parser.add_argument("--success-bonus", type=float, default=45.0)
    parser.add_argument("--collision-penalty", type=float, default=55.0)
    parser.add_argument("--penetration-scale", type=float, default=900.0)
    parser.add_argument("--contact-step-penalty", type=float, default=0.04)
    parser.add_argument("--residual-penalty", type=float, default=0.025)
    parser.add_argument("--jerk-penalty", type=float, default=0.020)
    parser.add_argument("--final-error-penalty", type=float, default=1.5)
    parser.add_argument("--ignored-action-penalty", type=float, default=0.004)

    args = parser.parse_args()
    result = train(args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
