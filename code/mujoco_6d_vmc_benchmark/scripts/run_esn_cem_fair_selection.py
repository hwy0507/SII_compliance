#!/usr/bin/env python3
"""Validation-only selection for readout-improved ESN versus tuned VMC.

The CEM checkpoint is frozen before this script runs.  Its CEM training seeds
must be disjoint from this script's validation and held-out test seeds.  The
script first selects whether the BC-parent or CEM-improved ESN is retained on
validation, then separately tunes VMC stiffness and residual budget on those
same validation realizations.  It evaluates only the two selected methods on
previously untouched test realizations.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
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
    return [train_fixture(np.random.default_rng(np.uint64(seed) * 1009 + index + 1))
            for index in range(count)]


def aggregate(rows: list[dict]) -> dict:
    return {
        "count": len(rows),
        "success_rate": float(np.mean([bool(row["task_success"]) for row in rows])),
        "mean_at_grasp_err_mm": float(np.mean([float(row["at_grasp_err_mm"]) for row in rows])),
        "mean_peak_force_n": float(np.mean([float(row["obstacle_force_n"]) for row in rows])),
        "mean_peak_torque_nm": float(np.mean([float(row["peak_torque_nm"]) for row in rows])),
        "mean_contact_bout_count": float(np.mean([int(row["contact_bout_count"]) for row in rows])),
        "hard_limit_count": int(sum(bool(row["hard_limit"]) for row in rows)),
    }


def score(summary: dict) -> tuple[float, float]:
    return summary["success_rate"], -summary["mean_at_grasp_err_mm"]


def evaluate_esn(menagerie: Path, model_path: Path, budget: float, seeds: list[int],
                 fixture_count: int, label: str) -> list[dict]:
    controller = load_controller(model_path)
    rows: list[dict] = []
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
    rows: list[dict] = []
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
    parser.add_argument("--esn-parent", type=Path, required=True)
    parser.add_argument("--esn-cem", type=Path, required=True)
    parser.add_argument("--esn-budget", type=float, default=0.05,
                        help="fixed during CEM train-only policy improvement")
    parser.add_argument("--validation-seeds", type=parse_int_list, required=True)
    parser.add_argument("--test-seeds", type=parse_int_list, required=True)
    parser.add_argument("--fixture-count", type=int, default=4)
    parser.add_argument("--vmc-budgets", type=parse_float_list, default=[0.02, 0.03, 0.05])
    parser.add_argument("--vmc-k-values", type=parse_float_list, default=[1.0, 1.5, 2.2, 3.2])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 0.0 < args.esn_budget <= 1.0:
        raise SystemExit("esn-budget must be in (0,1]")
    if args.fixture_count < 1 or set(args.validation_seeds) & set(args.test_seeds):
        raise SystemExit("fixture-count must be positive and validation/test seeds disjoint")

    candidates: list[dict] = []
    started = time.time()
    for name, path in (("bc_parent", args.esn_parent), ("cem_improved", args.esn_cem)):
        rows = evaluate_esn(args.menagerie, path, args.esn_budget, args.validation_seeds,
                            args.fixture_count, f"esn_{name}")
        summary = aggregate(rows)
        candidates.append({"family": "esn", "model": name, "budget": args.esn_budget, "summary": summary})
        print(f"[{time.time()-started:7.1f}s] esn {name}: {summary}", flush=True)
    for k in args.vmc_k_values:
        for budget in args.vmc_budgets:
            rows = evaluate_vmc(args.menagerie, k, budget, args.validation_seeds,
                                args.fixture_count, f"vmc_k{k:g}_b{budget:g}")
            summary = aggregate(rows)
            candidates.append({"family": "vmc", "k": k, "budget": budget, "summary": summary})
            print(f"[{time.time()-started:7.1f}s] vmc k{k:g} b{budget:g}: {summary}", flush=True)

    selected = {
        family: max((candidate for candidate in candidates if candidate["family"] == family),
                    key=lambda candidate: score(candidate["summary"]))
        for family in ("esn", "vmc")
    }
    print("selected", json.dumps(selected, indent=2), flush=True)
    esn_paths = {"bc_parent": args.esn_parent, "cem_improved": args.esn_cem}
    esn_choice, vmc_choice = selected["esn"], selected["vmc"]
    test_rows = evaluate_esn(args.menagerie, esn_paths[esn_choice["model"]], esn_choice["budget"],
                             args.test_seeds, args.fixture_count, "selected_esn")
    test_rows += evaluate_vmc(args.menagerie, vmc_choice["k"], vmc_choice["budget"],
                              args.test_seeds, args.fixture_count, "selected_vmc")
    output = {
        "schema_version": 1,
        "protocol": "cem_esn_train_only_then_validation_selection_then_heldout_test",
        "status": "confirmatory_after_train_only_cem",
        "esn_cem_contract": "frozen 32-D observation and reservoir; CEM only tuned seven bounded readout output gains on train-only MuJoCo rollouts",
        "selection_rule": ["maximize validation task_success rate", "break ties with minimum validation at-grasp error"],
        "validation_seeds": args.validation_seeds,
        "test_seeds": args.test_seeds,
        "fixture_count_per_seed": args.fixture_count,
        "fixture_generator": "train_fixture(seed*1009 + fixture_index + 1), documented bounded physical ranges",
        "esn_candidates": {"bc_parent": str(args.esn_parent), "cem_improved": str(args.esn_cem),
                           "fixed_budget": args.esn_budget},
        "vmc_k_candidates": args.vmc_k_values,
        "vmc_budget_candidates": args.vmc_budgets,
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
