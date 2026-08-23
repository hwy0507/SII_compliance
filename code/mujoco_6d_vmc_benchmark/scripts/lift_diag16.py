#!/usr/bin/env python3
from __future__ import annotations
import os as _os
from collections import defaultdict
_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np
import lift_experiment as L
from extraction_experiment import NeutralPolicy

L.STATIC_Z = 0.06
L.HX = 0.10
_os.environ["LIFT_BOARD_TILT_DEG"] = "25.0"
_os.environ["LIFT_BOARD_X_OFF"] = "0.0"

for hy in (0.015, 0.02, 0.025, 0.03):
    L.STATIC_HY = hy
    env = L.build_env("static", 0.03, 25.0, seed=7)
    env.reset(seed=7, options={"fixture_index": 0})
    board = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    who = defaultdict(float)
    done, step = False, 0
    while not done:
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            gid = con.geom2 if con.geom1 == board else (con.geom1 if con.geom2 == board else None)
            if gid is None: continue
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY, env.model.geom_bodyid[gid]) or "?"
            who[body] += 0.04
        _, _, done, _, _ = env.step(np.zeros(7))
        step += 1
    env.close()
    env2 = L.build_env("static", 0.03, 25.0, seed=7)
    tea = L.rollout(env2, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.7)); env2.close()
    env3 = L.build_env("static", 0.03, 25.0, seed=7)
    fw = L.rollout(env3, 7, NeutralPolicy()); env3.close()
    blk = who.get("target_object", 0)
    fing = who.get("left_finger", 0) + who.get("right_finger", 0)
    arm = sum(v for k, v in who.items() if k.startswith("fr3_link") or k == "hand")
    print(f"hy={hy:.3f}  blk={blk:.1f}s fing={fing:.1f}s arm={arm:.1f}s  "
          f"FW_ok={int(fw['completed'])} TEA_ok={int(tea['completed'])} "
          f"TEA_pk={tea['peak']:.0f} TEA_dg={tea['dodge_mm']:.0f}mm")
