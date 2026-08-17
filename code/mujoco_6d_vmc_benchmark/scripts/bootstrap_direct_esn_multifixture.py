#!/usr/bin/env python3
"""Create a reservoir-seed-specific Direct ESN bootstrap checkpoint.

The rod teacher is decimated from 4 ms to the deployed 40 ms Direct-ESN
period, while the no-rod neutral trace remains at 40 ms.  This gives formal
multi-reservoir training an actual source of model variation before DAgger.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNConfig, DirectESNController, DirectESNObservation


def _load_episode(path: Path, stride: int) -> tuple[list[DirectESNObservation], np.ndarray]:
    if stride < 1:
        raise ValueError("sample stride must be positive")
    with np.load(path, allow_pickle=False) as archive:
        required = {"joint_position", "joint_velocity", "wbc_task_twist", "pose_error", "wbc_twist_error", "teacher_action"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        sample = slice(None, None, stride)
        q = np.asarray(archive["joint_position"], dtype=float)[sample]
        qdot = np.asarray(archive["joint_velocity"], dtype=float)[sample]
        twist = np.asarray(archive["wbc_task_twist"], dtype=float)[sample]
        pose = np.asarray(archive["pose_error"], dtype=float)[sample]
        twist_error = np.asarray(archive["wbc_twist_error"], dtype=float)[sample]
        action = np.asarray(archive["teacher_action"], dtype=float)[sample]
    if not (q.shape == (len(q), 7) and qdot.shape == q.shape and twist.shape == (len(q), 6) and pose.shape == (len(q), 6) and twist_error.shape == (len(q), 6) and action.shape == (len(q), 7)):
        raise ValueError(f"{path}: invalid Direct ESN archive dimensions")
    observations = [DirectESNObservation(qi, qdoti, twisti, posei, twist_error_i) for qi, qdoti, twisti, posei, twist_error_i in zip(q, qdot, twist, pose, twist_error)]
    return observations, np.clip(action, -1.0, 1.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-rod-trace", type=Path, required=True)
    parser.add_argument("--base-no-rod-trace", type=Path, required=True)
    parser.add_argument("--output-model", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--reservoir-seed", type=int, required=True)
    parser.add_argument("--reservoir-size", type=int, default=160)
    parser.add_argument("--washout-steps", type=int, default=3)
    parser.add_argument("--rod-repeat", type=int, default=4)
    parser.add_argument("--neutral-repeat", type=int, default=3)
    args = parser.parse_args()
    if min(args.reservoir_size, args.washout_steps + 1, args.rod_repeat, args.neutral_repeat) < 1:
        raise ValueError("bootstrap dimensions/weights are invalid")
    config = DirectESNConfig(reservoir_size=args.reservoir_size, seed=args.reservoir_seed, dt_s=0.04)
    model = DirectESNController(config)
    episodes = []
    features_all, targets_all = [], []
    for name, path, stride, repeat in (
        ("rod", args.base_rod_trace, 10, args.rod_repeat),
        ("no_rod", args.base_no_rod_trace, 1, args.neutral_repeat),
    ):
        observations, actions = _load_episode(path, stride)
        if args.washout_steps >= len(observations):
            raise ValueError(f"{path}: washout exceeds episode length")
        features = model.features(observations, washout_steps=args.washout_steps)
        labels = actions[args.washout_steps:]
        features_all.extend([features] * repeat)
        targets_all.extend([labels] * repeat)
        episodes.append({"name": name, "path": str(path), "samples": len(features), "stride": stride, "repeat": repeat})
    design = np.concatenate(features_all, axis=0)
    targets = np.concatenate(targets_all, axis=0)
    mse = model.fit_readout(design, targets)
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    model.save_npz(args.output_model)
    summary = {
        "schema_version": 1,
        "method": "direct_esn_reservoir_seed_bootstrap",
        "model": str(args.output_model),
        "reservoir": asdict(config),
        "training_samples": len(design),
        "readout_training_mse": mse,
        "episodes": episodes,
    }
    args.output_summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
