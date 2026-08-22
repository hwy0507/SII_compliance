#!/usr/bin/env python3
"""WHY does the block escape?  Log fingers/contacts/forces around ejection."""
from __future__ import annotations

import os as _os

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np

import lift_experiment as L
from extraction_experiment import NeutralPolicy, board_force


def diagnose(policy, name):
    env = L.build_env("static", 0.05, 25.0, seed=7)
    env.reset(seed=7, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    f1 = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_JOINT, "finger_joint1")
    f1q = env.model.jnt_qposadr[f1]
    grip = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_ACTUATOR, "gripper")
    obj = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
    rows = []
    done, step = False, 0
    while not done:
        t = step * 0.04
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        o = env.data.xpos[env._target_body_id]
        dist = float(np.linalg.norm(o - hand))
        # contacts involving the object
        obj_touch, board_touch = "", ""
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            pair = {con.geom1, con.geom2}
            if obj in pair:
                other = con.geom2 if con.geom1 == obj else con.geom1
                nm = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, other) or (
                    "B:" + (mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                           env.model.geom_bodyid[other]) or "?"))
                w = np.zeros(6)
                mujoco.mj_contactForce(env.model, env.data, c, w)
                obj_touch += f"{nm}:{np.linalg.norm(w[:3]):.0f}N "
        af = float(env.data.actuator_force[grip])
        rows.append((t, float(env.data.qpos[f1q]), af, dist, float(o[2]),
                     board_force(env), obj_touch))
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        a = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        _, _, done, _, _ = env.step(a)
        step += 1
    env.close()
    print(f"### {name}")
    held = 0.0
    for i, (t, fq, af, dist, oz, bf, ot) in enumerate(rows):
        if dist < 0.16 and oz > 0.45:
            held = t
        if t > 2.0 and i % 3 == 0 and t < 7.2:
            lost = dist > 0.2
            print(f"  t={t:4.2f} finger_q={fq*1000:5.1f}mm gripF={af:6.1f}N "
                  f"hand-obj={dist*1000:4.0f}mm objz={oz:.2f} boardF={bf:5.0f}N "
                  f"obj_touch=[{ot}]{'  <== LOST' if lost else ''}")
    print(f"  held until {held:.2f}s")


diagnose(NeutralPolicy(), "FW on corridor (static 25)")
