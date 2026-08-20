#!/usr/bin/env python3
"""Quantify P1 (impact transient) vs P2 (sustained press) limit trips,
and test scenario-side mitigations: softer contact, slower lift."""
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


def run(name, *, y=0.85, z=0.0, slow=1.0, solref=None, lift_end=4.1):
    if solref is not None:
        _os.environ["LIFT_BOARD_SOLREF"] = str(solref)
    else:
        _os.environ.pop("LIFT_BOARD_SOLREF", None)
    env = L.build_env(L.Y_OFF_DEFAULT, L.TILT_DEFAULT, 7)
    stretch_lift(env, lift_end)
    env.reset(seed=7, options={"fixture_index": 0})
    stretch_lift(env, lift_end)  # reset rebuilds the reference
    teacher = L.LiftTeacher(y_yield=y, z_yield=z, slow=slow)
    first_contact = None
    trips = []          # (t, force) of RL steps with any joint at limit
    done, step = False, 0
    while not done:
        t = step * 0.04
        f = board_force(env)
        if f > 2.0 and first_contact is None:
            first_contact = t
        tau = env._last_torque_components["total"][:7] if env._last_torque_components else np.zeros(7)
        if np.any(np.abs(tau) > 0.98 * LIMITS):
            trips.append((t, f))
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        action = np.asarray(teacher.act(
            d["joint_position"], d["joint_velocity"], d["nominal_twist"],
            pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
            hand_x=float(hand[0]), hand_y=float(hand[1]), hand_z=float(hand[2]),
            contact=f > 2.0, time_s=t), dtype=float)
        _, _, done, _, info = env.step(action)
        step += 1
    fc = first_contact if first_contact else -1
    window = (fc, fc + 0.4)
    p1 = sum(1 for t, _ in trips if window[0] <= t <= window[1])
    p2 = len(trips) - p1
    print(f"{name:24s} ok={int(info['task_success'])} hard={int(info['hard_torque_limit'])} "
          f"fc={fc:5.2f}s trips: P1<0.4s={p1:3d} P2={p2:3d} "
          f"(t {trips[0][0]:.2f}-{trips[-1][0]:.2f})" if trips else
          f"{name:24s} ok={int(info['task_success'])} hard={int(info['hard_torque_limit'])} "
          f"fc={fc:5.2f}s trips: NONE")
    env.close()


run("base y0.85")
run("soft solref0.04", solref=0.04)
run("slow lift_end4.6", lift_end=4.6)
run("soft+slow", solref=0.04, lift_end=4.6)
run("slow-only y0 slow0 (FW)", lift_end=4.6, y=0.0, z=0.0, slow=0.0)
run("soft+slow y0 slow0 (FW)", solref=0.04, lift_end=4.6, y=0.0, z=0.0, slow=0.0)
