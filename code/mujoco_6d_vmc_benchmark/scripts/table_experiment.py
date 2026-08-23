#!/usr/bin/env python3
"""UNDER-TABLE EXTRACTION: complete self-contained experiment.

Scene: A big table top (with legs) above the workspace.  The block sits on
the lower surface BENEATH the table.  The arm reaches under to grasp, then
lifts — the wrist/hand hits the table's UNDERSIDE from directly below.
The compliance must yield to extract the arm past the table's free edge.

Usage (on server):
    python table_experiment.py          # verify + demo GIFs
    python table_experiment.py sweep    # parameter sweep
"""
from __future__ import annotations

import os as _os
import sys
from collections import defaultdict
from pathlib import Path

_os.environ.setdefault("MUJOCO_GL", "osmesa")
_os.environ["LIFT_PLANK_MODE"] = "servo"
_os.environ["LIFT_CUE"] = "0"

import mujoco
import numpy as np

# ── Scene modification: inject the extraction table into the XML ───────
TABLE_TOP_XML = """
  <body name="extraction_table" pos="{tx} {ty} {tz}">
    <geom name="table_top" type="box" size="{hx} {hy} 0.012"
      contype="5" conaffinity="5" rgba="0.55 0.42 0.25 1"
      friction="0.15 0.02 0.002" solref="0.008 1" solimp="0.92 0.99 0.001 0.5 2"/>
    <geom name="table_leg_a" type="cylinder" size="0.012 0.17" pos="{-leg_dx} {-leg_dy} -0.185"
      contype="5" conaffinity="5" rgba="0.45 0.35 0.20 1"/>
    <geom name="table_leg_b" type="cylinder" size="0.012 0.17" pos="{-leg_dx} {leg_dy} -0.185"
      contype="5" conaffinity="5" rgba="0.45 0.35 0.20 1"/>
    <geom name="table_leg_c" type="cylinder" size="0.012 0.17" pos="{leg_dx} {-leg_dy} -0.185"
      contype="5" conaffinity="5" rgba="0.45 0.35 0.20 1"/>
    <geom name="table_leg_d" type="cylinder" size="0.012 0.17" pos="{leg_dx} {leg_dy} -0.185"
      contype="5" conaffinity="5" rgba="0.45 0.35 0.20 1"/>
  </body>
"""

import lift_experiment as L
from extraction_experiment import NeutralPolicy, make_env, board_force


def build_table_env(seed: int = 7, noise: float = 0.0,
                    tx: float = 0.65, ty: float = 0.0, tz: float = 0.78,
                    hx: float = 0.18, hy: float = 0.15):
    """Build the FR3 scene + extraction table (injected via EXTRACTION_TABLE env)."""
    _os.environ["EXTRACTION_TABLE"] = "1"
    _os.environ["EXT_TABLE_X"] = str(tx)
    _os.environ["EXT_TABLE_Y"] = str(ty)
    _os.environ["EXT_TABLE_Z"] = str(tz)
    _os.environ["EXT_TABLE_HX"] = str(hx)
    _os.environ["EXT_TABLE_HY"] = str(hy)
    return make_env(None, seed, noise=noise, tilt=None)


class ExtractionTeacher:
    """Compliance for under-table extraction.

    When the wrist/hand contacts the table underside during the LIFT:
    1. Slow the WBC (stop pushing up into the table)
    2. Yield -x (pull BACK — extract past the table's -x edge)
    3. Release once the hand is past the edge
    """

    def __init__(self, x_yield: float = 0.6, slow: float = 1.0,
                 table_edge_x: float = 0.50, release_s: float = 0.4,
                 phase_guard_s: float = 2.7) -> None:
        self.x_yield = x_yield
        self.slow = slow
        self.table_edge_x = table_edge_x
        self.release_s = release_s
        self.phase_guard_s = phase_guard_s
        self.reset()

    def reset(self) -> None:
        self.engaged = False
        self.lost_s = 0.0

    def act(self, joint_position, joint_velocity, nominal_twist, *,
            pose_error=None, twist_error=None, hand_x=0.0, hand_y=0.0,
            hand_z=0.0, contact=False, time_s=0.0, nominal_y=0.0):
        action = np.zeros(7)
        if time_s < self.phase_guard_s:
            self.reset()
            return action
        if self.engaged:
            self.lost_s = 0.0 if contact else self.lost_s + 0.04
            if hand_x < self.table_edge_x or self.lost_s > self.release_s:
                self.engaged = False
                self.lost_s = 0.0
                return action
        elif contact:
            self.engaged = True
            self.lost_s = 0.0
        if self.engaged:
            action[0] = self.slow
            action[1] = -self.x_yield   # -x: EXTRACT backward past the table edge
        return action


def table_force(env) -> float:
    """Contact force between the extraction table and ANY body."""
    tid = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "table_top")
    if tid < 0:
        return 0.0
    total = 0.0
    for c in range(env.data.ncon):
        con = env.data.contact[c]
        if con.geom1 == tid or con.geom2 == tid:
            wrench = np.zeros(6)
            mujoco.mj_contactForce(env.model, env.data, c, wrench)
            total += float(np.linalg.norm(wrench[:3]))
    return total


