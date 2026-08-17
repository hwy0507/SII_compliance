#!/usr/bin/env python3
"""Run a frozen Direct ESN inside the fixed-WBC MuJoCo environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNController
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


def run_episode(controller_path: Path | None, *, menagerie: Path, fan_ye_model: Path | None, fan_ye_summary: Path | None, fixture_index: int, rod_enabled: bool, seed: int, fixed_wbc: bool = False) -> tuple[dict, list[dict]]:
    controller = None if fixed_wbc else DirectESNController.from_npz(controller_path)  # type: ignore[arg-type]
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=fan_ye_model,
        fan_ye_train_summary_json=fan_ye_summary, observation_mode="direct_esn",
        rod_enabled=rod_enabled, seed=seed,
    )
    try:
        env.reset(seed=seed, options={"fixture_index": fixture_index})
        if controller is not None:
            controller.reset()
        trace = []
        terminated = False
        info = {}
        while not terminated:
            diagnostic = env.diagnostics()
            if controller is None:
                action_vector = np.zeros(7, dtype=float)
                wbc_scale = 1.0
                yielding_twist = np.zeros(6, dtype=float)
                raw_readout = np.zeros(7, dtype=float)
            else:
                action = controller.act(
                    diagnostic["joint_position"], diagnostic["joint_velocity"], diagnostic["nominal_twist"],
                    pose_error=diagnostic["wbc_pose_error"], twist_error=diagnostic["wbc_twist_error"],
                )
                action_vector = action.bounded_filter_action
                wbc_scale = action.wbc_scale
                yielding_twist = action.yielding_twist
                raw_readout = action.raw_readout
            _, _, terminated, _, info = env.step(action_vector)
            trace.append({
                "time_s": diagnostic["time_s"], "wbc_scale": wbc_scale,
                "yielding_twist": np.asarray(yielding_twist).copy(), "raw_readout": np.asarray(raw_readout).copy(),
                "bounded_action": np.asarray(action_vector).copy(),
                "joint_position": diagnostic["joint_position"].copy(),
                "joint_velocity": diagnostic["joint_velocity"].copy(),
                "wbc_task_twist": diagnostic["nominal_twist"].copy(),
                "pose_error": diagnostic["wbc_pose_error"].copy(),
                "wbc_twist_error": diagnostic["wbc_twist_error"].copy(),
                "ee_position": diagnostic["ee_position"].copy(), "nominal_position": diagnostic["nominal_position"].copy(),
                "wbc_pose_error": diagnostic["wbc_pose_error"].copy(), "wbc_twist_error": diagnostic["wbc_twist_error"].copy(),
            })
        return info, trace
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller", type=Path, default=None)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fan-ye-model", type=Path, default=None)
    parser.add_argument("--fan-ye-summary", type=Path, default=None)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--no-rod", action="store_true")
    parser.add_argument("--fixed-wbc", action="store_true", help="record a zero-action fixed-WBC neutral trace")
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    args = parser.parse_args()
    info, trace = run_episode(
        args.controller, menagerie=args.menagerie, fan_ye_model=args.fan_ye_model,
        fan_ye_summary=args.fan_ye_summary, fixture_index=args.fixture_index,
        rod_enabled=not args.no_rod, seed=args.seed, fixed_wbc=args.fixed_wbc,
    )
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_trace.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(info, indent=2, default=lambda value: value.tolist() if isinstance(value, np.ndarray) else value) + "\n")
    np.savez_compressed(
        args.output_trace,
        time_s=np.asarray([item["time_s"] for item in trace]),
        wbc_scale=np.asarray([item["wbc_scale"] for item in trace]),
        yielding_twist=np.asarray([item["yielding_twist"] for item in trace]),
        raw_readout=np.asarray([item["raw_readout"] for item in trace]),
        bounded_action=np.asarray([item["bounded_action"] for item in trace]),
        joint_position=np.asarray([item["joint_position"] for item in trace]),
        joint_velocity=np.asarray([item["joint_velocity"] for item in trace]),
        wbc_task_twist=np.asarray([item["wbc_task_twist"] for item in trace]),
        pose_error=np.asarray([item["pose_error"] for item in trace]),
        # The rollout adapter intentionally does not expose contact force to
        # the student. For no-rod neutral archives this is the exact teacher
        # value; rod traces should use the dedicated privileged collector.
        contact_force=np.zeros(len(trace)),
        contact_normal=np.tile(np.array([0.0, 1.0, 0.0]), (len(trace), 1)),
        contact_duration_s=np.zeros(len(trace)),
        signed_distance_m=np.full(len(trace), 0.02),
        ee_position=np.asarray([item["ee_position"] for item in trace]),
        nominal_position=np.asarray([item["nominal_position"] for item in trace]),
        wbc_pose_error=np.asarray([item["wbc_pose_error"] for item in trace]),
        wbc_twist_error=np.asarray([item["wbc_twist_error"] for item in trace]),
    )
    print(json.dumps(info, indent=2, default=lambda value: value.tolist() if isinstance(value, np.ndarray) else value))


if __name__ == "__main__":
    main()
