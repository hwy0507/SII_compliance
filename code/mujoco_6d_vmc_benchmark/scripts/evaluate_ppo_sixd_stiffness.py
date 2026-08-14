#!/usr/bin/env python3
"""Frozen-policy matched rod/no-rod evaluation for six-dimensional PPO."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl_sixd_stiffness_env import PandaSixDStiffnessEnv, RL_DT, default_fixtures


def _run_episode(env: PandaSixDStiffnessEnv, model: PPO, normalizer: VecNormalize, fixture_index: int) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    observation, _ = env.reset(options={"fixture_index": fixture_index})
    trace: dict[str, list[np.ndarray | float]] = {key: [] for key in ("time", "ee_position", "nominal_position", "kappa", "torque", "recovery_drive_scale")}
    terminal: dict[str, Any] = {}
    while True:
        normalized = normalizer.normalize_obs(observation[None, :])[0]
        action, _ = model.predict(normalized, deterministic=True)
        observation, _, terminated, truncated, info = env.step(action)
        state = env.diagnostics()
        trace["time"].append(float(state["time_s"]))
        trace["ee_position"].append(np.asarray(state["ee_position"], dtype=float))
        trace["nominal_position"].append(np.asarray(state["nominal_position"], dtype=float))
        trace["kappa"].append(np.asarray(state["kappa"], dtype=float))
        trace["torque"].append(np.asarray(state["applied_torque"], dtype=float))
        trace["recovery_drive_scale"].append(float(state["recovery_drive_scale"]))
        if terminated or truncated:
            terminal = info
            break
    return {key: np.asarray(value) for key, value in trace.items()}, terminal


def _rejoin_latency(time: np.ndarray, position_error: np.ndarray, release_time_s: float) -> float | None:
    hold = max(1, int(round(0.080 / RL_DT)))
    for index in np.flatnonzero(time >= release_time_s):
        stop = index + hold
        if stop <= len(time) and bool(np.all(position_error[index:stop] <= 0.005)):
            return float(time[index] - release_time_s)
    return None


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    numeric = ("peak_paired_offset_mm", "paired_offset_rmse_mm", "recovery_rmse_mm", "peak_torque_nm", "peak_jerk_mps3", "peak_contact_force_n", "contact_impulse_ns")
    result: dict[str, Any] = {
        "episode_count": len(records),
        "task_success_count": sum(record["task_success"] for record in records),
        "effective_collision_count": sum(record["effective_collision"] for record in records),
        "matched_no_rod_task_success_count": sum(record["no_rod_task_success"] for record in records),
    }
    for key in numeric:
        values = np.asarray([record[key] for record in records], dtype=float)
        result[key] = {"mean": float(np.mean(values)), "std": float(np.std(values, ddof=0)), "min": float(np.min(values)), "max": float(np.max(values))}
    latencies = [record["rejoin_latency_s"] for record in records if record["rejoin_latency_s"] is not None]
    result["rejoin_latency_s"] = None if not latencies else {"mean": float(np.mean(latencies)), "std": float(np.std(latencies, ddof=0)), "count": len(latencies)}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True, help="PPO .zip model path")
    parser.add_argument("--vecnormalize", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-fixtures", type=int, default=None)
    parser.add_argument("--enable-drive-residual", action="store_true")
    parser.add_argument("--recovery-gate-hold-s", type=float, default=0.0)
    parser.add_argument("--recovery-error-weight", type=float, default=0.075)
    parser.add_argument("--recovery-progress-reward", type=float, default=0.040)
    parser.add_argument("--action-change-penalty", type=float, default=0.003)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fixtures = default_fixtures()
    if args.max_fixtures is not None:
        fixtures = fixtures[:args.max_fixtures]
    env_kwargs = dict(enable_drive_residual=args.enable_drive_residual, recovery_gate_hold_s=args.recovery_gate_hold_s, recovery_error_weight=args.recovery_error_weight, recovery_progress_reward=args.recovery_progress_reward, action_change_penalty=args.action_change_penalty)
    template = DummyVecEnv([lambda: PandaSixDStiffnessEnv(args.menagerie, fixtures=fixtures, seed=0, **env_kwargs)])
    normalizer = VecNormalize.load(str(args.vecnormalize), template)
    normalizer.training = False
    normalizer.norm_reward = False
    model = PPO.load(args.model, device="cpu")
    rod_env = PandaSixDStiffnessEnv(args.menagerie, fixtures=fixtures, rod_enabled=True, seed=1, **env_kwargs)
    no_rod_env = PandaSixDStiffnessEnv(args.menagerie, fixtures=fixtures, rod_enabled=False, seed=1, **env_kwargs)
    records: list[dict[str, Any]] = []
    try:
        for index, fixture in enumerate(fixtures):
            rod, rod_terminal = _run_episode(rod_env, model, normalizer, index)
            no_rod, no_rod_terminal = _run_episode(no_rod_env, model, normalizer, index)
            if rod["time"].shape != no_rod["time"].shape or not np.allclose(rod["time"], no_rod["time"]):
                raise RuntimeError("matched rollouts do not share a control grid")
            paired_offset = np.linalg.norm(rod["ee_position"] - no_rod["ee_position"], axis=1)
            position_error = np.linalg.norm(rod["ee_position"] - rod["nominal_position"], axis=1)
            release = fixture.rod_start_time_s + 0.64
            recovery = (rod["time"] > release) & (rod["time"] < fixture.grasp_time_s)
            record = {
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
                "mean_log_kappa_deviation": float(rod_terminal.get("mean_log_kappa_deviation", np.mean(np.abs(np.log(rod["kappa"] / rod["kappa"][0]))))),
                "mean_log_drive_deviation": float(rod_terminal.get("mean_log_drive_deviation", 0.0)),
                "mean_residual_gate": float(rod_terminal.get("mean_residual_gate", 0.0)),
            }
            records.append(record)
            np.savez_compressed(args.output_dir / f"fixture_{index:02d}_paired_trace.npz", rod_time=rod["time"], rod_ee_position=rod["ee_position"], no_rod_ee_position=no_rod["ee_position"], nominal_position=rod["nominal_position"], rod_kappa=rod["kappa"], no_rod_kappa=no_rod["kappa"], rod_torque=rod["torque"], rod_recovery_drive_scale=rod["recovery_drive_scale"], no_rod_recovery_drive_scale=no_rod["recovery_drive_scale"])
    finally:
        rod_env.close()
        no_rod_env.close()
        template.close()
    report = {
        "protocol": "frozen deterministic PPO; matched rod/no-rod physics rollouts; offline diagnostics only",
        "enable_drive_residual": args.enable_drive_residual,
        "recovery_gate_hold_s": args.recovery_gate_hold_s,
        "model": str(args.model),
        "vecnormalize": str(args.vecnormalize),
        "summary": _summary(records),
        "records": records,
    }
    (args.output_dir / "ppo_paired_evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
