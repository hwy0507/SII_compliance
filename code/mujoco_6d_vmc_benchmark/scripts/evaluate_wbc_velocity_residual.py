#!/usr/bin/env python3
"""Matched rod/no-rod evaluation for independent WBC residual controllers."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from train_wbc_velocity_residual import load_development_fixtures, reward_profile
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, RL_DT, VelocityResidualFixture
from wbc_velocity_residual_core import VelocityResidualSafetyConfig


def _run_episode(
    env: PandaWBCVelocityResidualEnv,
    model: PPO | None,
    normalizer: VecNormalize | None,
    fixture_index: int,
    fixed_action: np.ndarray | None,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    observation, _ = env.reset(options={"fixture_index": fixture_index})
    trace: dict[str, list[np.ndarray | float]] = {key: [] for key in (
        "time", "ee_position", "nominal_position", "ee_twist", "nominal_twist",
        "joint_position", "joint_velocity", "wbc_pose_error", "wbc_twist_error",
        "wbc_scale", "authority_gate", "yield_twist", "joint_velocity_command", "torque", "policy_action",
    )}
    terminal: dict[str, Any] = {}
    while True:
        if fixed_action is None:
            if model is None or normalizer is None:
                raise RuntimeError("PPO model and VecNormalize state are required for learned evaluation")
            normalized = normalizer.normalize_obs(observation[None, :])[0]
            action, _ = model.predict(normalized, deterministic=True)
        else:
            action = fixed_action
        observation, _, terminated, truncated, info = env.step(action)
        state = env.diagnostics()
        trace["time"].append(float(state["time_s"]))
        trace["ee_position"].append(state["ee_position"])
        trace["nominal_position"].append(state["nominal_position"])
        trace["ee_twist"].append(state["ee_twist"])
        trace["nominal_twist"].append(state["nominal_twist"])
        trace["joint_position"].append(state["joint_position"])
        trace["joint_velocity"].append(state["joint_velocity"])
        trace["wbc_pose_error"].append(state["wbc_pose_error"])
        trace["wbc_twist_error"].append(state["wbc_twist_error"])
        trace["wbc_scale"].append(float(state["wbc_scale"]))
        trace["authority_gate"].append(float(state["authority_gate"]))
        trace["yield_twist"].append(state["cartesian_yield_twist"])
        trace["joint_velocity_command"].append(state["joint_velocity_command"])
        trace["torque"].append(state["applied_torque"])
        trace["policy_action"].append(np.asarray(action, dtype=float))
        if terminated or truncated:
            terminal = info
            break
    return {key: np.asarray(value) for key, value in trace.items()}, terminal


def _rejoin_latency(time: np.ndarray, error: np.ndarray, release_time_s: float) -> float | None:
    hold = max(1, int(round(0.080 / RL_DT)))
    for index in np.flatnonzero(time >= release_time_s):
        if index + hold <= len(time) and bool(np.all(error[index:index + hold] <= 0.005)):
            return float(time[index] - release_time_s)
    return None


def _distribution(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(array)),
        "std": float(np.std(array, ddof=0)),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
    }


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "episode_count": len(records),
        "task_success_count": sum(record["task_success"] for record in records),
        "effective_collision_count": sum(record["effective_collision"] for record in records),
        "matched_no_rod_task_success_count": sum(record["no_rod_task_success"] for record in records),
        "hard_torque_limit_count": sum(record["hard_torque_limit"] for record in records),
    }
    for key in (
        "peak_paired_offset_mm", "paired_offset_rmse_mm", "recovery_rmse_mm",
        "peak_torque_nm", "peak_jerk_mps3", "peak_contact_force_n", "contact_impulse_ns",
        "mean_wbc_slowdown", "mean_yield_twist_norm", "action_slew_limited_fraction",
        "policy_action_saturation_fraction", "mean_authority_gate",
    ):
        result[key] = _distribution([float(record[key]) for record in records])
    latencies = [float(record["rejoin_latency_s"]) for record in records if record["rejoin_latency_s"] is not None]
    result["rejoin_latency_s"] = None if not latencies else {**_distribution(latencies), "count": len(latencies)}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, required=True)
    parser.add_argument("--fixture-split", choices=("train", "validation"), default="validation")
    parser.add_argument("--fan-ye-model-npz", type=Path, required=True)
    parser.add_argument("--fan-ye-train-summary-json", type=Path, required=True)
    parser.add_argument("--observation-mode", choices=PandaWBCVelocityResidualEnv.observation_modes, required=True)
    parser.add_argument("--reward-profile", choices=("balanced", "contact_safe", "recovery_priority", "impulse_constrained"), default="balanced")
    parser.add_argument("--model", type=Path, default=None)
    parser.add_argument("--vecnormalize", type=Path, default=None)
    parser.add_argument("--neutral-wbc", action="store_true", help="Evaluate all-zero action, exactly the fixed-WBC velocity controller.")
    parser.add_argument("--fixed-action", type=str, default=None, help="Comma-separated seven-vector for bounded authority smoke tests.")
    parser.add_argument("--max-fixtures", type=int, default=None)
    parser.add_argument("--residual-window-end-at-grasp", action="store_true", help="Return residual authority to fixed WBC from gripper-close onward.")
    parser.add_argument("--directional-phase-projection", action="store_true", help="Constrain yield/rejoin velocity to the causal WBC-error half-space.")
    parser.add_argument("--forecast-model-npz", type=Path, default=None, help="Fitted forecast readout required by fan_ye_forecast_esn.")
    args = parser.parse_args()
    fixed_action = None
    if args.neutral_wbc:
        fixed_action = np.zeros(7, dtype=np.float32)
    elif args.fixed_action is not None:
        fixed_action = np.asarray([float(value) for value in args.fixed_action.split(",")], dtype=np.float32)
        if fixed_action.shape != (7,):
            raise ValueError("--fixed-action must contain seven comma-separated values")
    if fixed_action is None and (args.model is None or args.vecnormalize is None):
        parser.error("learned evaluation requires --model and --vecnormalize")
    if fixed_action is not None and (args.model is not None or args.vecnormalize is not None):
        parser.error("fixed/neutral evaluation cannot be combined with learned model paths")
    if args.observation_mode == "fan_ye_forecast_esn" and args.forecast_model_npz is None:
        parser.error("fan_ye_forecast_esn requires --forecast-model-npz")
    fixtures = load_development_fixtures(args.fixture_manifest, args.fixture_split)
    if args.max_fixtures is not None:
        fixtures = fixtures[:args.max_fixtures]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env_kwargs = {
        "menagerie": args.menagerie,
        "fan_ye_model_npz": args.fan_ye_model_npz,
        "fan_ye_train_summary_json": args.fan_ye_train_summary_json,
        "observation_mode": args.observation_mode,
        "fixtures": fixtures,
        "reward_config": reward_profile(args.reward_profile),
        "safety_config": VelocityResidualSafetyConfig(directional_phase_projection=args.directional_phase_projection),
        "residual_window_end_at_grasp": args.residual_window_end_at_grasp,
        "forecast_model_npz": args.forecast_model_npz,
    }
    template = None
    normalizer = None
    model = None
    if fixed_action is None:
        template = DummyVecEnv([lambda: PandaWBCVelocityResidualEnv(**env_kwargs, rod_enabled=True, seed=0)])
        normalizer = VecNormalize.load(str(args.vecnormalize), template)
        normalizer.training = False
        normalizer.norm_reward = False
        model = PPO.load(args.model, device="cpu")
    rod_env = PandaWBCVelocityResidualEnv(**env_kwargs, rod_enabled=True, seed=1)
    no_rod_env = PandaWBCVelocityResidualEnv(**env_kwargs, rod_enabled=False, seed=1)
    records: list[dict[str, Any]] = []
    try:
        for index, fixture in enumerate(fixtures):
            rod, rod_terminal = _run_episode(rod_env, model, normalizer, index, fixed_action)
            no_rod, no_rod_terminal = _run_episode(no_rod_env, model, normalizer, index, fixed_action)
            if rod["time"].shape != no_rod["time"].shape or not np.allclose(rod["time"], no_rod["time"]):
                raise RuntimeError("matched direct-controller rollouts do not share a control grid")
            paired_offset = np.linalg.norm(rod["ee_position"] - no_rod["ee_position"], axis=1)
            position_error = np.linalg.norm(rod["ee_position"] - rod["nominal_position"], axis=1)
            release = fixture.rod_start_time_s + 0.64
            recovery = (rod["time"] > release) & (rod["time"] < fixture.grasp_time_s)
            record = {
                "fixture_index": index,
                "fixture": asdict(fixture),
                "task_success": bool(rod_terminal["task_success"]),
                "effective_collision": bool(rod_terminal["effective_collision"]),
                "no_rod_task_success": bool(no_rod_terminal["task_success"]),
                "hard_torque_limit": bool(rod_terminal["hard_torque_limit"]),
                "peak_paired_offset_mm": float(np.max(paired_offset) * 1000.0),
                "paired_offset_rmse_mm": float(np.sqrt(np.mean(paired_offset**2)) * 1000.0),
                "recovery_rmse_mm": float(np.sqrt(np.mean(position_error[recovery]**2)) * 1000.0),
                "rejoin_latency_s": _rejoin_latency(rod["time"], position_error, release),
                "peak_torque_nm": float(rod_terminal["peak_torque_nm"]),
                "peak_jerk_mps3": float(rod_terminal["peak_jerk_mps3"]),
                "peak_contact_force_n": float(rod_terminal["peak_contact_force_n"]),
                "contact_impulse_ns": float(rod_terminal["contact_impulse_ns"]),
                "mean_wbc_slowdown": float(rod_terminal["mean_wbc_slowdown"]),
                "mean_yield_twist_norm": float(rod_terminal["mean_yield_twist_norm"]),
                "mean_authority_gate": float(rod_terminal["mean_authority_gate"]),
                "action_slew_limited_fraction": float(rod_terminal["action_slew_limited_fraction"]),
                "policy_action_saturation_fraction": float(rod_terminal["policy_action_saturation_fraction"]),
            }
            records.append(record)
            np.savez_compressed(
                args.output_dir / f"fixture_{index:02d}_paired_trace.npz",
                rod_time=rod["time"],
                rod_ee_position=rod["ee_position"],
                no_rod_ee_position=no_rod["ee_position"],
                nominal_position=rod["nominal_position"],
                rod_ee_twist=rod["ee_twist"],
                rod_nominal_twist=rod["nominal_twist"],
                rod_joint_position=rod["joint_position"],
                rod_joint_velocity=rod["joint_velocity"],
                rod_wbc_pose_error=rod["wbc_pose_error"],
                rod_wbc_twist_error=rod["wbc_twist_error"],
                rod_wbc_scale=rod["wbc_scale"],
                rod_authority_gate=rod["authority_gate"],
                rod_yield_twist=rod["yield_twist"],
                rod_joint_velocity_command=rod["joint_velocity_command"],
                rod_torque=rod["torque"],
                rod_policy_action=rod["policy_action"],
            )
    finally:
        rod_env.close()
        no_rod_env.close()
        if template is not None:
            template.close()
    report = {
        "protocol": "frozen deterministic policy; matched rod/no-rod MuJoCo physics; offline diagnostics only",
        "controller_family": "independent_wbc_velocity_residual",
        "uses_vmc": False,
        "residual_window_end_at_grasp": args.residual_window_end_at_grasp,
        "observation_mode": args.observation_mode,
        "neutral_wbc": args.neutral_wbc,
        "fixed_action": None if fixed_action is None else fixed_action.tolist(),
        "model": None if args.model is None else str(args.model),
        "vecnormalize": None if args.vecnormalize is None else str(args.vecnormalize),
        "fixture_manifest": str(args.fixture_manifest),
        "fixture_split": args.fixture_split,
        "forecast_model_npz": None if args.forecast_model_npz is None else str(args.forecast_model_npz),
        "summary": _summary(records),
        "records": records,
    }
    (args.output_dir / "wbc_velocity_residual_paired_evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
