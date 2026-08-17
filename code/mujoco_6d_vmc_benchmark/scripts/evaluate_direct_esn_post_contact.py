#!/usr/bin/env python3
"""Matched post-contact benchmark for fixed WBC versus Direct ESN.

The benchmark separates the first contact impulse from the response after
contact.  It is deliberately an offline evaluator: contact force is read from
the saved rollout trace and is never part of the Direct ESN online input.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from run_direct_esn_mujoco import run_episode


def _stable_rejoin_time(time_s: np.ndarray, deviation_m: np.ndarray, start_s: float, threshold_m: float, window: int) -> float | None:
    eligible = np.flatnonzero(time_s >= start_s)
    for index in eligible:
        end = index + window
        if end <= len(deviation_m) and np.all(deviation_m[index:end] <= threshold_m):
            return float(time_s[index])
    return None


def _trapezoid_area(values: np.ndarray, time_s: np.ndarray) -> float:
    """Version-independent trapezoid integration for NumPy 2.x runtimes."""

    if len(values) < 2:
        return 0.0
    return float(np.sum(0.5 * (values[1:] + values[:-1]) * np.diff(time_s)))


def phase_metrics(
    info: dict[str, Any], trace: dict[str, np.ndarray], *, contact_threshold_n: float = 0.20,
    rejoin_threshold_m: float = 0.005, rejoin_window_steps: int = 3,
) -> dict[str, Any]:
    time_s = np.asarray(trace["time_s"], dtype=float)
    force_n = np.asarray(trace["contact_force"], dtype=float)
    ee = np.asarray(trace["ee_position"], dtype=float)
    nominal = np.asarray(trace["nominal_position"], dtype=float)
    impulse_delta_ns = np.asarray(trace["contact_impulse_delta_ns"], dtype=float)
    deviation_m = np.linalg.norm(ee - nominal, axis=1)
    contact = force_n >= contact_threshold_n
    dt = float(np.median(np.diff(time_s))) if len(time_s) > 1 else 0.04
    onset_indices = np.flatnonzero(contact)
    onset_s = None if len(onset_indices) == 0 else float(time_s[onset_indices[0]])
    last_contact_index = None if len(onset_indices) == 0 else int(onset_indices[-1])
    release_s = None if last_contact_index is None else float(time_s[last_contact_index] + dt)
    grasp_s = float(info["fixture"]["grasp_time_s"])
    scheduled_release_s = float(info["fixture"]["rod_start_time_s"]) + 0.64
    post_mask = np.zeros(len(time_s), dtype=bool) if release_s is None else (time_s >= release_s) & (time_s < grasp_s)
    rejoin_s = None if release_s is None else _stable_rejoin_time(
        time_s, deviation_m, release_s, rejoin_threshold_m, rejoin_window_steps,
    )
    metrics: dict[str, Any] = {
        "task_success": bool(info["task_success"]),
        "effective_collision": bool(info["effective_collision"]),
        "hard_torque_limit": bool(info["hard_torque_limit"]),
        "contact_onset_s": onset_s,
        "contact_release_s": release_s,
        "contact_duration_s": float(np.sum(contact) * dt),
        "peak_contact_force_n": float(np.max(force_n)) if len(force_n) else 0.0,
        "contact_impulse_ns": float(np.sum(impulse_delta_ns)),
        "peak_deviation_mm": float(1000.0 * np.max(deviation_m)) if len(deviation_m) else 0.0,
        "post_contact_rmse_mm": None if not np.any(post_mask) else float(1000.0 * np.sqrt(np.mean(deviation_m[post_mask] ** 2))),
        "post_contact_iae_mm_s": None if not np.any(post_mask) else float(1000.0 * _trapezoid_area(deviation_m[post_mask], time_s[post_mask])),
        "post_contact_peak_deviation_mm": None if not np.any(post_mask) else float(1000.0 * np.max(deviation_m[post_mask])),
        "rejoin_time_s": rejoin_s,
        "release_to_rejoin_latency_s": None if rejoin_s is None or release_s is None else float(rejoin_s - release_s),
        "scheduled_impactor_release_s": scheduled_release_s,
        "scheduled_release_to_rejoin_latency_s": None if rejoin_s is None else float(rejoin_s - scheduled_release_s),
        "peak_torque_nm": float(info["peak_torque_nm"]),
        "peak_jerk_mps3": float(info["peak_jerk_mps3"]),
        "peak_recovery_jerk_mps3": float(info["peak_recovery_jerk_mps3"]),
        "mean_wbc_slowdown": float(info["mean_wbc_slowdown"]),
        "mean_yield_twist_norm": float(info["mean_yield_twist_norm"]),
    }
    return metrics


def _trace_arrays(trace: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    keys = (
        "time_s", "wbc_scale", "yielding_twist", "raw_readout", "bounded_action", "pose_error",
        "ee_position", "nominal_position", "contact_force", "contact_seen", "contact_penetration_m",
        "contact_impulse_delta_ns",
    )
    return {key: np.asarray([item[key] for item in trace]) for key in keys}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller", type=Path, required=True)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--contact-threshold-n", type=float, default=0.20)
    parser.add_argument("--rejoin-threshold-mm", type=float, default=5.0)
    parser.add_argument("--rejoin-window-steps", type=int, default=3)
    args = parser.parse_args()
    if args.rejoin_window_steps < 1 or args.contact_threshold_n <= 0.0 or args.rejoin_threshold_mm <= 0.0:
        raise ValueError("benchmark thresholds must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    common = dict(menagerie=args.menagerie, fan_ye_model=None, fan_ye_summary=None, fixture_index=args.fixture_index, rod_enabled=True, seed=args.seed)
    fixed_info, fixed_trace = run_episode(None, **common, fixed_wbc=True)
    esn_info, esn_trace = run_episode(args.controller, **common, fixed_wbc=False)
    thresholds = dict(
        contact_threshold_n=args.contact_threshold_n,
        rejoin_threshold_mm=args.rejoin_threshold_mm,
        rejoin_window_steps=args.rejoin_window_steps,
    )
    metric_kwargs = dict(
        contact_threshold_n=args.contact_threshold_n,
        rejoin_threshold_m=args.rejoin_threshold_mm / 1000.0,
        rejoin_window_steps=args.rejoin_window_steps,
    )
    result = {
        "schema_version": 1,
        "method": "matched_post_contact_fixed_wbc_vs_direct_esn",
        "fixture_index": args.fixture_index,
        "seed": args.seed,
        "thresholds": thresholds,
        "fixed_wbc": phase_metrics(fixed_info, _trace_arrays(fixed_trace), **metric_kwargs),
        "direct_esn": phase_metrics(esn_info, _trace_arrays(esn_trace), **metric_kwargs),
    }
    for name, trace in (("fixed_wbc", fixed_trace), ("direct_esn", esn_trace)):
        np.savez_compressed(args.output_dir / f"{name}_trace.npz", **_trace_arrays(trace))
    (args.output_dir / "post_contact_benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
