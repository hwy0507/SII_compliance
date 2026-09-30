#!/usr/bin/env python3
"""Aggregate historical push results, with explicit evidence limits.

The source JSONs are copied from the server's ``unified_matrix_random_20260902``
run. Matching seed labels alone do not prove a matched experiment or identify
the current proposed checkpoint. Missing provenance stays unknown. The classical
impedance/admittance matrix is intentionally kept separate because it used a
different v7 source fixture and cannot be merged into this table.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


METHODS = ("esn", "mlp", "vmc", "paper_mpc")
METRICS = {
    "trajectory_rmse_m": "track_error_rmse_m",
    "peak_torque_nm": "terminal_info.peak_torque_nm",
    "peak_speed_mps": "ee_speed_peak_mps",
    "speed_p95_mps": "ee_speed_p95_mps",
}


def get(row: dict, key: str) -> float:
    if key.startswith("terminal_info."):
        value = row["terminal_info"][key.split(".", 1)[1]]
    else:
        value = row[key]
    value = float(value)
    if not np.isfinite(value):
        raise ValueError(f"Nonfinite metric: {key}")
    return value


def historical_push_gate(raw: dict) -> dict:
    """Consistency check on saved summaries; not a new physics audit."""
    checks = {
        "contact": raw["push_first_contact_s"] is not None,
        "duration": raw["push_contact_duration_s"] >= 1.2,
        "span": raw["push_contact_span_s"] is not None and raw["push_contact_span_s"] >= 1.5,
        "duty": raw["push_contact_duty_cycle"] >= .7,
        "displacement": raw["push_signed_actual_displacement_m"] >= .03,
        "recovery": raw["push_recovery_to_precontact_baseline_m"] is not None and raw["push_recovery_to_precontact_baseline_m"] <= .012,
        "grasp_lift": bool(raw["object_grasped_and_lifted"]),
        "penetration": raw["max_push_penetration_m"] <= .0005,
        "upstream": raw["max_upstream_penetration_m"] <= 1.e-8,
    }
    return {"accepted": all(checks.values()), "checks": checks}


def aggregate(root: Path) -> dict:
    rows = []
    raw_by_method = {}
    for method in METHODS:
        paths = sorted((root / method).glob("*.json"))
        if not paths:
            raise FileNotFoundError(f"missing method directory: {root / method}")
        raw_by_method[method] = {}
        for path in paths:
            raw = json.loads(path.read_text())
            seed = int(raw["seed"])
            if seed in raw_by_method[method]:
                raise ValueError(f"Duplicate seed {seed} in {method}")
            if raw.get("protocol") != "isolated_push_compliance":
                raise ValueError(f"Unexpected protocol in {path}")
            raw_by_method[method][seed] = raw
            legacy_gate = historical_push_gate(raw)
            rows.append({
                "method": method,
                "source": str(path.relative_to(root)),
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "seed": seed,
                "scenario_success": bool(raw["scenario_success"]),
                "task_success": bool(raw["task_success"]),
                "reported_geometry_valid": raw.get("geometry_valid"),
                "recorded_push_penetration_m": get(raw, "max_push_penetration_m"),
                "push_penetration_le_0p2mm": get(raw, "max_push_penetration_m") <= .0002,
                "historical_gate_reconstructed": legacy_gate["accepted"],
                "historical_gate_matches_record": legacy_gate["accepted"] == bool(raw["scenario_success"]),
                **{name: get(raw, field) for name, field in METRICS.items()},
            })
    seeds = set(raw_by_method[METHODS[0]])
    if any(set(raw_by_method[m]) != seeds for m in METHODS):
        raise ValueError("Methods do not share the same seed set")
    # These fields are actually present in the legacy JSON. They do not cover
    # the full controller, sensor, physics, checkpoint or nominal reference.
    fields = ("protocol", "record_duration_s", "grasp_time_s", "push_rod_stroke_m",
              "push_lateral_gain_scale", "push_recovery_wbc_gain_scale",
              "push_recovery_residual_scale")
    mismatch = {field: [seed for seed in sorted(seeds)
                       if any(raw_by_method[m][seed].get(field) !=
                              raw_by_method[METHODS[0]][seed].get(field)
                              for m in METHODS[1:])] for field in fields}
    fixture_mismatch = [seed for seed in sorted(seeds)
                        if any(raw_by_method[m][seed]["terminal_info"].get("fixture") !=
                               raw_by_method[METHODS[0]][seed]["terminal_info"].get("fixture")
                               for m in METHODS[1:])]
    summary = {}
    for method in METHODS:
        part = [row for row in rows if row["method"] == method]
        summary[method] = {
            "n": len(part),
            "scenario_successes": sum(row["scenario_success"] for row in part),
            "task_successes": sum(row["task_success"] for row in part),
            "push_penetration_le_0p2mm_count": sum(row["push_penetration_le_0p2mm"] for row in part),
            "historical_gate_matches_record_count": sum(row["historical_gate_matches_record"] for row in part),
            "historical_gate_check_passes": {
                check: sum(historical_push_gate(raw)["checks"][check] for raw in raw_by_method[method].values())
                for check in historical_push_gate(next(iter(raw_by_method[method].values())))["checks"]
            },
            "metrics": {
                metric: {
                    "mean": float(np.mean([row[metric] for row in part])),
                    "median": float(np.median([row[metric] for row in part])),
                    "max": float(np.max([row[metric] for row in part])),
                    "std_across_rollouts": float(np.std([row[metric] for row in part], ddof=1)) if len(part) > 1 else None,
                }
                for metric in METRICS
            },
        }
    return {
        "protocol": "isolated_push_compliance",
        "status": "historical diagnostic; not the canonical proposed-model comparison",
        "fixture_source": "server:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_matrix_random_20260902/push",
        "methods": METHODS,
        "metric_definitions": {
            "trajectory_rmse_m": "reported RMS Euclidean EE position error; original sampling/source not archived here",
            "peak_torque_nm": "reported terminal peak torque; original recording implementation not archived here",
            "peak_speed_mps": "reported max norm of EE linear velocity; not proven physics-substep peak",
            "speed_p95_mps": "95th percentile of EE linear speed, supplementary",
        },
        "fairness": {
            "matched_seed_labels": sorted(seeds),
            "same_fixture_count": len(seeds),
            "recorded_field_mismatches_by_seed": mismatch,
            "recorded_fixture_mismatch_seeds": fixture_mismatch,
            "same_nominal_reference": None,
            "same_controller_period": None,
            "same_safety_stack": None,
            "office_used_for_selection": None,
            "original_source_and_checkpoint_hashes_verified": False,
            "terminal_labels_unreliable": "All four methods report direct_esn/uses_vmc=false; these labels cannot identify the controller",
            "fixture_metadata_limitation": "terminal fixture rod_stroke=0.16 differs from varying top-level push_rod_stroke; it is not a complete fixture manifest",
            "unrelated_protocol_file": "guarded_protocol.json is a different 9-condition panel experiment; not provenance for these 120 rows",
        },
        "summary": summary,
        "rows": rows,
        "classical_impedance_admittance": {
            "excluded_from_this_table": True,
            "reason": "their 24-rollout matrix uses the separate v7 source fixture and different panel/rod protocol; merging would violate same-fixture fairness",
            "report": "docs/CLASSICAL_BASELINES_20260923.md",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = aggregate(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.output / "per_rollout.csv").open("w", newline="") as handle:
        columns = list(report["rows"][0])
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(report["rows"])
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
