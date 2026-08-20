#!/usr/bin/env python3
"""Sweep board geometry so that the WRIST/HAND strikes the face during the
lift and NOTHING ELSE touches (no object, no fingers, no descent contact).

Objective per config (teacher + FW rollouts):
  good = contact-seconds by {hand, fr3_link6, fr3_link7} in t>2.6
  bad  = ANY contact by {target_object, left_finger, right_finger}
         or ANY contact before t=2.6
Report: good/bad, who touched, teacher/FW completion."""
from __future__ import annotations

import os as _os
from collections import defaultdict

import mujoco
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force

GOOD = {"hand", "fr3_link6", "fr3_link7", "fr3_link5"}
BAD = {"target_object", "left_finger", "right_finger"}


def probe(env, policy=None, teacher=None):
    env.reset(seed=7, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    board = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    who = defaultdict(float)
    bad_secs, early_secs = 0.0, 0.0
    fint = peak = 0.0
    done, step = False, 0
    while not done:
        t = step * 0.04
        f = board_force(env)
        fint += f * 0.04
        peak = max(peak, f)
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            gid = None
            if con.geom1 == board:
                gid = con.geom2
            elif con.geom2 == board:
                gid = con.geom1
            if gid is None:
                continue
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                     env.model.geom_bodyid[gid]) or "?"
            who[body] += 0.04
            if body in BAD:
                bad_secs += 0.04
            if t < 2.6:
                early_secs += 0.04
        d = env.diagnostics()
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            hand = env.data.xpos[env._hand_id]
            a = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]),
                                       hand_y=float(hand[1]), hand_z=float(hand[2]),
                                       contact=f > 2.0, time_s=t,
                                       nominal_y=float(d["nominal_position"][1])), dtype=float)
        else:
            a = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        _, _, done, _, _ = env.step(a)
        step += 1
    good_secs = sum(v for k, v in who.items() if k in GOOD)
    return good_secs, bad_secs, early_secs, dict(who), fint, peak


import os
results = []
for x_off in (0.0, 0.05):
    for hx in (0.10, 0.14):
        for z_off in (0.15, 0.18):
            y_off = 0.07
            tilt = 25.0
            hy = 0.08
            L.HX = hx
            os.environ["LIFT_BOARD_X_OFF"] = str(x_off)
            L.Z_OFF_DEFAULT = z_off
            L.HY = hy
            L.TILT_DEFAULT = tilt
            L.Y_OFF_DEFAULT = y_off
            os.environ["LIFT_BOARD_X_OFF"] = str(x_off)
            env = L.build_env(y_off, tilt, 7)
            g, b, e, who, fint_t, peak_t = probe(env, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
            env.close()
            env = L.build_env(y_off, tilt, 7)
            gf, bf, ef, whof, fint_f, peak_f = probe(env, policy=NeutralPolicy())
            env.close()
            tag = (f"x+{x_off} hx={hx} z={z_off}")
            print(f"{tag:26s} TEA good={g:4.2f} bad={b:4.2f} early={e:4.2f} | "
                  f"FW good={gf:4.2f} bad={bf:4.2f} early={ef:4.2f} who(T)={ {k: round(v,2) for k,v in who.items()} }")
            results.append((b + e + bf + ef, -g, tag))
results.sort()
print("\n== ranked (least bad-contact first) ==")
for badsum, negg, tag in results[:6]:
    print(f"  {tag}  badsum={badsum:.2f} good=-{negg:.2f}")
