#!/usr/bin/env python3
"""Fit a Fan Ye-aligned ESN readout from safe analytic VMC teacher traces.

This is a *warm-start imitation stage*, not an ESN performance claim.  The
teacher action is a causal VMC tracking-error-gate schedule recorded by the
existing controller.  It does not consume rod/contact/force/obstacle arrays;
the student itself sees only q, qdot and WBC task twist.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from fan_ye_esn_design import FanYeAlignedESN, FanYeESNConfig, FanYeInputNormalizer, deployable_trace_from_arrays


DEPLOYABLE_KEYS = ("joint_position", "joint_velocity", "wbc_task_twist")


@dataclass(frozen=True)
class GatedVMCTeacherConfig:
    """Causal safe action template used only to initialize the ESN readout."""

    translation_log_kappa_softening: float = -0.55
    rotation_log_kappa_softening: float = -0.25
    recovery_drive_boost: float = 0.65
    gate_filter_time_constant_s: float = 0.0

    def __post_init__(self) -> None:
        if not all(-1.0 <= value <= 1.0 for value in (
            self.translation_log_kappa_softening, self.rotation_log_kappa_softening, self.recovery_drive_boost,
        )):
            raise ValueError("teacher actions must remain inside the ESN action box")
        if not 0.0 <= self.gate_filter_time_constant_s <= 1.0:
            raise ValueError("gate filter time constant must be in [0, 1] seconds")


def teacher_actions_from_gate(
    recovery_gate: np.ndarray,
    config: GatedVMCTeacherConfig = GatedVMCTeacherConfig(),
    *,
    sample_period_s: float = 0.04,
) -> np.ndarray:
    """Map recorded causal VMC recovery gate to a bounded seven-dimensional action."""

    gate = np.asarray(recovery_gate, dtype=float)
    if gate.ndim != 1 or not np.all(np.isfinite(gate)):
        raise ValueError("recovery_gate must be a finite one-dimensional array")
    if sample_period_s <= 0.0:
        raise ValueError("teacher sample period must be positive")
    clipped = np.clip(gate, 0.0, 1.0)
    # This is a causal label-side first-order filter, never an additional
    # student observation.  tau=0 exactly recovers the original teacher.
    if config.gate_filter_time_constant_s > 0.0:
        alpha = sample_period_s / (config.gate_filter_time_constant_s + sample_period_s)
        filtered = np.empty_like(clipped)
        previous = 0.0
        for index, value in enumerate(clipped):
            previous += alpha * (value - previous)
            filtered[index] = previous
        clipped = filtered
    return np.column_stack((
        np.repeat((config.translation_log_kappa_softening * clipped)[:, None], 3, axis=1),
        np.repeat((config.rotation_log_kappa_softening * clipped)[:, None], 3, axis=1),
        config.recovery_drive_boost * clipped,
    ))


def load_episode(
    path: Path,
    *,
    sample_stride: int,
    teacher_config: GatedVMCTeacherConfig = GatedVMCTeacherConfig(),
) -> tuple[np.ndarray, np.ndarray]:
    if sample_stride < 1:
        raise ValueError("sample_stride must be positive")
    with np.load(path) as archive:
        missing = set((*DEPLOYABLE_KEYS, "recovery_gate")) - set(archive.files)
        if missing:
            raise ValueError(f"{path}: missing required fields {sorted(missing)}")
        trace = deployable_trace_from_arrays(
            archive["joint_position"][::sample_stride], archive["joint_velocity"][::sample_stride], archive["wbc_task_twist"][::sample_stride],
        )
        # The gate is controller-internal teacher supervision, never a student
        # feature.  No rod/contact/force/obstacle archive key is accessed.
        target = teacher_actions_from_gate(
            archive["recovery_gate"][::sample_stride], teacher_config,
            sample_period_s=0.004 * sample_stride,
        )
    if len(trace) != len(target):
        raise ValueError(f"{path}: trace and target lengths differ")
    return trace, target


def _config_from_screen(screen: dict, candidate_index: int) -> FanYeESNConfig:
    for candidate in screen["candidates"]:
        if candidate["candidate_index"] == candidate_index:
            return FanYeESNConfig(**candidate["config"])
    raise ValueError(f"candidate index {candidate_index} not found in screen")


def fit_readout_from_traces(
    screen: dict,
    *,
    candidate_index: int,
    traces: list[Path],
    sample_stride: int,
    washout_steps: int,
    teacher_config: GatedVMCTeacherConfig = GatedVMCTeacherConfig(),
) -> tuple[FanYeAlignedESN, FanYeInputNormalizer, dict]:
    """Fit one fixed-reservoir readout, retaining the teacher configuration.

    This small public helper lets validation-only teacher-envelope scans reuse
    the exact training path of the standalone CLI.  The selected reservoir and
    all student features remain fixed; only offline analytic-teacher labels
    may change between scan points.
    """

    config = _config_from_screen(screen, candidate_index)
    if sample_stride < 1 or washout_steps < 0:
        raise ValueError("sample stride must be positive and washout non-negative")
    if abs(config.dt_s - 0.004 * sample_stride) > 1.0e-12:
        raise ValueError("sample stride is inconsistent with selected ESN dt_s")
    episodes = [load_episode(path, sample_stride=sample_stride, teacher_config=teacher_config) for path in traces]
    normalizer = FanYeInputNormalizer.from_actuation_traces([trace for trace, _ in episodes])
    model = FanYeAlignedESN(config)
    all_features, all_targets = [], []
    per_episode = []
    for path, (trace, target) in zip(traces, episodes):
        normalized = normalizer.transform(trace)
        features = model.features(normalized, washout_steps=washout_steps)
        targets = target[washout_steps:]
        all_features.append(features)
        all_targets.append(targets)
        per_episode.append({"path": str(path), "samples_after_washout": len(features)})
    design, targets = np.concatenate(all_features), np.concatenate(all_targets)
    model.fit_readout(design, targets)
    mse = float(np.mean((design @ model.readout.T - targets) ** 2))
    return model, normalizer, {
        "config": config,
        "episodes": per_episode,
        "training_samples": len(design),
        "readout_training_mse": mse,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timescale-screen-json", type=Path, required=True)
    parser.add_argument("--candidate-index", type=int, default=22)
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output-model-npz", type=Path, required=True)
    parser.add_argument("--output-summary-json", type=Path, required=True)
    parser.add_argument("--sample-stride", type=int, default=10)
    parser.add_argument("--washout-steps", type=int, default=25)
    parser.add_argument("--translation-log-kappa-softening", type=float, default=GatedVMCTeacherConfig.translation_log_kappa_softening)
    parser.add_argument("--rotation-log-kappa-softening", type=float, default=GatedVMCTeacherConfig.rotation_log_kappa_softening)
    parser.add_argument("--recovery-drive-boost", type=float, default=GatedVMCTeacherConfig.recovery_drive_boost)
    parser.add_argument("--gate-filter-time-constant-s", type=float, default=GatedVMCTeacherConfig.gate_filter_time_constant_s)
    args = parser.parse_args()
    screen = json.loads(args.timescale_screen_json.read_text())
    teacher_config = GatedVMCTeacherConfig(
        translation_log_kappa_softening=args.translation_log_kappa_softening,
        rotation_log_kappa_softening=args.rotation_log_kappa_softening,
        recovery_drive_boost=args.recovery_drive_boost,
        gate_filter_time_constant_s=args.gate_filter_time_constant_s,
    )
    model, normalizer, fit = fit_readout_from_traces(
        screen, candidate_index=args.candidate_index, traces=args.traces,
        sample_stride=args.sample_stride, washout_steps=args.washout_steps,
        teacher_config=teacher_config,
    )
    args.output_model_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output_model_npz, readout=model.readout, input_normalizer_scales=normalizer.scales)
    summary = {
        "schema_version": 1,
        "stage": "Fan Ye-aligned ESN ridge readout warm-start from causal analytic VMC teacher",
        "candidate_index": args.candidate_index,
        "config": asdict(fit["config"]),
        "student_input": list(DEPLOYABLE_KEYS),
        "student_excludes": ["rod_contact", "rod_force", "rod_penetration", "rod_state", "obstacle_pose_or_geometry", "future_release", "fixture_id", "recovery_gate"],
        "teacher": {"type": "causal analytic VMC recovery-gate template", "config": asdict(teacher_config), "source": "existing VMC tracking-error recovery_gate only"},
        "sample_stride": args.sample_stride,
        "washout_steps": args.washout_steps,
        "episodes": fit["episodes"],
        "training_samples": fit["training_samples"],
        "readout_training_mse": fit["readout_training_mse"],
        "model_npz": str(args.output_model_npz),
        "warning": "Training MSE is teacher-imitation fit only. It is not a closed-loop performance metric and must not be compared to VMC baselines.",
    }
    args.output_summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"candidate_index": args.candidate_index, "training_samples": fit["training_samples"], "readout_training_mse": fit["readout_training_mse"], "output_model": str(args.output_model_npz)}, indent=2))


if __name__ == "__main__":
    main()
