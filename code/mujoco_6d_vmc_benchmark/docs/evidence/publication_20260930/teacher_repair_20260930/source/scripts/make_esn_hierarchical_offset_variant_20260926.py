"""Calibrate a frozen hierarchical ESN selector offset and recompute metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fit_esn_gated_readout_20260926 import sigmoid
from fit_esn_history_adapter_20260925 import hidden_from_head, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--margin-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--selector-offset", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not np.isfinite(args.selector_offset) or not -3.0 <= args.selector_offset <= 0.0:
        raise ValueError("selector offset must be finite and in [-3, 0]")
    all_paths = {path.resolve() for path in args.rollout}
    positive_paths = {path.resolve() for path in args.margin_rollout}
    if not positive_paths <= all_paths:
        raise ValueError("margin rollouts must be a subset")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_hierarchical_margin_v1":
            raise ValueError("unsupported base contract")
        payload = {key: source[key].copy() for key in source.files if key != "metadata"}
        prior_metadata = json.loads(str(source["metadata"]))
    if float(prior_metadata["gate_offset"]) != 0.0:
        raise ValueError("calibration base must be the zero-offset checkpoint")

    positive_stage_min = int(prior_metadata.get("positive_stage_min", 3))
    hidden_rows = []
    labels = []
    for path in args.rollout:
        with np.load(path, allow_pickle=False) as data:
            observation = data["observation"].astype(np.float64)
            stage = data["stage"].astype(np.int64)
        features = features_from_observation(payload, observation)
        normalized = (features - payload["fmean"]) / payload["fstd"]
        hidden_rows.append(hidden_from_head(normalized, payload["w1"], payload["b1"]))
        labels.append(((stage >= positive_stage_min) & (path.resolve() in positive_paths)).astype(np.float64))
    hidden = np.concatenate(hidden_rows)
    target = np.concatenate(labels)
    positive = target > 0.5
    selector_b2 = np.array(float(payload["selector_b2"] + args.selector_offset))
    probability = sigmoid(
        np.tanh(hidden @ payload["selector_w1"].T + payload["selector_b1"])
        @ payload["selector_w2"] + selector_b2
    )
    prediction = probability >= 0.5
    metrics = {
        "positive_samples": int(np.sum(positive)),
        "negative_samples": int(np.sum(~positive)),
        "positive_probability_mean": float(np.mean(probability[positive])),
        "positive_probability_p05": float(np.quantile(probability[positive], 0.05)),
        "negative_probability_mean": float(np.mean(probability[~positive])),
        "negative_probability_p95": float(np.quantile(probability[~positive], 0.95)),
        "true_positive_rate": float(np.mean(prediction[positive])),
        "false_positive_rate": float(np.mean(prediction[~positive])),
    }
    payload["selector_b2"] = selector_b2
    metadata = {
        "method": "frozen_hierarchical_selector_offset_calibration",
        "base_sha256": sha(args.base),
        "selector_offset_from_zero": args.selector_offset,
        "positive_stage_min": positive_stage_min,
        "rollout_sha256": [sha(path) for path in args.rollout],
        "margin_rollout_sha256": [sha(path) for path in args.margin_rollout],
        "gate_metrics": metrics,
        "deployment_inputs": "unchanged proprio48; both gates read only reservoir-derived hidden state",
        "frozen_components": ["all R17 weights", "R15 base policy", "margin expert", "reservoir",
                              "normalization", "action projection", "safety filter",
                              "task and penetration gates"],
    }
    payload["metadata"] = json.dumps(metadata)
    checkpoint = args.output / "hierarchical_margin.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, **payload)
    report = {**metadata, "checkpoint_sha256": sha(checkpoint)}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
