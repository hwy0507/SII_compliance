#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from residual_compliance_fetch.controllers import ContactComplianceConfig
from residual_compliance_fetch.maniskill_demo import CommandConfig, DemoConfig, run_comparison
from residual_compliance_fetch.obstacles import CrossingSphereSpec
from residual_compliance_fetch.utils import ensure_conda_lib_path


def main() -> None:
    ensure_conda_lib_path()

    parser = argparse.ArgumentParser(
        description="Run Fetch arm residual compliance demo in ManiSkill/SAPIEN."
    )
    parser.add_argument("--env-id", default="ReplicaCAD_SceneManipulation-v1")
    parser.add_argument("--trajectory", default=None)
    parser.add_argument("--output-dir", default="outputs/fetch_residual_demo")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--render-mode", default="human", choices=["human", "none"])
    parser.add_argument("--record-gif", action="store_true")
    parser.add_argument(
        "--camera-view",
        default="side",
        choices=["side", "front", "iso", "close", "top"],
        help="Third-person recording camera preset.",
    )
    parser.add_argument(
        "--camera-target",
        type=float,
        nargs=3,
        default=[-0.62, 0.04, 1.45],
        help="World-space look-at target for the recording camera.",
    )
    parser.add_argument("--allowed-penetration", type=float, default=0.025)
    parser.add_argument("--contact-trigger-clearance", type=float, default=0.0)
    parser.add_argument("--normal-gain", type=float, default=1.50)
    parser.add_argument("--tangential-gain", type=float, default=0.30)
    parser.add_argument("--nominal-soften-gain", type=float, default=1.00)
    parser.add_argument("--force-proxy-threshold", type=float, default=0.35)
    parser.add_argument("--force-proxy-scale", type=float, default=0.45)
    parser.add_argument("--force-proxy-max-clearance", type=float, default=0.035)
    parser.add_argument("--bc-checkpoint", default=None)
    parser.add_argument("--include-records", action="store_true")
    parser.add_argument("--max-steps", type=int, default=420)
    parser.add_argument(
        "--no-early-stop",
        action="store_true",
        help="Keep recording until max_steps even after the arm reaches the target.",
    )
    parser.add_argument(
        "--allow-body-motion",
        action="store_true",
        help="Do not lock base/torso/head/gripper joints. For debugging only.",
    )
    parser.add_argument("--dt", type=float, default=1.0 / 30.0)
    parser.add_argument("--obstacle-radius", type=float, default=0.105)
    parser.add_argument("--obstacle-spawn-time", type=float, default=1.4)
    parser.add_argument(
        "--obstacle-end-time",
        type=float,
        default=None,
        help="Optional time when the obstacle disappears back to the hidden pose.",
    )
    parser.add_argument("--obstacle-start", type=float, nargs=3, default=[-0.54, -0.34, 1.48])
    parser.add_argument("--obstacle-velocity", type=float, nargs=3, default=[0.0, 0.36, 0.0])
    args = parser.parse_args()

    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    demo_config = DemoConfig(
        env_id=args.env_id,
        render_mode=args.render_mode,
        seed=args.seed,
        dt=args.dt,
        max_steps=args.max_steps,
        no_early_stop=bool(args.no_early_stop),
        lock_non_arm_joints=not bool(args.allow_body_motion),
        record_gif=bool(args.record_gif),
        camera_view=args.camera_view,
        camera_target=tuple(float(v) for v in args.camera_target),
        allowed_penetration=float(args.allowed_penetration),
        trajectory=args.trajectory,
        output_dir=args.output_dir,
    )
    command_config = CommandConfig()
    compliance_config = ContactComplianceConfig(
        contact_trigger_clearance=float(args.contact_trigger_clearance),
        normal_gain=float(args.normal_gain),
        tangential_gain=float(args.tangential_gain),
        nominal_soften_gain=float(args.nominal_soften_gain),
        force_proxy_threshold=float(args.force_proxy_threshold),
        force_proxy_scale=float(args.force_proxy_scale),
        force_proxy_max_clearance=float(args.force_proxy_max_clearance),
    )
    obstacle_spec = CrossingSphereSpec(
        radius=float(args.obstacle_radius),
        spawn_time=float(args.obstacle_spawn_time),
        end_time=None if args.obstacle_end_time is None else float(args.obstacle_end_time),
        start=tuple(float(v) for v in args.obstacle_start),
        velocity=tuple(float(v) for v in args.obstacle_velocity),
    )

    results = run_comparison(
        demo_config=demo_config,
        command_config=command_config,
        compliance_config=compliance_config,
        obstacle_spec=obstacle_spec,
        include_records=bool(args.include_records),
        bc_checkpoint=args.bc_checkpoint,
    )
    print(json.dumps(results["rollouts"], indent=2))
    print(f"Saved metrics to {results['metrics_path']}")


if __name__ == "__main__":
    main()
