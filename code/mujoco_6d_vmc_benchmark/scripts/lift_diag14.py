#!/usr/bin/env python3
"""Find the board height where the WRIST/HAND hits (not the block).
tilt=15 deg, sweep z_off/y_off, report which BODY contacts the board."""
from __future__ import annotations

import os as _os
from collections import defaultdict

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np

import lift_experiment as L
from extraction_experiment import NeutralPolicy

for y_off in (0.0, 0.02):
    for hy in (0.05, 0.06):
        L.STATIC_Z = z_off
        L.STATIC_HY = hy
        L.STATIC_Z = 0.03
        L.HX = 0.25
        L._os.environ["LIFT_BOARD_TILT_DEG"] = "15.0"
        env = L.build_env("static", y_off, 15.0, seed=7)
        env.reset(seed=7, options={"fixture_index": 0})
        board = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
        who = defaultdict(float)
        done, step = False, 0
        while not done:
            t = step * 0.04
            for c in range(env.data.ncon):
                con = env.data.contact[c]
                gid = con.geom2 if con.geom1 == board else (con.geom1 if con.geom2 == board else None)
                if gid is None:
                    continue
                body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                         env.model.geom_bodyid[gid]) or "?"
                who[body] += 0.04
            _, _, done, _, _ = env.step(np.zeros(7))
            step += 1
        env.close()
        block_hit = who.get("target_object", 0)
        finger_hit = who.get("left_finger", 0) + who.get("right_finger", 0)
        arm_hit = sum(v for k, v in who.items() if k.startswith("fr3_link") or k == "hand")
        tag = f"y={y_off:.2f} hy={hy:.2f}"
        env2 = L.build_env("static", y_off, 15.0, seed=7)
        fw = L.rollout(env2, 7, NeutralPolicy()); env2.close()
        env3 = L.build_env("static", y_off, 15.0, seed=7)
        tea = L.rollout(env3, 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.7)); env3.close()
        print(f"{tag:20s} block={block_hit:4.1f}s finger={finger_hit:4.1f}s arm={arm_hit:4.1f}s "
              f"FW_ok={int(fw['completed'])} TEA_ok={int(tea['completed'])} "
              f"TEA_peak={tea['peak']:.0f} TEA_dodge={tea['dodge_mm']:.0f}mm")
