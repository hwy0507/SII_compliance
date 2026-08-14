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


CONTACT_WINDOW_MERGE_S = 0.020


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
    """Return physical-contact windows, merging solver-scale gaps (<=20 ms)."""
    active = np.asarray(contact, dtype=bool)
    starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
    ends = np.flatnonzero(active & ~np.r_[active[1:], False])
    raw = [(float(time[start]), float(time[end])) for start, end in zip(starts, ends)]
    if not raw:
        return []
    merged = [raw[0]]
    for start, end in raw[1:]:
        previous_start, previous_end = merged[-1]
        if start - previous_end <= CONTACT_WINDOW_MERGE_S:
            merged[-1] = (previous_start, end)
        else:
            merged.append((start, end))
    return merged


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


def _dominant_paired_axis(rod: dict[str, np.ndarray], no_rod: dict[str, np.ndarray]) -> int:
    """Return the Cartesian axis carrying the largest rod-induced offset."""
    delta = np.asarray(rod["ee_position"]) - np.asarray(no_rod["ee_position"])
    return int(np.argmax(np.max(np.abs(delta), axis=0)))


def _phase_label(value: int) -> str:
    return {
        0: "approach",
        1: "contact",
        2: "unloading",
        3: "rejoined",
        4: "task / hold",
    }.get(int(value), "unknown")


def _phase_colors() -> dict[str, str]:
    return {
        "approach": "#d9eaf7",
        "contact": "#f8c8d4",
        "unloading": "#fce5b5",
        "rejoined": "#c9e7d2",
        "task / hold": "#e5e5e5",
        "unknown": "#eeeeee",
    }


