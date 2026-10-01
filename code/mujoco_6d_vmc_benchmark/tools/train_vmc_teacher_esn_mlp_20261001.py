#!/usr/bin/env python3
"""Train width-matched pure ESN and MLP readouts on the locked VMC bank.

Only canonical48D observations and the saved filtered teacher action7 are used.
This script never opens the simulator and never reads stage/contact/object
fields.  Two fixture identities are held out for replay evaluation; the lone
long-push fixture remains train-only and is reported as such.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys_path = str(ROOT / "scripts")
import sys
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_rows(manifest: Path, root: Path):
    data = json.loads(manifest.read_text())
    rows = []
    for category, entries in data["categories"].items():
        for entry in entries:
            # Only the nine certified identities are used.  Validation and
            # excluded/quarantined records are absent from categories.
            relative = Path(entry["folder"]) / "rollout.npz"
            path = root / relative
            if not path.is_file():
                raise FileNotFoundError(path)
            with np.load(path, allow_pickle=False) as archive:
                observation = np.asarray(archive["observation"], dtype=np.float32)
                action = np.asarray(archive["applied_action"], dtype=np.float32)
            if observation.ndim != 2 or observation.shape[1] != 48 or action.shape != (len(observation), 7):
                raise ValueError(f"invalid canonical trace {path}")
            rows.append({"category": category, "fixture_id": entry["fixture_id"],
                         "folder": entry["folder"], "path": str(path),
                         "trace_sha256": sha(path), "observation": observation,
                         "action": action, "model_sha256": entry["model_sha256"]})
    return rows, data


def split_rows(rows):
    # Frozen identity split: two held-out fixtures, one per category. The
    # sustained-push class has only one certified identity and is train-only.
    # The strict manifest contains passive_corner_0002 and active_short_0001
    # as the two collection identities reserved for replay; the short_0002
    # record failed the frozen rebound gate and is intentionally absent.
    validation_ids = {"passive_corner_train_0002", "active_short_train_0001"}
    train = [r for r in rows if r["fixture_id"] not in validation_ids]
    validation = [r for r in rows if r["fixture_id"] in validation_ids]
    if {r["category"] for r in train} != {"passive_corner", "active_short", "active_long"}:
        raise ValueError("train split lost a category")
    return train, validation


def fit_esn(train, validation, seed):
    all_obs = np.concatenate([r["observation"] for r in train], axis=0)
    mean = all_obs.mean(0).astype(np.float32)
    std = all_obs.std(0).clip(min=.03).astype(np.float32)
    actor = ESN128Proprio48Action7(mean, std, seed=seed)

    def features(rows):
        output = []
        for row in rows:
            actor.reset()
            output.append(np.stack([actor.features(x) for x in row["observation"]]).astype(np.float32))
        return output

    train_features = features(train)
    validation_features = features(validation)
    packed = np.concatenate(train_features)
    fmean = packed.mean(0).astype(np.float32)
    fstd = packed.std(0).clip(min=.03).astype(np.float32)
    x = np.concatenate([(v - fmean) / fstd for v in train_features]).astype(np.float32)
    y = np.concatenate([r["action"] for r in train]).astype(np.float32)
    xv = np.concatenate([(v - fmean) / fstd for v in validation_features]).astype(np.float32)
    yv = np.concatenate([r["action"] for r in validation]).astype(np.float32)

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    model = nn.Sequential(nn.Linear(176, 128), nn.Tanh(), nn.Linear(128, 7))
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    tx, ty, vx, vy = map(torch.from_numpy, (x, y, xv, yv))
    rng = np.random.default_rng(seed)
    best = float("inf")
    best_state = None
    history = []
    for epoch in range(120):
        order = rng.permutation(len(tx))
        losses = []
        for start in range(0, len(order), 2048):
            index = torch.from_numpy(order[start:start + 2048])
            raw = model(tx[index])
            pred = torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)
            loss = ((pred - ty[index]) ** 2).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.)
            optimizer.step()
            losses.append(float(loss.detach()))
        if epoch == 0 or (epoch + 1) % 10 == 0:
            with torch.no_grad():
                raw = model(vx)
                pred = torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)
                val = float(((pred - vy) ** 2).mean())
            history.append({"epoch": epoch + 1, "train_mse": float(np.mean(losses)), "validation_mse": val})
            if val < best:
                best = val
                best_state = {key: value.detach().numpy().copy() for key, value in model.state_dict().items()}
    assert best_state is not None
    checkpoint = dict(contract="proprio48_esn128_action7_v1", seed=np.int64(seed),
                      mean=mean, std=std, win=actor.win, w=actor.w, leak=actor.leak,
                      input_mask=actor.input_mask, alpha=np.float64(1.), output_gain=np.float64(1.),
                      fmean=fmean, fstd=fstd, w1=best_state["0.weight"], b1=best_state["0.bias"],
                      w2=best_state["2.weight"], b2=best_state["2.bias"])
    return checkpoint, history, best


def fit_mlp(train, validation, seed):
    all_obs = np.concatenate([r["observation"] for r in train], axis=0)
    mean = all_obs.mean(0).astype(np.float32)
    std = all_obs.std(0).clip(min=.03).astype(np.float32)
    x = np.concatenate([(r["observation"] - mean) / std for r in train]).astype(np.float32)
    y = np.concatenate([r["action"] for r in train]).astype(np.float32)
    xv = np.concatenate([(r["observation"] - mean) / std for r in validation]).astype(np.float32)
    yv = np.concatenate([r["action"] for r in validation]).astype(np.float32)
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    model = nn.Sequential(nn.Linear(48, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 7))
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    tx, ty, vx, vy = map(torch.from_numpy, (x, y, xv, yv))
    rng = np.random.default_rng(seed)
    best = float("inf")
    best_state = None
    history = []
    for epoch in range(120):
        order = rng.permutation(len(tx))
        losses = []
        for start in range(0, len(order), 2048):
            index = torch.from_numpy(order[start:start + 2048])
            raw = model(tx[index])
            pred = torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)
            loss = ((pred - ty[index]) ** 2).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.)
            optimizer.step()
            losses.append(float(loss.detach()))
        if epoch == 0 or (epoch + 1) % 10 == 0:
            with torch.no_grad():
                raw = model(vx)
                pred = torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)
                val = float(((pred - vy) ** 2).mean())
            history.append({"epoch": epoch + 1, "train_mse": float(np.mean(losses)), "validation_mse": val})
            if val < best:
                best = val
                best_state = {key: value.detach().numpy().copy() for key, value in model.state_dict().items()}
    assert best_state is not None
    checkpoint = dict(contract="proprio48_action7_mlp_v1", seed=np.int64(seed),
                      mean=mean, std=std, hidden=np.int64(128),
                      **{"0.weight": best_state["0.weight"], "0.bias": best_state["0.bias"],
                         "2.weight": best_state["2.weight"], "2.bias": best_state["2.bias"],
                         "4.weight": best_state["4.weight"], "4.bias": best_state["4.bias"]})
    return checkpoint, history, best


def replay(model, rows, kind):
    if kind == "esn":
        from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
        actor = ESN128Proprio48Action7.load(model)
    else:
        from current_student_policy_20260921 import load_current
        actor = load_current(model).obj if hasattr(load_current(model), "obj") else load_current(model)
    values = []
    for row in rows:
        if hasattr(actor, "reset"): actor.reset()
        prediction = np.stack([actor.act(obs) for obs in row["observation"]]).astype(np.float32)
        target = row["action"]
        contact = np.linalg.norm(row["observation"][:, 39:45], axis=1) > .02
        values.append({"fixture_id": row["fixture_id"], "category": row["category"],
                       "action_mse": float(np.mean((prediction - target) ** 2)),
                       "contact_action_mse": float(np.mean((prediction[contact] - target[contact]) ** 2)) if np.any(contact) else None,
                       "free_action_mse": float(np.mean((prediction[~contact] - target[~contact]) ** 2)) if np.any(~contact) else None,
                       "steps": len(target)})
    return values


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=2026100101)
    args = ap.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    train_rows, manifest = load_rows(args.manifest, args.root)
    train, validation = split_rows(train_rows)
    if len(train) < 6 or len(validation) != 2: raise ValueError("unexpected frozen split")
    esn, esn_history, esn_val = fit_esn(train, validation, args.seed)
    mlp, mlp_history, mlp_val = fit_mlp(train, validation, args.seed + 1)
    esn_path = args.output / "esn_best.npz"; mlp_path = args.output / "mlp_best.npz"
    np.savez_compressed(esn_path, **esn); np.savez_compressed(mlp_path, **mlp)
    esn_rows = replay(esn_path, validation, "esn")
    mlp_rows = replay(mlp_path, validation, "mlp")
    metadata = {
        "contract": "VMC_teacher_matched_ESN_MLP_20261001_v1", "seed": args.seed,
        "manifest": str(args.manifest), "manifest_sha256": sha(args.manifest),
        "train_fixture_ids": [r["fixture_id"] for r in train],
        "validation_fixture_ids": [r["fixture_id"] for r in validation],
        "teacher_trace_hashes": {r["fixture_id"]: r["trace_sha256"] for r in train_rows},
        "source_sha256": {str(Path(__file__)): sha(Path(__file__))},
        "forbidden_inputs": ["contact truth", "object/ball state", "event time", "task stage", "visual/range"],
        "esn_architecture": "48D -> 128 reservoir -> 128 readout -> 7D",
        "mlp_architecture": "48D -> 128 -> 128 -> 7D",
        "parameter_count_fairness": "Both trainable readouts have 23,687 parameters; ESN reservoir is fixed.",
        "esn_validation_mse": esn_val, "mlp_validation_mse": mlp_val,
        "esn_replay": esn_rows, "mlp_replay": mlp_rows,
        "checkpoint_sha256": {"esn": sha(esn_path), "mlp": sha(mlp_path)},
        "limitations": ["Only nine certified VMC fixtures existed; active_long has no held-out identity.",
                        "Replay metrics are teacher-action imitation, not closed-loop task success.",
                        "All source traces are development dt=1e-4 and retain their original gates."],
    }
    (args.output / "TRAINING_COMPLETE.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    (args.output / "training_history.json").write_text(json.dumps({"esn": esn_history, "mlp": mlp_history}, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__": main()
