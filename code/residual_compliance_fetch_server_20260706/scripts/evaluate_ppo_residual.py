#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

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


def build_env_config(args: argparse.Namespace, output_dir: str | Path) -> PPOEnvConfig:
    demo = DemoConfig(
        env_id=args.env_id,
        render_mode=args.render_mode,
        render_backend=str(args.render_backend),
        collision_only_visuals=bool(args.collision_only_visuals),
        seed=int(args.seed),
        dt=float(args.dt),
        max_steps=int(args.max_steps),
        no_early_stop=False,
        lock_non_arm_joints=not bool(args.allow_body_motion),
        record_gif=bool(args.record_gif),
        camera_view=str(args.camera_view),
        allowed_penetration=float(args.allowed_penetration),
        trajectory=args.trajectory,
        output_dir=str(output_dir),
    )
    command = CommandConfig()
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
    return PPOEnvConfig(
        demo=demo,
        command=command,
        compliance=compliance,
        reward=PPORewardConfig(),
        obstacle_sampler=str(args.sampler),
        action_scale=float(args.action_scale),
        use_nominal_softening=not bool(args.no_nominal_softening),
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {}
    return {
        "episodes": len(rows),
        "success_rate": mean(float(r.get("success", False)) for r in rows),
        "collision_rate": mean(float(r.get("collision", False)) for r in rows),
        "contact_rate": mean(float(r.get("contact_occurred", False)) for r in rows),
        "mean_max_penetration": mean(float(r.get("max_penetration", 0.0)) for r in rows),
        "mean_final_arm_error": mean(float(r.get("final_arm_error", 0.0)) for r in rows),
        "mean_contact_steps": mean(float(r.get("contact_steps", 0.0)) for r in rows),
        "mean_jerk": mean(float(r.get("mean_jerk", 0.0)) for r in rows),
        "mean_compliance_score": mean(float(r.get("compliance_score", 0.0)) for r in rows),
    }


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    from stable_baselines3 import PPO

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    model_path = _resolve(args.model)
    if model_path is None:
        raise ValueError("--model is required")
    output_dir = ensure_dir(_resolve(args.output_dir) or PROJECT_ROOT / "outputs/ppo_eval")
    bc_checkpoint = _resolve(args.bc_checkpoint)
    bc_meta = load_bc_metadata(bc_checkpoint) if bc_checkpoint else {}
    model = PPO.load(model_path, device=args.device)

    rows: list[dict[str, Any]] = []
    for ep in range(int(args.episodes)):
        ep_dir = ensure_dir(output_dir / f"episode_{ep:03d}")
        record_this = bool(args.record_gif and ep == int(args.gif_episode))
        env_config = build_env_config(args, ep_dir)
        env = ResidualComplianceFetchPPOEnv(
            env_config=env_config,
            seed=int(args.seed) + ep,
            link_vocab=bc_meta.get("link_vocab"),
            obs_mean=bc_meta.get("obs_mean"),
            obs_std=bc_meta.get("obs_std"),
            record_gif=record_this,
            output_dir=ep_dir,
        )
        obs, _ = env.reset()
        total_reward = 0.0
        done = False
        info: dict[str, Any] = {}
        while not done:
            action, _state = model.predict(obs, deterministic=bool(args.deterministic))
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += float(reward)
            done = bool(terminated or truncated)
        summary = dict(info.get("episode_summary", env.episode_summary or {}))
        summary["episode"] = ep
        summary["total_reward"] = float(total_reward)
        summary["artifacts"] = None
        if record_this:
            summary["artifacts"] = env.write_episode_artifacts(
                ep_dir,
                include_records=bool(args.include_records),
                gif_name="ppo_policy.gif",
            )
        env.close()
        rows.append(summary)
        print(
            f"episode={ep:03d} success={summary.get('success')} "
            f"collision={summary.get('collision')} "
            f"max_pen={float(summary.get('max_penetration', 0.0)):.4f} "
            f"score={float(summary.get('compliance_score', 0.0)):.2f} "
            f"reward={total_reward:.2f}"
        )

    result = {
        "model": model_path,
        "bc_checkpoint": bc_checkpoint,
        "config": vars(args),
        "summary": summarize(rows),
        "episodes": rows,
    }
    summary_path = output_dir / "ppo_eval_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    result["summary_path"] = str(summary_path)
    print(json.dumps(result["summary"], indent=2))
    print(f"Saved PPO eval summary to {summary_path}")
    return result


def main() -> None:
    ensure_conda_lib_path()
    parser = argparse.ArgumentParser(description="Evaluate and render a PPO residual policy.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--bc-checkpoint", default="runs/bc_body_locked_unfiltered_policy.pt")
    parser.add_argument("--output-dir", default="outputs/ppo_residual_eval")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--gif-episode", type=int, default=0)
    parser.add_argument("--record-gif", action="store_true")
    parser.add_argument("--include-records", action="store_true")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--device", default="auto")

    parser.add_argument("--env-id", default="Empty-v1")
    parser.add_argument("--render-backend", default="cpu")
    parser.add_argument("--collision-only-visuals", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--trajectory", default=None)
    parser.add_argument("--sampler", default="contact_heavy", choices=["contact_heavy", "broad"])
    parser.add_argument("--seed", type=int, default=900)
    parser.add_argument("--max-steps", type=int, default=420)
    parser.add_argument("--dt", type=float, default=1.0 / 30.0)
    parser.add_argument("--allowed-penetration", type=float, default=0.010)
    parser.add_argument("--render-mode", default="none", choices=["none", "human"])
    parser.add_argument("--camera-view", default="close")
    parser.add_argument("--allow-body-motion", action="store_true")

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
    args = parser.parse_args()
    evaluate(args)


if __name__ == "__main__":
    main()
