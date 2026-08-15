#!/usr/bin/env python3
"""Pre-select WBC-aware ESNs by Fan Ye-style timescale alignment.

This script reads only ``joint_position``, ``joint_velocity`` and
``wbc_task_twist`` from supplied MuJoCo traces.  It does not load contact,
rod, force, obstacle or fixture-ID arrays into a candidate ESN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fan_ye_esn_design import (
    FAN_YE_REFERENCE,
    FanYeInputNormalizer,
    deployable_trace_from_arrays,
    evaluate_fan_ye_candidate,
    pareto_frontier,
    random_fan_ye_configs,
)


DEPLOYABLE_TRACE_KEYS = ("joint_position", "joint_velocity", "wbc_task_twist")


def load_trace(path: Path, *, sample_stride: int) -> np.ndarray:
    if sample_stride < 1:
        raise ValueError("sample_stride must be positive")
    with np.load(path) as archive:
        missing = set(DEPLOYABLE_TRACE_KEYS) - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing deployable trace keys {sorted(missing)}")
        # Explicit key access is an information-flow guard: diagnostics stored
        # beside these arrays are never read by this ESN design procedure.
        return deployable_trace_from_arrays(
            archive["joint_position"][::sample_stride],
            archive["joint_velocity"][::sample_stride],
            archive["wbc_task_twist"][::sample_stride],
        )


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
    args = parser.parse_args()
    if args.candidate_count < 1 or args.dt_s <= 0.0 or args.max_frequency_hz <= 0.0:
        raise ValueError("candidate-count, dt-s and max-frequency-hz must be positive")
    raw_traces = [load_trace(path, sample_stride=args.sample_stride) for path in args.traces]
    normalizer = FanYeInputNormalizer.from_actuation_traces(raw_traces)
    normalized = [normalizer.transform(trace) for trace in raw_traces]
    metrics = []
    for index, config in enumerate(random_fan_ye_configs(args.candidate_count, dt_s=args.dt_s, seed=args.seed)):
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
        "adaptation": "Robot spectral probe is the WBC-aware 20-D deployable proprioceptive trace [q, qdot, wbc_task_twist], detrended to measure dynamics rather than static Panda posture. Candidate reservoir receives the same normalized trace. CR is compared by frequency containment and ESPI by post-washout state MSE across random initial states.",
        "information_boundary": {
            "read_trace_keys": list(DEPLOYABLE_TRACE_KEYS),
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
