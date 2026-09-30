"""Fit a reservoir readout with condition-separated progress labels.

The deployed policy still receives only the frozen 48-D proprioceptive input.
Trajectory membership is used solely to construct development targets.
"""
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
    parser.add_argument("--conservative-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--teacher-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--default-progress-gain-per-m", type=float, default=1.0)
    parser.add_argument("--conservative-progress-gain-per-m", type=float, required=True)
    parser.add_argument("--progress-deadband-m", type=float, default=0.012)
    parser.add_argument("--maximum-progress-action", type=float, default=0.30)
    parser.add_argument("--loaded-weight", type=float, default=2.0)
    parser.add_argument("--proximal", type=float, default=0.01)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    all_paths = {path.resolve() for path in args.rollout}
    conservative_paths = {path.resolve() for path in args.conservative_rollout}
    if not conservative_paths <= all_paths:
        raise ValueError("every conservative rollout must also be in --rollout")
    if not 0.0 <= args.conservative_progress_gain_per_m < args.default_progress_gain_per_m:
        raise ValueError("conservative gain must be nonnegative and below default gain")
    if args.progress_deadband_m < 0.0 or not 0.0 < args.maximum_progress_action < 1.0:
        raise ValueError("invalid progress parameters")
    args.output.mkdir(parents=True)

    model = load_model(args.checkpoint)
    teacher_config = json.loads(args.teacher_config.read_text())
    feature_chunks: list[np.ndarray] = []
    target_chunks: list[np.ndarray] = []
    stage_chunks: list[np.ndarray] = []
    shaped_by_group = {"default": 0, "conservative": 0}
    loaded_by_group = {"default": 0, "conservative": 0}
    floors_by_group: dict[str, list[np.ndarray]] = {"default": [], "conservative": []}
    for path in args.rollout:
        with np.load(path, allow_pickle=False) as data:
            observation = data["observation"].astype(np.float64)
            stage = data["stage"].astype(np.int64)
        target = teacher_labels(observation, teacher_config)
        group = "conservative" if path.resolve() in conservative_paths else "default"
        gain = (
            args.conservative_progress_gain_per_m
            if group == "conservative"
            else args.default_progress_gain_per_m
        )
        loaded = stage >= 3
        direction = observation[:, 45:48].copy()
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1.0e-9)
        pose_error = observation[:, 20:23]
        progress_error = np.maximum(
            np.sum(pose_error * direction, axis=1) - args.progress_deadband_m, 0.0
        )
        floor = np.minimum(gain * progress_error, args.maximum_progress_action)
        component = np.sum(target[:, 1:4] * direction, axis=1)
        apply = loaded & (floor > component)
        target[apply, 1:4] += (floor[apply] - component[apply])[:, None] * direction[apply]
        target = np.clip(target, -0.999, 0.999)
        shaped_by_group[group] += int(np.sum(apply))
        loaded_by_group[group] += int(np.sum(loaded))
        floors_by_group[group].append(floor[loaded])
        feature_chunks.append(features_from_observation(model, observation))
        target_chunks.append(target)
        stage_chunks.append(stage)

    fmean = np.asarray(model["fmean"], dtype=np.float64)
    fstd = np.asarray(model["fstd"], dtype=np.float64)
    w1 = np.asarray(model["w1"], dtype=np.float64)
    b1 = np.asarray(model["b1"], dtype=np.float64)
    hidden = np.concatenate([
        hidden_from_head((features - fmean) / fstd, w1, b1)
        for features in feature_chunks
    ])
    target = np.concatenate(target_chunks)
    stages = np.concatenate(stage_chunks)
    weights = np.where(stages >= 3, args.loaded_weight, 1.0)
    design = np.c_[hidden, np.ones(len(hidden))]
    logits = np.arctanh(np.clip(target, -0.999, 0.999))
    probability = np.clip(target[:, 0], 1.0e-4, 1.0 - 1.0e-4)
    logits[:, 0] = np.log(probability / (1.0 - probability))
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
    adapted_prediction = actions_from_logits(hidden @ adapted_w2 + adapted_b2)

    floor_statistics = {}
    for group, chunks in floors_by_group.items():
        values = np.concatenate(chunks)
        floor_statistics[group] = {
            "mean": float(np.mean(values)),
            "p95": float(np.quantile(values, 0.95)),
        }
    metadata = {
        "method": "condition_separated_reservoir_progress_readout",
        "scope": "development safety-recovery tradeoff; physical rollout required",
        "base_checkpoint_sha256": sha(args.checkpoint),
        "rollout_sha256": [sha(path) for path in args.rollout],
        "conservative_rollout_sha256": [sha(path) for path in args.conservative_rollout],
        "teacher_config_sha256": hashlib.sha256(args.teacher_config.read_bytes()).hexdigest(),
        "default_progress_gain_per_m": args.default_progress_gain_per_m,
        "conservative_progress_gain_per_m": args.conservative_progress_gain_per_m,
        "progress_deadband_m": args.progress_deadband_m,
        "maximum_progress_action": args.maximum_progress_action,
        "loaded_weight": args.loaded_weight,
        "proximal": args.proximal,
        "shaped_samples_by_group": shaped_by_group,
        "loaded_samples_by_group": loaded_by_group,
        "progress_floor_by_group": floor_statistics,
        "deployment_inputs": "unchanged proprio48; no stage, clock, geometry, fixture ID, or privileged state",
        "frozen_components": [
            "48D normalization", "heterogeneous-leak reservoir", "first readout layer",
            "action projection", "safety filter", "task and penetration gates",
        ],
    }
    checkpoint = args.output / "conditioned_progress_adapted.npz"
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

    def metrics(prediction: np.ndarray) -> dict[str, float]:
        difference = prediction - target
        return {
            "action_rmse": float(np.sqrt(np.mean(difference * difference))),
            "action_mae": float(np.mean(np.abs(difference))),
        }

    report = {
        **metadata,
        "episodes": len(args.rollout),
        "samples": int(len(target)),
        "base_on_targets": metrics(base_prediction),
        "adapted_on_targets": metrics(adapted_prediction),
        "checkpoint_sha256": sha(checkpoint),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "REPORT.md").write_text(
        "# Condition-separated reservoir progress readout\n\n```json\n"
        + json.dumps(report, indent=2) + "\n```\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
