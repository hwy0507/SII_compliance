#!/usr/bin/env python3
"""Plot WBC-relative trajectories and physical metrics from an impactor matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


IMPACTOR_LABELS = {
    "rod": "Rod",
    "ball": "Ball",
    "hand_proxy": "Hand-palm proxy",
}
CONTROLLER_LABELS = {
    "rigid": "Rigid",
    "impedance": "Impedance",
    "vmc_gated": "Six-spring VMC",
}
COLORS = {
    "rigid": "#c94c4c",
    "impedance": "#2f6f9f",
    "vmc_gated": "#16836b",
}


def _only_trace(folder: Path) -> Path:
    traces = sorted(folder.glob("rod_perturbation_*_trace.npz"))
    if len(traces) != 1:
        raise RuntimeError(f"expected one trace in {folder}, found {len(traces)}")
    return traces[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads((args.matrix_dir / "impactor_matrix_summary.json").read_text())
    rows = payload["rows"]
    impactors = ["rod", "ball", "hand_proxy"]
    controllers = ["rigid", "impedance", "vmc_gated"]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True, constrained_layout=True)
    for row_index, impactor in enumerate(impactors):
        trajectory_axis = axes[row_index]
        for controller in controllers:
            run_dir = args.matrix_dir / impactor / controller
            trace = np.load(_only_trace(run_dir))
            no_impact = np.load(_only_trace(run_dir / "no_impact"))
            time = trace["time"]
            window = (time >= 0.88) & (time <= 2.40)
            impact_deviation = (trace["ee_position"][:, 1] - trace["nominal_position"][:, 1]) * 1000.0
            no_impact_deviation = (no_impact["ee_position"][:, 1] - no_impact["nominal_position"][:, 1]) * 1000.0
            trajectory_axis.plot(time[window], impact_deviation[window], color=COLORS[controller], linewidth=1.9, label=CONTROLLER_LABELS[controller])
            if controller == "vmc_gated":
                trajectory_axis.plot(time[window], no_impact_deviation[window], color="#7f7f7f", linewidth=1.2, linestyle=":", label="Matched no-impact")
            summary = json.loads(next(run_dir.glob("rod_perturbation_*_summary.json")).read_text())
            start = summary["phase_analysis"]["primary_contact_start_s"]
            release = summary["phase_analysis"]["primary_contact_release_s"]
            if controller == "vmc_gated" and start is not None and release is not None:
                trajectory_axis.axvspan(start, release, color="#d8b365", alpha=0.16, label="Measured contact window")
                trajectory_axis.axvline(release, color="#555555", linewidth=0.9, linestyle="--", label="VMC release")
        trajectory_axis.axhline(0.0, color="#222222", linewidth=1.0, linestyle="--", label="WBC reference")
        trajectory_axis.set_title(f"{IMPACTOR_LABELS[impactor]}: physical departure and compliant return")
        trajectory_axis.set_ylabel("EE lateral deviation from WBC (mm)")
        trajectory_axis.grid(alpha=0.25)
        trajectory_axis.legend(loc="upper right", fontsize=8, ncol=3)
    axes[-1].set_xlabel("Time (s)")

    fig.suptitle("Same fixed-WBC grasp task: impact, yield, release, and return", fontsize=15)
    fig.savefig(args.output_dir / "impactor_matrix_wbc_deviation.png", dpi=200)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes = axes.ravel()
    for axis, metric, title, unit in zip(
        axes,
        ("contact_impulse_ns", "rejoin_latency_ms", "peak_recovery_jerk_mps3", "peak_torque_nm"),
        ("Physical contact impulse", "Release-to-rejoin latency", "Peak recovery jerk", "Peak joint torque"),
        ("N s", "ms", "m/s^3", "Nm"),
    ):
        x = np.arange(len(impactors))
        width = 0.22
        for index, controller in enumerate(controllers):
            values = [next(row for row in rows if row["impactor_type"] == impactor and row["controller"] == controller)[metric] for impactor in impactors]
            values = [np.nan if value is None else value for value in values]
            axis.bar(x + (index - 1) * width, values, width, label=CONTROLLER_LABELS[controller], color=COLORS[controller])
        axis.set_xticks(x, [IMPACTOR_LABELS[item] for item in impactors])
        axis.set_title(title)
        axis.set_ylabel(unit)
        axis.grid(axis="y", alpha=0.25)
    axes[-1].legend(loc="upper right", fontsize=8)
    fig.savefig(args.output_dir / "impactor_matrix_stability_metrics.png", dpi=200)


if __name__ == "__main__":
    main()
