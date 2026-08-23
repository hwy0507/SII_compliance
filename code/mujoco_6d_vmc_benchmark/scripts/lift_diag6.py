#!/usr/bin/env python3
"""WHO touches the board? Log contact bodies (not just force) for
FW / teacher / ESN on the default board."""
from __future__ import annotations

import os as _os
from collections import defaultdict

import mujoco
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy


def contact_parts(env, policy=None, teacher=None):
    env.reset(seed=7, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    board = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    who = defaultdict(float)   # body name -> contact seconds
    first = {}
    done, step = False, 0
    while not done:
        t = step * 0.04
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            gid = None
            if con.geom1 == board:
                gid = con.geom2
            elif con.geom2 == board:
                gid = con.geom1
            if gid is None:
                continue
            body = env.model.geom_bodyid[gid]
            name = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY, body) or f"geom{gid}"
            who[name] += 0.04
            first.setdefault(name, t)
        d = env.diagnostics()
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            hand = env.data.xpos[env._hand_id]
            from extraction_experiment import board_force
            a = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]), hand_y=float(hand[1]),
                                       hand_z=float(hand[2]), contact=board_force(env) > 2.0,
                                       time_s=t,
                                       nominal_y=float(d["nominal_position"][1])), dtype=float)
        else:
            a = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        _, _, done, _, _ = env.step(a)
        step += 1
    return who, first


import itertools
for z_off, y_off in itertools.product((0.06, 0.08, 0.10), (0.05, 0.07)):
    L.Z_OFF_DEFAULT = z_off
    L.Y_OFF_DEFAULT = y_off
    L.HY = 0.06
    L.HX = 0.20
    L._os.environ["LIFT_BOARD_TILT_DEG"] = "15.0"
    print(f"\n===== z={z_off} y={y_off} =====")
esn = None
for name, pol, tea in (("FW", NeutralPolicy(), None),):
    env = L.build_env(L.Y_OFF_DEFAULT, L.TILT_DEFAULT, 7)
    who, first = contact_parts(env, policy=pol, teacher=tea)
    env.close()
    print(f"### {name}")
    for body, secs in sorted(who.items(), key=lambda kv: -kv[1]):
        print(f"  {body:20s} {secs:5.2f}s (first at t={first[body]:.2f}s)")