def _plot_compliance_phase_zoom(
    rod: dict[str, np.ndarray],
    no_rod: dict[str, np.ndarray],
    args: argparse.Namespace,
    output_dir: Path,
    rejoin: dict[str, object],
) -> dict[str, object]:
    """Make a local, causal view of yielding and recovery.

    This figure intentionally uses the axis that actually separates the rod and
    no-rod trials.  It is a presentation view; the full-episode plots remain
    available for audit and metric reproduction.
    """
    time = rod["time"]
    start = args.compliance_zoom_start
    end = args.compliance_zoom_end
    mask = _window(time, start, end)
    t = time[mask]
    nominal = rod["nominal_position"][mask]
    actual = rod["ee_position"][mask]
    no_rod_position = no_rod["ee_position"][mask]
    paired = (actual - no_rod_position) * 1000.0
    nominal_delta = (actual - nominal) * 1000.0
    dominant = _dominant_paired_axis(rod, no_rod)
    lateral = dominant
    # Use Z as the second coordinate when the collision is lateral; otherwise
    # choose the largest remaining nominal-motion axis for a readable path.
    vertical = 2 if lateral != 2 else int(np.argmax(np.ptp(nominal, axis=0) * (np.arange(3) != lateral)))
    names = ["X", "Y", "Z"]
    windows = [(float(a), float(b)) for a, b in rejoin["contact_windows_s"]]
    rejoin_times = rejoin["rejoin_times_s"]

    explicit_force = rod.get("explicit_carriage_force", np.zeros((len(time), 3)))[mask]
    wrench = rod["vmc_wrench"][mask]
    spring_force = explicit_force if np.any(np.abs(explicit_force) > 1e-10) else wrench[:, :3]
    carriage = rod.get("carriage_displacement", np.zeros((len(time), 6)))[mask] * 1000.0
    force = rod["rod_force"][mask]
    speed = rod["ee_speed"][mask]
    colors = _phase_colors()

    fig, axes = plt.subplots(
        5, 1, figsize=(11.5, 13.0), sharex=False,
        gridspec_kw={"height_ratios": (2.0, 1.35, 1.35, 1.35, 0.34)},
        constrained_layout=True,
    )
    ax_path, ax_delta, ax_force, ax_motion, ax_phase = axes

    # 2-D path: the no-rod paired trial is the nominal closed-loop behavior,
    # while the black curve is the moving WBC-reference interface.
    ax_path.plot(nominal[:, lateral], nominal[:, vertical], color="black", lw=2.0, label="WBC reference (proxy)")
    ax_path.plot(no_rod_position[:, lateral], no_rod_position[:, vertical], color="#377eb8", ls="--", lw=1.5, label="no-rod control")
    ax_path.plot(actual[:, lateral], actual[:, vertical], color="#d81b60", lw=2.0, label="rod-perturbed control")
    ax_path.scatter(actual[0, lateral], actual[0, vertical], color="#555555", s=22, zorder=5, label="zoom start")
    ax_path.scatter(actual[-1, lateral], actual[-1, vertical], facecolors="white", edgecolors="#1f77b4", s=42, zorder=5, label="zoom end")
    for index, (contact_start, contact_end) in enumerate(windows):
        if contact_end < start or contact_start > end:
            continue
        onset = int(np.argmin(np.abs(t - contact_start)))
        release = int(np.argmin(np.abs(t - contact_end)))
        ax_path.scatter(actual[onset, lateral], actual[onset, vertical], color="#e45756", s=34, zorder=6, label="contact onset" if index == 0 else None)
        ax_path.scatter(actual[release, lateral], actual[release, vertical], color="#2a9d8f", marker="x", s=48, zorder=6, label="contact release" if index == 0 else None)
    for index, stamp in enumerate(rejoin_times):
        if stamp is None or not (start <= float(stamp) <= end):
            continue
        rejoin_index = int(np.argmin(np.abs(t - float(stamp))))
        ax_path.scatter(actual[rejoin_index, lateral], actual[rejoin_index, vertical], facecolors="white", edgecolors="#1f77b4", s=50, zorder=7, label="rejoined tube" if index == 0 else None)
    ax_path.set_xlabel(f"{names[lateral]} (m)")
    ax_path.set_ylabel(f"{names[vertical]} (m)")
    ax_path.set_title(f"2-D local trajectory ({names[lateral]}–{names[vertical]}): yielding and recovery")
    ax_path.grid(True, alpha=0.25)
    ax_path.legend(loc="best", frameon=False, ncol=2, fontsize=8)

    # The paired difference is the collision-induced displacement, separated
    # from nominal tracking error.
    ax_delta.plot(t, paired[:, lateral], color="#d81b60", lw=2.0, label=f"Δ{names[lateral]} = rod − no-rod")
    ax_delta.plot(t, nominal_delta[:, lateral], color="#9467bd", lw=1.1, ls=":", label=f"{names[lateral]} error to WBC proxy")
    ax_delta.axhline(0.0, color="black", lw=0.7)
    ax_delta.set_ylabel(f"Δ{names[lateral]} (mm)")
    ax_delta.set_title("Collision-induced lateral offset (paired rod − no-rod) and reference error")
    ax_delta.legend(loc="best", frameon=False, ncol=2, fontsize=8)

    ax_force.plot(t, force, color="#e45756", lw=1.8, label="physical rod–hand force")
    ax_force.plot(t, spring_force[:, lateral], color="#2a9d8f", lw=1.4, label=f"virtual spring F{names[lateral]}")
    ax_force.axhline(0.0, color="black", lw=0.7)
    ax_force.set_ylabel("Force (N)")
    ax_force.set_title("Causal link 1: physical impact force → virtual spring reaction")
    ax_force.legend(loc="best", frameon=False, ncol=2, fontsize=8)

    carriage_line = ax_motion.plot(t, carriage[:, lateral], color="#17becf", lw=2.0, label=f"virtual carriage Δ{names[lateral]}")
    ax_motion.axhline(0.0, color="black", lw=0.7)
    ax_motion.set_ylabel("carriage displacement (mm)", color="#17becf")
    ax_motion.tick_params(axis="y", labelcolor="#17becf")
    speed_axis = ax_motion.twinx()
    speed_line = speed_axis.plot(t, speed * 1000.0, color="#ff9f1c", lw=1.2, label="EE speed")
    speed_axis.set_ylabel("EE speed (mm/s)", color="#ff9f1c")
    speed_axis.tick_params(axis="y", labelcolor="#ff9f1c")
    speed_axis.spines["top"].set_visible(False)
    ax_motion.set_title("Causal link 2: spring/carriage yielding → end-effector motion")
    ax_motion.legend(carriage_line + speed_line, [line.get_label() for line in carriage_line + speed_line], loc="best", frameon=False, ncol=2, fontsize=8)

    # Phase ribbon gives the reader the event order without hiding short phases.
    phase = rod.get("phase")
    if phase is None:
        phase = np.zeros(len(time), dtype=np.int8)
        for a, b in windows:
            phase[(time >= a) & (time <= b)] = 1
    phase = np.asarray(phase)[mask]
    boundaries = np.flatnonzero(phase[1:] != phase[:-1]) + 1
    indices = np.r_[0, boundaries, len(phase)]
    for left, right in zip(indices[:-1], indices[1:]):
        label = _phase_label(phase[left])
        ax_phase.axvspan(t[left], t[right - 1], color=colors[label], alpha=0.95)
        if right - left > 2:
            ax_phase.text((t[left] + t[right - 1]) / 2, 0.5, label, ha="center", va="center", fontsize=8)
    ax_phase.set_ylim(0, 1)
    ax_phase.set_yticks([])
    ax_phase.set_xlabel("Time (s)")
    ax_phase.set_title("phase sequence", fontsize=9, loc="left")

    # Only the time-series panels share the event window.  The trajectory
    # panel must retain its own Cartesian x-axis; sharing it with time would
    # collapse the path into a misleading vertical line.
    ax_path.set_aspect("auto")
    for axis in axes[1:]:
        axis.set_xlim(start, end)

    for axis in axes[1:4]:
        for a, b in windows:
            if b >= start and a <= end:
                axis.axvspan(max(a, start), min(b, end), color="#ef476f", alpha=0.10, zorder=0)
                axis.axvline(b, color="#2ca02c", ls=":", lw=1.0)
        for stamp in rejoin_times:
            if stamp is not None and start <= float(stamp) <= end:
                axis.axvline(float(stamp), color="#1f77b4", ls="--", lw=1.0)
                axis.annotate("rejoin", (float(stamp), 0.96), xycoords=("data", "axes fraction"), rotation=90, va="top", fontsize=8, color="#1f77b4")
        _style(axis)
    fig.suptitle(
        f"Compliance phase zoom: dominant {names[lateral]}-axis | contact → unloading → rejoin",
        fontsize=14,
    )
    path = output_dir / "compliance_phase_zoom_results.png"
    fig.savefig(path, dpi=240)
    plt.close(fig)
    return {
        "figure": str(path),
        "zoom_window_s": [float(start), float(end)],
        "dominant_paired_axis": names[lateral],
        "secondary_path_axis": names[vertical],
        "peak_paired_axis_offset_mm": float(np.max(np.abs(paired[:, lateral]))),
        "peak_spring_force_n": float(np.max(np.abs(spring_force[:, lateral]))),
    }


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
    axtraj.plot(actual[:, 0], actual[:, 2], color="#d81b60", lw=1.6, label="actual EE: rod-perturbed control")
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


