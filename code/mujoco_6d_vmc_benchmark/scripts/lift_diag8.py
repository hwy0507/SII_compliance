#!/usr/bin/env python3
"""v4 dynamic-plank sweep: does the sweeping tilted plank strike the ARM
(hand/wrist/forearm) cleanly mid-lift, with zero object/finger contact and
zero pre-strike contact?  Teacher must complete, FW must fail."""
from __future__ import annotations

import os as _os
from collections import defaultdict

import mujoco
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
_os.environ["LIFT_PLANK_MODE"] = "launch"
import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force
from wbc_velocity_residual_env import VelocityResidualFixture

BAD = {"target_object", "left_finger", "right_finger"}
GOOD = {"hand", "fr3_link5", "fr3_link6", "fr3_link7", "fr3_link4"}


def plank_env(stroke, height, start, seed=7):
    fx = VelocityResidualFixture(stroke, height, start,
                                 impactor_type="plank", rod_approach_side="negative_y",
                                 rod_center_x_m=0.55, rod_center_y_m=0.0, rod_cycles=1)
    L._os.environ.pop("LIFT_BOARD_X_OFF", None)
    return L.make_env(None, seed, tilt=None, fixture=fx)


def probe(env, policy=None, teacher=None):
    env.reset(seed=7, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    board = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "rod_geom")
    who = defaultdict(float)
    first = {}
    bad_secs, early_secs = 0.0, 0.0
    fint = peak = 0.0
    done, step = False, 0
    while not done:
        t = step * 0.04
        f = 0.0
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            wrench = np.zeros(6)
            mujoco.mj_contactForce(env.model, env.data, c, wrench)
            other = None
            if con.geom1 == board:
                other = con.geom2
            elif con.geom2 == board:
                other = con.geom1
            if other is None:
                continue
            f += float(np.linalg.norm(wrench[:3]))
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                     env.model.geom_bodyid[other]) or "?"
            who[body] += 0.04
            first.setdefault(body, t)
            if body in BAD:
                bad_secs += 0.04
            if t < 2.7:
                early_secs += 0.04
        fint += f * 0.04
        peak = max(peak, f)
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
    return who, first, bad_secs, early_secs, fint, peak


import sys
def plank_env2(stroke, height, start, cycles):
    fx = VelocityResidualFixture(stroke, height, start,
                                 impactor_type="plank", rod_approach_side="negative_y",
                                 rod_center_x_m=0.55, rod_center_y_m=0.0,
                                 rod_cycles=cycles, cycle_period_s=0.80)
    return L.make_env(None, 7, tilt=None, fixture=fx)

def plank_env(s_, h_, t_, seed=7, v0=0.8):
    # launch mode: rod_stroke_m reused as launch speed (m/s)
    fx = VelocityResidualFixture(v0, h_, t_,
                                 impactor_type="plank", rod_approach_side="negative_y",
                                 rod_center_x_m=0.55, rod_center_y_m=0.0,
                                 rod_cycles=1, cycle_period_s=0.80)
    return L.make_env(None, seed, tilt=None, fixture=fx)

_os.environ["LIFT_PLANK_FORCE"] = "80"
_os.environ["LIFT_PLANK_KV"] = "40"
for start in (3.0,):
  for window in (1.0,):
    _os.environ["LIFT_PLANK_WINDOW"] = str(window)
    for height in (0.74, 0.76):
        v0 = 1.0
        stroke = v0
        env = plank_env(stroke, height, start)
        who, first, bad, early, fint_t, peak_t = probe(env, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
        env.close()
        m_t = L.rollout(plank_env(stroke, height, start), 7, teacher=L.LiftTeacher(y_yield=0.85, pre_t=2.70))
        env = plank_env(stroke, height, start)
        whof, firstf, badf, earlyf, fint_f, peak_f = probe(env, policy=NeutralPolicy())
        env.close()
        m_f = L.rollout(plank_env(stroke, height, start), 7, policy=NeutralPolicy())
        tag = f"t0={start} w={window} h={height}"
        print(f"{tag:18s} TEA done={int(m_t['completed'])} bad={bad:.2f} early={early:.2f} "
              f"Fint={fint_t:5.0f} peak={peak_t:4.0f} who={ {k: round(v,2) for k,v in who.items()} }")
        print(f"{'':18s} FW  done={int(m_f['completed'])} bad={badf:.2f} early={earlyf:.2f} "
              f"Fint={fint_f:5.0f} peak={peak_f:4.0f}")
