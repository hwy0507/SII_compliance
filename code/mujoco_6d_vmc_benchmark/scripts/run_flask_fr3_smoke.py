#!/usr/bin/env python3
"""Deterministic development smoke for the FR3 FLASK joint planner."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from flask_joint_planner import FlaskJointPlanner, FlaskPlannerConfig


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    lower = np.array([-2.7437, -1.7837, -2.9007, -3.0421, -2.8065, 0.5445, -3.0159])
    upper = np.array([2.7437, 1.7837, 2.9007, -0.1518, 2.8065, 4.5169, 3.0159])
    velocity = np.array([2.17, 2.17, 2.17, 2.17, 2.61, 2.61, 2.61])
    acceleration = np.full(7, 10.0)
    start = np.array([-0.8, -0.7, 0.6, -1.8, -0.5, 2.2, 0.4])
    goal = np.array([0.8, 0.7, -0.6, -1.0, 0.5, 1.4, -0.4])

    def collision(q: np.ndarray) -> bool:
        # A synthetic joint-space keep-out region makes the direct edge fail,
        # exercising the sampling tree. Replace this callback by
        # MuJoCoFR3CollisionChecker for scene-aware planning.
        return abs(float(q[0])) < 0.14 and abs(float(q[1])) < 0.40

    config = FlaskPlannerConfig(
        velocity_limits=velocity,
        acceleration_limits=acceleration,
        joint_lower=lower,
        joint_upper=upper,
        steering_time=0.45,
        min_steering_time=0.08,
        max_steering_time=2.5,
        samples_per_segment=31,
        max_iterations=1800,
        goal_bias=0.20,
        seed=20261002,
    )
    planner = FlaskJointPlanner(config, collision_fn=collision)
    started = time.perf_counter()
    trajectory = planner.plan(start, goal)
    elapsed_ms = 1000.0 * (time.perf_counter() - started)
    if trajectory is None:
        raise SystemExit("FLASK smoke failed to find a trajectory")
    times, q, velocity_samples, acceleration_samples = trajectory.sample_times(40)
    report = {
        "protocol": "development_smoke",
        "planner": "flask_joint_planner_v1",
        "seed": config.seed,
        "dof": trajectory.dof,
        "segments": len(trajectory.segments),
        "duration_s": trajectory.duration,
        "planning_time_ms": elapsed_ms,
        "collision_samples": int(sum(collision(sample) for sample in q)),
        "max_abs_velocity_radps": float(np.max(np.abs(velocity_samples))),
        "max_abs_acceleration_radps2": float(np.max(np.abs(acceleration_samples))),
        "start_q": start.tolist(),
        "goal_q": goal.tolist(),
        "goal_error_inf": float(np.max(np.abs(trajectory.goal[0] - goal))),
        "constraints_pass": bool(
            np.all(q >= lower - 1e-9)
            and np.all(q <= upper + 1e-9)
            and np.all(np.abs(velocity_samples) <= velocity[None, :] + 1e-8)
            and np.all(np.abs(acceleration_samples) <= acceleration[None, :] + 1e-7)
            and not any(collision(sample) for sample in q)
        ),
        "note": "Synthetic joint-space obstacle; no MuJoCo geometry or hardware claim.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
