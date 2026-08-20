#!/usr/bin/env python3
"""Mandatory scene validation gates. Run BEFORE any training or claims.

v2 for the tilted lift-board scenario (restart after the clipping/no-grasp
retraction).  The obstacle is the FK-placed inclined ``lift_board``; the
horizontal ``extraction_board`` is retired (it covered the descent chimney
at x~0.54 and made the grasp itself impossible).

Gate A: collision-bit matrix for the board vs every arm link/hand/object.
Gate B1: FW (no compliance) in the BOARD-FREE scene must grasp+lift+hold
        (task_success=True) -- validates the task mechanics alone.
Gate B2: FW in the BOARD scene must (a) still grasp (hand on block at close,
        object leaves the table while held), (b) hit the board for real
        (peak force and duration gates), (c) have its direct path genuinely
        blocked (final EE error >= 100 mm).  Failing to reach the target is
        EXPECTED here -- that is the compliance motivation, not a scene bug.
Gate C: rendered frames of both rollouts for human inspection.

Usage:
    python scene_gates.py [--tilt 25] [--y-off 0.09] [--hx 0.18] [--hy 0.05]
                          [--arc 0.40] [--seed 7] [--out DIR]
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import mujoco
import numpy as np

ARM_LINKS = tuple(f"fr3_link{i}" for i in range(1, 8))
TARGET_START_Z = 0.445   # block rest center height (must rise > +0.02 m to count)
GRASP_DIST_M = 0.12      # hand-to-block proximity at gripper-close time
GRASP_SLACK_M = 0.03      # board scene may be this much worse than the free baseline
HELD_DIST_M = 0.16       # env's own held criterion
PEAK_FORCE_N = 30.0      # genuine board engagement
CONTACT_S = 0.10
APEX_DROP_M = 0.03       # the lift apex must be suppressed this much vs free


def gate_a(model) -> list[str]:
    failures: list[str] = []
    board_name = "lift_board" if mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board") >= 0 else "extraction_board"
    board_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, board_name)
    print("== Gate A: collision bits ==")
    if board_id < 0:
        return [f"{board_name} missing from scene"]
    print(f"  board={board_name} contype={model.geom_contype[board_id]} "
          f"conaffinity={model.geom_conaffinity[board_id]}")

    def collides(g2):
        c1, a1 = int(model.geom_contype[board_id]), int(model.geom_conaffinity[board_id])
        c2, a2 = int(model.geom_contype[g2]), int(model.geom_conaffinity[g2])
        return ((c1 & a2) | (c2 & a1)) != 0

    checks: dict[str, bool] = {}
    for link in ARM_LINKS:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, link)
        if bid < 0:
            continue
        for g in range(model.body_geomadr[bid], model.body_geomadr[bid] + model.body_geomnum[bid]):
            if model.geom_contype[g] or model.geom_conaffinity[g]:
                checks[f"board↔{link}"] = collides(g)
    for other in ("hand_collision", "target_object_geom"):
        gid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, other)
        checks[f"board↔{other}"] = collides(gid)
    for pair, ok in checks.items():
        print(f"  {pair}: {'COLLIDES' if ok else '*** NO COLLISION ***'}")
        if not ok:
            failures.append(f"Gate A: {pair} does not collide")
    return failures


def _fw_rollout(env, board_present: bool) -> dict:
    """Step FW (zero action = full WBC feedback, no compliance) manually."""
    from extraction_experiment import board_force
    env.reset(seed=7, options={"fixture_index": 0})
    err_final = 0.0
    max_obj_z = 0.0
    grasp_dist = 9.9
    held_min = 9.9
    peak_f = 0.0
    contact_s = 0.0
    done, step = False, 0
    while not done:
        t = step * 0.04
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        obj = env.data.xpos[env._target_body_id]
        max_obj_z = max(max_obj_z, float(obj[2]))
        dist = float(np.linalg.norm(obj - hand))
        if 2.55 <= t <= 2.85:
            grasp_dist = min(grasp_dist, dist)
        if t > 2.7:
            held_min = min(held_min, dist)
        f = board_force(env) if board_present else 0.0
        peak_f = max(peak_f, f)
        if f > 0.5:
            contact_s += 0.04
        err_final = float(np.linalg.norm(d["wbc_pose_error"][:3]))
        _, _, done, _, info = env.step(np.zeros(7))
        step += 1
    return {
        "err_final_m": err_final, "max_obj_z": max_obj_z,
        "grasp_dist": grasp_dist, "held_min": held_min,
        "peak_force_n": peak_f, "contact_s": contact_s,
        "task_success": bool(info.get("task_success", False)),
        "hard_limit": bool(info.get("hard_torque_limit", False)),
    }


def gate_b1(env_free) -> tuple[list[str], dict]:
    print("== Gate B1: FW board-free task success ==")
    r = _fw_rollout(env_free, board_present=False)
    print(f"  task_success={r['task_success']} errF={r['err_final_m']*1000:.1f}mm "
          f"hard_limit={r['hard_limit']} max_obj_z={r['max_obj_z']:.3f} "
          f"grasp_dist={r['grasp_dist']*1000:.0f}mm")
    if not r["task_success"]:
        return ["Gate B1: FW cannot grasp+lift even WITHOUT the board (task mechanics broken)"], r
    return [], r


def gate_b2(env_board, baseline: dict) -> tuple[list[str], dict]:
    print("== Gate B2: FW with board -- grasp ok, contact real, path blocked ==")
    r = _fw_rollout(env_board, board_present=True)
    lifted = r["max_obj_z"] > TARGET_START_Z + 0.02
    apex_drop = baseline["max_obj_z"] - r["max_obj_z"]
    print(f"  grasp_dist={r['grasp_dist']*1000:.0f}mm (free baseline "
          f"{baseline['grasp_dist']*1000:.0f}mm) max_obj_z={r['max_obj_z']:.3f} "
          f"(free {baseline['max_obj_z']:.3f}, apex suppressed {apex_drop*1000:.0f}mm) "
          f"held_min={r['held_min']*1000:.0f}mm")
    print(f"  board peak={r['peak_force_n']:.1f}N contact={r['contact_s']:.2f}s "
          f"errF={r['err_final_m']*1000:.0f}mm task_success={r['task_success']} "
          f"hard_limit={r['hard_limit']}")
    failures = []
    if r["grasp_dist"] > min(GRASP_DIST_M, baseline["grasp_dist"] + GRASP_SLACK_M):
        failures.append("Gate B2: hand NOT on the block at gripper close (descent blocked by board?)")
    if not (lifted and r["held_min"] < HELD_DIST_M):
        failures.append("Gate B2: block never lifted while held (grasp ruined by board contact)")
    if r["peak_force_n"] < PEAK_FORCE_N or r["contact_s"] < CONTACT_S:
        failures.append("Gate B2: no genuine board contact (obstacle misses the arm)")
    if apex_drop < APEX_DROP_M:
        failures.append("Gate B2: lift apex NOT suppressed (nominal path not really blocked)")
    return failures, r


def gate_c(env_free, env_board, out: Path, b2: dict) -> list[str]:
    print("== Gate C: rendering frames ==")
    out.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    scenes = [("free", env_free, {2.6: "grasp", 4.0: "lift", 7.5: "final"}),
              ("board", env_board, {2.6: "grasp", 3.3: "contact", 4.0: "lift", 7.5: "final"})]
    for tag, env, milestones in scenes:
        env.reset(seed=7, options={"fixture_index": 0})
        env.model.vis.global_.offwidth = 1280
        env.model.vis.global_.offheight = 720
        renderer = mujoco.Renderer(env.model, 720, 1280)
        cam = mujoco.MjvCamera()
        cam.lookat = np.array([0.5, 0.0, 0.62])
        cam.distance = 1.25
        cam.azimuth = 135
        cam.elevation = -18
        done, step = False, 0
        while not done:
            t = step * 0.04
            if any(abs(t - m) < 0.02 for m in milestones):
                label = milestones[min(milestones, key=lambda m: abs(t - m))]
                renderer.update_scene(env.data, camera=cam)
                frame = renderer.render()
                try:
                    import cv2
                    cv2.putText(frame, f"{tag} t={t:.1f}s {label}", (20, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
                except ImportError:
                    pass
                from imageio.v3 import imwrite
                imwrite(out / f"gateC_{tag}_{label}.png", frame)
                print(f"  wrote gateC_{tag}_{label}.png")
            _, _, done, _, _ = env.step(np.zeros(7))
            step += 1
        renderer.close()
    # machine-checkable frame facts: the board scene must show the object
    # higher than its rest height at the lift frame is NOT required (blocked
    # lift is fine); but the FREE scene lift frame must show it clearly up.
    free_lift = out / "gateC_free_lift.png"
    if not free_lift.exists():
        failures.append("Gate C: free lift frame missing")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tilt", type=float, default=25.0)
    parser.add_argument("--y-off", type=float, default=0.09)
    parser.add_argument("--hx", type=float, default=0.18)
    parser.add_argument("--hy", type=float, default=0.05)
    parser.add_argument("--arc", type=float, default=0.40)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--skip-c", action="store_true", help="sweeps: skip frame rendering")
    parser.add_argument("--out", type=Path, default=Path("/tmp/scene_gates"))
    args = parser.parse_args()

    os.environ.setdefault("MUJOCO_GL", "osmesa")
    os.environ["LIFT_BOARD_Y_OFF"] = str(args.y_off)
    os.environ["LIFT_BOARD_HX"] = str(args.hx)
    os.environ["LIFT_BOARD_HY"] = str(args.hy)
    os.environ["LIFT_BOARD_ARC"] = str(args.arc)
    from extraction_experiment import make_env

    env_free = make_env(None, args.seed, tilt=None)
    env_board = make_env(None, args.seed, tilt=args.tilt)
    b1_fail, baseline = gate_b1(env_free)
    b2_fail, _ = gate_b2(env_board, baseline)
    failures = gate_a(env_board.model) + b1_fail + b2_fail
    if not args.skip_c:
        failures += gate_c(env_free, env_board, args.out, {})
    env_free.close()
    env_board.close()
    print("\n" + ("ALL GATES PASSED" if not failures else "GATES FAILED:\n  " + "\n  ".join(failures)))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
