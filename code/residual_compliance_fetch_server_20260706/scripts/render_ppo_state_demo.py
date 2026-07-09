#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.controllers import ContactComplianceConfig
from residual_compliance_fetch.maniskill_demo import CommandConfig, DemoConfig, refresh_link_positions
from residual_compliance_fetch.ppo_env import PPOEnvConfig, PPORewardConfig, ResidualComplianceFetchPPOEnv, load_bc_metadata
from residual_compliance_fetch.utils import ensure_dir


def _resolve(path: str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    return str(p if p.is_absolute() else PROJECT_ROOT / p)


def _make_env_config(args: argparse.Namespace, output_dir: Path) -> PPOEnvConfig:
    demo = DemoConfig(
        env_id=args.env_id,
        render_mode="none",
        render_backend=args.render_backend,
        collision_only_visuals=True,
        seed=int(args.seed),
        dt=float(args.dt),
        max_steps=int(args.max_steps),
        allowed_penetration=float(args.allowed_penetration),
        lock_non_arm_joints=not bool(args.allow_body_motion),
        trajectory=args.trajectory,
        output_dir=str(output_dir),
    )
    compliance = ContactComplianceConfig(
        contact_trigger_clearance=float(args.contact_trigger_clearance),
        max_residual_qdot=float(args.max_residual_qdot),
        recovery_decay=float(args.recovery_decay),
    )
    return PPOEnvConfig(
        demo=demo,
        command=CommandConfig(),
        compliance=compliance,
        reward=PPORewardConfig(),
        obstacle_sampler=str(args.sampler),
        action_scale=float(args.action_scale),
        use_nominal_softening=not bool(args.no_nominal_softening),
    )


def _capture_frame(env: ResidualComplianceFetchPPOEnv, t: float, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    states = refresh_link_positions(env.link_states, env.robot)
    link_positions = {s.name: np.asarray(s.position, dtype=float).tolist() for s in states}
    obs_pos = np.asarray(env.obstacle._last_position, dtype=float).tolist() if env.obstacle is not None else [0, 0, -10]
    record = env.metrics.records[-1] if env.metrics and env.metrics.records else None
    return {
        "t": float(t),
        "links": link_positions,
        "obstacle": obs_pos,
        "obstacle_radius": float(env.obstacle.radius if env.obstacle is not None else 0.0),
        "min_clearance": float(record.min_clearance if record else 0.0),
        "residual_norm": float(np.linalg.norm(record.qdot_residual) if record else 0.0),
        "active_link": None if record is None else record.active_link,
        "contact_depth": float(record.contact_depth if record else 0.0),
        "summary": summary,
    }


def _draw_frame(frame: dict[str, Any], all_frames: list[dict[str, Any]], out_path: Path, *, title: str) -> None:
    fig = plt.figure(figsize=(9.6, 6.4), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_xlim(0.0, 1.25)
    ax.set_ylim(-0.30, 0.48)
    ax.set_zlim(0.65, 1.28)
    ax.set_xlabel("x / m")
    ax.set_ylabel("y / m")
    ax.set_zlabel("z / m")
    ax.view_init(elev=22, azim=-58)
    ax.set_title(title, pad=14)

    names = [
        "shoulder_pan_link",
        "shoulder_lift_link",
        "upperarm_roll_link",
        "elbow_flex_link",
        "forearm_roll_link",
        "wrist_flex_link",
        "wrist_roll_link",
        "gripper_link",
    ]
    pts = np.array([frame["links"][n] for n in names if n in frame["links"]], dtype=float)
    if len(pts):
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#2563eb", linewidth=4, marker="o", markersize=5)
        ax.scatter(pts[-1, 0], pts[-1, 1], pts[-1, 2], color="#f97316", s=70, label="EE / gripper")

    ee_path = []
    for f in all_frames:
        p = f["links"].get("gripper_link")
        if p is not None:
            ee_path.append(p)
        if f is frame:
            break
    if len(ee_path) > 1:
        ee = np.asarray(ee_path, dtype=float)
        ax.plot(ee[:, 0], ee[:, 1], ee[:, 2], color="#6b7280", linewidth=1.5, alpha=0.7, label="EE path")

    center = np.asarray(frame["obstacle"], dtype=float)
    radius = float(frame["obstacle_radius"])
    if center[2] > -1.0 and radius > 0:
        u = np.linspace(0, 2 * np.pi, 24)
        v = np.linspace(0, np.pi, 12)
        xs = center[0] + radius * np.outer(np.cos(u), np.sin(v))
        ys = center[1] + radius * np.outer(np.sin(u), np.sin(v))
        zs = center[2] + radius * np.outer(np.ones_like(u), np.cos(v))
        ax.plot_surface(xs, ys, zs, color="#dc2626", alpha=0.35, linewidth=0)
        ax.scatter(center[0], center[1], center[2], color="#991b1b", s=40, label="moving obstacle")

    clearance = float(frame["min_clearance"])
    residual = float(frame["residual_norm"])
    contact_depth = float(frame["contact_depth"])
    active = frame.get("active_link") or "none"
    status = "contact" if clearance <= 0 else "near" if clearance < 0.03 else "clear"
    text = (
        f"t = {frame['t']:.2f}s\n"
        f"clearance = {clearance:.4f} m\n"
        f"contact depth = {contact_depth:.4f} m\n"
        f"residual ||qdot|| = {residual:.3f}\n"
        f"active link = {active}\n"
        f"state = {status}"
    )
    ax.text2D(0.02, 0.77, text, transform=ax.transAxes, fontsize=10, family="monospace",
              bbox=dict(boxstyle="round,pad=0.45", facecolor="white", edgecolor="#d1d5db", alpha=0.92))
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--bc-checkpoint", default="runs/bc_body_locked_unfiltered_policy.pt")
    parser.add_argument("--output-dir", default="outputs/ppo_state_demo")
    parser.add_argument("--env-id", default="Empty-v1")
    parser.add_argument("--render-backend", default="cpu")
    parser.add_argument("--sampler", default="contact_heavy", choices=["contact_heavy", "broad"])
    parser.add_argument("--seed", type=int, default=44)
    parser.add_argument("--dt", type=float, default=1.0 / 30.0)
    parser.add_argument("--max-steps", type=int, default=160)
    parser.add_argument("--allowed-penetration", type=float, default=0.010)
    parser.add_argument("--contact-trigger-clearance", type=float, default=0.025)
    parser.add_argument("--max-residual-qdot", type=float, default=0.90)
    parser.add_argument("--recovery-decay", type=float, default=0.82)
    parser.add_argument("--action-scale", type=float, default=0.90)
    parser.add_argument("--trajectory", default=None)
    parser.add_argument("--allow-body-motion", action="store_true")
    parser.add_argument("--no-nominal-softening", action="store_true")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--stride", type=int, default=2)
    parser.add_argument("--fps", type=float, default=12.0)
    args = parser.parse_args()

    out_dir = ensure_dir(_resolve(args.output_dir) or PROJECT_ROOT / "outputs/ppo_state_demo")
    frames_dir = ensure_dir(out_dir / "frames")
    model = PPO.load(_resolve(args.model), device="cpu")
    bc_meta = load_bc_metadata(_resolve(args.bc_checkpoint)) if args.bc_checkpoint else {}
    env = ResidualComplianceFetchPPOEnv(
        env_config=_make_env_config(args, out_dir),
        seed=int(args.seed),
        link_vocab=bc_meta.get("link_vocab"),
        obs_mean=bc_meta.get("obs_mean"),
        obs_std=bc_meta.get("obs_std"),
        record_gif=False,
        output_dir=out_dir,
    )

    obs, _ = env.reset()
    sim_frames: list[dict[str, Any]] = []
    done = False
    total_reward = 0.0
    step = 0
    while not done:
        action, _ = model.predict(obs, deterministic=bool(args.deterministic))
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += float(reward)
        if step % max(1, int(args.stride)) == 0:
            sim_frames.append(_capture_frame(env, step * float(args.dt)))
        done = bool(terminated or truncated)
        step += 1
    summary = dict(env.episode_summary or {})
    summary["total_reward"] = total_reward
    summary["seed"] = int(args.seed)
    summary["contact_trigger_clearance"] = float(args.contact_trigger_clearance)
    if sim_frames:
        sim_frames[-1]["summary"] = summary

    png_paths: list[Path] = []
    for i, frame in enumerate(sim_frames):
        png_path = frames_dir / f"frame_{i:04d}.png"
        _draw_frame(frame, sim_frames, png_path, title="PPO residual compliance demo from true simulation states")
        png_paths.append(png_path)

    gif_path = out_dir / "ppo_residual_state_demo.gif"
    images = [imageio.imread(path) for path in png_paths]
    imageio.mimsave(gif_path, images, fps=float(args.fps))
    records_path = out_dir / "ppo_residual_state_demo_records.json"
    with records_path.open("w", encoding="utf-8") as f:
        json.dump({"summary": summary, "frames": sim_frames}, f, indent=2)
    env.close()
    print(json.dumps({"gif": str(gif_path), "records": str(records_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
