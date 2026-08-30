from pathlib import Path

import mujoco
import numpy as np

from .mujoco_env import FR3MuJoCoEnv
from .tabletop_demo import HOME, build_segments, look_at_quaternion, solve_position_nullspace_view_ik


def main() -> None:
    env = FR3MuJoCoEnv(Path("scenes/fr3_office_v28_dynamic_predictable.xml"))
    env.reset(HOME)
    _, _, _, _, _, candidates = build_segments(env)
    candidate = next(c for c in candidates if c.name == "approach_left+place_left")
    hand_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "fr3_hand")
    camera_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_CAMERA, "wrist_rgbd")
    for segment in candidate.segments:
        if segment.phase not in {"LIFT", "CARRY AROUND CLUTTER"}:
            continue
        env.data.qpos[env.qpos_adrs] = segment.q
        mujoco.mj_forward(env.model, env.data)
        hand = env.data.xpos[hand_id].copy()
        focus = np.array([0.32, -0.12, 0.96], dtype=np.float64)
        q_view = solve_position_nullspace_view_ik(
            env, hand_id, hand, look_at_quaternion(hand, focus), segment.q, view_gain=0.9
        )
        env.data.qpos[env.qpos_adrs] = q_view
        mujoco.mj_forward(env.model, env.data)
        cam_pos = env.data.cam_xpos[camera_id].copy()
        cam_rot = env.data.cam_xmat[camera_id].reshape(3, 3)
        forward = -cam_rot[:, 2]
        desired = focus - cam_pos
        desired /= max(np.linalg.norm(desired), 1.0e-9)
        print(segment.phase, "hand", hand.tolist(), "cam", cam_pos.tolist(), "forward", forward.tolist(), "desired", desired.tolist(), "dot", float(np.dot(forward, desired)))


if __name__ == "__main__":
    main()
