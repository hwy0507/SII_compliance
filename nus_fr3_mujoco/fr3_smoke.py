"""Server-side MuJoCo FR3 smoke test."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .mujoco_env import FR3MuJoCoEnv
from .nominal_controller import FR3NominalVelocityServo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="/home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3/fr3.xml",
    )
    parser.add_argument("--steps", type=int, default=25)
    args = parser.parse_args()

    env = FR3MuJoCoEnv(Path(args.model))
    state = env.reset()
    controller = FR3NominalVelocityServo(env)
    q_target = state.q.copy()
    q_target[0] += 0.05
    from .contracts import FR3Waypoint

    waypoint = FR3Waypoint(0.0, tuple(q_target), "smoke")
    max_error = 0.0
    for _ in range(args.steps):
        state = env.state()
        command = controller.compute(state, waypoint)
        state = env.step(command.torque, q_cmd=command.q_cmd, qdot_cmd=command.qdot_cmd)
        max_error = max(max_error, float(np.linalg.norm(waypoint.q - state.q)))
    print(
        "fr3 mujoco smoke passed: "
        f"nq={env.model.nq} nv={env.model.nv} nu={env.model.nu} "
        f"time={state.time_s:.4f}s max_error={max_error:.6f} "
        f"contacts={env.contact_summary()['contact_count']}"
    )


if __name__ == "__main__":
    main()
