#!/usr/bin/env python3
"""Fit a Direct ESN linear readout from privileged teacher archives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNConfig, DirectESNController, DirectESNObservation
from esn_compliance import ESNObservation


def load_episode(path: Path, sample_stride: int = 1) -> tuple[list[ESNObservation], np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        required = {"joint_position", "joint_velocity", "wbc_task_twist", "pose_error", "wbc_twist_error", "teacher_action"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing required fields {sorted(missing)}")
        index = slice(None, None, sample_stride)
        q = np.asarray(archive["joint_position"])[index]
        qdot = np.asarray(archive["joint_velocity"])[index]
        twist = np.asarray(archive["wbc_task_twist"])[index]
        pose_error = np.asarray(archive["pose_error"])[index]
        twist_error = np.asarray(archive["wbc_twist_error"])[index]
        target = np.asarray(archive["teacher_action"], dtype=float)[index]
    if not (q.ndim == 2 and q.shape[1] == 7 and qdot.shape == q.shape and twist.shape == (len(q), 6) and target.shape == (len(q), 7)):
        raise ValueError(f"{path}: invalid trace dimensions")
    observations = [DirectESNObservation(qi, qdoti, twisti, posei, twisti_error) for qi, qdoti, twisti, posei, twisti_error in zip(q, qdot, twist, pose_error, twist_error)]
    return observations, np.clip(target, -1.0, 1.0)


def fit_direct_esn(traces: list[Path], *, config: DirectESNConfig, sample_stride: int, washout_steps: int, neutral_repeat: int = 1) -> tuple[DirectESNController, dict]:
    if not traces:
        raise ValueError("at least one teacher archive is required")
    if sample_stride < 1 or washout_steps < 0 or neutral_repeat < 1:
        raise ValueError("sample_stride/washout must be valid and neutral_repeat positive")
    model = DirectESNController(config)
    all_features, all_targets, episodes = [], [], []
    for path in traces:
        observations, target = load_episode(path, sample_stride=sample_stride)
        if washout_steps >= len(observations):
            raise ValueError(f"{path}: washout is longer than episode")
        features = model.features(observations, washout_steps=washout_steps)
        target_after_washout = target[washout_steps:]
        repeats = neutral_repeat if any(token in path.stem.lower() for token in ("no_rod", "neutral", "nominal")) else 1
        all_features.extend([features] * repeats)
        all_targets.extend([target_after_washout] * repeats)
        episodes.append({"path": str(path), "samples": len(features), "fit_repeat": repeats})
    design = np.concatenate(all_features, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    mse = model.fit_readout(design, targets)
    return model, {"training_samples": len(design), "readout_training_mse": mse, "episodes": episodes, "config": config.__dict__}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-model", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--reservoir-size", type=int, default=160)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--sample-stride", type=int, default=1)
    parser.add_argument("--washout-steps", type=int, default=25)
    parser.add_argument("--neutral-repeat", type=int, default=1)
    args = parser.parse_args()
    # Trace decimation changes which samples are used for fitting, not the
    # physical controller period. MuJoCo executes the Direct ESN at 40 ms.
    sample_dt = 0.04
    config = DirectESNConfig(
        reservoir_size=args.reservoir_size,
        seed=args.seed,
        dt_s=sample_dt,
        time_constant_s=0.12,
    )
    model, summary = fit_direct_esn(args.traces, config=config, sample_stride=args.sample_stride, washout_steps=args.washout_steps, neutral_repeat=args.neutral_repeat)
    args.output_model.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    model.save_npz(args.output_model)
    payload = {"schema_version": 1, "method": "direct_esn_compliant_controller", "contract": model.contract(), "model_npz": str(args.output_model), **summary}
    args.output_summary.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"training_samples": summary["training_samples"], "readout_training_mse": summary["readout_training_mse"], "output_model": str(args.output_model)}, indent=2))


if __name__ == "__main__":
    main()
