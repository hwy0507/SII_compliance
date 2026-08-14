#!/usr/bin/env python3
"""Build an auditable selected-energy-safety V2/V3 holdout comparison.

The selected configuration must already be frozen by an independent validation
scan.  This tool only reads completed benchmark JSON files; it does not run
MuJoCo, tune a parameter, or alter a fixture manifest.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


METRICS = (
    "recovery_rmse_mm",
    "recovery_iae_mm_s",
    "rejoin_latency_s",
    "post_contact_jerk_p95_mps3",
    "peak_torque_nm",
    "torque_rate_peak_nmps",
)
CONTROLLERS = ("rigid", "impedance", "vmc_gated", "vmc_energy_default", "vmc_energy_selected")
DISPLAY = {
    "rigid": "Rigid",
    "impedance": "Impedance",
    "vmc_gated": "VMC-gated",
    "vmc_energy_default": "VMC-energy\n(default)",
    "vmc_energy_selected": "VMC-energy\n(selected)",
}
COLORS = {
    "rigid": "#4b5563",
    "impedance": "#2563eb",
    "vmc_gated": "#d97706",
    "vmc_energy_default": "#9333ea",
    "vmc_energy_selected": "#dc2626",
}
def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _by_controller(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["controller"]: row for row in payload["aggregate_common_valid_all_controllers"]}


def _mean(row: dict[str, Any], metric: str) -> float:
    metric_data = row.get(metric)
    if metric_data is None:
        raise ValueError(f"{row['controller']} has no valid value for {metric}")
    return float(metric_data["mean"])


def _validate_fixture_pair(
    name: str, baseline: dict[str, Any], selected: dict[str, Any],
) -> None:
    baseline_ids = sorted(baseline["common_valid_fixture_ids_all_controllers"])
    selected_ids = sorted(selected["common_valid_fixture_ids_all_controllers"])
    if baseline_ids != selected_ids:
        raise ValueError(f"{name} selected fixture IDs do not match the frozen baseline common-valid set")
    selected_rows = _by_controller(selected)
    if set(selected_rows) != {"vmc_energy"}:
        raise ValueError(f"{name} selected holdout must contain only vmc_energy, got {sorted(selected_rows)}")
    selected_row = selected_rows["vmc_energy"]
    if selected_row["valid_count"] != len(baseline_ids):
        raise ValueError(f"{name} selected holdout has incomplete valid coverage")


def _assemble_split(
    name: str, baseline: dict[str, Any], default_energy: dict[str, Any], selected: dict[str, Any],
) -> dict[str, Any]:
    _validate_fixture_pair(name, baseline, selected)
    base_rows = _by_controller(baseline)
    default_rows = _by_controller(default_energy)
    required = {"rigid", "impedance", "vmc_gated"}
    missing = required - set(base_rows)
    if missing:
        raise ValueError(f"{name} baseline is missing {sorted(missing)}")
    if "vmc_energy" not in default_rows:
        raise ValueError(f"{name} default-energy reference is missing vmc_energy")
    rows = {
        "rigid": base_rows["rigid"],
        "impedance": base_rows["impedance"],
        "vmc_gated": base_rows["vmc_gated"],
        "vmc_energy_default": default_rows["vmc_energy"],
        "vmc_energy_selected": _by_controller(selected)["vmc_energy"],
    }
    result = {
        "fixture_count": len(baseline["common_valid_fixture_ids_all_controllers"]),
        "fixture_ids": sorted(baseline["common_valid_fixture_ids_all_controllers"]),
        "methods": {
            controller: {metric: _mean(row, metric) for metric in METRICS}
            for controller, row in rows.items()
        },
    }
    selected_metrics = result["methods"]["vmc_energy_selected"]
    result["selected_relative_change_percent"] = {
        reference: {
            # A zero-valued reference (for example rigid's instantaneous
            # rejoin latency in this finite benchmark) has no meaningful
            # percentage denominator.  Preserve the absolute values above
            # and represent the relative quantity as null rather than divide
            # by zero or fabricate a huge finite number.
            metric: None if values[metric] == 0.0 else 100.0 * (selected_metrics[metric] / values[metric] - 1.0)
            for metric in METRICS
        }
        for reference, values in result["methods"].items()
        if reference != "vmc_energy_selected"
    }
    return result


def _plot(comparison: dict[str, Any], output: Path) -> None:
    # Reserve a fixed top band for the global legend.  Constrained layout can
    # otherwise place that legend on top of the first row's panel titles.
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.5), constrained_layout=False)
    fig.subplots_adjust(top=0.89, bottom=0.09, left=0.07, right=0.985, hspace=0.30, wspace=0.15)
    for row_index, split in enumerate(("V2", "V3")):
        methods = comparison["splits"][split]["methods"]
        for col_index, (metric, y_label, title) in enumerate((
            ("peak_torque_nm", "Peak torque (N·m)", "Accuracy–torque"),
            ("post_contact_jerk_p95_mps3", "Post-contact jerk P95 (m/s³)", "Accuracy–smoothness"),
        )):
            axis = axes[row_index, col_index]
            for controller in CONTROLLERS:
                values = methods[controller]
                x, y = values["recovery_rmse_mm"], values[metric]
                marker = "*" if controller == "vmc_energy_selected" else "o"
                size = 150 if controller == "vmc_energy_selected" else 72
                axis.scatter(x, y, s=size, marker=marker, color=COLORS[controller], zorder=3)
            axis.set(
                xlabel="Recovery RMSE (mm)", ylabel=y_label,
                title=f"{split} {title} (common-valid n={comparison['splits'][split]['fixture_count']})",
            )
            axis.grid(alpha=0.25)
            axis.spines[["top", "right"]].set_visible(False)
    handles = [
        Line2D(
            [], [], color=COLORS[controller], marker="*" if controller == "vmc_energy_selected" else "o",
            linestyle="", markersize=12 if controller == "vmc_energy_selected" else 7,
            label=DISPLAY[controller].replace("\n", " "),
        )
        for controller in CONTROLLERS
    ]
    fig.legend(handles=handles, loc="upper center", ncol=len(handles), frameon=False, bbox_to_anchor=(0.5, 0.985))
    fig.savefig(output, dpi=240)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-baseline", type=Path, required=True)
    parser.add_argument("--v2-default-energy", type=Path, required=True)
    parser.add_argument("--v2-selected", type=Path, required=True)
    parser.add_argument("--v3-baseline", type=Path, required=True)
    parser.add_argument("--v3-selected", type=Path, required=True)
    parser.add_argument("--selected-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    selected_config = _load(args.selected_config)
    required_config_fields = {
        "initial_energy_j", "minimum_energy_j", "maximum_energy_j", "damping_recharge_efficiency",
        "minimum_direction_scale", "direction_transition_speed_mps", "smoothing_time_constant_s",
    }
    if required_config_fields - set(selected_config):
        raise ValueError("selected configuration JSON is incomplete")
    v2_selected = _load(args.v2_selected)
    v3_selected = _load(args.v3_selected)
    expected_config = {key: selected_config[key] for key in required_config_fields}
    for split, payload in (("V2", v2_selected), ("V3", v3_selected)):
        if payload["protocol"]["energy_safety_config"] != expected_config:
            raise ValueError(f"{split} did not record the exact frozen selected configuration")

    comparison = {
        "protocol": {
            "selection": "configuration frozen by separate validation scan before V2/V3 evaluation",
            "comparison_rule": "V2/V3 values use each frozen suite's common-valid fixture set; no post-hoc tuning",
            "selected_config": expected_config,
            "selected_config_label": selected_config.get("label"),
        },
        "splits": {
            "V2": _assemble_split("V2", _load(args.v2_baseline), _load(args.v2_default_energy), v2_selected),
            "V3": _assemble_split("V3", _load(args.v3_baseline), _load(args.v3_baseline), v3_selected),
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "energy_safety_final_holdout_comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
    with (args.output_dir / "energy_safety_final_holdout_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("split", "common_valid_fixture_count", "controller", *METRICS), lineterminator="\n")
        writer.writeheader()
        for split, split_data in comparison["splits"].items():
            for controller, values in split_data["methods"].items():
                writer.writerow({"split": split, "common_valid_fixture_count": split_data["fixture_count"], "controller": controller, **values})
    _plot(comparison, args.output_dir / "energy_safety_final_holdout_pareto.png")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
