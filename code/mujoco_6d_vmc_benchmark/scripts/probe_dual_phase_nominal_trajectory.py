"""Record the board-free physical rollout used to calibrate dual-board geometry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--boards", choices=("enabled", "disabled"), default="disabled")
    args = parser.parse_args()
    fixture = VelocityResidualFixture(0.170, 0.541, 99.0, grasp_time_s=2.4)
    env = PandaWBCVelocityResidualEnv(
        args.menagerie, None, None, "direct_esn", fixtures=(fixture,), rod_enabled=False,
        robot="fr3", wbc_backend="paper_mpc", execution_mode="torque_residual",
        residual_torque_scale=0.02, lift_board_tilt_deg=15.0,
        lift_board_contact_mode="dual_phase_longitudinal", seed=args.seed,
    )
    env.reset(seed=args.seed, options={"fixture_index": 0})
    assert env.model is not None and env.data is not None
    if args.boards == "disabled":
        for board_id in env._dual_board_geom_ids.values():
            env.model.geom_contype[board_id] = 0
            env.model.geom_conaffinity[board_id] = 0
        mujoco.mj_forward(env.model, env.data)
    geom_names = ("hand_collision", "fr3_link7_collision", "fr3_link6_collision")
    geom_ids = {
        name: mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, name)
        for name in geom_names
    }
    samples: list[dict[str, object]] = []
    done = False
    while not done:
        time_s = env.step_count * 0.040
        if env.step_count % 5 == 0:
            samples.append({
                "time_s": time_s,
                "target_position_m": env.data.xpos[env._target_body_id].tolist(),
                "geoms": {
                    name: {
                        "position_m": env.data.geom_xpos[geom_id].tolist(),
                        "rotation": env.data.geom_xmat[geom_id].reshape(3, 3).tolist(),
                    }
                    for name, geom_id in geom_ids.items()
                },
            })
        _, _, terminated, truncated, info = env.step(np.zeros(7, dtype=np.float32))
        done = bool(terminated or truncated)
    payload = {"samples": samples, "terminal": info}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(info, sort_keys=True))


if __name__ == "__main__":
    main()
