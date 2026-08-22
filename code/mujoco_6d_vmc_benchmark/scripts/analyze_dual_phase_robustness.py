#!/usr/bin/env python3
"""Paired bootstrap analysis for the robustness evaluator's condition schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


METRICS = {
    "pre_peak_force_n": ("pregrasp", "peak_force_n", "lower"),
    "pre_impulse_ns": ("pregrasp", "contact_impulse_ns", "lower"),
    "post_peak_force_n": ("postgrasp", "peak_force_n", "lower"),
    "post_impulse_ns": ("postgrasp", "contact_impulse_ns", "lower"),
    "peak_jerk_mps3": (None, "peak_jerk_mps3", "lower"),
    "final_target_lift_m": (None, "final_target_lift_m", "higher"),
}


def value(row: dict, path: tuple[str | None, str, str]) -> float:
    group, key, _ = path
    return float(row[key] if group is None else row[group][key])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", default="VMC")
    parser.add_argument("--methods", nargs="+", default=("ESN",))
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20266701)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    keyed: dict[str, dict[tuple[int, str], dict]] = {}
    for row in payload["rows"]:
        condition = row["condition"]
        key = (int(condition["seed"]), str(condition["name"]))
        keyed.setdefault(str(row["method"]), {})[key] = row
    if args.baseline not in keyed:
        raise ValueError(f"missing baseline {args.baseline!r}")
    keys = sorted(keyed[args.baseline])
    rng = np.random.default_rng(args.seed)
    samples = rng.integers(0, len(keys), size=(args.bootstrap, len(keys)))
    comparisons = {}
    for method in args.methods:
        if method not in keyed or set(keyed[method]) != set(keys):
            raise ValueError(f"{method}: conditions do not exactly match baseline")
        physical_pairs = [
            bool(keyed[method][key]["physical_audit_pass"])
            and bool(keyed[args.baseline][key]["physical_audit_pass"])
            for key in keys
        ]
        comparison = {"all_pairs_physical_audit_pass": bool(all(physical_pairs))}
        for name, path in METRICS.items():
            differences = np.asarray([
                value(keyed[method][key], path) - value(keyed[args.baseline][key], path)
                for key in keys
            ])
            boot = differences[samples].mean(axis=1)
            wins = differences < 0.0 if path[2] == "lower" else differences > 0.0
            comparison[name] = {
                "mean_difference_method_minus_baseline": float(np.mean(differences)),
                "paired_bootstrap_95ci": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                "paired_condition_win_rate": float(np.mean(wins)), "direction": path[2],
            }
        ratios = np.asarray([
            np.mean([
                value(keyed[method][key], METRICS[name])
                / max(value(keyed[args.baseline][key], METRICS[name]), .05)
                for name in list(METRICS)[:5]
            ])
            for key in keys
        ])
        boot = ratios[samples].mean(axis=1)
        comparison["five_metric_ratio_to_baseline"] = {
            "mean": float(np.mean(ratios)),
            "paired_bootstrap_95ci": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
            "lower_is_better": True,
        }
        comparisons[method] = comparison
    output = {
        "schema_version": 1, "input": str(args.input), "baseline": args.baseline,
        "paired_condition_count": len(keys), "bootstrap_replicates": args.bootstrap,
        "unit_of_resampling": "matched pre-registered condition/seed", "comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
