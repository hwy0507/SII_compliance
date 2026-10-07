#!/usr/bin/env python3
"""Train a pure ESN readout with torque-oriented smoothness/robustness terms.

The reservoir and the canonical48D/action7 actor contract remain frozen.  The
extra terms are readout-only: action increment energy and deterministic
proprioceptive-noise consistency.  No contact truth, event time, object state,
task phase or geometry is used by the actor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def bounded(raw: np.ndarray) -> np.ndarray:
    out = np.clip(raw, -1.0, 1.0)
    out[:, 0] = np.clip(raw[:, 0], 0.0, 1.0)
    return out


def features(data: dict[str, np.ndarray], checkpoint: Path, observations: np.ndarray | None = None) -> np.ndarray:
    actor = OfficeVMCMemoryESN(checkpoint)
    obs = data["observation"] if observations is None else observations
    episodes = data["episode"]
    values = []
    for episode in np.unique(episodes):
        actor.reset()
        for index in np.flatnonzero(episodes == episode):
            values.append(actor.features(obs[index]))
    # Keep the design matrix compact; normal equations are accumulated in
    # float64 below.  This also keeps the local single-process memory budget
    # below the project's 3 GiB limit.
    return np.asarray(values, dtype=np.float32)


def differences(x: np.ndarray, episodes: np.ndarray) -> np.ndarray:
    result = np.zeros_like(x)
    for episode in np.unique(episodes):
        idx = np.flatnonzero(episodes == episode)
        if len(idx) > 1:
            result[idx[1:]] = x[idx[1:]] - x[idx[:-1]]
    return result


def noisy_observations(data: dict[str, np.ndarray], seed: int, scale: float) -> np.ndarray:
    rng = np.random.default_rng(seed)
    obs = data["observation"].copy()
    # Noise is used only to make the readout locally robust.  The actor still
    # receives exactly the original 48 proprioceptive fields at deployment.
    field_scale = np.maximum(np.std(obs[data["train"]], axis=0), 0.005)
    obs += rng.normal(size=obs.shape) * field_scale[None, :] * scale
    return obs


def fit_candidate(x: np.ndarray, y: np.ndarray, episodes: np.ndarray, train: np.ndarray,
                  ridge: float, smooth_weight: float, action_weight: float,
                  noise_x: np.ndarray | None, noise_weight: float) -> tuple[np.ndarray, dict]:
    # ``x`` and optional ``noise_x`` are already normalized by the caller.
    xn = x
    x_train = xn[train]
    y_train = y[train].astype(np.float32)
    gram = x_train.T.astype(np.float64) @ x_train.astype(np.float64)
    rhs = x_train.T.astype(np.float64) @ y_train.astype(np.float64)
    if noise_x is not None and noise_weight > 0:
        # ``noise_x`` is normalized by the caller with the clean feature
        # scale.  Dividing again would both reference a non-local variable
        # and over-normalize the perturbation features.
        nx_train = noise_x[train]
        gram += noise_weight * (nx_train.T.astype(np.float64) @ nx_train.astype(np.float64))
        rhs += noise_weight * (nx_train.T.astype(np.float64) @ y_train.astype(np.float64))
    if smooth_weight > 0:
        dx = differences(xn, episodes)[train]
        gram += smooth_weight * (dx.T.astype(np.float64) @ dx.astype(np.float64))
    if action_weight > 0:
        gram += action_weight * (x_train.T.astype(np.float64) @ x_train.astype(np.float64))
    gram += ridge * np.eye(x_train.shape[1])
    coeff = np.linalg.solve(gram, rhs)
    # Context-only action remains prohibited by the actor contract.
    coeff[-12:] = 0.0
    return coeff, {}


def episode_metrics(pred: np.ndarray, target: np.ndarray, episodes: np.ndarray, mask: np.ndarray) -> dict:
    delta = differences(pred, episodes)
    m = mask
    return {
        "mse": float(np.mean((pred[m] - target[m]) ** 2)),
        "delta_energy": float(np.mean(delta[m] ** 2)),
        "action_energy": float(np.mean(pred[m] ** 2)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--parent-checkpoint", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=2026100701)
    ap.add_argument("--noise-scale", type=float, default=0.005)
    ap.add_argument("--noise-weight", type=float, default=0.25)
    ap.add_argument("--ridge", type=float, nargs="+", default=[0.01, 0.1, 1.0])
    ap.add_argument("--smooth-weight", type=float, nargs="+", default=[0.0, 0.01, 0.05, 0.1])
    ap.add_argument("--action-weight", type=float, nargs="+", default=[0.0, 0.001, 0.005])
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    data = {k: v for k, v in np.load(args.data, allow_pickle=False).items()}
    required = {"observation", "episode", "train", "requested_teacher_action"}
    if not required.issubset(data):
        raise ValueError(f"missing fields: {sorted(required - set(data))}")
    if len(np.unique(data["episode"][data["train"]])) != 20 or len(np.unique(data["episode"][~data["train"]])) != 5:
        raise ValueError("expected frozen 20/5 identity split")
    args.output.mkdir(parents=True)
    x = features(data, args.parent_checkpoint)
    y = data["requested_teacher_action"].astype(np.float64)
    episodes = data["episode"]
    train = data["train"].astype(bool)
    feature_scale = np.maximum(x[train].std(axis=0), 0.005).astype(np.float32)
    x /= feature_scale
    noise_x = None
    if args.noise_scale > 0 and args.noise_weight > 0:
        noise_x = features(data, args.parent_checkpoint, noisy_observations(data, args.seed, args.noise_scale))
        noise_x /= feature_scale
    candidates = []
    selected = None
    for smooth in args.smooth_weight:
        for action in args.action_weight:
            for ridge in args.ridge:
                coeff, info = fit_candidate(x, y, episodes, train, ridge, smooth, action, noise_x, args.noise_weight)
                prediction = bounded(x @ coeff)
                val = episode_metrics(prediction, y, episodes, ~train)
                # Fixed validation objective: preserve requested action while
                # penalizing high-frequency readout changes and large action.
                score = val["mse"] + 0.25 * val["delta_energy"] + 0.05 * val["action_energy"]
                row = dict(ridge=float(ridge), smooth_weight=float(smooth), action_weight=float(action),
                           noise_scale=float(args.noise_scale), noise_weight=float(args.noise_weight),
                           train=episode_metrics(prediction, y, episodes, train), validation=val,
                           validation_score=float(score))
                candidates.append(row)
                if selected is None or score < selected["validation_score"]:
                    selected = row | {"coeff": coeff, "feature_scale": feature_scale}
    if selected is None:
        raise RuntimeError("no candidate")
    values = {}
    with np.load(args.parent_checkpoint, allow_pickle=False) as parent:
        values = {key: parent[key].copy() for key in parent.files if key != "weights"}
    values["weights"] = selected["coeff"] / selected["feature_scale"][:, None]
    checkpoint = args.output / "checkpoint.npz"
    np.savez_compressed(checkpoint, **values)
    deployed = OfficeVMCMemoryESN(checkpoint)
    replay = []
    for episode in np.unique(episodes):
        deployed.reset()
        for index in np.flatnonzero(episodes == episode):
            replay.append(deployed.act(data["observation"][index]))
    replay = np.asarray(replay)
    expected = bounded(x @ selected["coeff"])
    parity = float(np.max(np.abs(replay - expected)))
    # The checkpoint stores weights as float32 and the deployment actor also
    # evaluates float32 features.  A sub-micro-unit discrepancy is expected
    # after serialization; reject only a materially different replay.
    if parity > 2e-5:
        raise ValueError(f"deployment parity failure: {parity}")
    serial = {k: v for k, v in selected.items() if k not in ("coeff", "feature_scale")}
    serial["checkpoint_sha256"] = sha(checkpoint)
    meta = {
        "status": "complete",
        "contract": "VMC_teacher_ESN_torque_generalization_readout_20261007_v1",
        "parent_checkpoint_sha256": sha(args.parent_checkpoint),
        "training_data_sha256": sha(args.data),
        "checkpoint_sha256": sha(checkpoint),
        "source_sha256": {str(Path(__file__)): sha(Path(__file__)),
                          str(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py"): sha(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py")},
        "reservoir_frozen": True,
        "identity_split": {"train": 20, "validation": 5},
        "actor_contract": "canonical48D/action7 pure proprioception",
        "forbidden_inputs": ["contact truth", "object/ball state", "event time", "task stage", "visual/range"],
        "selected": serial,
        "candidate_count": len(candidates),
        "candidates": [{k: v for k, v in c.items()} for c in candidates],
        "export_parity_max_abs": parity,
        "unchanged": ["office-v6", "original gate", "actuator amplitude/rate limits", "formal dt=5e-5 reserved"],
        "selection_note": "Validation-only objective; no final heldout outcome was used.",
    }
    (args.output / "TRAINING_COMPLETE.json").write_text(json.dumps(meta, indent=2) + "\n")
    (args.output / "execution.json").write_text(json.dumps({"status": "complete", "command": sys.argv,
                                                               "checkpoint_sha256": meta["checkpoint_sha256"],
                                                               "training_data_sha256": meta["training_data_sha256"]}, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
