#!/usr/bin/env python3
"""Compare the completed V4 five-side holdout without further simulation.

The default ladder contains rigid, impedance, VMC-gated, and default
VMC-energy.  A separate single-method run evaluates the frozen selected
VMC-energy configuration.  This utility forms the intersection of valid
fixtures across *all five* methods before calculating any numerical
comparison, thereby preserving both validity rates and fair paired means.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


METRICS = (
    "recovery_rmse_mm", "recovery_iae_mm_s", "rejoin_latency_s",
    "yield_peak_error_mm", "post_contact_speed_p95_mps",
    "post_contact_jerk_p95_mps3", "peak_torque_nm", "torque_p95_nm",
    "torque_rms_nm", "torque_rate_peak_nmps", "peak_contact_force_n",
    "contact_impulse_ns",
)
METHODS = ("rigid", "impedance", "vmc_gated", "vmc_energy_default", "vmc_energy_selected")
DISPLAY = {
    "rigid": "Rigid", "impedance": "Impedance", "vmc_gated": "VMC-gated",
    "vmc_energy_default": "VMC-energy (default)",
    "vmc_energy_selected": "VMC-energy (selected)",
}
COLORS = {
    "rigid": "#4b5563", "impedance": "#2563eb", "vmc_gated": "#d97706",
    "vmc_energy_default": "#9333ea", "vmc_energy_selected": "#dc2626",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _valid_rows(payload: dict[str, Any], controller: str) -> list[dict[str, Any]]:
    return [row for row in payload["rows"] if row["controller"] == controller and row["valid"]]


def _mean(rows: list[dict[str, Any]], metric: str) -> float | None:
    values = [float(row[metric]) for row in rows if row[metric] is not None]
    return None if not values else float(np.mean(values))


def _aggregate(rows_by_method: dict[str, list[dict[str, Any]]], fixture_ids: set[str]) -> dict[str, dict[str, Any]]:
    return {
        method: {
            "valid_count_on_common_set": len([row for row in rows if row["fixture_id"] in fixture_ids]),
            **{metric: _mean([row for row in rows if row["fixture_id"] in fixture_ids], metric) for metric in METRICS},
        }
        for method, rows in rows_by_method.items()
    }


def _per_side(rows_by_method: dict[str, list[dict[str, Any]]], fixture_ids: set[str]) -> dict[str, dict[str, dict[str, float | None]]]:
    sides = sorted({row["approach_side"] for rows in rows_by_method.values() for row in rows if row["fixture_id"] in fixture_ids})
    return {
        side: {
            method: {
                metric: _mean([row for row in rows if row["fixture_id"] in fixture_ids and row["approach_side"] == side], metric)
                for metric in METRICS
            }
            for method, rows in rows_by_method.items()
        }
        for side in sides
    }


def _plot(methods: dict[str, dict[str, Any]], fixture_count: int, output: Path, title_prefix: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9), constrained_layout=True)
    fig.suptitle(title_prefix, fontsize=15)
    panels = (
        ("peak_torque_nm", "Peak torque (N·m)", "Accuracy–torque"),
        ("post_contact_jerk_p95_mps3", "Post-contact jerk P95 (m/s³)", "Accuracy–smoothness"),
    )
    for axis, (metric, y_label, title) in zip(axes, panels):
        label_offsets = {
            "peak_torque_nm": {
                "rigid": (5, 6), "impedance": (5, 6), "vmc_gated": (5, 6),
                "vmc_energy_default": (-100, 10), "vmc_energy_selected": (5, -11),
            },
            "post_contact_jerk_p95_mps3": {
                "rigid": (5, 6), "impedance": (5, 6), "vmc_gated": (5, 6),
                "vmc_energy_default": (-94, 10), "vmc_energy_selected": (5, 7),
            },
        }[metric]
        for method in METHODS:
            point = methods[method]
            axis.scatter(
                point["recovery_rmse_mm"], point[metric], s=150 if method.endswith("selected") else 76,
                marker="*" if method.endswith("selected") else "o", color=COLORS[method], zorder=3,
            )
            axis.annotate(
                DISPLAY[method], (point["recovery_rmse_mm"], point[metric]),
                xytext=label_offsets[method], textcoords="offset points", fontsize=8,
            )
        axis.set(xlabel="Recovery RMSE (mm)", ylabel=y_label, title=f"{title} (common-valid n={fixture_count})")
        axis.grid(alpha=0.25)
        axis.spines[["top", "right"]].set_visible(False)
    fig.savefig(output, dpi=240)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--default-ladder", type=Path, required=True)
    parser.add_argument("--selected-ladder", type=Path, required=True)
    parser.add_argument("--selected-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--expected-reference-source",
        help="Require both ladders to record this source, preventing accidental proxy/WBC result mixing.",
    )
    parser.add_argument("--title-prefix", default="V4 five-side holdout")
    args = parser.parse_args()

    default, selected, config = _load(args.default_ladder), _load(args.selected_ladder), _load(args.selected_config)
    if args.expected_reference_source is not None:
        for label, payload in (("default", default), ("selected", selected)):
            if payload["protocol"].get("reference_source") != args.expected_reference_source:
                raise ValueError(f"{label} ladder does not use the expected reference source")
    config_fields = {
        "initial_energy_j", "minimum_energy_j", "maximum_energy_j", "damping_recharge_efficiency",
        "minimum_direction_scale", "direction_transition_speed_mps", "smoothing_time_constant_s",
    }
    frozen_config = {key: config[key] for key in config_fields}
    if selected["protocol"]["energy_safety_config"] != frozen_config:
        raise ValueError("selected V4 run did not record the exact frozen safety configuration")
    rows_by_method = {
        "rigid": _valid_rows(default, "rigid"),
        "impedance": _valid_rows(default, "impedance"),
        "vmc_gated": _valid_rows(default, "vmc_gated"),
        "vmc_energy_default": _valid_rows(default, "vmc_energy"),
        "vmc_energy_selected": _valid_rows(selected, "vmc_energy"),
    }
    fixture_sets = {method: {row["fixture_id"] for row in rows} for method, rows in rows_by_method.items()}
    common_ids = sorted(set.intersection(*fixture_sets.values()))
    if not common_ids:
        raise RuntimeError("V4 ladder has no common-valid fixture across the five methods")
    common_set = set(common_ids)
    methods = _aggregate(rows_by_method, common_set)
    selected_metrics = methods["vmc_energy_selected"]
    relative_to_selected = {
        reference: {
            metric: None if values[metric] in (None, 0.0) or selected_metrics[metric] is None else 100.0 * (selected_metrics[metric] / values[metric] - 1.0)
            for metric in METRICS
        }
        for reference, values in methods.items() if reference != "vmc_energy_selected"
    }
    comparison = {
        "protocol": {
            "scope": "V4 frozen five-side axis-aligned physical collision holdout; positive_z excluded; not sign-complete or arbitrary continuous 3-D impact",
            "comparison_rule": "all numerical controller comparisons use the valid-fixture intersection across rigid, impedance, VMC-gated, default VMC-energy, and frozen selected VMC-energy",
            "selected_config_label": config.get("label"), "selected_config": frozen_config,
            "reference_source": default["protocol"].get("reference_source"),
        },
        "valid_fixture_ids_by_method": {method: sorted(ids) for method, ids in fixture_sets.items()},
        "common_valid_fixture_ids": common_ids,
        "common_valid_fixture_count": len(common_ids),
        "methods": methods,
        "selected_relative_change_percent": relative_to_selected,
        "methods_by_approach_side_on_common_valid": _per_side(rows_by_method, common_set),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "v4_final_holdout_comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
    with (args.output_dir / "v4_final_holdout_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("common_valid_fixture_count", "controller", *METRICS), lineterminator="\n")
        writer.writeheader()
        for method, values in methods.items():
            writer.writerow({"common_valid_fixture_count": len(common_ids), "controller": method, **{metric: values[metric] for metric in METRICS}})
    _plot(methods, len(common_ids), args.output_dir / "v4_final_holdout_pareto.png", args.title_prefix)
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