def _plot_rejoin_dynamics(
    rod: dict[str, np.ndarray],
    no_rod: dict[str, np.ndarray],
    args: argparse.Namespace,
    output_dir: Path,
    rejoin: dict[str, object],
) -> dict[str, object]:
    """Plot velocity, physical contact, virtual wrench, and motor torque together."""
    time = rod["time"]
    mask = _window(time, args.time_start, args.time_end)
    t = time[mask]
    wrench = rod["vmc_wrench"][mask]
    explicit_force = rod.get("explicit_carriage_force", np.zeros((len(time), 3)))[mask]
    explicit_moment = rod.get("explicit_carriage_moment", np.zeros((len(time), 3)))[mask]
    use_explicit_translation = bool(np.any(np.abs(explicit_force) > 1e-10))
    use_explicit_rotation = bool(np.any(np.abs(explicit_moment) > 1e-10))
    translation_force = explicit_force if use_explicit_translation else wrench[:, :3]
    motor_torque = rod["torque_applied"][mask]
    windows = [(float(start), float(end)) for start, end in rejoin["contact_windows_s"]]
    rejoin_times = rejoin["rejoin_times_s"]

    def mark_events(axis: plt.Axes, include_legend: bool = False) -> None:
        for index, (start, end) in enumerate(windows):
            axis.axvspan(start, end, color="#ef476f", alpha=0.10, label="physical rod contact" if include_legend and index == 0 else None)
            axis.axvline(end, color="#2ca02c", ls=":", lw=0.9, label="contact release" if include_legend and index == 0 else None)
        for index, stamp in enumerate(rejoin_times):
            if stamp is not None:
                axis.axvline(float(stamp), color="#1f77b4", ls="--", lw=0.9, label="rejoined reference tube" if include_legend and index == 0 else None)

    fig, axes = plt.subplots(3, 2, figsize=(13.0, 10.2), sharex=True, constrained_layout=True)
    ax_speed, ax_force_norm, ax_force_channels, ax_moment_channels, ax_joint_1_4, ax_joint_5_7 = axes.flat
    speed = rod["ee_speed"][mask]
    speed_no_rod = no_rod["ee_speed"][mask]
    ax_speed.plot(t, speed, color="#d81b60", lw=1.3, label="rod-perturbed control")
    ax_speed.plot(t, speed_no_rod, color="#377eb8", lw=1.0, ls="--", label="no-rod control")
    ax_speed.set(ylabel="EE speed (m/s)", title="End-effector speed: check for surge")
    mark_events(ax_speed, include_legend=True)
    ax_speed.legend(loc="best", frameon=False, fontsize=8)

    virtual_force_norm = np.linalg.norm(translation_force, axis=1)
    ax_force_norm.plot(t, rod["rod_force"][mask], color="#2ca02c", lw=1.3, label="physical rod–hand force")
    ax_force_norm.plot(t, virtual_force_norm, color="#9467bd", lw=1.1, label="‖virtual spring force‖")
    ax_force_norm.set(ylabel="Force (N)", title="Physical contact and virtual restoring force")
    mark_events(ax_force_norm, include_legend=True)
    ax_force_norm.legend(loc="best", frameon=False, fontsize=8)

    force_label = "explicit-carriage" if use_explicit_translation else "virtual"
    for channel, color, label in zip(range(3), ("#e41a1c", "#377eb8", "#4daf4a"), ("Fx", "Fy", "Fz")):
        ax_force_channels.plot(t, translation_force[:, channel], color=color, lw=1.0, label=label)
    ax_force_channels.axhline(0.0, color="black", lw=0.6)
    ax_force_channels.set(ylabel="Spring force (N)", title=f"Translational channels ({force_label})")
    mark_events(ax_force_channels)
    ax_force_channels.legend(loc="best", frameon=False, ncol=3, fontsize=8)

    rotational_moment = explicit_moment if use_explicit_rotation else wrench[:, 3:]
    moment_label = "explicit-carriage" if use_explicit_rotation else "virtual"
    for channel, color, label in zip(range(3), ("#e41a1c", "#377eb8", "#4daf4a"), ("Mx", "My", "Mz")):
        ax_moment_channels.plot(t, rotational_moment[:, channel], color=color, lw=1.0, label=label)
    ax_moment_channels.axhline(0.0, color="black", lw=0.6)
    ax_moment_channels.set(ylabel="Spring moment (N·m)", title=f"Six-spring rotational channels ({moment_label})")
    mark_events(ax_moment_channels)
    ax_moment_channels.legend(loc="best", frameon=False, ncol=3, fontsize=8)

    for joint in range(4):
        ax_joint_1_4.plot(t, motor_torque[:, joint], lw=0.9, label=f"J{joint + 1}")
    ax_joint_1_4.set(ylabel="Motor torque (N·m)", title="Applied motor torque: proximal joints")
    mark_events(ax_joint_1_4)
    ax_joint_1_4.legend(loc="best", frameon=False, ncol=2, fontsize=8)

    for joint in range(4, 7):
        ax_joint_5_7.plot(t, motor_torque[:, joint], lw=0.9, label=f"J{joint + 1}")
    ax_joint_5_7.set(ylabel="Motor torque (N·m)", title="Applied motor torque: distal joints")
    mark_events(ax_joint_5_7)
    ax_joint_5_7.legend(loc="best", frameon=False, ncol=3, fontsize=8)

    for axis in axes.flat:
        _style(axis)
    fig.suptitle("Dynamic response during WBC-reference departure and rejoin", fontsize=14)
    path = output_dir / "wbc_rejoin_dynamics_results.png"
    fig.savefig(path, dpi=220)
    plt.close(fig)
    return {
        "peak_ee_speed_mps": float(np.max(speed)),
        "peak_no_rod_ee_speed_mps": float(np.max(speed_no_rod)),
        "peak_physical_contact_force_n": float(np.max(rod["rod_force"][mask])),
        "peak_virtual_force_n": float(np.max(virtual_force_norm)),
        "peak_virtual_moment_nm": float(np.max(np.linalg.norm(rotational_moment, axis=1))),
        "peak_applied_motor_torque_nm": float(np.max(np.abs(motor_torque))),
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
    parser.add_argument("--compliance-zoom-start", type=float, default=1.10, help="Start of the local yielding/recovery presentation view.")
    parser.add_argument("--compliance-zoom-end", type=float, default=1.90, help="End of the local yielding/recovery presentation view.")
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
    metrics["dynamic_response"] = _plot_rejoin_dynamics(rod, no_rod, args, args.output_dir, rejoin_metrics)
    metrics["compliance_phase_zoom"] = _plot_compliance_phase_zoom(rod, no_rod, args, args.output_dir, rejoin_metrics)
    (args.output_dir / "trajectory_error_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
