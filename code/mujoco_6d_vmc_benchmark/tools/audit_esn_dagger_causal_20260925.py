"""Offline causal audit for the 48-D ESN DAgger development checkpoints.

The audit replays the recorded observations only.  It does not create a
MuJoCo model and it does not change a checkpoint, gate, or safety parameter.
It separates the final readout output from the common velocity-residual
filter, then checks the replay against the action saved by the physical run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import load_model, sha
from fit_esn_onpolicy_readout_20260925 import actions_from_logits, features_from_observation, teacher_labels
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


def _finite_stats(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "rms": float(np.sqrt(np.mean(values * values))),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def _action_stats(pred: np.ndarray, reference: np.ndarray, target: np.ndarray) -> dict:
    diff = pred - reference
    delta = np.diff(pred, axis=0)
    target_delta = np.diff(target, axis=0)
    return {
        "rmse_vs_recorded": float(np.sqrt(np.mean(diff * diff))),
        "max_abs_vs_recorded": float(np.max(np.abs(diff))),
        "rmse_vs_teacher": float(np.sqrt(np.mean((pred - target) ** 2))),
        "delta_rms": float(np.sqrt(np.mean(delta * delta))),
        "delta_rmse_vs_teacher": float(np.sqrt(np.mean((delta - target_delta) ** 2))),
        "sign_flip_fraction_x": float(np.mean(pred[1:, 1] * pred[:-1, 1] < 0.0)),
        "near_bound_fraction": float(np.mean(np.abs(pred) >= 0.98)),
        "per_channel_rms": [float(v) for v in np.sqrt(np.mean(pred * pred, axis=0))],
    }


def _replay_checkpoint(model_path: Path, observation: np.ndarray, recorded: np.ndarray,
                       stage: np.ndarray, config: dict) -> tuple[dict, dict[str, np.ndarray]]:
    model = load_model(model_path)
    features = features_from_observation(model, observation)
    normalized = (features - np.asarray(model["fmean"], dtype=np.float64)) / np.asarray(model["fstd"], dtype=np.float64)
    hidden = np.tanh(normalized @ np.asarray(model["w1"], dtype=np.float64).T + np.asarray(model["b1"], dtype=np.float64))
    logits = hidden @ np.asarray(model["w2"], dtype=np.float64).T + np.asarray(model["b2"], dtype=np.float64)
    projected = actions_from_logits(logits)
    output_gain = float(model["output_gain"])
    alpha = float(model["alpha"])
    bounded = np.zeros_like(projected)
    previous = np.zeros(7, dtype=np.float64)
    for i, row in enumerate(projected * output_gain):
        previous += alpha * (row - previous)
        bounded[i] = previous

    safety = VelocityResidualActionFilter(
        VelocityResidualSafetyConfig(maximum_linear_yield_mps=0.32)
    )
    filtered_scale = np.zeros(len(bounded), dtype=np.float64)
    filtered_yield = np.zeros((len(bounded), 6), dtype=np.float64)
    slew = np.zeros(len(bounded), dtype=np.int8)
    amplitude = np.zeros(len(bounded), dtype=np.int8)
    for i, action in enumerate(bounded):
        applied = safety.filter(action, 0.04)
        filtered_scale[i] = applied.wbc_scale
        filtered_yield[i] = applied.cartesian_yield_twist
        slew[i] = int(applied.slew_limited)
        amplitude[i] = int(applied.amplitude_saturated)

    teacher = teacher_labels(observation, config)
    loaded = stage >= 3
    training_z = normalized
    summary = {
        "checkpoint": str(model_path.resolve()),
        "checkpoint_sha256": sha(model_path),
        "samples": int(len(observation)),
        "recorded_action_replay": _action_stats(bounded, recorded, teacher),
        "teacher_action": {
            "rmse": float(np.sqrt(np.mean((teacher - recorded) ** 2))),
            "per_channel_rmse": [float(v) for v in np.sqrt(np.mean((teacher - recorded) ** 2, axis=0))],
        },
        "loaded_lift": {
            "samples": int(np.sum(loaded)),
            "raw_logit": {"mean": [float(v) for v in np.mean(logits[loaded], axis=0)],
                          "std": [float(v) for v in np.std(logits[loaded], axis=0)]},
            "bounded_action": _action_stats(bounded[loaded], recorded[loaded], teacher[loaded]),
            "safety_filter": {
                "slew_fraction": float(np.mean(slew[loaded])),
                "amplitude_fraction": float(np.mean(amplitude[loaded])),
                "scale": _finite_stats(filtered_scale[loaded]),
                "yield_mps": _finite_stats(filtered_yield[loaded]),
            },
            "feature_z": {
                "rms": float(np.sqrt(np.mean(training_z[loaded] ** 2))),
                "p95_abs": float(np.percentile(np.abs(training_z[loaded]), 95)),
                "max_abs": float(np.max(np.abs(training_z[loaded]))),
            },
        },
        "all_steps": {
            "safety_filter": {
                "slew_fraction": float(np.mean(slew)),
                "amplitude_fraction": float(np.mean(amplitude)),
                "scale": _finite_stats(filtered_scale),
                "yield_mps": _finite_stats(filtered_yield),
            },
            "bounded_action": {
                "saturation_fraction_per_channel": [float(v) for v in np.mean(np.abs(bounded) >= 0.98, axis=0)],
                "sign_flip_fraction_per_channel": [float(v) for v in np.mean(bounded[1:] * bounded[:-1] < 0.0, axis=0)],
                "delta_rms_per_channel": [float(v) for v in np.sqrt(np.mean(np.diff(bounded, axis=0) ** 2, axis=0))],
            },
        },
    }
    arrays = {
        "stage": stage,
        "recorded_action": recorded,
        "teacher_action": teacher,
        "raw_logits": logits,
        "projected_action": projected,
        "bounded_action": bounded,
        "filtered_scale": filtered_scale,
        "filtered_yield": filtered_yield,
        "slew_limited": slew,
        "amplitude_saturated": amplitude,
        "feature_z": training_z,
    }
    return summary, arrays


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--checkpoint", type=Path, nargs="+", required=True)
    parser.add_argument("--teacher-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not args.checkpoint:
        raise ValueError("at least one checkpoint is required")
    args.output.mkdir(parents=True)
    config = json.loads(args.teacher_config.read_text())
    report = {
        "method": "offline_esn_dagger_readout_filter_causal_audit",
        "scope": "development rollout audit; no MuJoCo and no validation selection",
        "source_sha256": {
            Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "fit_esn_history_adapter_20260925.py": hashlib.sha256((Path(__file__).resolve().parents[1] / "scripts" / "fit_esn_history_adapter_20260925.py").read_bytes()).hexdigest(),
        },
        "teacher_config_sha256": hashlib.sha256(args.teacher_config.read_bytes()).hexdigest(),
        "safety_replay": {"dt_s": 0.04, "maximum_linear_yield_mps": 0.32, "note": "direct_esn runner bypasses phase gates; this replays only the shared amplitude/slew filter"},
        "rollouts": [],
    }
    for rollout in args.rollout:
        with np.load(rollout, allow_pickle=False) as z:
            observation = z["observation"].astype(np.float64)
            recorded = z["action"].astype(np.float64)
            stage = z["stage"].astype(np.int64)
        if observation.shape[1] != 48 or recorded.shape[1] != 7 or len(observation) != len(recorded):
            raise ValueError(f"invalid rollout shapes in {rollout}: {observation.shape}, {recorded.shape}")
        row = {"rollout": str(rollout.resolve()), "rollout_sha256": sha(rollout), "checkpoints": {}}
        rollout_dir = args.output / rollout.parent.name
        rollout_dir.mkdir()
        for checkpoint in args.checkpoint:
            key = checkpoint.stem
            summary, arrays = _replay_checkpoint(checkpoint, observation, recorded, stage, config)
            row["checkpoints"][key] = summary
            np.savez_compressed(rollout_dir / f"{key}.npz", **arrays)
        report["rollouts"].append(row)
    report["checkpoint_sha256"] = {path.stem: sha(path) for path in args.checkpoint}
    (args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    lines = [
        "# ESN DAgger causal audit (offline)", "",
        "This audit replays recorded 48-D observations only. It does not create MuJoCo, change a checkpoint, modify a gate, or select a validation model.", "",
        "## Interpretation", "",
        "The `recorded_action_replay` error checks whether the checkpoint's reservoir/readout replay matches the action saved by the physical rollout. The safety numbers are a deterministic replay of the shared amplitude/slew filter with the runner's direct-ESN linear-yield limit (0.32 m/s); they are not new physical measurements.", "",
    ]
    for row in report["rollouts"]:
        lines += [f"## `{Path(row['rollout']).name}`", ""]
        for key, summary in row["checkpoints"].items():
            replay = summary["recorded_action_replay"]
            loaded = summary["loaded_lift"]
            lines += [
                f"### `{key}`",
                f"- checkpoint SHA256: `{summary['checkpoint_sha256']}`",
                f"- action replay RMSE vs recorded: `{replay['rmse_vs_recorded']:.3e}`; max abs: `{replay['max_abs_vs_recorded']:.3e}`",
                f"- loaded-lift samples: `{loaded['samples']}`; loaded action RMSE vs recorded: `{loaded['bounded_action']['rmse_vs_recorded']:.6f}`",
                f"- loaded safety slew fraction: `{loaded['safety_filter']['slew_fraction']:.4f}`; amplitude fraction: `{loaded['safety_filter']['amplitude_fraction']:.4f}`",
                f"- loaded feature z RMS / p95 / max: `{loaded['feature_z']['rms']:.4f}` / `{loaded['feature_z']['p95_abs']:.4f}` / `{loaded['feature_z']['max_abs']:.4f}`",
                "",
            ]
    lines += [
        "## Decision boundary", "",
        "A lower offline action error is not a task-success result. The physical DAgger rollouts remain development-only and must be evaluated on untouched validation fixtures before any deployment claim.", "",
    ]
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(args.output), "rollouts": len(report["rollouts"]), "checkpoints": len(args.checkpoint)}, indent=2))


if __name__ == "__main__":
    main()
