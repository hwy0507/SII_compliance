"""Run one predeclared ESN checkpoint on the fixed 9301 loaded-lift fixture."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=9301)
    p.add_argument("--push-angle", type=float, default=-0.05)
    p.add_argument("--push-height", type=float, default=0.58)
    p.add_argument("--payload-mass", type=float, default=0.1)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    repo = Path(__file__).resolve().parent
    root = repo.parent
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
               MUJOCO_GL="egl", PANELS_ENABLED="1", UNIFIED_6D_TEACHER="1",
               PRIMITIVE_RUNNER_PATH=str(repo / "run_primitive_teacher_v7_20260917.py"),
               CORE_VMC_CONFIG='{"stiffness_6d": [520, 360, 1400, 12, 10, 14], "damping_6d": [32, 27, 62, 3, 2.7, 3.3], "mass_6d": [0.5, 0.5, 0.8, 0.06, 0.06, 0.08], "wrench_limit_6d": [35, 35, 50, 3, 3, 3], "deadband_6d": [0.2, 0.2, 0.2, 0.03, 0.03, 0.03], "velocity_limit_6d": [0.12, 0.12, 0.16, 0.55, 0.55, 0.65], "offset_limit_6d": [0.18, 0.18, 0.18, 0.35, 0.35, 0.35], "action_limit_6d": [0.16, 0.16, 0.2, 0.6, 0.6, 0.6], "offset_tracking_gain_6d": 1.4, "filter_tau": 0.04, "axis_rotation_rpy": [0.35, 0, -0.25]}',
               PANEL_CONFIG='{"layout": "raised_hand_rim", "pad_bottom_z": 0.55, "pad_top_z": 0.71, "pad_lower_y": -0.15, "pad_upper_y": -0.085, "front_inner_x": 0.595, "back_inner_x": 0.5, "pad_thickness": 0.015, "end_effector_only": false, "rod_height_m": 0.58, "workstation": true}')
    args_list = [
        sys.executable, str(repo / "run_with_substep_metrics_20260923.py"),
        "--runner", str(repo / "run_panel_push_20260920.py"),
        "--metrics-output", str(args.output / "metrics"), "--",
        "--output", str(args.output / "rollout"), "--model", str(args.model),
        "--scene", "push", "--menagerie", str(root / "outputs/canonical_rl_assets_20260923/menagerie"),
        "--duration", "24.0", "--nominal-speed", "0.08", "--mixture", "0.0", "--seed", str(args.seed),
        "--yaw", "0.0", "--shift", "0.0", "--width", "0.05", "--cup-mass", "0.3",
        "--ball-mass", "0.2", "--ball-speed", "1.5", "--ball-angle", "0.0", "--ball-height-offset", "0.0",
        "--ball-vertical-speed", "1.3", "--ball-radius", "0.06", "--ball-shell", "0.005",
        "--ball-contact-time", "0.008", "--ball-contact-damping", "0.75", "--push-hold", "1000000.0",
        "--push-angle", str(args.push_angle), "--push-height", str(args.push_height), "--push-force", "12.0", "--push-target-x", "0.57",
        "--push-stroke", "0.18", "--push-press", "0.5", "--push-retract", "1.0", "--corner-height", "0.7",
        "--corner-friction", "0.2", "--payload-mass", str(args.payload_mass), "--event-stage", "loaded_lift", "--event-delay", "0.0",
        "--stiffness", "200.0", "--tangent-speed", "0.0", "--damping", "20.0", "--force-on", "0.5",
        "--contact-tau", "0.12", "--release-tau", "0.45", "--memory-tau", "1.2", "--teacher-force-source", "estimated",
        "--teacher-profile", "memory", "--force-target", "1.0", "--normal-gain", "0.015", "--dt", "0.0001",
    ]
    with (args.output / "run.log").open("w") as log:
        done = subprocess.run(args_list, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT)
    (args.output / "status.json").write_text('{"status": %d}\n' % done.returncode)
    if done.returncode:
        raise SystemExit(done.returncode)


if __name__ == "__main__":
    main()
