"""Matched MLP/ESN action-distillation training on an audited teacher bank.

The MLP and nonlinear ESN share the same episode-balanced sample schedule,
scaled action loss, optimizer, number of updates, and checkpoint-selection
metric.  The linear ESN is fitted separately by weighted ridge regression and
is reported as a classical low-capacity ESN, not as a parameter-matched peer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import torch
from torch import nn

from esn128_action7_20260918 import ESN128Action7
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7


SCENES = ("ball", "push", "corner", "table_corner")


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def trace_path(root: Path, row: dict) -> Path:
    path = Path(row["trace"])
    return path if path.is_absolute() else root / path


def normalization(root: Path) -> tuple[np.ndarray, np.ndarray]:
    candidates = (
        root / "dataset" / "normalization_train_only.npz",
        root / "normalization_train_only.npz",
    )
    path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None:
        raise FileNotFoundError("normalization_train_only.npz")
    with np.load(path, allow_pickle=False) as data:
        return data["mean"].astype(np.float32), data["std"].astype(np.float32)


def load_sequences(root: Path, manifest: dict, input_dim: int) -> tuple[list[dict], list[np.ndarray], list[np.ndarray]]:
    rows = manifest["train"] + manifest["validation"] + manifest["test"]
    observations, actions = [], []
    for row in rows:
        with np.load(trace_path(root, row), allow_pickle=False) as data:
            observation = data["observation"].astype(np.float32)
            action = data["teacher_action"].astype(np.float32)
        if observation.ndim != 2 or observation.shape[1] != input_dim or action.shape != (len(observation), 7):
            raise ValueError(f"Invalid action7 trace: {row['trace']}")
        observations.append(observation)
        actions.append(action)
    return rows, observations, actions


def reservoir_features(observations: list[np.ndarray], actor: ESN128Action7) -> list[np.ndarray]:
    features = []
    for sequence in observations:
        actor.reset()
        features.append(np.stack([actor.features(observation) for observation in sequence]).astype(np.float32))
    return features


def balanced_metric(rows: list[dict], predictions: list[np.ndarray], actions: list[np.ndarray], scale: np.ndarray) -> dict:
    per_scene = {}
    for scene in SCENES:
        episode_raw, episode_scaled = [], []
        for row, prediction, target in zip(rows, predictions, actions):
            if row["scene"] != scene:
                continue
            error = (prediction - target) ** 2
            episode_raw.append(float(error.mean()))
            episode_scaled.append(float((error / (scale ** 2)).mean()))
        if not episode_raw:
            raise ValueError(f"No {scene} episodes in evaluation split")
        per_scene[scene] = {
            "action_mse": float(np.mean(episode_raw)),
            "scaled_mse": float(np.mean(episode_scaled)),
            "episodes": len(episode_raw),
        }
    return {
        "balanced_action_mse": float(np.mean([value["action_mse"] for value in per_scene.values()])),
        "balanced_scaled_mse": float(np.mean([value["scaled_mse"] for value in per_scene.values()])),
        "per_scene": per_scene,
    }


def activate(raw: torch.Tensor) -> torch.Tensor:
    return torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)


def train_gradient_model(args, rows, observations, actions, mean, std, train_n, validation_n):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    actor_class = ESN128Proprio48Action7 if args.input_dim == 48 else ESN128Action7
    actor = actor_class(mean, std, seed=args.seed)
    normalized = [np.clip((sequence - mean) / std, -12, 12).astype(np.float32) for sequence in observations]
    if args.model == "esn_nonlinear":
        raw_features = reservoir_features(observations, actor)
        feature_arrays = [np.concatenate((x, state[:, args.input_dim:]), axis=1) for x, state in zip(normalized, raw_features)]
        model = nn.Sequential(nn.Linear(args.input_dim + 128, 128), nn.Tanh(), nn.Linear(128, 7))
    else:
        feature_arrays = normalized
        model = nn.Sequential(nn.Linear(args.input_dim, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 7))

    clean_train_n = len(args.manifest["train_clean"])
    if args.model == "esn_nonlinear":
        clean_features = np.concatenate(feature_arrays[:clean_train_n])
        feature_mean = clean_features.mean(0).astype(np.float32)
        feature_std = clean_features.std(0).clip(min=.03).astype(np.float32)
        feature_arrays = [(features - feature_mean) / feature_std for features in feature_arrays]
    else:
        # CurrentMLP applies the dataset mean/std directly at deployment.
        # Keep training features identical to that deployed computation.
        feature_mean = np.zeros(args.input_dim, dtype=np.float32)
        feature_std = np.ones(args.input_dim, dtype=np.float32)
    scale = np.concatenate(actions[:clean_train_n]).std(0).clip(min=.03).astype(np.float32)

    lengths = np.asarray([len(features) for features in feature_arrays], dtype=np.int64)
    starts = np.r_[0, np.cumsum(lengths)]
    features = torch.as_tensor(np.concatenate(feature_arrays), device=device)
    targets = torch.as_tensor(np.concatenate(actions), device=device)
    scale_tensor = torch.as_tensor(scale, device=device)
    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)

    scene_episodes = {
        scene: np.asarray([index for index, row in enumerate(rows[:train_n]) if row["scene"] == scene], dtype=np.int64)
        for scene in SCENES
    }
    if any(len(indices) == 0 for indices in scene_episodes.values()):
        raise ValueError("Every scene needs at least one training episode")

    def sample_indices(epoch: int, step: int) -> np.ndarray:
        rng = np.random.default_rng(args.seed * 1_000_003 + epoch * args.steps_per_epoch + step)
        per_scene = args.batch_size // len(SCENES)
        selected = []
        for scene in SCENES:
            episode_ids = rng.choice(scene_episodes[scene], size=per_scene, replace=True)
            offsets = (rng.random(per_scene) * lengths[episode_ids]).astype(np.int64)
            selected.append(starts[episode_ids] + offsets)
        return np.concatenate(selected)

    def predict_split(begin: int, end: int) -> tuple[list[np.ndarray], list[np.ndarray], list[dict]]:
        model.eval(); predictions = []
        with torch.no_grad():
            for index in range(begin, end):
                predictions.append(activate(model(features[starts[index]:starts[index + 1]])).cpu().numpy())
        return predictions, actions[begin:end], rows[begin:end]

    best = float("inf"); best_epoch = 0; best_state = None; history = []; started = time.time()
    for epoch in range(args.epochs):
        model.train(); running = 0.
        for step in range(args.steps_per_epoch):
            indices = torch.as_tensor(sample_indices(epoch, step), device=device)
            optimizer.zero_grad(set_to_none=True)
            prediction = activate(model(features[indices]))
            loss = (((prediction - targets[indices]) / scale_tensor) ** 2).mean()
            loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.); optimizer.step()
            running += float(loss.detach())
        if epoch == 0 or (epoch + 1) % args.evaluate_every == 0:
            prediction, target, selected_rows = predict_split(train_n, train_n + validation_n)
            metric = balanced_metric(selected_rows, prediction, target, scale)
            record = {"epoch": epoch + 1, "loss": running / args.steps_per_epoch,
                      "validation": metric, "elapsed_s": time.time() - started}
            history.append(record); print(json.dumps(record), flush=True)
            if metric["balanced_scaled_mse"] < best:
                best = metric["balanced_scaled_mse"]; best_epoch = epoch + 1
                best_state = {key: value.detach().cpu().numpy().copy() for key, value in model.state_dict().items()}
            dump(args.output / "status.json", {"phase": "training", **record, "best_epoch": best_epoch})

    model.load_state_dict({key: torch.as_tensor(value, device=device) for key, value in best_state.items()})
    validation_prediction, validation_target, validation_rows = predict_split(train_n, train_n + validation_n)
    test_prediction, test_target, test_rows = predict_split(train_n + validation_n, len(rows))
    validation = balanced_metric(validation_rows, validation_prediction, validation_target, scale)
    test = balanced_metric(test_rows, test_prediction, test_target, scale)

    if args.model == "mlp":
        checkpoint = {"contract": "proprio48_action7_mlp_v1" if args.input_dim == 48 else "current_four_scene_action7_mlp_v1", "mean": mean, "std": std,
                      "hidden": np.int64(128), **best_state}
    else:
        actor.head.update(fmean=feature_mean, fstd=feature_std,
                          w1=best_state["0.weight"], b1=best_state["0.bias"],
                          w2=best_state["2.weight"], b2=best_state["2.bias"])
        actor.save(args.output / "best.npz", {
            "training": "matched_action7_v1", "seed": args.seed, "best_epoch": best_epoch,
            "dataset_manifest_sha256": args.dataset_sha,
        })
        checkpoint = None
    if checkpoint is not None:
        with (args.output / "best.npz").open("wb") as stream:
            np.savez_compressed(stream, **checkpoint)
    return {
        "best_epoch": best_epoch, "validation": validation, "test": test,
        "trainable_parameters": sum(parameter.numel() for parameter in model.parameters()),
        "history": history, "elapsed_s": time.time() - started,
    }


def train_linear_esn(args, rows, observations, actions, mean, std, train_n, validation_n):
    actor_class = ESN128Proprio48Action7 if args.input_dim == 48 else ESN128Action7
    actor = actor_class(mean, std, seed=args.seed)
    feature_arrays = reservoir_features(observations, actor)
    clean_train_n = len(args.manifest["train_clean"])
    scale = np.concatenate(actions[:clean_train_n]).std(0).clip(min=.03).astype(np.float64)
    feature_dim=args.input_dim+128+1
    x_tx = np.zeros((feature_dim, feature_dim), dtype=np.float64)
    x_ty = np.zeros((feature_dim, 7), dtype=np.float64)
    scene_counts = {scene: sum(row["scene"] == scene for row in rows[:train_n]) for scene in SCENES}
    for row, features, target in zip(rows[:train_n], feature_arrays[:train_n], actions[:train_n]):
        x = np.c_[features, np.ones(len(features))].astype(np.float64)
        clipped = np.clip(target.astype(np.float64), -0.999, 0.999)
        logits = np.arctanh(clipped)
        logits[:, 0] = np.log(np.clip(target[:, 0], 1e-4, 1 - 1e-4) / np.clip(1 - target[:, 0], 1e-4, 1))
        weight = 1. / (len(SCENES) * scene_counts[row["scene"]] * len(features))
        x_tx += weight * x.T @ x
        x_ty += weight * x.T @ logits

    def infer(weights, begin, end):
        predictions = []
        for features in feature_arrays[begin:end]:
            raw = np.c_[features, np.ones(len(features))] @ weights
            prediction = np.tanh(raw); prediction[:, 0] = 1. / (1. + np.exp(-np.clip(raw[:, 0], -60, 60)))
            predictions.append(prediction.astype(np.float32))
        return predictions

    best = None
    for ridge in args.ridge_grid:
        regularizer = np.eye(feature_dim) * ridge; regularizer[-1, -1] = 0.
        weights = np.linalg.solve(x_tx + regularizer, x_ty)
        predictions = infer(weights, train_n, train_n + validation_n)
        metric = balanced_metric(rows[train_n:train_n + validation_n], predictions,
                                 actions[train_n:train_n + validation_n], scale)
        candidate = (metric["balanced_scaled_mse"], ridge, weights, metric)
        if best is None or candidate[0] < best[0]:
            best = candidate
    _, ridge, weights, validation = best
    test_predictions = infer(weights, train_n + validation_n, len(rows))
    test = balanced_metric(rows[train_n + validation_n:], test_predictions,
                           actions[train_n + validation_n:], scale)
    with (args.output / "best.npz").open("wb") as stream:
        np.savez_compressed(stream, contract="proprio48_linear_esn_action7_v1" if args.input_dim == 48 else "linear_esn_action7_v1", mean=mean, std=std,
                            seed=np.int64(args.seed), win=actor.win, w=actor.w, leak=actor.leak,
                            weights=weights.astype(np.float32), ridge=np.float64(ridge))
    return {"best_ridge": ridge, "validation": validation, "test": test,
            "trainable_parameters": int(weights.size)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", choices=("mlp", "esn_nonlinear", "esn_linear"), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--steps-per-epoch", type=int, default=48)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--evaluate-every", type=int, default=5)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    parser.add_argument("--ridge-grid", type=float, nargs="+", default=(1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.))
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    args.manifest = json.loads((args.dataset / "manifest.json").read_text())
    ready = json.loads((args.dataset / "READY.json").read_text())
    if not ready.get("ready"):
        raise RuntimeError("Dataset is not independently marked READY")
    args.dataset_sha = hashlib.sha256((args.dataset / "manifest.json").read_bytes()).hexdigest()
    mean, std = normalization(args.dataset)
    args.input_dim=int(len(mean))
    if args.input_dim not in (45,48):raise ValueError(f"Unsupported observation dimension {args.input_dim}")
    rows, observations, actions = load_sequences(args.dataset, args.manifest, args.input_dim)
    train_n = len(args.manifest["train"]); validation_n = len(args.manifest["validation"])
    protocol = {
        "model": args.model, "seed": args.seed, "dataset_manifest_sha256": args.dataset_sha,
        "observation_dim": args.input_dim, "action_dim": 7, "reservoir_units": 128 if "esn" in args.model else 0,
        "fairness_group": "mlp_vs_esn_nonlinear_matched_sampler_loss_updates_seed",
        "sampler": "uniform scene, uniform episode, uniform time",
        "loss": "per-action training-std scaled MSE",
        "epochs": args.epochs, "steps_per_epoch": args.steps_per_epoch, "batch_size": args.batch_size,
        "office_used_for_training_or_selection": False,
    }
    dump(args.output / "protocol.json", protocol)
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    if args.model == "esn_linear":
        result = train_linear_esn(args, rows, observations, actions, mean, std, train_n, validation_n)
    else:
        result = train_gradient_model(args, rows, observations, actions, mean, std, train_n, validation_n)
    complete = {**protocol, **result, "complete": True,
                "checkpoint_sha256": hashlib.sha256((args.output / "best.npz").read_bytes()).hexdigest()}
    dump(args.output / "TRAINING_COMPLETE.json", complete)
    dump(args.output / "status.json", {"phase": "complete", **complete})
    print(json.dumps(complete), flush=True)


if __name__ == "__main__":
    main()
