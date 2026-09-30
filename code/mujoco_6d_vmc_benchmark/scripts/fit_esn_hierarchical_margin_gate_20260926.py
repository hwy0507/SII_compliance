"""Fit a margin selector above an already frozen two-expert ESN policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fit_esn_gated_readout_20260926 import sigmoid
from fit_esn_history_adapter_20260925 import hidden_from_head, load_model, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation


SHARED = ("mean", "std", "win", "w", "leak", "input_mask", "alpha",
          "output_gain", "fmean", "fstd", "w1", "b1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-gated", type=Path, required=True)
    parser.add_argument("--margin-expert", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--margin-rollout", type=Path, nargs="*", default=[])
    parser.add_argument("--all-rollouts-positive", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hidden", type=int, default=16)
    parser.add_argument("--steps", type=int, default=6000)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--gate-offset", type=float, default=0.0)
    parser.add_argument("--positive-stage-min", type=int, default=3)
    parser.add_argument("--positive-stage-max", type=int)
    parser.add_argument("--hard-negative-stage", type=int)
    parser.add_argument("--seed", type=int, default=20260926)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if (args.hidden < 2 or args.steps < 1 or args.learning_rate <= 0 or args.l2 <= 0
            or args.positive_stage_min < 0
            or (args.positive_stage_max is not None and args.positive_stage_max < args.positive_stage_min)
            or (args.hard_negative_stage is not None and args.hard_negative_stage < 0)):
        raise ValueError("invalid training parameters")
    all_paths = {path.resolve() for path in args.rollout}
    positive_paths = ({path.resolve() for path in args.rollout} if args.all_rollouts_positive
                      else {path.resolve() for path in args.margin_rollout})
    if not positive_paths <= all_paths:
        raise ValueError("margin rollouts must be a subset")
    args.output.mkdir(parents=True)

    with np.load(args.base_gated, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_gated_mlp_v1":
            raise ValueError("base must use the R15 gated MLP contract")
        base = {key: source[key].copy() for key in source.files}
    margin = load_model(args.margin_expert)
    for key in SHARED:
        if not np.array_equal(np.asarray(base[key]), np.asarray(margin[key])):
            raise ValueError(f"base and margin expert differ at {key}")

    hidden_rows = []
    labels = []
    stage_rows = []
    for path in args.rollout:
        with np.load(path, allow_pickle=False) as data:
            observation = data["observation"].astype(np.float64)
            stage = data["stage"].astype(np.int64)
        features = features_from_observation(margin, observation)
        normalized = (features - np.asarray(base["fmean"])) / np.asarray(base["fstd"])
        hidden_rows.append(hidden_from_head(normalized, np.asarray(base["w1"]), np.asarray(base["b1"])))
        positive_stage = stage >= args.positive_stage_min
        if args.positive_stage_max is not None:
            positive_stage &= stage <= args.positive_stage_max
        labels.append((positive_stage & (path.resolve() in positive_paths)).astype(np.float64))
        stage_rows.append(stage)
    x = np.concatenate(hidden_rows)
    target = np.concatenate(labels)
    all_stage = np.concatenate(stage_rows)
    positive = target > 0.5
    npos = float(np.sum(positive))
    nneg = float(len(target) - npos)
    if npos == 0 or nneg == 0:
        raise ValueError("selector needs both classes")
    hard_negative = np.zeros(len(target), dtype=bool)
    if args.hard_negative_stage is None:
        sample_weight = np.where(positive, 0.5 / npos, 0.5 / nneg) * len(target)
    else:
        hard_negative = (~positive) & (all_stage == args.hard_negative_stage)
        other_negative = (~positive) & (~hard_negative)
        nhard = float(np.sum(hard_negative))
        nother = float(np.sum(other_negative))
        if nhard == 0 or nother == 0:
            raise ValueError("hard-negative weighting needs nonempty hard and other groups")
        sample_weight = np.where(
            positive, (1.0 / 3.0) / npos,
            np.where(hard_negative, (1.0 / 3.0) / nhard, (1.0 / 3.0) / nother),
        ) * len(target)

    rng = np.random.default_rng(args.seed)
    params = [rng.normal(0, 0.05, (args.hidden, x.shape[1])), np.zeros(args.hidden),
              rng.normal(0, 0.05, args.hidden), np.array(0.0)]
    moments = [np.zeros_like(value) for value in params]
    variances = [np.zeros_like(value) for value in params]
    beta1, beta2 = 0.9, 0.999
    history = []
    for step in range(1, args.steps + 1):
        w1, b1, w2, b2 = params
        hidden = np.tanh(x @ w1.T + b1)
        logit = hidden @ w2 + b2
        probability = sigmoid(logit)
        delta = sample_weight * (probability - target) / len(target)
        back = delta[:, None] * w2 * (1.0 - hidden * hidden)
        gradients = [back.T @ x + args.l2 * w1, np.sum(back, axis=0),
                     hidden.T @ delta + args.l2 * w2, np.array(np.sum(delta))]
        for index, gradient in enumerate(gradients):
            moments[index] = beta1 * moments[index] + (1.0 - beta1) * gradient
            variances[index] = beta2 * variances[index] + (1.0 - beta2) * gradient * gradient
            params[index] -= args.learning_rate * (moments[index] / (1.0 - beta1 ** step)) / (
                np.sqrt(variances[index] / (1.0 - beta2 ** step)) + 1.0e-8)
        if step == 1 or step % 500 == 0 or step == args.steps:
            loss = np.sum(sample_weight * (np.logaddexp(0.0, logit) - target * logit)) / len(target)
            loss += 0.5 * args.l2 * (np.sum(w1 * w1) + np.sum(w2 * w2))
            history.append({"step": step, "loss": float(loss)})

    selector_w1, selector_b1, selector_w2, selector_b2 = params
    selector_b2 = np.array(float(selector_b2 + args.gate_offset))
    probability = sigmoid(np.tanh(x @ selector_w1.T + selector_b1) @ selector_w2 + selector_b2)
    prediction = probability >= 0.5
    metrics = {
        "positive_samples": int(npos),
        "negative_samples": int(nneg),
        "positive_probability_mean": float(np.mean(probability[positive])),
        "positive_probability_p05": float(np.quantile(probability[positive], 0.05)),
        "negative_probability_mean": float(np.mean(probability[~positive])),
        "negative_probability_p95": float(np.quantile(probability[~positive], 0.95)),
        "true_positive_rate": float(np.mean(prediction[positive])),
        "false_positive_rate": float(np.mean(prediction[~positive])),
    }
    if args.hard_negative_stage is not None:
        metrics["hard_negative_samples"] = int(np.sum(hard_negative))
        metrics["hard_negative_false_positive_rate"] = float(np.mean(prediction[hard_negative]))
        metrics["hard_negative_probability_p95"] = float(np.quantile(probability[hard_negative], 0.95))
    metadata = {
        "method": "hierarchical_reservoir_state_margin_selector",
        "base_gated_sha256": sha(args.base_gated),
        "margin_expert_sha256": sha(args.margin_expert),
        "rollout_sha256": [sha(path) for path in args.rollout],
        "margin_rollout_sha256": [sha(path) for path in args.margin_rollout],
        "all_rollouts_positive": args.all_rollouts_positive,
        "hidden": args.hidden,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "l2": args.l2,
        "gate_offset": args.gate_offset,
        "positive_stage_min": args.positive_stage_min,
        "positive_stage_max": args.positive_stage_max,
        "hard_negative_stage": args.hard_negative_stage,
        "seed": args.seed,
        "gate_metrics": metrics,
        "history": history,
        "deployment_inputs": "unchanged proprio48; both gates read only reservoir-derived hidden state",
        "frozen_components": ["R15 base experts and gate", "margin expert", "48D normalization",
                              "heterogeneous-leak reservoir", "first readout layer", "action projection",
                              "safety filter", "task and penetration gates"],
    }
    checkpoint = args.output / "hierarchical_margin.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(
            stream, contract="proprio48_esn128_action7_hierarchical_margin_v1",
            metadata=json.dumps(metadata), seed=np.int64(margin["seed"]),
            **{key: np.asarray(margin[key]) for key in SHARED},
            base_yield_w2=np.asarray(base["yield_w2"]), base_yield_b2=np.asarray(base["yield_b2"]),
            base_clearance_w2=np.asarray(base["clearance_w2"]), base_clearance_b2=np.asarray(base["clearance_b2"]),
            base_gate_w1=np.asarray(base["gate_w1"]), base_gate_b1=np.asarray(base["gate_b1"]),
            base_gate_w2=np.asarray(base["gate_w2"]), base_gate_b2=np.asarray(base["gate_b2"]),
            margin_w2=np.asarray(margin["w2"]), margin_b2=np.asarray(margin["b2"]),
            selector_w1=selector_w1, selector_b1=selector_b1,
            selector_w2=selector_w2, selector_b2=selector_b2,
        )
    report = {**metadata, "checkpoint_sha256": sha(checkpoint)}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
