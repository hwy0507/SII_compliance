"""Fit a proximal ESN readout on fixed-teacher contact histories.

This is an offline development diagnostic.  The reservoir, 48-D observation
contract, action projection, safety filter and task gates remain unchanged.
Only the final ESN readout is adapted using six pre-archived training-side
teacher traces; six validation-side traces are evaluated once and never used
for selection.  No MuJoCo environment is created by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model(path: Path) -> dict[str, np.ndarray | str | float | int]:
    with np.load(path, allow_pickle=False) as z:
        required = {
            "contract", "seed", "mean", "std", "win", "w", "leak",
            "input_mask", "alpha", "output_gain", "fmean", "fstd",
            "w1", "b1", "w2", "b2",
        }
        missing = required - set(z.files)
        if missing:
            raise ValueError(f"checkpoint missing fields: {sorted(missing)}")
        out: dict[str, np.ndarray | str | float | int] = {
            "contract": str(z["contract"]),
            "seed": int(z["seed"]),
            "alpha": float(z["alpha"]),
            "output_gain": float(z["output_gain"]),
        }
        for key in ("mean", "std", "win", "w", "leak", "input_mask", "fmean", "fstd", "w1", "b1", "w2", "b2"):
            out[key] = z[key].copy()
    if out["contract"] != "proprio48_esn128_action7_v1":
        raise ValueError(f"expected 48-D ESN checkpoint, got {out['contract']}")
    return out


def rollout_features(model: dict, trace: Path) -> tuple[np.ndarray, np.ndarray]:
    with np.load(trace, allow_pickle=False) as z:
        observation = z["observation"].astype(np.float64)
        target = z["teacher_action"].astype(np.float64)
    if observation.shape != (600, 48) or target.shape != (600, 7):
        raise ValueError(f"invalid trace shapes in {trace}: {observation.shape}, {target.shape}")
    mean = np.asarray(model["mean"], dtype=np.float64)
    std = np.asarray(model["std"], dtype=np.float64)
    mask = np.asarray(model["input_mask"], dtype=np.float64)
    win = np.asarray(model["win"], dtype=np.float64)
    recurrent = np.asarray(model["w"], dtype=np.float64)
    leak = np.asarray(model["leak"], dtype=np.float64)
    x = np.clip((observation - mean) / std, -12.0, 12.0) * mask
    state = np.zeros(128, dtype=np.float64)
    features = []
    for row in x:
        state += leak * (np.tanh(win @ np.r_[1.0, row] + recurrent @ state) - state)
        features.append(np.r_[row, state])
    return np.asarray(features), np.clip(target, -1.0, 1.0)


def hidden_from_head(features: np.ndarray, w1: np.ndarray, b1: np.ndarray) -> np.ndarray:
    return np.tanh(features @ w1.T + b1)


def actions_from_logits(logits: np.ndarray) -> np.ndarray:
    out = np.tanh(logits)
    out[:, 0] = 1.0 / (1.0 + np.exp(-np.clip(logits[:, 0], -60.0, 60.0)))
    return out


def target_logits(target: np.ndarray) -> np.ndarray:
    logits = np.arctanh(np.clip(target, -0.999, 0.999))
    p = np.clip(target[:, 0], 1.0e-4, 1.0 - 1.0e-4)
    logits[:, 0] = np.log(p / (1.0 - p))
    return logits


def action_stats(pred: np.ndarray, target: np.ndarray) -> dict[str, float]:
    diff = pred - target
    pred_d = np.diff(pred, axis=0)
    target_d = np.diff(target, axis=0)
    sign = (pred[1:, 1] * pred[:-1, 1]) < 0.0
    return {
        "action_rmse": float(np.sqrt(np.mean(diff * diff))),
        "action_mae": float(np.mean(np.abs(diff))),
        "delta_rmse": float(np.sqrt(np.mean((pred_d - target_d) ** 2))),
        "delta_mae": float(np.mean(np.abs(pred_d - target_d))),
        "pred_delta_rms": float(np.sqrt(np.mean(pred_d * pred_d))),
        "target_delta_rms": float(np.sqrt(np.mean(target_d * target_d))),
        "x_sign_flip_fraction": float(np.mean(sign)),
        "nonfinite": float(np.sum(~np.isfinite(pred))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=2500)
    parser.add_argument("--lr", type=float, default=1.0e-3)
    parser.add_argument("--smoothness", type=float, default=0.10)
    parser.add_argument("--proximal", type=float, default=1.0e-3)
    parser.add_argument("--seed", type=int, default=20260925)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    args.output.mkdir(parents=True)

    model = load_model(args.checkpoint)
    archive = args.archive
    train_ids = [
        "train_9600_approach", "train_9600_loaded_lift",
        "train_9601_approach", "train_9601_loaded_lift",
        "train_9602_approach", "train_9602_loaded_lift",
    ]
    validation_ids = [
        "validation_9610_approach", "validation_9610_loaded_lift",
        "validation_9611_approach", "validation_9611_loaded_lift",
        "validation_9612_approach", "validation_9612_loaded_lift",
    ]
    train = [rollout_features(model, archive / "jobs" / job / "rollout" / "rollout.npz") for job in train_ids]
    validation = [rollout_features(model, archive / "jobs" / job / "rollout" / "rollout.npz") for job in validation_ids]
    fmean = np.asarray(model["fmean"], dtype=np.float64)
    fstd = np.asarray(model["fstd"], dtype=np.float64)
    train_features = np.concatenate([(features - fmean) / fstd for features, _ in train], axis=0)
    train_targets = np.concatenate([target for _, target in train], axis=0)
    val_features = np.concatenate([(features - fmean) / fstd for features, _ in validation], axis=0)
    val_targets = np.concatenate([target for _, target in validation], axis=0)

    np.random.default_rng(args.seed)  # record the seed without introducing stochastic fitting
    w1 = np.asarray(model["w1"], dtype=np.float64)
    b1 = np.asarray(model["b1"], dtype=np.float64)
    base_w2 = np.asarray(model["w2"], dtype=np.float64)
    base_b2 = np.asarray(model["b2"], dtype=np.float64)
    hidden_train = hidden_from_head(train_features, w1, b1)
    hidden_val = hidden_from_head(val_features, w1, b1)
    design = np.c_[hidden_train, np.ones(len(hidden_train))]
    logits = target_logits(train_targets)
    # The finite-difference term is represented as a second linear system on
    # consecutive hidden features.  This preserves a closed-form NumPy fit.
    delta_design = design[1:] - design[:-1]
    delta_logits = logits[1:] - logits[:-1]
    reg = np.eye(design.shape[1], dtype=np.float64) * args.proximal
    reg[-1, -1] = args.proximal * 0.1
    lhs = design.T @ design + args.smoothness * (delta_design.T @ delta_design) + reg
    rhs = design.T @ logits + args.smoothness * (delta_design.T @ delta_logits)
    base_weights = np.vstack((base_w2.T, base_b2))
    # Small proximal ridge around the audited last layer prevents the adapter
    # from becoming a new unconstrained policy.
    lhs += args.proximal * np.eye(lhs.shape[0])
    rhs += args.proximal * base_weights
    weights = np.linalg.solve(lhs, rhs)
    adapted_w2, adapted_b2 = weights[:-1], weights[-1]
    train_pred = actions_from_logits(hidden_train @ adapted_w2 + adapted_b2)
    val_pred = actions_from_logits(hidden_val @ adapted_w2 + adapted_b2)
    base_train_pred = actions_from_logits(hidden_train @ base_w2.T + base_b2)
    base_val_pred = actions_from_logits(hidden_val @ base_w2.T + base_b2)
    history = [{"fit": "closed_form_ridge", "train": action_stats(train_pred, train_targets),
                "validation": action_stats(val_pred, val_targets)}]

    metadata = {
        "method": "proximal_readout_history_adapter",
        "scope": "offline fixed-teacher development diagnostic; no MuJoCo rollout",
        "base_checkpoint_sha256": sha(args.checkpoint),
        "archive": str(archive.resolve()),
        "train_jobs": train_ids,
        "validation_jobs": validation_ids,
        "seed": args.seed,
        "steps": args.steps,
        "learning_rate": args.lr,
        "smoothness_weight": args.smoothness,
        "proximal_weight": args.proximal,
        "device": "numpy",
        "frozen_components": ["48D input normalization", "reservoir", "first readout layer", "action projection", "safety filter", "task gates"],
        "limitations": [
            "teacher-history action metrics are not closed-loop task success",
            "validation traces are development diagnostics, not held-out office tests",
            "no gate, fixture, or safety threshold was changed",
            "a physical deployment is required before claiming improvement",
        ],
    }
    output_checkpoint = args.output / "adapted.npz"
    with output_checkpoint.open("wb") as stream:
        np.savez_compressed(
            stream,
            contract="proprio48_esn128_action7_v1",
            metadata=json.dumps(metadata),
            seed=np.int64(model["seed"]),
            mean=np.asarray(model["mean"]), std=np.asarray(model["std"]),
            win=np.asarray(model["win"]), w=np.asarray(model["w"]), leak=np.asarray(model["leak"]),
            input_mask=np.asarray(model["input_mask"]), alpha=np.float64(model["alpha"]),
            output_gain=np.float64(model["output_gain"]),
            fmean=np.asarray(model["fmean"]), fstd=np.asarray(model["fstd"]),
            w1=np.asarray(model["w1"]), b1=np.asarray(model["b1"]),
            w2=adapted_w2.T, b2=adapted_b2,
        )
    report = {
        **metadata,
        "checkpoint_sha256": sha(output_checkpoint),
        "base_train": action_stats(base_train_pred, train_targets),
        "adapted_train": action_stats(train_pred, train_targets),
        "base_validation": action_stats(base_val_pred, val_targets),
        "adapted_validation": action_stats(val_pred, val_targets),
        "history": history,
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    lines = [
        "# ESN history adapter (offline development diagnostic)", "",
        "This artifact adapts only the final readout of the frozen 48-D ESN.",
        "It does not run MuJoCo and does not change action projection, safety filtering, or task gates.", "",
        "| split | base action RMSE | adapted action RMSE | base delta RMSE | adapted delta RMSE | adapted x sign flips |", "|---|---:|---:|---:|---:|---:|",
    ]
    for name, base, adapted in (
        ("train", report["base_train"], report["adapted_train"]),
        ("validation", report["base_validation"], report["adapted_validation"]),
    ):
        lines.append(f"| {name} | {base['action_rmse']:.6f} | {adapted['action_rmse']:.6f} | {base['delta_rmse']:.6f} | {adapted['delta_rmse']:.6f} | {adapted['x_sign_flip_fraction']:.4f} |")
    lines += ["", "Interpretation is limited to teacher-action imitation and temporal consistency. The validation rows are not closed-loop task evidence; a separate predeclared physical rollout is required.", "", f"Base checkpoint SHA256: `{report['base_checkpoint_sha256']}`", f"Adapted checkpoint SHA256: `{report['checkpoint_sha256']}`"]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(args.output), "report": report}, indent=2))


if __name__ == "__main__":
    main()
