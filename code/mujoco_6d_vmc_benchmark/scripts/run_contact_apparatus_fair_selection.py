#!/usr/bin/env python3
"""Fair validation-only ESN/VMC selection under physical apparatus variation.

Each rollout uses a finite-mass rod with sampled slide damping, servo gain and
force limit, and MuJoCo contact softness.  Those physics values are written to
the result manifest but remain outside both controllers' observations.  The
configuration rule is fixed before held-out test evaluation: maximize task
success, then minimize at-grasp error.  No candidate may be changed after the
test result is produced.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from record_contact_apparatus_traces import train_fixture  # noqa: E402
from run_benchmark import TORQUE_LIMITS  # noqa: E402
from run_paper_mpc_benchmark import run_rollout  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402


def parse_int_list(value: str) -> list[int]:
    values = list(dict.fromkeys(int(item.strip()) for item in value.split(",") if item.strip()))
    if not values:
        raise argparse.ArgumentTypeError("list cannot be empty")
    return values


def parse_float_list(value: str) -> list[float]:
    values = list(dict.fromkeys(float(item.strip()) for item in value.split(",") if item.strip()))
    if not values or any(not np.isfinite(item) or item <= 0.0 for item in values):
        raise argparse.ArgumentTypeError("list must contain positive finite values")
    return values


def fixtures_for_seed(seed: int, count: int) -> list:
    # Physical fixture draws are deterministic and manifest-recordable.  They
    # differ from the train generator seeds, and validation/test seed ranges
    # are disjoint by construction.
    return [train_fixture(np.random.default_rng(np.uint64(seed) * 1009 + index + 1)) for index in range(count)]


def aggregate(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "mean_contact_bout_count": float(np.mean([int(row["contact_bout_count"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
    }


def score(summary: dict) -> tuple[float, float]:
    return (summary["success_rate"], -summary["mean_at_grasp_err_mm"])


def evaluate_esn(menagerie: Path, model_path: Path, budget: float, seeds: list[int],
                 fixture_count: int, label: str) -> list[dict]:
    controller = load_controller(model_path)
    rows = []
    for seed in seeds:
        for index, fixture in enumerate(fixtures_for_seed(seed, fixture_count)):
            row = run_rollout(menagerie, fixture, impactor_kind="apparatus_rod", controller=controller,
                              residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{index}")
            row["fixture_index"] = index
            rows.append(row)
    return rows


def evaluate_vmc(menagerie: Path, k: float, budget: float, seeds: list[int],
                 fixture_count: int, label: str) -> list[dict]:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    config = replace(base, k_translation_base=k,
                     k_rotation_base=base.k_rotation_base * k / base.k_translation_base)
    rows = []
    for seed in seeds:
        for index, fixture in enumerate(fixtures_for_seed(seed, fixture_count)):
            controller = VMCTorqueBaseline(config, TORQUE_LIMITS * budget)
            row = run_rollout(menagerie, fixture, impactor_kind="apparatus_rod", controller=controller,
                              residual_scale=budget, seed=seed, verbose_name=f"{label}/fx{index}")
            row["fixture_index"] = index
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn-101", type=Path, required=True)
    parser.add_argument("--esn-202", type=Path, required=True)
    parser.add_argument("--esn-303", type=Path, required=True)
    parser.add_argument("--validation-seeds", type=parse_int_list, default=[20260921, 20260922, 20260923, 20260924, 20260925])
    parser.add_argument("--test-seeds", type=parse_int_list, default=[20260926, 20260927, 20260928, 20260929, 20260930])
    parser.add_argument("--fixture-count", type=int, default=4)
    parser.add_argument("--budgets", type=parse_float_list, default=[0.02, 0.03, 0.05])
    parser.add_argument("--vmc-k-values", type=parse_float_list, default=[1.0, 1.5, 2.2, 3.2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.fixture_count < 1 or set(args.validation_seeds) & set(args.test_seeds):
        raise SystemExit("fixture-count must be positive and validation/test seeds must be disjoint")

    esn_paths = {"esn101": args.esn_101, "esn202": args.esn_202, "esn303": args.esn_303}
    candidates = []
    elapsed = time.time()
    for name, path in esn_paths.items():
        for budget in args.budgets:
            rows = evaluate_esn(args.menagerie, path, budget, args.validation_seeds, args.fixture_count, f"{name}_b{budget:g}")
            summary = aggregate(rows)
            candidates.append({"family": "esn", "model": name, "budget": budget, "summary": summary})
            print(f"[{time.time()-elapsed:7.1f}s] {name} b{budget:g}: {summary}", flush=True)
    for k in args.vmc_k_values:
        for budget in args.budgets:
            rows = evaluate_vmc(args.menagerie, k, budget, args.validation_seeds, args.fixture_count, f"vmc_k{k:g}_b{budget:g}")
            summary = aggregate(rows)
            candidates.append({"family": "vmc", "k": k, "budget": budget, "summary": summary})
            print(f"[{time.time()-elapsed:7.1f}s] vmc k{k:g} b{budget:g}: {summary}", flush=True)

    selected = {}
    for family in ("esn", "vmc"):
        selected[family] = max((candidate for candidate in candidates if candidate["family"] == family), key=lambda c: score(c["summary"]))
    print("selected", json.dumps(selected, indent=2), flush=True)
    esn_choice = selected["esn"]
    vmc_choice = selected["vmc"]
    test_rows = evaluate_esn(args.menagerie, esn_paths[esn_choice["model"]], esn_choice["budget"],
                             args.test_seeds, args.fixture_count, "selected_esn")
    test_rows += evaluate_vmc(args.menagerie, vmc_choice["k"], vmc_choice["budget"],
                              args.test_seeds, args.fixture_count, "selected_vmc")
    output = {
        "schema_version": 1,
        "protocol": "contact_apparatus_domain_randomization_validation_selection_then_heldout_test",
        "status": "confirmatory_after_development_calibration",
        "selection_rule": ["maximize validation task_success rate", "break ties with minimum validation at-grasp error"],
        "observation_contract": "q, qdot, nominal_twist, pose_error, wbc_twist_error only",
        "teacher_training_contract": "train-only VMC k=1.5 traces under physical apparatus randomization; apparatus parameters not in ESN input",
        "validation_seeds": args.validation_seeds,
        "test_seeds": args.test_seeds,
        "fixture_count_per_seed": args.fixture_count,
        "fixture_generator": "train_fixture(seed*1009 + fixture_index + 1), documented bounded physical ranges",
        "budget_candidates": args.budgets,
        "vmc_k_candidates": args.vmc_k_values,
        "validation_candidates": candidates,
        "selected": selected,
        "test_summary": {
            "esn": aggregate([row for row in test_rows if row["name"].startswith("selected_esn/")]),
            "vmc": aggregate([row for row in test_rows if row["name"].startswith("selected_vmc/")]),
        },
        "test_rows": test_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"selected": selected, "test_summary": output["test_summary"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
