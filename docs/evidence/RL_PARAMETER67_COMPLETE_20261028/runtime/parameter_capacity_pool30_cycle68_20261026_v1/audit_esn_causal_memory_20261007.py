#!/usr/bin/env python3
"""Audit whether a causal reservoir transient helps where memory matters.

This is an offline, pre-registered mechanism audit for the state-delta ESN
experiment.  It compares intact chronological replay with a reset-per-sample
counterfactual on the same identity-held-out sequences and reports the error
in quiet versus transient windows.  No simulator labels or forbidden actor
fields are used; the reset run is diagnostic only and is never a task result.
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
from current_student_policy_20260921 import load_current


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def replay(model: Path, observations: np.ndarray, episodes: np.ndarray,
           reset_each: bool) -> np.ndarray:
    actor = load_current(model)
    outputs = []
    for episode in np.unique(episodes):
        if not reset_each:
            actor.reset()
        for index in np.flatnonzero(episodes == episode):
            if reset_each:
                actor.reset()
            outputs.append(actor.act(observations[index]))
    return np.asarray(outputs, dtype=np.float64)


def mse(prediction: np.ndarray, target: np.ndarray, mask: np.ndarray) -> float:
    if not np.any(mask):
        return float("nan")
    return float(np.mean((prediction[mask] - target[mask]) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--parent", type=Path, required=True)
    ap.add_argument("--rnn", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    data = np.load(args.data, allow_pickle=False)
    observations = data["observation"].astype(np.float64)
    episodes = data["episode"]
    target = data["requested_teacher_action"].astype(np.float64)
    held_out = ~data["train"].astype(bool)
    if len(np.unique(episodes[held_out])) != 5:
        raise ValueError("Expected fixed five identity-held-out episodes")
    results = {}
    for name, model in (("parent_esn", args.parent),
                        ("causal_delta_esn", args.candidate),
                        ("matched_rnn", args.rnn)):
        intact = replay(model, observations, episodes, False)
        reset = replay(model, observations, episodes, True)
        if intact.shape != target.shape or reset.shape != target.shape:
            raise ValueError(f"Unexpected output shape for {name}")
        # The reservoir delta is a causal internal diagnostic.  Its threshold
        # is deliberately derived from the frozen parent state, never labels.
        transient = np.zeros(len(observations), dtype=bool)
        if name != "matched_rnn":
            parent_actor = load_current(args.parent)
            delta_norm = np.zeros(len(observations), dtype=np.float64)
            for episode in np.unique(episodes):
                parent_actor.reset(); previous = parent_actor.state.copy()
                for index in np.flatnonzero(episodes == episode):
                    parent_actor.act(observations[index])
                    delta = parent_actor.state - previous
                    previous = parent_actor.state.copy()
                    delta_norm[index] = np.sqrt(np.mean(delta * delta))
            transient = delta_norm >= np.quantile(delta_norm[held_out], .75)
        else:
            # RNN has no shared ESN state in this audit; use the same public
            # proprioceptive load transition to define an exogenous diagnostic
            # window, without feeding it into the actor.
            load = observations[:, 39:45]
            load_delta = np.linalg.norm(np.diff(load, axis=0, prepend=load[:1]), axis=1)
            transient = load_delta >= np.quantile(load_delta[held_out], .75)
        masks = {
            "held_out": held_out,
            "held_out_transient": held_out & transient,
            "held_out_quiet": held_out & ~transient,
        }
        intact_mse = {k: mse(intact, target, v) for k, v in masks.items()}
        reset_mse = {k: mse(reset, target, v) for k, v in masks.items()}
        results[name] = {
            "model": str(model),
            "model_sha256": sha(model),
            "intact_mse": intact_mse,
            "reset_per_sample_mse": reset_mse,
            "memory_gap": {k: reset_mse[k] - intact_mse[k] for k in masks},
            "held_out_transient_rows": int(masks["held_out_transient"].sum()),
            "held_out_quiet_rows": int(masks["held_out_quiet"].sum()),
        }
    report = {
        "status": "complete",
        "experiment": "causal reservoir state-delta readout memory stress audit",
        "data_sha256": sha(args.data),
        "candidate_sha256": sha(args.candidate),
        "parent_sha256": sha(args.parent),
        "rnn_sha256": sha(args.rnn),
        "identity_split": "25 episodes: 20 train, 5 held-out; held-out-only metrics",
        "actor_contract": "canonical48D/action7 pure proprioception",
        "forbidden_inputs": ["contact truth", "object/ball state", "event time", "task stage", "visual/range"],
        "reset_definition": "reset reservoir at every observation; diagnostic counterfactual only",
        "transient_definition": "top quartile of frozen-parent reservoir delta norm on held-out rows",
        "results": results,
        "limitations": [
            "Offline action replay is not closed-loop task success.",
            "Reset-per-sample is a causal memory ablation, not a baseline controller.",
            "All physical claims require unchanged development and formal workers.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
