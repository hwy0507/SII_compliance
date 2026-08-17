#!/usr/bin/env python3
"""Evaluate a frozen Direct ESN readout on a deployable trace archive.

This evaluator is deliberately trace-level: it verifies that the deployed
student can reproduce privileged teacher actions without reading any teacher
fields.  Closed-loop MuJoCo metrics are added by the later rollout adapter.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNController
from esn_compliance import ESNObservation


def evaluate(model_path: Path, trace_path: Path, *, washout_steps: int = 0, sample_stride: int = 1) -> dict:
    model = DirectESNController.from_npz(model_path)
    with np.load(trace_path, allow_pickle=False) as archive:
        required = {"joint_position", "joint_velocity", "wbc_task_twist", "teacher_action"}
        missing = required - set(archive.files)
        if missing:
            raise ValueError(f"{trace_path}: missing required fields {sorted(missing)}")
        index = slice(None, None, sample_stride)
        q = np.asarray(archive["joint_position"], dtype=float)[index]
        qdot = np.asarray(archive["joint_velocity"], dtype=float)[index]
        twist = np.asarray(archive["wbc_task_twist"], dtype=float)[index]
        target = np.asarray(archive["teacher_action"], dtype=float)[index]
    if q.shape != (len(q), 7) or qdot.shape != q.shape or twist.shape != (len(q), 6) or target.shape != (len(q), 7):
        raise ValueError("invalid deployable trace dimensions")
    observations = [ESNObservation(qi, qdoti, twisti) for qi, qdoti, twisti in zip(q, qdot, twist)]
    model.reset()
    predictions = []
    scales = []
    yields = []
    saturation = []
    for observation in observations:
        action = model.act(observation.joint_position, observation.joint_velocity, observation.wbc_task_twist)
        predictions.append(action.bounded_filter_action)
        scales.append(action.wbc_scale)
        yields.append(action.yielding_twist)
        saturation.append(np.abs(action.raw_readout) > 2.0)
    predictions = np.asarray(predictions)
    target = np.clip(target, -1.0, 1.0)
    start = min(max(washout_steps, 0), len(predictions))
    error = predictions[start:] - target[start:]
    return {
        "method": "direct_esn_compliant_controller",
        "model": str(model_path),
        "trace": str(trace_path),
        "samples": int(len(predictions)),
        "washout_steps": int(start),
        "teacher_student_action_mse": float(np.mean(error ** 2)) if len(error) else float("nan"),
        "teacher_student_action_mae": float(np.mean(np.abs(error))) if len(error) else float("nan"),
        "action_saturation_fraction": float(np.mean(np.asarray(saturation))) if saturation else 0.0,
        "mean_wbc_scale": float(np.mean(scales)) if scales else 1.0,
        "minimum_wbc_scale": float(np.min(scales)) if scales else 1.0,
        "mean_yield_twist_norm": float(np.mean(np.linalg.norm(yields, axis=1))) if yields else 0.0,
        "max_yield_twist_norm": float(np.max(np.linalg.norm(yields, axis=1))) if yields else 0.0,
        "student_input_fields": ["joint_position", "joint_velocity", "wbc_task_twist"],
        "privileged_fields_used_online": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--washout-steps", type=int, default=25)
    parser.add_argument("--sample-stride", type=int, default=1)
    args = parser.parse_args()
    result = evaluate(args.model, args.trace, washout_steps=args.washout_steps, sample_stride=args.sample_stride)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

