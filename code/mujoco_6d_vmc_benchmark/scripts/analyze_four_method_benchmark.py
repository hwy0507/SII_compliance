#!/usr/bin/env python3
"""Summarize a matched four-method benchmark with paired bootstrap CIs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def bootstrap_mean(values: np.ndarray, rng: np.random.Generator, samples: int) -> list[float]:
    if not len(values):
        return [float("nan"), float("nan")]
    means = np.mean(values[rng.integers(0, len(values), size=(samples, len(values)))], axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def exact_paired_sign_test(a: np.ndarray, b: np.ndarray) -> dict:
    # Exact two-sided binomial test on discordant matched success outcomes.
    a_only, b_only = int(np.sum((a == 1) & (b == 0))), int(np.sum((a == 0) & (b == 1)))
    n, k = a_only + b_only, min(a_only, b_only)
    if n == 0:
        p = 1.0
    else:
        p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"method_a_only": a_only, "method_b_only": b_only, "both_success": int(np.sum((a == 1) & (b == 1))),
            "both_fail": int(np.sum((a == 0) & (b == 0))), "two_sided_exact_p": p}


def paired_values(left: list[dict], right: list[dict], key: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    index = lambda rows: {(int(r["seed"]), int(r["fixture_index"])): r for r in rows}
    li, ri = index(left), index(right)
    keys = sorted(li.keys() & ri.keys())
    diffs, seed_ids = [], []
    for pair in keys:
        a, b = li[pair].get(key), ri[pair].get(key)
        if a is not None and b is not None and np.isfinite(float(a)) and np.isfinite(float(b)):
            diffs.append(float(a) - float(b))
            seed_ids.append(pair[0])
    return np.asarray(diffs), np.asarray(seed_ids), np.asarray(keys)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20261599)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    by_method: dict[str, list[dict]] = {}
    for row in data["rows"]:
        by_method.setdefault(row["method"], []).append(row)
    proposed = "esn_proposed_frozen_cem"
    if proposed not in by_method:
        raise SystemExit(f"{args.input}: missing {proposed}")
    rng = np.random.default_rng(args.seed)
    comparisons = {}
    for other in by_method:
        if other == proposed:
            continue
        result = {}
        for metric in ("at_grasp_err_mm", "peak_postimpact_err_mm", "obstacle_force_n", "peak_torque_nm", "contact_bout_count"):
            diff, seeds, _ = paired_values(by_method[proposed], by_method[other], metric)
            seed_means = np.asarray([diff[seeds == seed].mean() for seed in np.unique(seeds)]) if len(diff) else diff
            result[metric] = {"mean_esn_minus_other": float(diff.mean()) if len(diff) else None,
                              "fixture_95ci": bootstrap_mean(diff, rng, args.bootstrap_samples),
                              "seed_95ci": bootstrap_mean(seed_means, rng, args.bootstrap_samples),
                              "count": int(len(diff))}
        # paired_values returns ESN - other; recover binary vectors explicitly for a sign test.
        li = {(r["seed"], r["fixture_index"]): r for r in by_method[proposed]}
        ri = {(r["seed"], r["fixture_index"]): r for r in by_method[other]}
        pairs = sorted(li.keys() & ri.keys())
        result["success_matched"] = exact_paired_sign_test(
            np.asarray([bool(li[p]["task_success"]) for p in pairs], dtype=int),
            np.asarray([bool(ri[p]["task_success"]) for p in pairs], dtype=int))
        comparisons[f"{proposed}_minus_{other}"] = result
    output = {"schema_version": 1, "input": str(args.input), "summary": data["summary"],
              "paired_comparisons": comparisons, "bootstrap_samples": args.bootstrap_samples,
              "bootstrap_seed": args.seed}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