def rollout_table(env, seed, policy=None, teacher=None):
    """Rollout with table-contact tracking."""
    env.reset(seed=seed, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    if teacher is not None:
        teacher.reset()
    errors, forces = [], []
    who = defaultdict(float)
    max_obj_z = 0.0
    final_obj_hand = 9.9
    done, info = False, {}
    tid = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "table_top")
    while not done:
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        obj = env.data.xpos[env._target_body_id]
        max_obj_z = max(max_obj_z, float(obj[2]))
        final_obj_hand = float(np.linalg.norm(obj - hand))
        f = table_force(env)
        for c in range(env.data.ncon):
            con = env.data.contact[c]
            gid = con.geom2 if con.geom1 == tid else (con.geom1 if con.geom2 == tid else None)
            if gid is None:
                continue
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY,
                                     env.model.geom_bodyid[gid]) or "?"
            who[body] += 0.04
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            action = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]),
                                            hand_y=float(hand[1]), hand_z=float(hand[2]),
                                            contact=f > 2.0, time_s=float(d["time_s"]),
                                            nominal_y=float(d["nominal_position"][1])), dtype=float)
        elif policy is not None:
            action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        else:
            action = np.zeros(7)
        errors.append(float(np.linalg.norm(d["wbc_pose_error"][:3])))
        forces.append(f)
        _, _, done, _, info = env.step(action)
    completed = bool(max_obj_z > 0.52 and final_obj_hand < 0.16)
    blk = who.get("target_object", 0)
    ee = sum(v for k, v in who.items() if k in ("hand", "left_finger", "right_finger",
                                                 "fr3_link7", "fr3_link6"))
    return dict(completed=completed, peak=float(max(forces)),
                Fint=float(np.sum(forces) * 0.04), errF=float(errors[-1] * 1000),
                max_obj_z=max_obj_z, blk=blk, ee=ee,
                who=dict((k, round(v, 1)) for k, v in who.items()))


def render_gif(env_fn, name, policy_fn, outpath, cam_azim=180):
    """Render a rollout to GIF."""
    env = env_fn()
    env.reset(seed=7, options={"fixture_index": 0})
    env.model.vis.global_.offwidth = 1280
    env.model.vis.global_.offheight = 720
    renderer = mujoco.Renderer(env.model, 720, 1280)
    cam = mujoco.MjvCamera()
    cam.lookat = np.array([0.52, 0.0, 0.62])
    cam.distance = 0.85
    cam.azimuth = cam_azim
    cam.elevation = -5
    frames = []
    done, step = False, 0
    if hasattr(policy_fn, "reset"):
        policy_fn.reset()
    while not done:
        t = step * 0.04
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        f = table_force(env)
        if step % 2 == 0:
            renderer.update_scene(env.data, camera=cam)
            frame = renderer.render()
            try:
                import cv2
                cv2.putText(frame, name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)
                cv2.putText(frame, f"t={t:4.1f}s", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
                if f > 0.5:
                    cv2.putText(frame, f"F={f:.0f}N", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            except ImportError:
                pass
            frames.append(frame.copy())
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if callable(policy_fn):
            action = policy_fn(args, kw, d, hand, f, t, env)
        else:
            action = np.zeros(7)
        _, _, done, _, _ = env.step(action)
        step += 1
    renderer.close()
    env.close()
    from imageio.v3 import imwrite
    imwrite(outpath, frames, duration=40, loop=0)
    print(f"wrote {outpath} ({len(frames)} frames)", flush=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    outdir = Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/docs/lift_results/table")
    outdir.mkdir(parents=True, exist_ok=True)

    if mode == "sweep":
        print("== table parameter sweep ==")
        for tz in (0.74, 0.76, 0.78, 0.80, 0.82):
            for tx in (0.60, 0.65, 0.70):
                _os.environ["EXT_TABLE_X"] = str(tx)
                _os.environ["EXT_TABLE_Z"] = str(tz)
                env = build_table_env(seed=7, tx=tx, tz=tz)
                fw = rollout_table(env, 7, policy=NeutralPolicy())
                env.close()
                env2 = build_table_env(seed=7, tx=tx, tz=tz)
                tea = rollout_table(env2, 7,
                                    teacher=ExtractionTeacher(table_edge_x=tx - 0.18))
                env2.close()
                print(f"tx={tx:.2f} tz={tz:.2f}  FW: ok={int(fw['completed'])} pk={fw['peak']:.0f}N  "
                      f"TEA: ok={int(tea['completed'])} pk={tea['peak']:.0f}N errF={tea['errF']:.1f}mm",
                      flush=True)
        print("SWEEP-DONE")
        return

    # Demo mode
    print("== under-table extraction demo ==")
    env_fn = lambda: build_table_env(seed=7)

    # FW
    env = env_fn()
    fw = rollout_table(env, 7, policy=NeutralPolicy())
    env.close()
    print(f"FW:  ok={int(fw['completed'])} pk={fw['peak']:.0f}N blk={fw['blk']:.1f}s EE={fw['ee']:.1f}s")
    print(f"     who={fw['who']}")

    # Teacher
    tea = ExtractionTeacher(table_edge_x=0.50)
    env2 = env_fn()
    tm = rollout_table(env2, 7, teacher=tea)
    env2.close()
    print(f"TEA: ok={int(tm['completed'])} pk={tm['peak']:.0f}N blk={tm['blk']:.1f}s EE={tm['ee']:.1f}s errF={tm['errF']:.1f}mm")
    print(f"     who={tm['who']}")

    # GIFs
    render_gif(env_fn, "FW",
               lambda args, kw, d, hand, f, t, env:
               np.asarray(NeutralPolicy().act(*args, **kw).bounded_filter_action, dtype=float),
               outdir / "table_FW.gif")
    _tea = ExtractionTeacher(table_edge_x=0.50)
    render_gif(env_fn, "TEACHER",
               lambda args, kw, d, hand, f, t, env:
               np.asarray(_tea.act(*args, **kw, hand_x=float(hand[0]), hand_y=float(hand[1]),
                                   hand_z=float(hand[2]), contact=f > 2.0, time_s=t,
                                   nominal_y=0.0), dtype=float),
               outdir / "table_TEACHER.gif")
    print("TABLE-DEMO-DONE")


if __name__ == "__main__":
    main()
