#!/usr/bin/env python3
"""Evaluate the deployable error-gated return-drive controller with zero PPO residuals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from evaluate_ppo_sixd_stiffness import _rejoin_latency, _summary
from rl_sixd_stiffness_env import PandaSixDStiffnessEnv, RL_DT, default_fixtures


def rollout(env: PandaSixDStiffnessEnv, fixture_index: int) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    observation, _ = env.reset(options={"fixture_index": fixture_index})
    action = np.zeros(env.action_space.shape, dtype=np.float32)
    trace: dict[str, list[np.ndarray | float]] = {key: [] for key in ("time", "ee_position", "nominal_position", "kappa", "torque", "recovery_drive_scale")}
    while True:
        observation, _, terminated, truncated, terminal = env.step(action)
        state = env.diagnostics()
        trace["time"].append(float(state["time_s"]))
        trace["ee_position"].append(np.asarray(state["ee_position"], dtype=float))
        trace["nominal_position"].append(np.asarray(state["nominal_position"], dtype=float))
        trace["kappa"].append(np.asarray(state["kappa"], dtype=float))
        trace["torque"].append(np.asarray(state["applied_torque"], dtype=float))
        trace["recovery_drive_scale"].append(float(state["recovery_drive_scale"]))
        if terminated or truncated:
            return {key: np.asarray(value) for key, value in trace.items()}, terminal


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--recovery-gate-hold-s", type=float, default=0.0)
    parser.add_argument("--recovery-error-weight", type=float, default=0.075)
    parser.add_argument("--recovery-progress-reward", type=float, default=0.040)
    parser.add_argument("--action-change-penalty", type=float, default=0.003)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixtures = default_fixtures()
    env_kwargs = dict(enable_drive_residual=True, recovery_gate_hold_s=args.recovery_gate_hold_s, recovery_error_weight=args.recovery_error_weight, recovery_progress_reward=args.recovery_progress_reward, action_change_penalty=args.action_change_penalty)
    rod_env = PandaSixDStiffnessEnv(args.menagerie, fixtures=fixtures, rod_enabled=True, seed=1, **env_kwargs)
    no_rod_env = PandaSixDStiffnessEnv(args.menagerie, fixtures=fixtures, rod_enabled=False, seed=1, **env_kwargs)
    records: list[dict[str, Any]] = []
    try:
        for index, fixture in enumerate(fixtures):
            rod, rod_terminal = rollout(rod_env, index)
            no_rod, no_rod_terminal = rollout(no_rod_env, index)
            if rod["time"].shape != no_rod["time"].shape or not np.allclose(rod["time"], no_rod["time"]):
                raise RuntimeError("matched rollouts do not share a control grid")
            paired_offset = np.linalg.norm(rod["ee_position"] - no_rod["ee_position"], axis=1)
            position_error = np.linalg.norm(rod["ee_position"] - rod["nominal_position"], axis=1)
            release = fixture.rod_start_time_s + 0.64
            recovery = (rod["time"] > release) & (rod["time"] < fixture.grasp_time_s)
            records.append({
                "fixture_index": index,
                "fixture": fixture.__dict__,
                "task_success": bool(rod_terminal["task_success"]),
                "effective_collision": bool(rod_terminal["effective_collision"]),
                "no_rod_task_success": bool(no_rod_terminal["task_success"]),
                "peak_paired_offset_mm": float(np.max(paired_offset) * 1000.0),
                "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired_offset**2)) * 1000.0),
                "recovery_rmse_mm": float(np.sqrt(np.mean(position_error[recovery]**2)) * 1000.0),
                "rejoin_latency_s": _rejoin_latency(rod["time"], position_error, release),
                "peak_torque_nm": float(rod_terminal["peak_torque_nm"]),
                "peak_jerk_mps3": float(rod_terminal["peak_jerk_mps3"]),
                "peak_contact_force_n": float(rod_terminal["peak_contact_force_n"]),
                "contact_impulse_ns": float(rod_terminal["contact_impulse_ns"]),
                "mean_log_kappa_deviation": float(rod_terminal["mean_log_kappa_deviation"]),
                "mean_log_drive_deviation": float(rod_terminal["mean_log_drive_deviation"]),
                "mean_residual_gate": float(rod_terminal["mean_residual_gate"]),
            })
            np.savez_compressed(args.output_dir / f"fixture_{index:02d}_paired_trace.npz", rod_time=rod["time"], rod_ee_position=rod["ee_position"], no_rod_ee_position=no_rod["ee_position"], nominal_position=rod["nominal_position"], rod_kappa=rod["kappa"], rod_torque=rod["torque"], rod_recovery_drive_scale=rod["recovery_drive_scale"])
    finally:
        rod_env.close()
        no_rod_env.close()
    report = {
        "protocol": "zero residuals in the deployable 52-D error-gated return-drive environment; matched rod/no-rod physics rollouts",
        "recovery_gate_hold_s": args.recovery_gate_hold_s,
        "summary": _summary(records),
        "records": records,
    }
    (args.output_dir / "zero_drive_residual_paired_evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
