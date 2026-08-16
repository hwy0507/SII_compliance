#!/usr/bin/env python3
"""Pre-select WBC-aware ESNs by Fan Ye-style timescale alignment.

This script reads only deployable robot/WBC state from supplied MuJoCo traces.
The v2 input mode additionally reads measured WBC pose/twist error.  It never
loads contact, rod, force, obstacle or fixture-ID arrays into a candidate ESN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation
from fan_ye_esn_design import (
    FAN_YE_REFERENCE,
    FanYeInputNormalizer,
    deployable_trace_from_arrays,
    evaluate_fan_ye_candidate,
    pareto_frontier,
    random_fan_ye_configs,
)
from fan_ye_esn_rl_adapter import encode_applied_residual_context, encode_wbc_current_feature


DEPLOYABLE_TRACE_KEYS = ("joint_position", "joint_velocity", "wbc_task_twist")
WBC_ERROR_TRACE_KEYS = (
    "joint_position", "joint_velocity", "wbc_task_twist",
    "wbc_pose_error", "wbc_twist_error",
)
WBC_ERROR_ACTION_TRACE_KEYS = WBC_ERROR_TRACE_KEYS + ("wbc_scale", "yield_twist")


def load_trace(path: Path, *, sample_stride: int, input_mode: str) -> np.ndarray:
    if sample_stride < 1:
        raise ValueError("sample_stride must be positive")
    with np.load(path) as archive:
        keys = DEPLOYABLE_TRACE_KEYS if input_mode == "legacy20" else (
            WBC_ERROR_TRACE_KEYS if input_mode == "wbc_error32" else WBC_ERROR_ACTION_TRACE_KEYS
        )
        direct = {
            "joint_position": "joint_position", "joint_velocity": "joint_velocity",
            "wbc_task_twist": "wbc_task_twist", "wbc_pose_error": "wbc_pose_error",
            "wbc_twist_error": "wbc_twist_error",
            "wbc_scale": "wbc_scale", "yield_twist": "yield_twist",
        }
        paired = {
            "joint_position": "rod_joint_position", "joint_velocity": "rod_joint_velocity",
            "wbc_task_twist": "rod_nominal_twist", "wbc_pose_error": "rod_wbc_pose_error",
            "wbc_twist_error": "rod_wbc_twist_error",
            "wbc_scale": "rod_wbc_scale", "yield_twist": "rod_yield_twist",
        }
        mapping = direct if set(direct[key] for key in keys) <= set(archive.files) else paired
        actual_keys = tuple(mapping[key] for key in keys)
        missing = set(actual_keys) - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing deployable trace keys {sorted(missing)}")
        # Explicit key access is an information-flow guard: diagnostics stored
        # beside these arrays are never read by this ESN design procedure.
        legacy = deployable_trace_from_arrays(
            archive[mapping["joint_position"]][::sample_stride],
            archive[mapping["joint_velocity"]][::sample_stride],
            archive[mapping["wbc_task_twist"]][::sample_stride],
        )
        if input_mode == "legacy20":
            return legacy
        pose_error = archive[mapping["wbc_pose_error"]][::sample_stride]
        twist_error = archive[mapping["wbc_twist_error"]][::sample_stride]
        if pose_error.shape != (len(legacy), 6) or twist_error.shape != (len(legacy), 6):
            raise ValueError(f"{path}: invalid WBC error trace shape")
        current = np.asarray([
            encode_wbc_current_feature(
                ESNObservation(row[:7] * 3.0, row[7:14] * 3.0, row[14:20] * np.array([0.60] * 3 + [2.0] * 3)),
                pose, twist,
            )
            for row, pose, twist in zip(legacy, pose_error, twist_error, strict=True)
        ], dtype=float)
        if input_mode == "wbc_error32":
            return current
        wbc_scale = archive[mapping["wbc_scale"]][::sample_stride]
        yield_twist = archive[mapping["yield_twist"]][::sample_stride]
        if wbc_scale.shape != (len(current),) or yield_twist.shape != (len(current), 6):
            raise ValueError(f"{path}: invalid applied residual trace shape")
        context = np.asarray([
            encode_applied_residual_context(scale, twist)
            for scale, twist in zip(wbc_scale, yield_twist, strict=True)
        ], dtype=float)
        return np.concatenate((current, context), axis=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--candidate-count", type=int, default=256)
    parser.add_argument("--dt-s", type=float, default=0.040, help="ESN update interval after trace subsampling.")
    parser.add_argument("--sample-stride", type=int, default=10, help="4 ms MuJoCo trace -> 25 Hz ESN by default.")
    parser.add_argument("--washout-steps", type=int, default=25)
    parser.add_argument("--max-frequency-hz", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--input-mode", choices=("legacy20", "wbc_error32", "wbc_error_action39"), default="legacy20")
    args = parser.parse_args()
    if args.candidate_count < 1 or args.dt_s <= 0.0 or args.max_frequency_hz <= 0.0:
        raise ValueError("candidate-count, dt-s and max-frequency-hz must be positive")
    raw_traces = [load_trace(path, sample_stride=args.sample_stride, input_mode=args.input_mode) for path in args.traces]
    normalizer = FanYeInputNormalizer.from_actuation_traces(raw_traces)
    normalized = [normalizer.transform(trace) for trace in raw_traces]
    metrics = []
    for index, config in enumerate(random_fan_ye_configs(
        args.candidate_count, dt_s=args.dt_s, seed=args.seed, input_dimension=raw_traces[0].shape[1],
    )):
        # Average per-episode dynamics scores. This prevents an episode
        # boundary from becoming an artificial high-frequency transition.
        episode_metrics = [evaluate_fan_ye_candidate(config, trace, candidate_index=index, washout_steps=args.washout_steps, max_frequency_hz=args.max_frequency_hz) for trace in normalized]
        metrics.append(type(episode_metrics[0])(
            containment_ratio=float(np.mean([item.containment_ratio for item in episode_metrics])),
            echo_state_property_index=float(np.mean([item.echo_state_property_index for item in episode_metrics])),
            robot_bandwidth_hz=float(np.mean([item.robot_bandwidth_hz for item in episode_metrics])),
            reservoir_bandwidth_hz=float(np.mean([item.reservoir_bandwidth_hz for item in episode_metrics])),
            candidate_index=index, config=config,
        ))
    frontier = pareto_frontier(metrics)
    output = {
        "schema_version": 1,
        "method": "Fan Ye et al.-inspired robot-reservoir timescale alignment before readout training",
        "citation": FAN_YE_REFERENCE,
        "adaptation": "Robot spectral probe is the WBC-aware deployable trace, detrended to measure dynamics rather than static Panda posture. The error-aware mode is [q, qdot, wbc_task_twist, measured WBC pose error, measured WBC twist error]; the closed-loop mode appends only the previous shared-safety-filtered residual command. Candidate reservoir receives the same normalized trace. CR is compared by frequency containment and ESPI by post-washout state MSE across random initial states.",
        "information_boundary": {
            "input_mode": args.input_mode,
            "read_trace_keys": list(DEPLOYABLE_TRACE_KEYS if args.input_mode == "legacy20" else (WBC_ERROR_TRACE_KEYS if args.input_mode == "wbc_error32" else WBC_ERROR_ACTION_TRACE_KEYS)),
            "excluded": ["rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "contact_normal", "future_release", "fixture_id"],
        },
        "input_trace_count": len(normalized),
        "input_trace_paths": [str(path) for path in args.traces],
        "normalizer_absolute_median_scales": normalizer.scales.tolist(),
        "sampling": {"dt_s": args.dt_s, "sample_stride": args.sample_stride, "washout_steps": args.washout_steps, "max_frequency_hz": args.max_frequency_hz},
        "candidate_count": len(metrics),
        "pareto_frontier_count": len(frontier),
        "candidates": [item.as_dict() for item in sorted(metrics, key=lambda item: item.candidate_index)],
        "pareto_frontier_ranked": [item.as_dict() for item in frontier],
        "selection_rule": "Do not train a readout until reservoir preselection is frozen. Choose among CR-high/ESPI-low Pareto candidates using only the ESN validation split; do not reuse the WBC-aware V4 final test.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "candidate_count": len(metrics), "pareto_frontier_count": len(frontier),
        "best_containment_ratio": frontier[0].containment_ratio if frontier else None,
        "best_espi": min(item.echo_state_property_index for item in metrics),
        "output_json": str(args.output_json),
    }, indent=2))


if __name__ == "__main__":
    main()
