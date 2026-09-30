"""Fit one ESN readout on several student-on-policy development rollouts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import actions_from_logits, hidden_from_head, load_model, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation, teacher_labels


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--rollout", type=Path, nargs="+", required=True)
    p.add_argument("--teacher-config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--proximal", type=float, default=0.01)
    p.add_argument("--on-policy-weight", type=float, default=8.0)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if len(args.rollout) < 2:
        raise ValueError("multi-fit requires at least two rollouts")
    args.output.mkdir(parents=True)
    model = load_model(args.checkpoint)
    config = json.loads(args.teacher_config.read_text())
    feature_chunks, target_chunks = [], []
    for path in args.rollout:
        with np.load(path, allow_pickle=False) as z:
            observation = z["observation"].astype(np.float64)
        features = features_from_observation(model, observation)
        target = teacher_labels(observation, config)
        feature_chunks.append(features)
        target_chunks.append(target)
    fmean = np.asarray(model["fmean"], dtype=np.float64)
    fstd = np.asarray(model["fstd"], dtype=np.float64)
    hidden_chunks = [hidden_from_head((f - fmean) / fstd, np.asarray(model["w1"], dtype=np.float64), np.asarray(model["b1"], dtype=np.float64)) for f in feature_chunks]
    hidden = np.concatenate(hidden_chunks, axis=0)
    target = np.concatenate(target_chunks, axis=0)
    design = np.c_[hidden, np.ones(len(hidden))]
    logits = np.arctanh(np.clip(target, -0.999, 0.999))
    p0 = np.clip(target[:, 0], 1.0e-4, 1.0 - 1.0e-4)
    logits[:, 0] = np.log(p0 / (1.0 - p0))
    base_w2 = np.asarray(model["w2"], dtype=np.float64)
    base_b2 = np.asarray(model["b2"], dtype=np.float64)
    base_weights = np.vstack((base_w2.T, base_b2))
    lhs = args.on_policy_weight * (design.T @ design) + args.proximal * np.eye(design.shape[1])
    rhs = args.on_policy_weight * (design.T @ logits) + args.proximal * base_weights
    lhs[-1, -1] -= args.proximal * 0.9
    weights = np.linalg.solve(lhs, rhs)
    adapted_w2, adapted_b2 = weights[:-1], weights[-1]
    base_pred = actions_from_logits(hidden @ base_w2.T + base_b2)
    adapted_pred = actions_from_logits(hidden @ adapted_w2 + adapted_b2)

    metadata = {
        "method": "multi_student_on_policy_vmc_relabel_readout",
        "scope": "development DAgger iteration; physical rollout required",
        "base_checkpoint_sha256": sha(args.checkpoint),
        "rollout_sha256": [sha(path) for path in args.rollout],
        "teacher_config_sha256": hashlib.sha256(args.teacher_config.read_bytes()).hexdigest(),
        "frozen_components": ["48D normalization", "reservoir", "first readout layer", "action projection", "safety filter", "task gates"],
        "on_policy_weight": args.on_policy_weight,
        "proximal_weight": args.proximal,
        "episodes": len(args.rollout),
        "limitations": ["development fixtures only", "labels are teacher relabels", "no validation fixture used for selection"],
    }
    checkpoint = args.output / "onpolicy_multi_adapted.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, contract="proprio48_esn128_action7_v1", metadata=json.dumps(metadata),
            seed=np.int64(model["seed"]), mean=np.asarray(model["mean"]), std=np.asarray(model["std"]),
            win=np.asarray(model["win"]), w=np.asarray(model["w"]), leak=np.asarray(model["leak"]),
            input_mask=np.asarray(model["input_mask"]), alpha=np.float64(model["alpha"]), output_gain=np.float64(model["output_gain"]),
            fmean=np.asarray(model["fmean"]), fstd=np.asarray(model["fstd"]), w1=np.asarray(model["w1"]), b1=np.asarray(model["b1"]),
            w2=adapted_w2.T, b2=adapted_b2)
    def metric(pred):
        diff = pred - target
        return {"action_rmse": float(np.sqrt(np.mean(diff * diff))), "action_mae": float(np.mean(np.abs(diff))),
                "x_sign_flip_fraction": float(np.mean(pred[:, 1] * target[:, 1] < 0.0))}
    report = {**metadata, "checkpoint_sha256": sha(checkpoint), "samples": int(len(target)),
              "base_on_policy": metric(base_pred), "adapted_on_policy": metric(adapted_pred)}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "REPORT.md").write_text("# Multi-episode ESN on-policy relabel\n\n" + json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
