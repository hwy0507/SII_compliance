#!/usr/bin/env python3
"""Check the fixed Fan Ye ESN actor-input interface on physical WBC traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation
from fan_ye_esn_rl_adapter import FanYeESNRLObservationAdapter


def transform_trace(adapter: FanYeESNRLObservationAdapter, path: Path, *, stride: int) -> np.ndarray:
    with np.load(path) as archive:
        required = {"joint_position", "joint_velocity", "wbc_task_twist"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing deployable fields {sorted(missing)}")
        q, qdot, twist = (archive[key][::stride] for key in ("joint_position", "joint_velocity", "wbc_task_twist"))
    adapter.reset()
    return np.asarray([adapter.observe(ESNObservation(qi, qdoti, ti)) for qi, qdoti, ti in zip(q, qdot, twist)], dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--train-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--validation-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=10)
    args = parser.parse_args()
    if args.stride < 1:
        raise ValueError("stride must be positive")
    adapter = FanYeESNRLObservationAdapter(args.model_npz, args.train_summary_json)
    def summarize(paths: list[Path]) -> dict:
        features = [transform_trace(adapter, path, stride=args.stride) for path in paths]
        stacked = np.concatenate(features)
        return {"trace_count": len(features), "samples": int(len(stacked)), "feature_shape": list(stacked.shape), "finite": bool(np.all(np.isfinite(stacked))), "feature_abs_max": float(np.max(np.abs(stacked)))}
    result = {"stage": "Fan Ye ESN WBC-aware RL-interface smoke only; no RL optimization", "actor_input": list(adapter.student_input_fields), "actor_excludes": list(adapter.excluded_fields), "feature_dimension": adapter.feature_dimension, "reservoir_state_dimension": adapter.reservoir.config.reservoir_size, "train": summarize(args.train_traces), "validation": summarize(args.validation_traces), "warning": "This verifies the deployable ESN actor feature interface on physical traces. It is not an RL training, reward, or performance claim."}
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
