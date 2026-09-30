#!/usr/bin/env python3
"""VERIFY the blocking-board scenario:
1. Block NEVER touches the board (blk=0.0s)
2. GRIPPER (fingers/hand) hits the board
3. NO clipping (board thick 15mm, stiff contact)
4. Someone CAN complete the task
5. Render a frame at contact time for visual confirmation
"""
from __future__ import annotations

import os as _os
from collections import defaultdict

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np

import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force


def verify(height, target):
    _os.environ["BLOCK_BOARD_TARGET"] = str(target)
    env = L.build_env("blocking", height, 3.0, seed=7)
    env.reset(seed=7, options={"fixture_index": 0})

    # contact tracking
    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "moving_obstacle_geom")
    who = defaultdict(float)
    max_pen = 0.0
    done, step = False, 0
    contact_frame = None
    renderer = None
    while not done:
        t = step * 0.04
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            gid = con.geom2 if con.geom1 == board_id else (con.geom1 if con.geom2 == board_id else None)
            if gid is None:
                continue
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                     env.model.geom_bodyid[gid]) or "?"
            who[body] += 0.04
            max_pen = max(max_pen, float(con.dist))
        # render contact frame
        if 3.4 <= t <= 3.5 and renderer is None:
            env.model.vis.global_.offwidth = 1280
            env.model.vis.global_.offheight = 720
            renderer = mujoco.Renderer(env.model, 720, 1280)
            cam = mujoco.MjvCamera()
            cam.lookat = np.array([0.50, 0.0, 0.62])
            cam.distance = 0.70
            cam.azimuth = 180
            cam.elevation = -5
            renderer.update_scene(env.data, camera=cam)
            contact_frame = renderer.render()
        _, _, done, _, _ = env.step(np.zeros(7))
        step += 1
    if renderer:
        renderer.close()
    env.close()

    # teacher/FW completion
    env2 = L.build_env("blocking", height, 3.0, seed=7)
    tea = L.rollout(env2, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.7))
    env2.close()
    env3 = L.build_env("blocking", height, 3.0, seed=7)
    fw = L.rollout(env3, 7, NeutralPolicy())
    env3.close()

    blk = who.get("target_object", 0)
    fing = who.get("left_finger", 0) + who.get("right_finger", 0)
    hand_t = who.get("hand", 0)
    arm = sum(v for k, v in who.items() if k.startswith("fr3_link"))

    print(f"  h={height:.2f} tgt={target:.2f}: blk={blk:.1f}s fing={fing:.1f}s "
          f"hand={hand_t:.1f}s arm={arm:.1f}s pen={max_pen*1000:.1f}mm "
          f"FW_ok={int(fw['completed'])} TEA_ok={int(tea['completed'])} "
          f"TEA_pk={tea['peak']:.0f}N dg={tea['dodge_mm']:.0f}mm")

    if contact_frame is not None:
        from imageio.v3 import imwrite
        imwrite(f"/tmp/block_verify_h{height:.2f}_t{target:.2f}.png", contact_frame)
        print(f"  -> frame saved /tmp/block_verify_h{height:.2f}_t{target:.2f}.png")

    return blk == 0.0 and (fing > 0 or hand_t > 0) and tea["completed"]


print("== blocking-board verification ==")
for h in (0.62, 0.64, 0.66, 0.68):
    for tgt in (0.28, 0.32):
        ok = verify(h, tgt)
        if ok:
            print(f"  *** PASS at h={h} tgt={tgt} ***")
print("DONE")
