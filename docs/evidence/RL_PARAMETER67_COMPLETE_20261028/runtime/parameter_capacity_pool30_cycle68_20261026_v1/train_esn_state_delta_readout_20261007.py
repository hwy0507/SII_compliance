#!/usr/bin/env python3
"""Fit a fixed-reservoir ESN readout with an explicit causal state-delta channel.

The reservoir, input map, leak rates, teacher data, identity split and public
48D/action7 interface remain fixed.  Only the final linear readout is fitted.
The extra ``state_delta`` and ``abs(state_delta)`` features expose the causal
transient already present in the reservoir state, allowing a readout to
separate a short collision response from slow recovery without contact truth,
event time, object state or any environment change.
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


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def make_features(data, checkpoint: Path):
    actor = OfficeVMCMemoryESN(checkpoint)
    observations = data["observation"]
    episodes = data["episode"]
    features = []
    deltas = []
    for episode in np.unique(episodes):
        actor.reset()
        previous = actor.state.copy()
        for index in np.flatnonzero(episodes == episode):
            base = actor.features(observations[index])
            delta = actor.state - previous
            previous = actor.state.copy()
            features.append(base)
            deltas.append(delta)
    base = np.asarray(features, dtype=np.float64)
    delta = np.asarray(deltas, dtype=np.float64)
    # ``OfficeVMCMemoryESN.features`` inserts the causal delta immediately
    # after the signed/absolute load+state block and before context products.
    # Keep the offline design matrix in exactly that deployment order.
    prefix, suffix = base[:, :268], base[:, 268:]
    augmented = np.concatenate((prefix, delta, np.abs(delta), suffix), axis=1)
    return augmented


def bounded(raw, readout_activation="tanh"):
    """Match the deployed ESN action decoder exactly."""
    result = (np.clip(raw, -1.0, 1.0) if readout_activation == "clipped_linear"
              else np.tanh(raw))
    result[:, 0] = np.clip(raw[:, 0], 0.0, 1.0)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--parent-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ridge", type=float, nargs="+", default=[0.01, 0.1, 1.0])
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if any(value <= 0 for value in args.ridge):
        raise ValueError("Ridge values must be positive")
    args.output.mkdir(parents=True)
    data = np.load(args.data, allow_pickle=False)
    required = {"observation", "episode", "train", "importance", "requested_teacher_action"}
    if not required.issubset(data.files):
        raise ValueError(f"Missing data fields: {sorted(required - set(data.files))}")
    if sha(args.parent_checkpoint) != "acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7":
        raise ValueError("Parent checkpoint is not the registered readout-refit ESN")
    with np.load(args.parent_checkpoint, allow_pickle=False) as parent:
        readout_activation = str(parent["readout_activation"]) if "readout_activation" in parent.files else "tanh"
    observations = data["observation"]
    episodes = data["episode"]
    train = data["train"].astype(bool)
    target = data["requested_teacher_action"].astype(np.float64)
    importance = data["importance"].astype(np.float64)
    if not np.allclose(importance, 1.0):
        raise ValueError("The registered delta screen requires the unmodified teacher weights")
    if len(np.unique(episodes[train])) != 20 or len(np.unique(episodes[~train])) != 5:
        raise ValueError("Unexpected fixed identity split")
    features = make_features(data, args.parent_checkpoint)
    if features.shape != (len(target), 808):
        raise ValueError(f"Unexpected augmented feature shape: {features.shape}")
    scale = np.maximum(features[train].std(axis=0), 0.005)
    normalized = features / scale
    candidates = []
    selected = None
    selected_weights = None
    for ridge in args.ridge:
        design = normalized[train]
        gram = design.T @ design + float(ridge) * np.eye(design.shape[1])
        rhs = design.T @ target[train]
        coefficients = np.linalg.solve(gram, rhs)
        # Context-only action is forbidden by the deployment contract.  The
        # fixed context may modulate remembered load through the interaction
        # block, but cannot create an action from zero load.
        coefficients[-12:] = 0.0
        prediction = bounded(normalized @ coefficients, readout_activation)
        train_mse = float(np.mean((prediction[train] - target[train]) ** 2))
        validation_mse = float(np.mean((prediction[~train] - target[~train]) ** 2))
        candidate_path = args.output / f"candidate_ridge_{ridge:g}.npz"
        np.savez_compressed(candidate_path, weights=coefficients, feature_scale=scale)
        row = dict(ridge=float(ridge), train_mse=train_mse,
                   validation_mse=validation_mse, checkpoint_sha256=sha(candidate_path))
        candidates.append(row)
        if selected is None or validation_mse < selected["validation_mse"]:
            selected = row
            selected_weights = coefficients
    if selected is None or selected_weights is None:
        raise RuntimeError("No readout candidate")
    with np.load(args.parent_checkpoint, allow_pickle=False) as parent:
        values = {key: parent[key].copy() for key in parent.files if key not in ("weights", "state_delta_readout")}
    # The deployed actor receives raw feature vectors; convert the normalized
    # ridge coefficients back to raw-feature coefficients before export.
    values["weights"] = selected_weights / scale[:, None]
    values["state_delta_readout"] = np.array(True)
    # The expanded weights already contain the delta columns.  Keep the
    # optional deployment residual neutral so the adapter accepts this
    # checkpoint without applying a second correction.
    values["state_delta_weights"] = np.zeros((2 * 128, 7), dtype=np.float64)
    values["state_delta_scale"] = np.ones(2 * 128, dtype=np.float64)
    values["state_delta_output_gain"] = np.array(0.0)
    checkpoint = args.output / "checkpoint.npz"
    np.savez_compressed(checkpoint, **values)
    deployed = OfficeVMCMemoryESN(checkpoint)
    replay = []
    for episode in np.unique(episodes):
        deployed.reset()
        for index in np.flatnonzero(episodes == episode):
            replay.append(deployed.act(observations[index]))
    replay = np.asarray(replay)
    expected = bounded(normalized @ selected_weights, readout_activation)
    parity_error = float(np.max(np.abs(replay - expected)))
    if parity_error > 1e-10:
        raise ValueError(f"Inference parity failure: {parity_error}")
    metadata = dict(
        status="complete",
        contract="VMC_teacher_ESN_state_delta_readout_20261007_v1",
        parent_checkpoint_sha256=sha(args.parent_checkpoint),
        checkpoint_sha256=sha(checkpoint),
        training_data_sha256=sha(args.data),
        source_sha256={str(Path(__file__)): sha(Path(__file__)),
                       str(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py"):
                           sha(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py")},
        reservoir_width=128,
        reservoir_and_input_map_frozen=True,
        trained_parameters=int(selected_weights.size),
        feature_definition="existing context readout features + causal state_delta + abs(state_delta)",
        feature_dimension=int(features.shape[1]),
        candidate_ridges=candidates,
        selected=selected,
        export_parity_max_abs=parity_error,
        actor_contract="canonical48D/action7 pure proprioception",
        forbidden_inputs=["contact truth", "object/ball state", "event time", "task stage", "visual/range"],
        unchanged=["office-v6", "original gate", "actuator amplitude/rate limits", "formal dt=5e-5 reserved"],
        limitation="Offline identity-holdout improvement only; no closed-loop success claim until the frozen development worker evaluates this checkpoint.",
    )
    write(args.output / "TRAINING_COMPLETE.json", metadata)
    write(args.output / "execution.json", dict(status="complete", command=sys.argv,
                                                  checkpoint_sha256=metadata["checkpoint_sha256"],
                                                  training_data_sha256=metadata["training_data_sha256"]))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
