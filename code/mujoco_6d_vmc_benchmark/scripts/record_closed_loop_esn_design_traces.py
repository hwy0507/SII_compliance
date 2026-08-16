#!/usr/bin/env python3
"""Record development-train traces for causal closed-loop ESN preselection.

The probe is a fixed WBC-error feedback law, not a learned controller and not a
performance baseline.  Its sole purpose is to expose the joint/WBC/residual
filter dynamics that a closed-loop reservoir must represent.  It reads only
current WBC pose/twist error and produces bounded residual proposals; contact
signals, rod state, obstacle geometry, release time, and fixture ID are never
read by the probe.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from train_wbc_velocity_residual import load_development_fixtures
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


def probe_action(pose_error: np.ndarray, twist_error: np.ndarray) -> np.ndarray:
    """A bounded, causal excitation of the shared residual safety adapter.

    The WBC error is target-minus-measured.  The translational residual yields
    opposite the observed departure; twist feedback adds a small damping-like
    component.  This is deliberately fixed before any ESN screen and is never
    compared by reward or final task score.
    """

    pose = np.asarray(pose_error, dtype=float)
    twist = np.asarray(twist_error, dtype=float)
    if pose.shape != (6,) or twist.shape != (6,) or not np.all(np.isfinite(pose)) or not np.all(np.isfinite(twist)):
        raise ValueError("probe needs finite six-dimensional WBC errors")
    action = np.zeros(7, dtype=np.float32)
    departure = float(np.linalg.norm(pose[:3]))
    authority = float(np.clip((departure - 0.002) / 0.015, 0.0, 0.55))
    action[0] = authority
    action[1:4] = np.clip(-7.0 * pose[:3] - 0.18 * twist[:3], -0.42, 0.42) * authority
    action[4:7] = np.clip(-0.65 * pose[3:] - 0.06 * twist[3:], -0.16, 0.16) * authority
    return np.clip(action, -1.0, 1.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "validation"), default="train")
    parser.add_argument("--max-fixtures", type=int, default=None)
    args = parser.parse_args()
    fixtures = load_development_fixtures(args.fixture_manifest, args.split)
    if args.max_fixtures is not None:
        fixtures = fixtures[:args.max_fixtures]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = PandaWBCVelocityResidualEnv(
        menagerie=args.menagerie,
        fan_ye_model_npz=args.fan_ye_model_npz,
        fan_ye_train_summary_json=args.fan_ye_train_summary_json,
        observation_mode="current_mlp", fixtures=fixtures, rod_enabled=True, seed=20260950,
    )
    try:
        for fixture_index in range(len(fixtures)):
            _, _ = env.reset(options={"fixture_index": fixture_index})
            trace = {key: [] for key in (
                "joint_position", "joint_velocity", "wbc_task_twist", "wbc_pose_error",
                "wbc_twist_error", "wbc_scale", "yield_twist", "policy_action",
            )}
            while True:
                state = env.diagnostics()
                action = probe_action(state["wbc_pose_error"], state["wbc_twist_error"])
                _, _, terminated, truncated, _ = env.step(action)
                applied = env.diagnostics()
                trace["joint_position"].append(applied["joint_position"])
                trace["joint_velocity"].append(applied["joint_velocity"])
                trace["wbc_task_twist"].append(applied["nominal_twist"])
                trace["wbc_pose_error"].append(applied["wbc_pose_error"])
                trace["wbc_twist_error"].append(applied["wbc_twist_error"])
                trace["wbc_scale"].append(applied["wbc_scale"])
                trace["yield_twist"].append(applied["cartesian_yield_twist"])
                trace["policy_action"].append(action)
                if terminated or truncated:
                    break
            np.savez_compressed(
                args.output_dir / f"{args.split}_fixture_{fixture_index:02d}_closed_loop_probe.npz",
                **{key: np.asarray(value) for key, value in trace.items()},
            )
    finally:
        env.close()


if __name__ == "__main__":
    main()
