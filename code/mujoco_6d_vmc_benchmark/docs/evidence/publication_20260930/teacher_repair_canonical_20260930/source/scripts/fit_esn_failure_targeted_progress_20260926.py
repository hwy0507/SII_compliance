"""Fit a readout with progress recovery only on declared failure histories."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import actions_from_logits, hidden_from_head, load_model, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation, teacher_labels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--recovery-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--teacher-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress-gain-per-m", type=float, default=1.0)
    parser.add_argument("--progress-deadband-m", type=float, default=0.012)
    parser.add_argument("--maximum-progress-action", type=float, default=0.30)
    parser.add_argument("--loaded-weight", type=float, default=2.0)
    parser.add_argument("--proximal", type=float, default=0.01)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    all_paths = {path.resolve() for path in args.rollout}
    recovery_paths = {path.resolve() for path in args.recovery_rollout}
    if not recovery_paths <= all_paths:
        raise ValueError("every recovery rollout must also be in --rollout")

    model = load_model(args.checkpoint)
    config = json.loads(args.teacher_config.read_text())
    features_all: list[np.ndarray] = []
    targets_all: list[np.ndarray] = []
    stages_all: list[np.ndarray] = []
    shaped_samples = 0
    loaded_recovery_samples = 0
    for path in args.rollout:
        with np.load(path, allow_pickle=False) as data:
            observation = data["observation"].astype(np.float64)
            stage = data["stage"].astype(np.int64)
        target = teacher_labels(observation, config)
        if path.resolve() in recovery_paths:
            loaded = stage >= 3
            direction = observation[:, 45:48].copy()
            direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1.0e-9)
            error = observation[:, 20:23]
            progress_error = np.maximum(
                np.sum(error * direction, axis=1) - args.progress_deadband_m, 0.0
            )
            floor = np.minimum(
                args.progress_gain_per_m * progress_error, args.maximum_progress_action
            )
            component = np.sum(target[:, 1:4] * direction, axis=1)
            apply = loaded & (floor > component)
            target[apply, 1:4] += (floor[apply] - component[apply])[:, None] * direction[apply]
            target = np.clip(target, -0.999, 0.999)
            shaped_samples += int(np.sum(apply))
            loaded_recovery_samples += int(np.sum(loaded))
        features_all.append(features_from_observation(model, observation))
        targets_all.append(target)
        stages_all.append(stage)

    fmean = np.asarray(model["fmean"], dtype=np.float64)
    fstd = np.asarray(model["fstd"], dtype=np.float64)
    hidden = np.concatenate([
        hidden_from_head(
            (features - fmean) / fstd,
            np.asarray(model["w1"], dtype=np.float64),
            np.asarray(model["b1"], dtype=np.float64),
        )
        for features in features_all
    ])
    target = np.concatenate(targets_all)
    stages = np.concatenate(stages_all)
    weights = np.where(stages >= 3, args.loaded_weight, 1.0)
    design = np.c_[hidden, np.ones(len(hidden))]
    logits = np.arctanh(np.clip(target, -0.999, 0.999))
    p0 = np.clip(target[:, 0], 1.0e-4, 1.0 - 1.0e-4)
    logits[:, 0] = np.log(p0 / (1.0 - p0))
    base_w2 = np.asarray(model["w2"], dtype=np.float64)
    base_b2 = np.asarray(model["b2"], dtype=np.float64)
    base = np.vstack((base_w2.T, base_b2))
    weighted_design = design * weights[:, None]
    lhs = design.T @ weighted_design + args.proximal * np.eye(design.shape[1])
    rhs = weighted_design.T @ logits + args.proximal * base
    lhs[-1, -1] -= args.proximal * 0.9
    solved = np.linalg.solve(lhs, rhs)
    adapted_w2, adapted_b2 = solved[:-1], solved[-1]
    base_prediction = actions_from_logits(hidden @ base_w2.T + base_b2)
    prediction = actions_from_logits(hidden @ adapted_w2 + adapted_b2)

    metadata = {
        "method": "failure_targeted_reservoir_progress_readout",
        "base_checkpoint_sha256": sha(args.checkpoint),
        "rollout_sha256": [sha(path) for path in args.rollout],
        "recovery_rollout_sha256": [sha(path) for path in args.recovery_rollout],
        "teacher_config_sha256": hashlib.sha256(args.teacher_config.read_bytes()).hexdigest(),
        "progress_gain_per_m": args.progress_gain_per_m,
        "progress_deadband_m": args.progress_deadband_m,
        "maximum_progress_action": args.maximum_progress_action,
        "loaded_weight": args.loaded_weight,
        "proximal": args.proximal,
        "shaped_samples": shaped_samples,
        "loaded_recovery_samples": loaded_recovery_samples,
        "deployment_inputs": "unchanged proprio48; no stage, clock, geometry, or privileged state",
        "frozen_components": [
            "48D normalization", "heterogeneous-leak reservoir", "first readout layer",
            "action projection", "safety filter", "task and penetration gates",
        ],
    }
    checkpoint = args.output / "targeted_progress_adapted.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(
            stream, contract="proprio48_esn128_action7_v1", metadata=json.dumps(metadata),
            seed=np.int64(model["seed"]), mean=np.asarray(model["mean"]), std=np.asarray(model["std"]),
            win=np.asarray(model["win"]), w=np.asarray(model["w"]), leak=np.asarray(model["leak"]),
            input_mask=np.asarray(model["input_mask"]), alpha=np.float64(model["alpha"]),
            output_gain=np.float64(model["output_gain"]), fmean=np.asarray(model["fmean"]),
            fstd=np.asarray(model["fstd"]), w1=np.asarray(model["w1"]), b1=np.asarray(model["b1"]),
            w2=adapted_w2.T, b2=adapted_b2,
        )

    def score(values: np.ndarray) -> dict[str, float]:
        difference = values - target
        return {
            "rmse": float(np.sqrt(np.mean(difference * difference))),
            "mae": float(np.mean(np.abs(difference))),
        }

    report = {
        **metadata,
        "episodes": len(args.rollout),
        "samples": int(len(target)),
        "base_on_targets": score(base_prediction),
        "adapted_on_targets": score(prediction),
        "checkpoint_sha256": sha(checkpoint),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "REPORT.md").write_text(
        "# Failure-targeted reservoir progress readout\n\n```json\n"
        + json.dumps(report, indent=2) + "\n```\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
