#!/usr/bin/env python3
"""Paired, seed-clustered uncertainty analysis for dual-phase held-out rows."""

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
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20265801)
    parser.add_argument("--baseline", default="VMC")
    parser.add_argument("--methods", nargs="+", default=None,
                        help="methods to compare; default is every non-baseline method")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    rows = payload["rows"]
    keyed: dict[str, dict[tuple[int, float, float], dict]] = {}
    for row in rows:
        key = (int(row["seed"]), float(row["board_y_offset_m"]), float(row["board_z_offset_m"]))
        keyed.setdefault(row["method"], {})[key] = row
    methods = list(keyed)
    if args.baseline not in keyed:
        raise ValueError(f"unknown baseline {args.baseline!r}; choices are {sorted(keyed)}")
    keys = sorted(keyed[args.baseline])
    if any(set(keyed[method]) != set(keys) for method in methods):
        raise ValueError("methods do not have exactly matched held-out conditions")
    seeds = sorted({key[0] for key in keys})
    by_seed = {seed: [key for key in keys if key[0] == seed] for seed in seeds}
    rng = np.random.default_rng(args.seed)
    samples = rng.integers(0, len(seeds), size=(args.bootstrap, len(seeds)))
    analysis = {}
    selected_methods = args.methods or [method for method in methods if method != args.baseline]
    for method in selected_methods:
        if method == args.baseline:
            continue
        if method not in keyed:
            raise ValueError(f"unknown comparison method {method!r}; choices are {sorted(keyed)}")
        comparison = {}
        for metric, path in METRICS.items():
            cluster_differences = []
            paired_differences = []
            wins = []
            for seed in seeds:
                local = []
                for key in by_seed[seed]:
                    candidate = value(keyed[method][key], path)
                    baseline = value(keyed[args.baseline][key], path)
                    difference = candidate - baseline
                    local.append(difference)
                    paired_differences.append(difference)
                    wins.append(candidate < baseline if path[2] == "lower" else candidate > baseline)
                cluster_differences.append(float(np.mean(local)))
            cluster_differences = np.asarray(cluster_differences)
            boot = cluster_differences[samples].mean(axis=1)
            comparison[metric] = {
                "mean_difference_method_minus_baseline": float(np.mean(paired_differences)),
                "cluster_bootstrap_95ci": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                "paired_condition_win_rate": float(np.mean(wins)),
                "direction": path[2],
            }
        # Predeclared five-metric physical score.  Ratios are computed within
        # matched conditions, then clustered by seed like the raw endpoints.
        score_clusters = []
        score_rows = []
        score_metrics = list(METRICS)[:5]
        for seed in seeds:
            local = []
            for key in by_seed[seed]:
                ratios = [
                    value(keyed[method][key], METRICS[name])
                    / max(value(keyed[args.baseline][key], METRICS[name]), .05)
                    for name in score_metrics
                ]
                local.append(float(np.mean(ratios)))
                score_rows.append(local[-1])
            score_clusters.append(float(np.mean(local)))
        score_clusters = np.asarray(score_clusters)
        boot = score_clusters[samples].mean(axis=1)
        comparison["five_metric_ratio_to_baseline"] = {
            "mean": float(np.mean(score_rows)),
            "cluster_bootstrap_95ci": [float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
            "lower_is_better": True,
        }
        analysis[method] = comparison
    output = {
        "schema_version": 1, "input": str(args.input),
        "unit_of_resampling": "seed cluster (all board offsets retained within each sampled seed)",
        "bootstrap_replicates": args.bootstrap, "seed_count": len(seeds),
        "paired_condition_count": len(keys), "baseline": args.baseline,
        f"comparisons_to_{args.baseline.lower()}": analysis,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
