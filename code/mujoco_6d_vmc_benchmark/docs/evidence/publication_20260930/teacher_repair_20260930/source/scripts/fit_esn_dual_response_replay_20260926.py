"""Fit an ESN readout with condition-separated yield and clearance replay."""
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
    parser.add_argument("--moderate-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--yield-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--clearance-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--teacher-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--default-progress-gain-per-m", type=float, default=1.0)
    parser.add_argument("--moderate-progress-gain-per-m", type=float, default=0.5)
    parser.add_argument("--yield-progress-gain-per-m", type=float, default=0.0)
    parser.add_argument("--clearance-progress-gain-per-m", type=float, required=True)
    parser.add_argument("--progress-deadband-m", type=float, default=0.012)
    parser.add_argument("--maximum-progress-action", type=float, default=0.30)
    parser.add_argument("--loaded-weight", type=float, default=2.0)
    parser.add_argument("--yield-weight-multiplier", type=float, default=2.0)
    parser.add_argument("--clearance-weight-multiplier", type=float, default=2.0)
    parser.add_argument("--proximal", type=float, default=0.05)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    all_paths = {path.resolve() for path in args.rollout}
    path_groups = {
        "moderate": {path.resolve() for path in args.moderate_rollout},
        "yield": {path.resolve() for path in args.yield_rollout},
        "clearance": {path.resolve() for path in args.clearance_rollout},
    }
    if any(not paths <= all_paths for paths in path_groups.values()):
        raise ValueError("all replay groups must be subsets of --rollout")
    if any(path_groups[a] & path_groups[b] for a, b in (("moderate", "yield"), ("moderate", "clearance"), ("yield", "clearance"))):
        raise ValueError("replay groups must be disjoint")
    if not (
        args.clearance_progress_gain_per_m > args.default_progress_gain_per_m
        > args.moderate_progress_gain_per_m > args.yield_progress_gain_per_m >= 0.0
    ):
        raise ValueError("gains must satisfy clearance > default > moderate > yield >= 0")
    if min(args.yield_weight_multiplier, args.clearance_weight_multiplier) < 1.0:
        raise ValueError("replay weight multipliers must be >= 1")
    if args.progress_deadband_m < 0.0 or not 0.0 < args.maximum_progress_action < 1.0:
        raise ValueError("invalid progress parameters")
    args.output.mkdir(parents=True)

    model = load_model(args.checkpoint)
    teacher_config = json.loads(args.teacher_config.read_text())
    feature_chunks: list[np.ndarray] = []
    target_chunks: list[np.ndarray] = []
    stage_chunks: list[np.ndarray] = []
    group_chunks: list[np.ndarray] = []
    group_names = ("default", "moderate", "yield", "clearance")
    gains = {
        "default": args.default_progress_gain_per_m,
        "moderate": args.moderate_progress_gain_per_m,
        "yield": args.yield_progress_gain_per_m,
        "clearance": args.clearance_progress_gain_per_m,
    }
    shaped = {name: 0 for name in group_names}
    loaded_count = {name: 0 for name in group_names}
    for path in args.rollout:
        resolved = path.resolve()
        group = next((name for name in ("moderate", "yield", "clearance") if resolved in path_groups[name]), "default")
        group_code = group_names.index(group)
        with np.load(path, allow_pickle=False) as data:
            observation = data["observation"].astype(np.float64)
            stage = data["stage"].astype(np.int64)
        target = teacher_labels(observation, teacher_config)
        loaded = stage >= 3
        direction = observation[:, 45:48].copy()
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1.0e-9)
        pose_error = observation[:, 20:23]
        progress_error = np.maximum(
            np.sum(pose_error * direction, axis=1) - args.progress_deadband_m, 0.0
        )
        floor = np.minimum(gains[group] * progress_error, args.maximum_progress_action)
        component = np.sum(target[:, 1:4] * direction, axis=1)
        apply = loaded & (floor > component)
        target[apply, 1:4] += (floor[apply] - component[apply])[:, None] * direction[apply]
        target = np.clip(target, -0.999, 0.999)
        shaped[group] += int(np.sum(apply))
        loaded_count[group] += int(np.sum(loaded))
        feature_chunks.append(features_from_observation(model, observation))
        target_chunks.append(target)
        stage_chunks.append(stage)
        group_chunks.append(np.full(len(stage), group_code, dtype=np.int8))

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
    groups = np.concatenate(group_chunks)
    weights = np.where(stages >= 3, args.loaded_weight, 1.0)
    weights *= np.where(groups == group_names.index("yield"), args.yield_weight_multiplier, 1.0)
    weights *= np.where(groups == group_names.index("clearance"), args.clearance_weight_multiplier, 1.0)
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

    metadata = {
        "method": "reservoir_dual_yield_clearance_replay_readout",
        "scope": "development dual-response replay; physical rollout required",
        "base_checkpoint_sha256": sha(args.checkpoint),
        "rollout_sha256": [sha(path) for path in args.rollout],
        "moderate_rollout_sha256": [sha(path) for path in args.moderate_rollout],
        "yield_rollout_sha256": [sha(path) for path in args.yield_rollout],
        "clearance_rollout_sha256": [sha(path) for path in args.clearance_rollout],
        "teacher_config_sha256": hashlib.sha256(args.teacher_config.read_bytes()).hexdigest(),
        "progress_gains_per_m": gains,
        "progress_deadband_m": args.progress_deadband_m,
        "maximum_progress_action": args.maximum_progress_action,
        "loaded_weight": args.loaded_weight,
        "yield_weight_multiplier": args.yield_weight_multiplier,
        "clearance_weight_multiplier": args.clearance_weight_multiplier,
        "proximal": args.proximal,
        "shaped_samples_by_group": shaped,
        "loaded_samples_by_group": loaded_count,
        "deployment_inputs": "unchanged proprio48; no stage, clock, geometry, fixture ID, or privileged state",
        "frozen_components": [
            "48D normalization", "heterogeneous-leak reservoir", "first readout layer",
            "action projection", "safety filter", "task and penetration gates",
        ],
    }
    checkpoint = args.output / "dual_response_adapted.npz"
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
        "# Reservoir dual yield/clearance replay\n\n```json\n"
        + json.dumps(report, indent=2) + "\n```\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
