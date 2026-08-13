#!/usr/bin/env python3
"""Create paper-style trajectory/error plots for paired rod and no-rod traces.

The nominal trace is the current WBC-reference interface (a reachable
trajectory proxy in this benchmark), not a live WBC output.  The script keeps
that distinction in every figure label so the same plotting code can later be
used with recorded WBC pose/twist data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _load(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: np.asarray(data[key]) for key in data.files}


def _window(time: np.ndarray, start: float | None, end: float | None) -> np.ndarray:
    mask = np.ones(time.shape, dtype=bool)
    if start is not None:
        mask &= time >= start
    if end is not None:
        mask &= time <= end
    return mask


def _shade_events(
    ax: plt.Axes,
    rod_start: float,
    rod_end: float,
    grasp_time: float,
    rod_cycles: int = 1,
    rod_cycle_period: float = 0.80,
) -> None:
    profile_duration = rod_end - rod_start
    for cycle in range(rod_cycles):
        start = rod_start + cycle * rod_cycle_period
        end = start + profile_duration
        ax.axvspan(start, end, color="#ef476f", alpha=0.10, label="rod contact window" if cycle == 0 else None)
        ax.axvline(end, color="#d62728", ls="--", lw=0.9, label="rod retracted" if cycle == 0 else None)
    ax.axvline(grasp_time, color="#2ca02c", ls=":", lw=1.0, label="gripper closure")


def _style(ax: plt.Axes, xlabel: str = "Time (s)") -> None:
    ax.grid(True, alpha=0.25, lw=0.6)
    ax.set_xlabel(xlabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _contact_windows(time: np.ndarray, contact: np.ndarray) -> list[tuple[float, float]]:
    """Return contiguous physical-contact windows from the recorded trace."""
    active = np.asarray(contact, dtype=bool)
    starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
    ends = np.flatnonzero(active & ~np.r_[active[1:], False])
    return [(float(time[start]), float(time[end])) for start, end in zip(starts, ends)]


def _rejoin_times(
    time: np.ndarray,
    error_mm: np.ndarray,
    windows: list[tuple[float, float]],
    threshold_mm: float,
    hold_s: float,
) -> list[float | None]:
    """Find the first sustained post-release return inside the error tube."""
    result: list[float | None] = []
    dt = float(np.median(np.diff(time)))
    hold_samples = max(1, int(np.ceil(hold_s / dt)))
    for _, release in windows:
        candidates = np.flatnonzero(time >= release)
        found = None
        for index in candidates:
            end = min(len(error_mm), index + hold_samples)
            if end - index == hold_samples and np.all(error_mm[index:end] <= threshold_mm):
                found = float(time[index])
                break
        result.append(found)
    return result


def _plot_rejoin_trajectory(
    rod: dict[str, np.ndarray],
    no_rod: dict[str, np.ndarray],
    args: argparse.Namespace,
    output_dir: Path,
) -> dict[str, object]:
    """Write a direct WBC-reference/actual trajectory and recovery-time figure."""
    time = rod["time"]
    mask = _window(time, args.time_start, args.time_end)
    t = time[mask]
    nominal = rod["nominal_position"][mask]
    actual = rod["ee_position"][mask]
    baseline = no_rod["ee_position"][mask]
    error_mm = np.linalg.norm(actual - nominal, axis=1) * 1000.0
    windows_all = _contact_windows(time, rod["rod_contact"])
    windows = [(start, end) for start, end in windows_all if end >= args.time_start and start <= (args.time_end or time[-1])]
    rejoin_all = _rejoin_times(time, np.linalg.norm(rod["ee_position"] - rod["nominal_position"], axis=1) * 1000.0, windows, args.rejoin_threshold_mm, args.rejoin_hold_s)

    fig, (axtraj, axerr) = plt.subplots(1, 2, figsize=(13.0, 5.8), gridspec_kw={"width_ratios": (1.15, 1.0)}, constrained_layout=True)
    # A 2D X-Z projection is easier to read than a 3D perspective for this
    # benchmark: X captures the approach direction and Z captures the grasp
    # descent.  The two trajectories are deliberately drawn in the same axes.
    axtraj.plot(nominal[:, 0], nominal[:, 2], color="black", lw=2.2, label="WBC reference (proxy)")
    axtraj.plot(actual[:, 0], actual[:, 2], color="#d81b60", lw=1.6, label="actual EE: rod + VMC")
    axtraj.plot(baseline[:, 0], baseline[:, 2], color="#377eb8", ls="--", lw=1.0, label="no-rod control")
    axtraj.set(xlabel="X (m)", ylabel="Z (m)", title="2D X–Z trajectory: departure and rejoin")
    axtraj.grid(True, alpha=0.25)
    axtraj.set_aspect("equal", adjustable="datalim")
    axtraj.legend(loc="best", frameon=False, fontsize=8)
    for cycle, (start, end) in enumerate(windows):
        onset = int(np.argmin(np.abs(t - start)))
        release = int(np.argmin(np.abs(t - end)))
        axtraj.scatter(actual[onset, 0], actual[onset, 2], c="#ff7f0e", s=34, zorder=5, label="contact onset" if cycle == 0 else None)
        axtraj.scatter(actual[release, 0], actual[release, 2], c="#2ca02c", s=38, marker="x", zorder=5, label="contact release" if cycle == 0 else None)
    for cycle, rejoin in enumerate(rejoin_all, start=1):
        if rejoin is None:
            continue
        index = int(np.argmin(np.abs(t - rejoin)))
        axtraj.scatter(actual[index, 0], actual[index, 2], facecolors="white", edgecolors="#1f77b4", s=48, zorder=6)
        axtraj.annotate(f"R{cycle}", (actual[index, 0], actual[index, 2]), xytext=(4, 4), textcoords="offset points", fontsize=8, color="#1f77b4")

    axerr.plot(t, error_mm, color="#d81b60", lw=1.5, label="‖actual EE − WBC reference‖")
    axerr.axhline(args.rejoin_threshold_mm, color="black", ls="--", lw=1.0, label=f"rejoin tube ({args.rejoin_threshold_mm:.1f} mm)")
    for cycle, ((start, end), rejoin) in enumerate(zip(windows, rejoin_all), start=1):
        axerr.axvspan(start, end, color="#ef476f", alpha=0.10)
        axerr.axvline(end, color="#2ca02c", ls=":", lw=0.9)
        if rejoin is not None:
            axerr.axvline(rejoin, color="#1f77b4", ls="--", lw=0.9)
            axerr.annotate(f"R{cycle}: {rejoin - end:.2f}s", (rejoin, args.rejoin_threshold_mm), xytext=(3, 8), textcoords="offset points", fontsize=7, color="#1f77b4")
    axerr.set(xlabel="Time (s)", ylabel="Position error (mm)", title="Time to return to WBC reference tube")
    axerr.legend(loc="best", frameon=False, fontsize=8)
    axerr.grid(True, alpha=0.25)
    fig.suptitle("2D end-effector trajectory departure and rejoin relative to WBC-reference interface", fontsize=14)
    path = output_dir / "wbc_rejoin_trajectory_results.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return {
        "rejoin_threshold_mm": args.rejoin_threshold_mm,
        "rejoin_hold_s": args.rejoin_hold_s,
        "contact_windows_s": [[start, end] for start, end in windows],
        "rejoin_times_s": rejoin_all,
        "rejoin_latency_s": [None if value is None else value - end for value, (_, end) in zip(rejoin_all, windows)],
        "figure": str(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rod-trace", type=Path, required=True)
    parser.add_argument("--no-rod-trace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rod-start", type=float, default=1.08)
    parser.add_argument("--rod-end", type=float, default=1.72)
    parser.add_argument("--grasp-time", type=float, default=2.30)
    parser.add_argument("--time-start", type=float, default=0.0)
    parser.add_argument("--time-end", type=float, default=None)
    parser.add_argument("--rod-cycles", type=int, default=1)
    parser.add_argument("--rod-cycle-period", type=float, default=0.80)
    parser.add_argument("--rejoin-threshold-mm", type=float, default=5.0, help="Distance tube used to declare return to WBC reference.")
    parser.add_argument("--rejoin-hold-s", type=float, default=0.08, help="Time the error must remain inside the rejoin tube.")
    args = parser.parse_args()

    rod = _load(args.rod_trace)
    no_rod = _load(args.no_rod_trace)
    time = rod["time"]
    mask = _window(time, args.time_start, args.time_end)
    t = time[mask]
    nominal = rod["nominal_position"][mask]
    actual = rod["ee_position"][mask]
    baseline = no_rod["ee_position"][mask]
    nominal_error = np.linalg.norm(actual - nominal, axis=1) * 1000.0
    paired_offset = np.linalg.norm(actual - baseline, axis=1) * 1000.0
    axis_error = (actual - nominal) * 1000.0
    paired_axis = (actual - baseline) * 1000.0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "legend.fontsize": 7})

    fig, axes = plt.subplots(3, 3, figsize=(12.2, 8.3), sharex=True, constrained_layout=True)
    names = ["X", "Y", "Z"]
    for axis, name, index in zip(axes[0], names, range(3)):
        axis.plot(t, nominal[:, index], color="black", lw=1.4, label="WBC reference (proxy)")
        axis.plot(t, actual[:, index], color="#d81b60", lw=1.0, label="rod + VMC")
        axis.plot(t, baseline[:, index], color="#377eb8", lw=0.9, ls="--", label="no-rod control")
        axis.set_title(f"{name} position (m)")
        _shade_events(axis, args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
        _style(axis)
    axes[0, 0].legend(loc="best", frameon=False)

    for axis, name, index in zip(axes[1], names, range(3)):
        axis.plot(t, axis_error[:, index], color="#d81b60", lw=1.0, label="rod − reference")
        axis.plot(t, paired_axis[:, index], color="#377eb8", lw=0.9, ls="--", label="rod − no-rod")
        axis.axhline(0.0, color="black", lw=0.6)
        axis.set_title(f"{name} deviation (mm)")
        _shade_events(axis, args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
        _style(axis)
    axes[1, 0].legend(loc="best", frameon=False)

    axes[2, 0].plot(t, nominal_error, color="#d81b60", lw=1.2)
    axes[2, 0].set_title("‖EE − WBC reference‖ (mm)")
    _shade_events(axes[2, 0], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
    _style(axes[2, 0])
    axes[2, 1].plot(t, paired_offset, color="#377eb8", lw=1.2)
    axes[2, 1].set_title("‖rod EE − no-rod EE‖ (mm)")
    _shade_events(axes[2, 1], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
    _style(axes[2, 1])
    axes[2, 2].plot(t, rod["ee_speed"][mask], color="#ff7f0e", lw=1.0, label="EE speed")
    axes[2, 2].plot(t, rod["rod_force"][mask], color="#2ca02c", lw=1.0, label="rod contact force (N)")
    axes[2, 2].set_title("Motion and contact force")
    _shade_events(axes[2, 2], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
    axes[2, 2].legend(loc="best", frameon=False)
    _style(axes[2, 2])
    fig.suptitle("End-effector trajectory and disturbance error: phase-scheduled 6D VMC", fontsize=13)
    fig.savefig(args.output_dir / "trajectory_error_results.png", dpi=220)
    plt.close(fig)

    fig, axes = plt.subplots(3, 3, figsize=(12.2, 8.3), sharex=True, constrained_layout=True)
    carriage = rod["carriage_displacement"][mask]
    wrench = rod["vmc_wrench"][mask]
    for index, name in enumerate(["Fx", "Fy", "Fz"]):
        axes[0, index].plot(t, wrench[:, index], color="#2ca02c", lw=1.0)
        axes[0, index].set_title(f"{name} (N)")
        _shade_events(axes[0, index], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
        _style(axes[0, index])
    for index, name in enumerate(["Mx", "My", "Mz"]):
        axes[1, index].plot(t, wrench[:, index + 3], color="#9467bd", lw=1.0)
        axes[1, index].set_title(f"{name} (N·m)")
        _shade_events(axes[1, index], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
        _style(axes[1, index])
    for index, name in enumerate(["Δx", "Δy", "Δz"]):
        axes[2, index].plot(t, carriage[:, index] * 1000.0, color="#17becf", lw=1.0)
        axes[2, index].set_title(f"virtual carriage {name} (mm)")
        _shade_events(axes[2, index], args.rod_start, args.rod_end, args.grasp_time, args.rod_cycles, args.rod_cycle_period)
        _style(axes[2, index])
    fig.suptitle("Six-spring virtual wrench and carriage response", fontsize=13)
    fig.savefig(args.output_dir / "six_spring_response_results.png", dpi=220)
    plt.close(fig)

    release = int(np.flatnonzero(time >= args.rod_end)[0])
    before_close = int(np.flatnonzero(time < args.grasp_time)[-1])
    plotted_indices = np.flatnonzero(mask)
    release_local = int(np.flatnonzero(plotted_indices == release)[0])
    before_close_matches = np.flatnonzero(plotted_indices == before_close)
    before_close_local = int(before_close_matches[0]) if len(before_close_matches) else len(plotted_indices) - 1
    metrics = {
        "reference_label": "WBC reference interface (reachable moving-trajectory proxy in this benchmark)",
        "peak_nominal_error_mm": float(np.max(nominal_error)),
        "peak_paired_rod_offset_mm": float(np.max(paired_offset)),
        "error_at_rod_release_mm": float(np.linalg.norm(rod["ee_position"][release] - rod["nominal_position"][release]) * 1000.0),
        "error_before_closure_mm": float(np.linalg.norm(rod["ee_position"][before_close] - rod["nominal_position"][before_close]) * 1000.0),
        "release_to_closure_error_reduction_mm": float(nominal_error[release_local] - nominal_error[before_close_local]),
        "nominal_position_rmse_mm": float(np.sqrt(np.mean(nominal_error**2))),
        "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired_offset**2))),
    }
    rejoin_metrics = _plot_rejoin_trajectory(rod, no_rod, args, args.output_dir)
    metrics["rejoin"] = rejoin_metrics
    (args.output_dir / "trajectory_error_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
