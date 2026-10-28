#!/usr/bin/env python3
"""Add a causal reservoir-state-delta residual to a frozen ESN readout.

This is a deliberately conservative ESN experiment: the existing selected
readout is retained, while a small ridge-fitted correction sees only the
current reservoir change and its magnitude.  It tests whether ESN memory is
useful specifically for transient collision/recovery behavior.  No model,
gate, scene or actor input is changed.
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
    values = []
    for episode in np.unique(episodes):
        actor.reset()
        previous = actor.state.copy()
        for index in np.flatnonzero(episodes == episode):
            base = actor.features(observations[index])
            delta = actor.state - previous
            previous = actor.state.copy()
            values.append(np.r_[base[:268], delta, np.abs(delta), base[268:]])
    return np.asarray(values, dtype=np.float64)


def decode_raw(raw, readout_activation="tanh"):
    """Match ``OfficeVMCMemoryESN.act`` exactly for the parent contract."""
    result = (np.clip(raw, -1.0, 1.0) if readout_activation == "clipped_linear"
              else np.tanh(raw))
    # The registered parent uses the non-axis-separable action contract.  Its
    # first action is a positive scale decoded from the preactivation.
    result[:, 0] = np.clip(raw[:, 0], 0.0, 1.0)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--parent-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ridge", type=float, nargs="+", default=[0.01, 0.1, 1.0, 10.0])
    parser.add_argument("--gate-threshold", type=float, default=None,
                        help="Optional RMS normalized state-delta threshold for a causal transient gate")
    parser.add_argument("--output-gain", type=float, default=1.0,
                        help="Fixed multiplier on the causal residual readout")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if any(value <= 0 for value in args.ridge):
        raise ValueError("Ridge values must be positive")
    if not np.isfinite(args.output_gain) or not 0 <= args.output_gain <= 1:
        raise ValueError("Output gain must be in [0, 1]")
    args.output.mkdir(parents=True)
    if sha(args.parent_checkpoint) != "acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7":
        raise ValueError("Parent checkpoint is not the registered readout-refit ESN")
    data = np.load(args.data, allow_pickle=False)
    required = {"observation", "episode", "train", "requested_teacher_action"}
    if not required.issubset(data.files):
        raise ValueError(f"Missing data fields: {sorted(required - set(data.files))}")
    train = data["train"].astype(bool)
    episodes = data["episode"]
    target = data["requested_teacher_action"].astype(np.float64)
    if len(np.unique(episodes[train])) != 20 or len(np.unique(episodes[~train])) != 5:
        raise ValueError("Unexpected fixed identity split")
    features = make_features(data, args.parent_checkpoint)
    if features.shape != (len(target), 808):
        raise ValueError(f"Unexpected feature shape: {features.shape}")
    with np.load(args.parent_checkpoint, allow_pickle=False) as parent:
        parent_weights = parent["weights"].copy()
        readout_activation = str(parent["readout_activation"]) if "readout_activation" in parent.files else "tanh"
    if parent_weights.shape != (552, 7):
        raise ValueError("Unexpected parent readout shape")
    # Parent order is [prefix(268), suffix(284)]; the delta variant inserts
    # [delta(128), abs(delta)(128)] between those blocks.
    expanded_parent = np.zeros((808, 7), dtype=np.float64)
    expanded_parent[:268] = parent_weights[:268]
    expanded_parent[524:] = parent_weights[268:]
    base_raw = features @ expanded_parent
    base_action = decode_raw(base_raw, readout_activation)
    delta = features[:, 268:524]
    scale = np.maximum(delta[train].std(axis=0), 0.005)
    normalized_delta = delta / scale
    if args.gate_threshold is not None:
        if not np.isfinite(args.gate_threshold) or args.gate_threshold <= 0:
            raise ValueError("Gate threshold must be positive")
        delta_norm = np.sqrt(np.mean(normalized_delta[:, :128] ** 2, axis=1))
        gate = np.clip(delta_norm / args.gate_threshold, 0.0, 1.0)
    else:
        gate = np.ones(len(delta), dtype=np.float64)
    residual_target = target - base_action
    candidates = []
    selected = None
    selected_coefficients = None
    design = normalized_delta[train] * gate[train, None]
    for ridge in args.ridge:
        coefficients = np.linalg.solve(
            design.T @ design + float(ridge) * np.eye(design.shape[1]),
            design.T @ residual_target[train],
        )
        correction = (normalized_delta * gate[:, None]) @ coefficients * args.output_gain
        # Residuals are added in the preactivation domain.  Adding them after
        # clipping the parent action would create an offline/deployment
        # mismatch and artificially inflate the apparent improvement.
        prediction = decode_raw(base_raw + correction, readout_activation)
        row = dict(ridge=float(ridge),
                   train_mse=float(np.mean((prediction[train] - target[train]) ** 2)),
                   validation_mse=float(np.mean((prediction[~train] - target[~train]) ** 2)),
                   correction_rms=float(np.sqrt(np.mean(correction ** 2))))
        candidates.append(row)
        if selected is None or row["validation_mse"] < selected["validation_mse"]:
            selected = row
            selected_coefficients = coefficients
    if selected is None or selected_coefficients is None:
        raise RuntimeError("No residual candidate")
    selected_correction = (normalized_delta * gate[:, None]) @ selected_coefficients * args.output_gain
    checkpoint = args.output / "checkpoint.npz"
    with np.load(args.parent_checkpoint, allow_pickle=False) as parent:
        values = {key: parent[key].copy() for key in parent.files
                  if key not in ("weights", "state_delta_readout", "state_delta_weights", "state_delta_scale")}
    values.update(
        weights=expanded_parent,
        state_delta_readout=np.array(True),
        state_delta_weights=selected_coefficients / scale[:, None],
        state_delta_scale=scale,
    )
    if args.gate_threshold is not None:
        values["state_delta_gate_threshold"] = np.array(float(args.gate_threshold))
    values["state_delta_output_gain"] = np.array(float(args.output_gain))
    np.savez_compressed(checkpoint, **values)
    deployed = OfficeVMCMemoryESN(checkpoint)
    # Exact deployment parity is checked on a bounded prefix of each held-out
    # identity.  A full 34k-row actor replay is a separate physical audit and
    # is intentionally not hidden inside fitting (the context readout is
    # comparatively expensive per action).
    replay = []
    expected_rows = []
    parity_indices = []
    for episode in np.unique(episodes[~train]):
        indices = np.flatnonzero(episodes == episode)[:16]
        deployed.reset()
        for index in indices:
            replay.append(deployed.act(data["observation"][index]))
            expected_rows.append(decode_raw(base_raw[index:index + 1] + selected_correction[index:index + 1], readout_activation)[0])
            parity_indices.append(int(index))
    replay = np.asarray(replay)
    expected = np.asarray(expected_rows)
    parity_error = float(np.max(np.abs(replay - expected)))
    # BLAS row-vector accumulation and the actor's scalar step can differ by
    # a few ulps after the 128-unit reservoir update; retain a tight explicit
    # numerical bound while avoiding a false failure from that ordering.
    if parity_error > 1e-6:
        raise ValueError(f"Inference parity failure: {parity_error}")
    metadata = dict(
        status="complete",
        contract="VMC_teacher_ESN_state_delta_residual_20261007_v1",
        parent_checkpoint_sha256=sha(args.parent_checkpoint),
        checkpoint_sha256=sha(checkpoint),
        training_data_sha256=sha(args.data),
        source_sha256={str(Path(__file__)): sha(Path(__file__)),
                       str(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py"):
                           sha(ROOT / "scripts" / "office_vmc_memory_esn_20260927.py")},
        reservoir_width=128,
        reservoir_and_parent_readout_frozen=True,
        trained_parameters=int(selected_coefficients.size),
        feature_definition="frozen parent ESN + causal state_delta and abs(state_delta) residual",
        causal_gate_threshold=(float(args.gate_threshold) if args.gate_threshold is not None else None),
        causal_residual_output_gain=float(args.output_gain),
        feature_dimension=int(features.shape[1]),
        candidate_ridges=candidates,
        selected=selected,
        export_parity_max_abs=parity_error,
        export_parity_rows=len(parity_indices),
        export_parity_scope="first 16 observations of each held-out identity",
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
