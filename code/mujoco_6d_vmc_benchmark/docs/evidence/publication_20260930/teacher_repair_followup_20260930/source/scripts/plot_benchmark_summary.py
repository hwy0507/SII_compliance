#!/usr/bin/env python3
"""Create presentation-ready figures from paired ladder and geometry summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _style(axis: plt.Axes) -> None:
    axis.grid(True, axis="y", alpha=0.22)
    axis.spines[["top", "right"]].set_visible(False)


def _bar(axis: plt.Axes, labels: list[str], values: list[float], title: str, ylabel: str, invalid: list[bool]) -> None:
    colors = ["#d81b60" if not bad else "#a9a9a9" for bad in invalid]
    bars = axis.bar(labels, values, color=colors)
    for bar, value, bad in zip(bars, values, invalid):
        axis.annotate("invalid" if bad else f"{value:.2f}", (bar.get_x() + bar.get_width() / 2, bar.get_height()), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8, color="#555555")
    axis.set(title=title, ylabel=ylabel)
    _style(axis)


def plot_ladder(payload: dict[str, Any], output_dir: Path) -> Path:
    rows = payload["rows"]
    labels = [row["controller"] for row in rows]
    invalid = [not row["valid"] for row in rows]
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 7.2), constrained_layout=True)
    _bar(axes[0, 0], labels, [row["peak_nominal_error_mm"] for row in rows], "Peak reference deviation", "mm", invalid)
    _bar(axes[0, 1], labels, [row["release_to_rejoin_latency_s"] or np.nan for row in rows], "Release-to-rejoin latency", "s", invalid)
    _bar(axes[0, 2], labels, [row["peak_contact_force_n"] for row in rows], "Physical rod–hand force", "N", invalid)
    _bar(axes[1, 0], labels, [row["peak_torque_nm"] for row in rows], "Peak applied motor torque", "N·m", invalid)
    _bar(axes[1, 1], labels, [row["jerk_peak_mps3"] for row in rows], "Peak end-effector jerk", "m/s³", invalid)
    _bar(axes[1, 2], labels, [row["secondary_contact_count"] for row in rows], "Secondary contacts", "count", invalid)
    fig.suptitle("Fixed-reference low-level compliance baseline ladder\nGrey bars fail a task/contact/torque validity gate", fontsize=14)
    path = output_dir / "baseline_ladder_summary.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def _matrix(rows: list[dict[str, Any]], heights: list[float], strokes: list[float], key: str) -> np.ndarray:
    values = np.full((len(heights), len(strokes)), np.nan)
    for row in rows:
        i = heights.index(row["height_m"])
        j = strokes.index(row["stroke_m"])
        # The physical-task validity gate filters broken runs.  The contact
        # regime further says whether the realised collision belongs in the
        # nominal comparison set; stress cases remain visible elsewhere.
        if row["valid"] and row.get("contact_regime", "nominal_contact") == "nominal_contact":
            values[i, j] = row[key]
    return values


def plot_geometry(payload: dict[str, Any], output_dir: Path) -> Path:
    rows = payload["rows"]
    heights = sorted({row["height_m"] for row in rows})
    strokes = sorted({row["stroke_m"] for row in rows})
    specifications = [
        ("contact_peak_n", "Peak physical contact force (N)", "viridis"),
        ("rejoin_latency_s", "Release-to-rejoin latency (s)", "magma_r"),
        ("peak_nominal_error_mm", "Peak reference deviation (mm)", "magma_r"),
        ("secondary_contact_count", "Secondary contact count", "cividis"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.3), constrained_layout=True)
    for axis, (key, title, cmap) in zip(axes.flat, specifications):
        values = _matrix(rows, heights, strokes, key)
        image = axis.imshow(values, cmap=cmap, aspect="auto")
        axis.set(title=title, xlabel="rod stroke (m)", ylabel="rod height (m)")
        axis.set_xticks(range(len(strokes)), [f"{value:.2f}" for value in strokes])
        axis.set_yticks(range(len(heights)), [f"{value:.2f}" for value in heights])
        for i in range(len(heights)):
            for j in range(len(strokes)):
                if np.isnan(values[i, j]):
                    row = next(row for row in rows if row["height_m"] == heights[i] and row["stroke_m"] == strokes[j])
                    label = row.get("contact_regime", "invalid").replace("_", "\n")
                    axis.text(j, i, label, ha="center", va="center", color="#4a4a4a", fontsize=7, fontweight="bold")
                else:
                    axis.text(j, i, f"{values[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
        fig.colorbar(image, ax=axis, shrink=0.85)
    fig.suptitle("Rod geometry matrix: coloured = nominal-contact task-success; labels = other realised regimes", fontsize=14)
    path = output_dir / "geometry_matrix_summary.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ladder-json", type=Path, required=True)
    parser.add_argument("--geometry-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ladder = plot_ladder(_load(args.ladder_json), args.output_dir)
    geometry = plot_geometry(_load(args.geometry_json), args.output_dir)
    print(json.dumps({"baseline_ladder_figure": str(ladder), "geometry_matrix_figure": str(geometry)}, indent=2))


if __name__ == "__main__":
    main()
