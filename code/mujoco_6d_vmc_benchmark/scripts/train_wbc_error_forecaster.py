#!/usr/bin/env python3
"""Fit and validate a causal Fan Ye ESN future WBC-error predictor.

The predictor maps the 32-D deployable state at time t to the normalized WBC
pose error at t + 120 ms.  Its targets are used only while fitting/evaluating
the forecast model on the isolated post-V4 development splits.  At deployment
the actor receives the ESN prediction, never future simulator state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from esn_compliance import ESNObservation
from fan_ye_esn_rl_adapter import (
    FORECAST_HORIZON_S,
    WBC_POSE_ERROR_SCALE,
    FixedErrorForecaster,
    encode_kinematic_pose_forecast,
    encode_wbc_current_feature,
)


RL_DT = 0.040
FORECAST_STEPS = int(round(FORECAST_HORIZON_S / RL_DT))


def _finite(array: np.ndarray, columns: int, label: str) -> np.ndarray:
    value = np.asarray(array, dtype=float)
    if value.ndim != 2 or value.shape[1] != columns or len(value) <= FORECAST_STEPS or not np.all(np.isfinite(value)):
        raise ValueError(f"{label} must be a finite T x {columns} trace longer than the forecast horizon")
    return value


def load_current_and_target(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load only policy-legal present signals and future pose-error labels."""

    with np.load(path) as archive:
        required = (
            "joint_position", "joint_velocity", "wbc_task_twist",
            "wbc_pose_error", "wbc_twist_error",
        )
        missing = set(required) - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing forecast arrays {sorted(missing)}")
        q = _finite(archive["joint_position"], 7, "joint_position")
        qdot = _finite(archive["joint_velocity"], 7, "joint_velocity")
        task_twist = _finite(archive["wbc_task_twist"], 6, "wbc_task_twist")
        pose = _finite(archive["wbc_pose_error"], 6, "wbc_pose_error")
        twist = _finite(archive["wbc_twist_error"], 6, "wbc_twist_error")
    if not (len(q) == len(qdot) == len(task_twist) == len(pose) == len(twist)):
        raise ValueError(f"{path}: trace arrays have inconsistent lengths")
    current = np.asarray([
        encode_wbc_current_feature(ESNObservation(qi, qdoti, command), error, derivative)
        for qi, qdoti, command, error, derivative in zip(q, qdot, task_twist, pose, twist, strict=True)
    ], dtype=float)
    targets = pose[FORECAST_STEPS:] / WBC_POSE_ERROR_SCALE
    kinematic = np.asarray([
        encode_kinematic_pose_forecast(error, derivative)
        for error, derivative in zip(pose[:-FORECAST_STEPS], twist[:-FORECAST_STEPS], strict=True)
    ], dtype=float)
    return current, targets, kinematic


def design_and_targets(paths: list[Path]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    designs: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    kinematic_predictions: list[np.ndarray] = []
    for path in paths:
        current, future, kinematic = load_current_and_target(path)
        forecaster = FixedErrorForecaster()
        design = np.asarray([forecaster.advance(row) for row in current[:-FORECAST_STEPS]], dtype=float)
        designs.append(design)
        targets.append(future)
        kinematic_predictions.append(kinematic)
    return np.concatenate(designs), np.concatenate(targets), np.concatenate(kinematic_predictions)


def _metrics(prediction: np.ndarray, target: np.ndarray) -> dict[str, float]:
    error = np.asarray(prediction, dtype=float) - np.asarray(target, dtype=float)
    translational = error[:, :3] * WBC_POSE_ERROR_SCALE[:3]
    rotational = error[:, 3:] * WBC_POSE_ERROR_SCALE[3:]
    return {
        "normalized_rmse": float(np.sqrt(np.mean(error**2))),
        "translation_rmse_mm": float(np.sqrt(np.mean(translational**2)) * 1000.0),
        "rotation_rmse_rad": float(np.sqrt(np.mean(rotational**2))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--validation-traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-model-npz", type=Path, required=True)
    parser.add_argument("--output-report-json", type=Path, required=True)
    parser.add_argument("--ridge-lambda", type=float, default=1.0e-3)
    args = parser.parse_args()
    if args.ridge_lambda < 0.0:
        raise ValueError("ridge-lambda must be non-negative")
    train_design, train_targets, _ = design_and_targets(args.train_traces)
    gram = train_design.T @ train_design + args.ridge_lambda * np.eye(train_design.shape[1])
    readout = np.linalg.solve(gram, train_design.T @ train_targets).T
    if not np.all(np.isfinite(readout)):
        raise RuntimeError("future-error ridge readout became non-finite")
    validation_design, validation_targets, validation_kinematic = design_and_targets(args.validation_traces)
    validation_esn = validation_design @ readout.T
    report = {
        "stage": "development-only fixed-reservoir 120-ms WBC pose-error forecast",
        "horizon_s": FORECAST_HORIZON_S,
        "horizon_control_steps": FORECAST_STEPS,
        "readout": "ridge regression on fixed fast/slow Fan Ye reservoir features",
        "input_contract": ["q(7)", "qdot(7)", "WBC task twist(6)", "WBC pose error(6)", "WBC twist error(6)"],
        "excluded_inputs": ["contact", "force", "rod state", "obstacle geometry", "future release", "fixture id", "reward"],
        "train_trace_count": len(args.train_traces),
        "validation_trace_count": len(args.validation_traces),
        "ridge_lambda": args.ridge_lambda,
        "train_metrics": _metrics(train_design @ readout.T, train_targets),
        "validation_esn_metrics": _metrics(validation_esn, validation_targets),
        "validation_kinematic_metrics": _metrics(validation_kinematic, validation_targets),
        "validation_relative_translation_rmse": float(
            _metrics(validation_esn, validation_targets)["translation_rmse_mm"]
            / max(_metrics(validation_kinematic, validation_targets)["translation_rmse_mm"], 1.0e-12)
        ),
        "selection_policy": "Promote only if forecast is finite and development-validation error is informative versus the matched causal kinematic baseline. Do not use V4 final.",
    }
    args.output_model_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output_model_npz, forecast_readout=readout, forecast_horizon_s=np.array(FORECAST_HORIZON_S),
    )
    args.output_report_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_report_json.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
