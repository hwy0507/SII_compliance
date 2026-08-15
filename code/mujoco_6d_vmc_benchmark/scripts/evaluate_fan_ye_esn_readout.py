#!/usr/bin/env python3
"""Evaluate a fitted Fan-Ye ESN readout on held-out teacher traces only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer
from train_fan_ye_esn_readout import GatedVMCTeacherConfig, load_episode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--sample-stride", type=int, default=10)
    parser.add_argument("--washout-steps", type=int, default=25)
    args = parser.parse_args()
    summary = json.loads(args.train_summary_json.read_text())
    config = FanYeESNConfig(**summary["config"])
    teacher_config = GatedVMCTeacherConfig(**summary["teacher"]["config"])
    with np.load(args.model_npz) as archive:
        normalizer = FanYeInputNormalizer(archive["input_normalizer_scales"])
        readout = archive["readout"]
    episodes = []
    all_error = []
    for path in args.traces:
        trace, teacher = load_episode(path, sample_stride=args.sample_stride, teacher_config=teacher_config)
        model = FanYeAlignedESN(config)
        model.set_readout(readout)
        normalized = normalizer.transform(trace)
        predictions = np.asarray([model.action(row) for row in normalized], dtype=float)
        error = predictions[args.washout_steps:] - teacher[args.washout_steps:]
        mse = float(np.mean(error ** 2))
        episodes.append({"path": str(path), "samples_after_washout": len(error), "teacher_mse": mse, "prediction_abs_max": float(np.max(np.abs(predictions)))})
        all_error.append(error)
    merged = np.concatenate(all_error)
    result = {
        "schema_version": 1,
        "stage": "held-out analytic-teacher readout generalization only",
        "student_input": summary["student_input"],
        "student_excludes": summary["student_excludes"],
        "candidate_index": summary["candidate_index"],
        "teacher_config": summary["teacher"]["config"],
        "training_teacher_mse": summary["readout_training_mse"],
        "validation_teacher_mse": float(np.mean(merged ** 2)),
        "episodes": episodes,
        "warning": "This is teacher-action MSE on held-out traces, not a closed-loop task, collision, torque, or tracking benchmark.",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"validation_teacher_mse": result["validation_teacher_mse"], "episodes": len(episodes), "output_json": str(args.output_json)}, indent=2))


if __name__ == "__main__":
    main()
