#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import mean

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.controllers import ContactComplianceConfig
from residual_compliance_fetch.maniskill_demo import CommandConfig, DemoConfig, run_comparison
from residual_compliance_fetch.obstacles import (
    randomized_contact_heavy_crossing_sphere,
    randomized_crossing_sphere,
)
from residual_compliance_fetch.utils import ensure_conda_lib_path, ensure_dir


def summarize_rollouts(episodes: list[dict]) -> dict:
    summary: dict[str, dict] = {}
    modes: list[str] = []
    for episode in episodes:
        for mode in episode.get("rollouts", {}):
            if mode not in modes:
                modes.append(mode)
    for mode in modes:
        rows = [ep["rollouts"][mode] for ep in episodes]
        summary[mode] = {
            "episodes": len(rows),
            "success_rate": mean(float(r["success"]) for r in rows) if rows else 0.0,
            "collision_rate": mean(float(r["collision"]) for r in rows) if rows else 0.0,
            "contact_rate": mean(float(r.get("contact_occurred", False)) for r in rows)
            if rows
            else 0.0,
            "mean_min_clearance": mean(float(r["min_clearance"]) for r in rows) if rows else 0.0,
            "mean_max_penetration": mean(float(r.get("max_penetration", 0.0)) for r in rows)
            if rows
            else 0.0,
            "mean_final_arm_error": mean(float(r["final_arm_error"]) for r in rows) if rows else 0.0,
            "mean_jerk": mean(float(r["mean_jerk"]) for r in rows) if rows else 0.0,
            "mean_steps": mean(float(r["steps"]) for r in rows) if rows else 0.0,
            "mean_contact_steps": mean(
                float(r.get("contact_steps", 0.0)) for r in rows
            )
            if rows
            else 0.0,
            "mean_contact_compliance_steps": mean(
                float(r.get("contact_compliance_steps", 0.0)) for r in rows
            )
            if rows
            else 0.0,
            "mean_force_proxy_steps": mean(
                float(r.get("force_proxy_steps", 0.0)) for r in rows
            )
            if rows
            else 0.0,
            "mean_max_force_proxy_level": mean(
                float(r.get("max_force_proxy_level", 0.0)) for r in rows
            )
            if rows
            else 0.0,
            "mean_qvel_tracking_error": mean(
                float(r.get("mean_qvel_tracking_error", 0.0)) for r in rows
            )
            if rows
            else 0.0,
            "mean_compliance_score": mean(
                float(r.get("compliance_score", 0.0)) for r in rows
            )
            if rows
            else 0.0,
        }
    return summary


def main() -> None:
    ensure_conda_lib_path()

    parser = argparse.ArgumentParser(
        description="Randomized batch evaluation for Fetch residual compliance."
    )
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", default="outputs/randomized_eval")
    parser.add_argument("--max-steps", type=int, default=420)
    parser.add_argument("--render-mode", default="none", choices=["none", "human"])
    parser.add_argument(
        "--sampler",
        default="broad",
        choices=["broad", "contact_heavy"],
        help="Obstacle sampling distribution.",
    )
    parser.add_argument("--include-records", action="store_true")
    parser.add_argument("--allowed-penetration", type=float, default=0.025)
    parser.add_argument("--contact-trigger-clearance", type=float, default=0.0)
    parser.add_argument("--normal-gain", type=float, default=1.50)
    parser.add_argument("--tangential-gain", type=float, default=0.30)
    parser.add_argument("--nominal-soften-gain", type=float, default=1.00)
    parser.add_argument("--force-proxy-threshold", type=float, default=0.35)
    parser.add_argument("--force-proxy-scale", type=float, default=0.45)
    parser.add_argument("--force-proxy-max-clearance", type=float, default=0.035)
    parser.add_argument("--bc-checkpoint", default=None)
    args = parser.parse_args()

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    output_dir = ensure_dir(args.output_dir)
    rng = np.random.default_rng(int(args.seed))
    episodes: list[dict] = []

    for ep_idx in range(int(args.episodes)):
        if args.sampler == "contact_heavy":
            obstacle_spec = randomized_contact_heavy_crossing_sphere(rng)
        else:
            obstacle_spec = randomized_crossing_sphere(rng)
        ep_dir = ensure_dir(output_dir / f"episode_{ep_idx:03d}")
        demo_config = DemoConfig(
            seed=int(args.seed) + ep_idx,
            render_mode=args.render_mode,
            max_steps=int(args.max_steps),
            record_gif=False,
            output_dir=str(ep_dir),
            allowed_penetration=float(args.allowed_penetration),
        )
        result = run_comparison(
            demo_config=demo_config,
            command_config=CommandConfig(),
            compliance_config=ContactComplianceConfig(
                contact_trigger_clearance=float(args.contact_trigger_clearance),
                normal_gain=float(args.normal_gain),
                tangential_gain=float(args.tangential_gain),
                nominal_soften_gain=float(args.nominal_soften_gain),
                force_proxy_threshold=float(args.force_proxy_threshold),
                force_proxy_scale=float(args.force_proxy_scale),
                force_proxy_max_clearance=float(args.force_proxy_max_clearance),
            ),
            obstacle_spec=obstacle_spec,
            include_records=bool(args.include_records),
            bc_checkpoint=args.bc_checkpoint,
        )
        episodes.append(
            {
                "episode": ep_idx,
                "obstacle": obstacle_spec.__dict__,
                "rollouts": result["rollouts"],
                "metrics_path": result["metrics_path"],
            }
        )

        base = result["rollouts"]["baseline"]
        compliance = result["rollouts"]["contact_compliance"]
        bc = result["rollouts"].get("bc_policy")
        bc_text = ""
        if bc is not None:
            bc_text = (
                f" bc_policy(collision={bc['collision']}, contact={bc['contact_occurred']}, "
                f"max_pen={bc['max_penetration']:.3f}, success={bc['success']})"
            )
        print(
            f"episode={ep_idx:03d} "
            f"baseline(collision={base['collision']}, contact={base['contact_occurred']}, "
            f"max_pen={base['max_penetration']:.3f}, success={base['success']}) "
            f"contact_compliance(collision={compliance['collision']}, contact={compliance['contact_occurred']}, "
            f"max_pen={compliance['max_penetration']:.3f}, success={compliance['success']})"
            f"{bc_text}"
        )

    summary = {
        "config": {
            "episodes": int(args.episodes),
            "seed": int(args.seed),
            "sampler": str(args.sampler),
            "include_records": bool(args.include_records),
            "allowed_penetration": float(args.allowed_penetration),
            "contact_trigger_clearance": float(args.contact_trigger_clearance),
            "normal_gain": float(args.normal_gain),
            "tangential_gain": float(args.tangential_gain),
            "nominal_soften_gain": float(args.nominal_soften_gain),
            "force_proxy_threshold": float(args.force_proxy_threshold),
            "force_proxy_scale": float(args.force_proxy_scale),
            "force_proxy_max_clearance": float(args.force_proxy_max_clearance),
            "bc_checkpoint": args.bc_checkpoint,
        },
        "summary": summarize_rollouts(episodes),
        "episodes": episodes,
    }

    summary_path = output_dir / "randomized_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary["summary"], indent=2))
    print(f"Saved randomized summary to {summary_path}")


if __name__ == "__main__":
    main()
