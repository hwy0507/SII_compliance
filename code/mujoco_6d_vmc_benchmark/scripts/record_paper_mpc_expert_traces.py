#!/usr/bin/env python3
"""Record expert traces on the Paper-MPC nominal controller for ESN/MLP BC.

The previously trained students were distilled under the FixedWBC nominal
controller; the Paper-MPC waypoint-tracking nominal shifts the state
distribution, so the compliance students are re-distilled here.  The expert
is the tuned torque-mode spring-carriage VMC (stable and task-successful on
the Paper-MPC nominal), following the coverage-behavior-cloning recipe:
training fixtures + approach-side coverage + a neutral no-rod trace.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_benchmark import TORQUE_LIMITS  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import (  # noqa: E402
    PandaWBCVelocityResidualEnv,
    default_velocity_residual_fixtures,
)

RL_DT = 0.04


def record(menagerie: Path, fixture, out: Path, *, k: float, budget: float,
           seed: int, side: str | None = None, lift_board: bool = False) -> dict:
    fx = fixture if side is None else replace(fixture, rod_approach_side=side)
    cfg = VMCTorqueBaseline.from_npz(Path("/tmp/vmc_k2.2_s0.03.npz")).config
    from vmc_compliance_baseline import SpringCarriageConfig
    cfg = replace(cfg, k_translation_base=k,
                  k_rotation_base=cfg.k_rotation_base * k / cfg.k_translation_base)
    expert = VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget)
    kwargs = dict(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=True, seed=seed, robot="fr3",
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fx,),
    )
    if lift_board:
        kwargs["lift_board_tilt_deg"] = 40.0
    env = PandaWBCVelocityResidualEnv(**kwargs)
    env.reset(seed=seed, options={"fixture_index": 0})
    expert.reset()
    buf = {key: [] for key in (
        "joint_position", "joint_velocity", "wbc_task_twist",
        "pose_error", "wbc_twist_error", "bounded_action")}
    done = False
    info = {}
    while not done:
        d = env.diagnostics()
        act = expert.act(
            d["joint_position"], d["joint_velocity"], d["nominal_twist"],
            hand_jacobian=d.get("hand_jacobian"),
            pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        buf["joint_position"].append(d["joint_position"])
        buf["joint_velocity"].append(d["joint_velocity"])
        buf["wbc_task_twist"].append(d["nominal_twist"])
        buf["pose_error"].append(d["wbc_pose_error"])
        buf["wbc_twist_error"].append(d["wbc_twist_error"])
        buf["bounded_action"].append(act.bounded_filter_action)
        _, _, done, _, info = env.step(act.bounded_filter_action)
    arrays = {key: np.asarray(value) for key, value in buf.items()}
    np.savez_compressed(out, **arrays)
    env.close()
    return dict(path=str(out), steps=len(arrays["joint_position"]),
                success=bool(info.get("task_success", False)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--k", type=float, default=2.2)
    parser.add_argument("--budget", type=float, default=0.05)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = default_velocity_residual_fixtures()
    jobs = []
    # Training severities fx0-fx2 (fx3 held out) with side coverage.
    for i in (0, 1, 2):
        jobs.append((fixtures[i], f"rod_fx{i}_a.npz", 20260820 + i, None))
    jobs.append((fixtures[1], "rod_fx1_posx.npz", 20260831, "positive_x"))
    jobs.append((fixtures[2], "rod_fx2_negx.npz", 20260832, "negative_x"))
    # Neutral no-rod trace (rod parked).
    jobs.append((replace(fixtures[1], rod_start_time_s=99.0), "no_rod.npz", 20260833, None))
    for fixture, name, seed, side in jobs:
        summary = record(args.menagerie, fixture, args.out_dir / name,
                         k=args.k, budget=args.budget, seed=seed, side=side)
        print(summary, flush=True)


if __name__ == "__main__":
    main()
