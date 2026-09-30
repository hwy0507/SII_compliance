#!/usr/bin/env python3
"""Run zero-residual WBC-aware Gym rollouts through the Fan Ye ESN actor API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from rl_sixd_stiffness_env import Fixture, PandaSixDStiffnessEnv


def fixtures_from_manifest(path: Path, split: str) -> tuple[Fixture, ...]:
    manifest = json.loads(path.read_text())
    if manifest.get("reference_source") != "fixed_panda_wbc":
        raise ValueError("WBC-aware ESN rollout requires a fixed_panda_wbc fixture manifest")
    rows = manifest.get("splits", {}).get(split, [])
    if not rows:
        raise ValueError(f"manifest has no {split} fixtures")
    return tuple(Fixture(
        rod_stroke_m=float(row["rod_stroke_m"]), rod_height_m=float(row["rod_height_m"]),
        rod_start_time_s=float(row["rod_start_time_s"]), grasp_time_s=float(row["grasp_time_s"]),
        rod_approach_side=row["rod_approach_side"], rod_center_x_m=float(row["rod_center_x_m"]), rod_center_y_m=float(row["rod_center_y_m"]),
    ) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "validation"), default="train")
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--max-fixtures", type=int, default=2)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    fixtures = fixtures_from_manifest(args.fixture_manifest, args.split)[:args.max_fixtures]
    if not fixtures:
        raise ValueError("max-fixtures must retain at least one fixture")
    env = PandaSixDStiffnessEnv(
        args.menagerie, fixtures=fixtures, reference_source="fixed_panda_wbc",
        enable_drive_residual=True, recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
        recovery_jerk_weight=0.02, fan_ye_model_npz=args.model_npz,
        fan_ye_train_summary_json=args.train_summary_json, seed=20260815,
    )
    records = []
    try:
        for index, fixture in enumerate(fixtures):
            observation, _ = env.reset(options={"fixture_index": index})
            if observation.shape != (84,) or not np.all(np.isfinite(observation)):
                raise RuntimeError("invalid Fan Ye WBC actor observation")
            reward = 0.0
            while True:
                observation, step_reward, terminated, truncated, info = env.step(np.zeros(7, dtype=np.float32))
                reward += step_reward
                if terminated or truncated:
                    records.append({"fixture": fixture.__dict__, "actor_feature_dimension": len(observation), "finite": bool(np.all(np.isfinite(observation)),), "return": float(reward), "terminal": info})
                    break
    finally:
        env.close()
    result = {"stage": "zero-residual WBC-aware Fan Ye ESN Gym interface smoke; no RL optimization", "reference_source": "fixed_panda_wbc", "actor_observation": "normalized q/qdot/WBC twist plus fixed Fan Ye reservoir state", "feature_dimension": 84, "split": args.split, "records": records, "warning": "This validates the online Gym interface and safety path only. A zero action is not a trained RL policy."}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"fixtures": len(records), "feature_dimension": 84, "finite": all(row["finite"] for row in records), "terminal_success": [row["terminal"]["task_success"] for row in records]}, indent=2))


if __name__ == "__main__":
    main()
