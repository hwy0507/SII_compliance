#!/usr/bin/env python3
"""Mandatory scene validation gates. Run BEFORE any training or claims.

Gate A: collision-bit matrix -- the exact bug that let the arm ghost through
        the board (links 1/1 vs board 4/4 = no collision).
Gate B: task success -- the exact bug that every metric ignored the grasp.
Gate C: visual frames for human inspection.

Usage:
    python scene_gates.py [--board-underside-z 0.615] [--edge-y 0.05] [--out DIR]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np

ARM_LINKS = tuple(f"fr3_link{i}" for i in range(1, 8))


def gate_a(model) -> list[str]:
    failures: list[str] = []
    board_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "extraction_board")

    def bits(gid):
        return int(model.geom_contype[gid]), int(model.geom_conaffinity[gid])

    def collides(g1, g2):
        c1, a1 = bits(g1)
        c2, a2 = bits(g2)
        return ((c1 & a2) | (c2 & a1)) != 0

    print("== Gate A: collision bits ==")
    if board_id < 0:
        return ["extraction_board missing from scene"]
    print(f"  board: contype={model.geom_contype[board_id]} conaffinity={model.geom_conaffinity[board_id]}")
    checks = {}
    for link in ARM_LINKS:
        bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, link)
        if bid < 0:
            continue
        for g in range(model.body_geomadr[bid], model.body_geomadr[bid] + model.body_geomnum[bid]):
            if model.geom_contype[g] or model.geom_conaffinity[g]:
                checks[f"board↔{link}"] = collides(board_id, g)
    hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
    obj_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "target_object_geom")
    checks["board↔hand"] = collides(board_id, hand_id)
    checks["board↔object"] = collides(board_id, obj_id)
    checks["hand↔object"] = collides(hand_id, obj_id)
    for pair, ok in checks.items():
        print(f"  {pair}: {'COLLIDES' if ok else '*** NO COLLISION ***'}")
        if not ok:
            failures.append(f"Gate A: {pair} does not collide")
    return failures


def gate_b(env) -> list[str]:
    print("== Gate B: FW task success (no compliance) ==")
    from extraction_experiment import rollout, NeutralPolicy
    metrics = rollout(env, 7, NeutralPolicy())
    print(f"  task_success={metrics.get('task_success', 'N/A')} "
          f"errF={metrics['err_final_mm']:.1f}mm Fint={metrics['force_integral']:.1f}Ns "
          f"dodge={metrics.get('crossed')}")
    if not metrics.get("task_success", False):
        return ["Gate B: FW does not grasp+lift the block (scene task invalid)"]
    return []


def gate_c(env, out: Path) -> list[str]:
    print("== Gate C: rendering frames ==")
    out.mkdir(parents=True, exist_ok=True)
    from extraction_experiment import rollout, NeutralPolicy
    env.reset(seed=7, options={"fixture_index": 0})
    env.model.vis.global_.offwidth = 1280
    env.model.vis.global_.offheight = 720
    renderer = mujoco.Renderer(env.model, 720, 1280)
    cam = mujoco.MjvCamera()
    cam.lookat = np.array([0.5, 0.0, 0.6])
    cam.distance = 1.1
    cam.azimuth = 135
    cam.elevation = -18
    milestones = {0.8: "approach", 2.6: "grasp", 4.0: "lift", 7.5: "final"}
    done, step = False, 0
    while not done:
        t = step * 0.04
        if any(abs(t - m) < 0.02 for m in milestones):
            label = milestones[min(milestones, key=lambda m: abs(t - m))]
            renderer.update_scene(env.data, camera=cam)
            frame = renderer.render()
            try:
                import cv2
                cv2.putText(frame, f"t={t:.1f}s {label}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
            except ImportError:
                pass
            from imageio.v3 import imwrite
            imwrite(out / f"gateC_{label}.png", frame)
            print(f"  wrote {out / f'gateC_{label}.png'}")
        d = env.diagnostics()
        a = np.zeros(7)
        _, _, done, _, _ = env.step(a)
        step += 1
    renderer.close()
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board-underside-z", type=float, default=0.615)
    parser.add_argument("--edge-y", type=float, default=0.05)
    parser.add_argument("--out", type=Path, default=Path("/tmp/scene_gates"))
    args = parser.parse_args()

    import os
    os.environ.setdefault("MUJOCO_GL", "osmesa")
    os.environ["BOARD_EDGE_Y"] = str(args.edge_y)
    from extraction_experiment import make_env, BOARDS

    env = make_env(args.board_underside_z, 7)
    failures = gate_a(env.model) + gate_b(env) + gate_c(env, args.out)
    env.close()
    print("\n" + ("ALL GATES PASSED" if not failures else "GATES FAILED:\n  " + "\n  ".join(failures)))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
