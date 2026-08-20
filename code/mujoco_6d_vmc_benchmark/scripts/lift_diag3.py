#!/usr/bin/env python3
"""Sweep board friction / tilt / solref to find a passable-but-demanding scene:
teacher should clear hard-limit (ok=1) with low force; FW contrast preserved."""
from __future__ import annotations

import os as _os
import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force

LIMITS = np.asarray([87.0] * 4 + [12.0] * 3)


def stretch_lift(env, lift_end: float):
    env.reference.times = env.reference.times.copy()
    env.reference.times[3] = lift_end


def run(name, *, y=0.85, z=0.0, slow=1.0, solref=0.04, friction=0.06,
        tilt=25.0, lift_end=4.1, quiet=False):
    _os.environ["LIFT_BOARD_SOLREF"] = str(solref)
    _os.environ["LIFT_BOARD_FRICTION"] = str(friction)
    env = L.build_env(L.Y_OFF_DEFAULT, tilt, 7)
    stretch_lift(env, lift_end)
    env.reset(seed=7, options={"fixture_index": 0})
    stretch_lift(env, lift_end)
    teacher = L.LiftTeacher(y_yield=y, z_yield=z, slow=slow)
    policy = None if y or slow else NeutralPolicy()
    first_contact, trips = None, []
    fint, peak, ct, apex = 0.0, 0.0, 0.0, 0.0
    err = 0.0
    done, step = False, 0
    while not done:
        t = step * 0.04
        f = board_force(env)
        fint += f * 0.04
        peak = max(peak, f)
        ct += 0.04 if f > 0.5 else 0.0
        obj = env.data.xpos[env._target_body_id]
        apex = max(apex, float(obj[2]))
        if f > 2.0 and first_contact is None:
            first_contact = t
        tau = env._last_torque_components["total"][:7] if env._last_torque_components else np.zeros(7)
        if np.any(np.abs(tau) > 0.98 * LIMITS):
            trips.append(t)
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        if teacher is not None and (y or slow):
            action = np.asarray(teacher.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
                hand_x=float(hand[0]), hand_y=float(hand[1]), hand_z=float(hand[2]),
                contact=f > 2.0, time_s=t), dtype=float)
        else:
            action = np.zeros(7)
        err = float(np.linalg.norm(d["wbc_pose_error"][:3]))
        _, _, done, _, info = env.step(action)
        step += 1
    print(f"{name:34s} ok={int(info['task_success'])} Fint={fint:6.1f} peak={peak:5.0f}N "
          f"ct={ct:4.2f}s trips={len(trips):3d} apex={apex:.3f} errF={err*1000:5.1f}mm")
    env.close()
    return info


run("T y0.85 fric0.06 solref0.04")
run("T y0.85 fric0.03 solref0.04", friction=0.03)
run("T y0.85 fric0.06 tilt30", tilt=30.0)
run("T y0.85 fric0.03 tilt30", friction=0.03, tilt=30.0)
run("T y0.85 fric0.06 slow4.6", lift_end=4.6)
run("FW fric0.06 (contrast?)", y=0.0, slow=0.0)
run("FW fric0.03 tilt30", y=0.0, slow=0.0, friction=0.03, tilt=30.0)
