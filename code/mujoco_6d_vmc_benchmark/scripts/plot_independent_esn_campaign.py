#!/usr/bin/env python3
"""Plot auditable multi-seed results for independent ESN-vs-MLP runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


PROFILE_ORDER = ("balanced", "contact_safe", "recovery_priority")
PROFILE_COLORS = {
    "balanced": "#0f766e",
    "contact_safe": "#be123c",
    "recovery_priority": "#a16207",
}


def _paired_rows(payload: dict, profile: str) -> list[dict]:
    return [
        row for row in payload["rows"]
        if row["profile"] == profile and row["mlp_gate"] and row["esn_gate"]
    ]


def _mean_std(rows: list[dict], metric: str) -> tuple[float, float]:
    values = np.asarray([row["difference_esn_minus_mlp"][metric] for row in rows], dtype=float)
    return float(np.mean(values)), float(np.std(values, ddof=0))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--phase-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary_json.read_text())
    phase = json.loads(args.phase_json.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.2), constrained_layout=True)
    metrics = (
        ("recovery_rmse_mm", "Recovery RMSE difference (ESN - MLP), mm"),
        ("rejoin_latency_s", "Rejoin latency difference (ESN - MLP), s"),
        ("contact_impulse_ns", "Contact impulse difference (ESN - MLP), N s"),
    )
    for axis, (metric, label) in zip(axes.flat[:3], metrics, strict=True):
        for index, profile_name in enumerate(PROFILE_ORDER):
            rows = _paired_rows(summary, profile_name)
            values = np.asarray([row["difference_esn_minus_mlp"][metric] for row in rows], dtype=float)
            x = np.full(values.shape, index, dtype=float) + np.linspace(-0.12, 0.12, len(values))
            axis.scatter(x, values, s=34, color=PROFILE_COLORS[profile_name], alpha=0.85, zorder=3)
            mean, std = _mean_std(rows, metric)
            axis.errorbar(index, mean, yerr=std, color="#111827", capsize=4, lw=1.5, zorder=4)
        axis.axhline(0.0, color="#4b5563", lw=1.0)
        axis.set_xticks(range(len(PROFILE_ORDER)), [name.replace("_", "\n") for name in PROFILE_ORDER])
        axis.set_ylabel(label)
        axis.grid(axis="y", alpha=0.22)

    axis = axes.flat[3]
    phase_names = ("pre_contact", "loading", "recovery", "post_grasp")
    phase_labels = ("Pre-contact", "Loading", "Recovery", "Post-grasp")
    recovery_delta = [phase["by_phase_esn_minus_mlp"][name]["tracking_rmse_mm"] for name in phase_names]
    torque_delta = [phase["by_phase_esn_minus_mlp"][name]["peak_torque_nm"] for name in phase_names]
    positions = np.arange(len(phase_names))
    width = 0.38
    axis.bar(positions - width / 2, [item["mean"] for item in recovery_delta], width, yerr=[item["std"] for item in recovery_delta], capsize=3, color="#0f766e", label="Tracking RMSE (mm)")
    twin = axis.twinx()
    twin.bar(positions + width / 2, [item["mean"] for item in torque_delta], width, yerr=[item["std"] for item in torque_delta], capsize=3, color="#d97706", label="Peak torque (Nm)")
    axis.axhline(0.0, color="#4b5563", lw=1.0)
    twin.axhline(0.0, color="#4b5563", lw=1.0)
    axis.set_xticks(positions, phase_labels, rotation=16, ha="right")
    axis.set_ylabel("ESN - MLP tracking RMSE (mm)", color="#0f766e")
    twin.set_ylabel("ESN - MLP peak torque (Nm)", color="#d97706")
    handles_a, labels_a = axis.get_legend_handles_labels()
    handles_b, labels_b = twin.get_legend_handles_labels()
    axis.legend(handles_a + handles_b, labels_a + labels_b, loc="upper left", frameon=False)
    fig.suptitle("Independent Fan Ye ESN versus matched current-state MLP", fontsize=15)
    figure_path = args.output_dir / "independent_esn_multiseed_summary.png"
    fig.savefig(figure_path, dpi=220)
    plt.close(fig)
    print(figure_path)


if __name__ == "__main__":
    main()
