#!/usr/bin/env python3
"""Render full-scene + collision-close GIFs for all dual-board methods."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v3 as iio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from evaluate_dual_phase_four_method import controller_action, fixture, make_vmc
from mlp_compliance_baseline import MLPComplianceController
from vmc_compliance_baseline import load_controller
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv


def font(size: int):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(path, size) if path.is_file() else ImageFont.load_default()


def render_one(
    menagerie: Path, label: str, controller, output: Path, *, seed: int, budget: float,
    y_offset: float, z_offset: float, fps: float,
) -> dict[str, object]:
    env = PandaWBCVelocityResidualEnv(
        menagerie, None, None, "direct_esn", fixtures=(fixture(seed),), rod_enabled=False,
        robot="fr3", wbc_backend="paper_mpc", execution_mode="torque_residual",
        residual_torque_scale=budget, lift_board_tilt_deg=15.0,
        lift_board_contact_mode="dual_phase_longitudinal",
        lift_board_y_offset_m=y_offset, lift_board_z_offset_m=z_offset, seed=seed,
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    assert env.model is not None and env.data is not None
    board_ids = env._dual_board_geom_ids
    board_midpoint = np.mean([env.model.geom_pos[index] for index in board_ids.values()], axis=0)
    renderer = mujoco.Renderer(env.model, height=360, width=480)
    close = mujoco.MjvCamera()
    close.type = mujoco.mjtCamera.mjCAMERA_FREE
    close.lookat[:] = board_midpoint + np.array([0.0, 0.0, 0.015])
    close.distance = 0.58
    # View from the contact side of the vertical post-grasp plank.  The
    # opposite azimuth puts the orange board in front of the hand and hides
    # the interface that the demo is meant to show.
    close.azimuth = -42.0
    close.elevation = -20.0
    frames: list[np.ndarray] = []
    keyframes: dict[str, np.ndarray] = {}
    stride = max(1, int(round(1.0 / (fps * .04))))
    done = False
    info: dict[str, object] = {}
    step = 0
    while not done:
        diagnostics = env.diagnostics()
        t = step * .04
        contact_state = {}
        for name, board_id in board_ids.items():
            touching, force, penetration, _, _, partners = env._board_contact_diagnostics(board_id)
            contact_state[name] = {
                "touching": touching, "force": force, "penetration": penetration,
                "partners": partners,
            }
        cumulative = env.dual_board_metrics
        pre_first = cumulative.get("pregrasp_board", {}).get("first_contact_s")
        post_first = cumulative.get("postgrasp_board", {}).get("first_contact_s")
        # Contact is integrated at the 4-ms MuJoCo rate whereas video frames
        # are emitted at the 40-ms policy rate.  Mark the first policy frame
        # immediately after a substep-only contact so a short VMC/ESN touch is
        # visible in the GIF instead of falling between frames.
        pre_recent = pre_first is not None and 0.0 <= t - float(pre_first) <= .08
        post_recent = post_first is not None and 0.0 <= t - float(post_first) <= .08
        if step % stride == 0:
            renderer.update_scene(env.data, camera="rod_track")
            global_image = Image.fromarray(renderer.render()).convert("RGB")
            renderer.update_scene(env.data, camera=close)
            close_image = Image.fromarray(renderer.render()).convert("RGB")
            image = Image.new("RGB", (960, 360))
            image.paste(global_image, (0, 0))
            image.paste(close_image, (480, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 960, 79), fill=(10, 15, 25))
            draw.text((12, 6), label, fill="white", font=font(21))
            draw.text((12, 34), f"full task   t={t:4.2f}s   left: global / right: contact close-up",
                      fill=(205, 220, 240), font=font(14))
            pre = contact_state["pregrasp_board"]
            post = contact_state["postgrasp_board"]
            phase = "PRE-GRASP CONTACT" if pre["touching"] or pre_recent else (
                "POST-GRASP CONTACT" if post["touching"] or post_recent else (
                    "DESCEND / GRASP" if t < 2.7 else "LIFT / CARRY"
                )
            )
            color = (255, 202, 82) if pre["touching"] or post["touching"] or pre_recent or post_recent else (175, 215, 190)
            pre_force = pre["force"] if pre["touching"] else (
                float(cumulative["pregrasp_board"]["peak_force_n"]) if pre_recent else 0.0)
            post_force = post["force"] if post["touching"] else (
                float(cumulative["postgrasp_board"]["peak_force_n"]) if post_recent else 0.0)
            draw.text((12, 56),
                      f"{phase}   pre F={pre_force:.1f}N   post F={post_force:.1f}N",
                      fill=color, font=font(14))
            frames.append(np.asarray(image))
            if (pre["touching"] or pre_recent) and "pre_contact" not in keyframes:
                keyframes["pre_contact"] = np.asarray(image)
            if t >= 2.70 and "grasp" not in keyframes:
                keyframes["grasp"] = np.asarray(image)
            if (post["touching"] or post_recent) and "post_contact" not in keyframes:
                keyframes["post_contact"] = np.asarray(image)
        action = controller_action(controller, diagnostics)
        _, _, terminated, truncated, info = env.step(action)
        done = bool(terminated or truncated)
        step += 1
    renderer.close()
    env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output, np.stack(frames), duration=1.0 / fps, loop=0)
    for name, frame in keyframes.items():
        iio.imwrite(output.with_name(f"{output.stem}_{name}.png"), frame)
    return {
        "method": label, "gif": str(output), "seed": seed,
        "task_success": bool(info["task_success"]),
        "dual_phase_geometry_valid": bool(info["dual_phase_geometry_valid"]),
        "dual_board_metrics": info["dual_board_metrics"],
        "final_target_lift_m": info["final_target_lift_m"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--mlp", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20265701)
    parser.add_argument("--budget", type=float, default=.04)
    parser.add_argument("--vmc-stiffness", type=float, default=.5)
    parser.add_argument("--board-y-offset", type=float, default=.00075)
    parser.add_argument("--board-z-offset", type=float, default=-.001)
    parser.add_argument("--fps", type=float, default=12.5)
    parser.add_argument("--only", choices=("paper", "vmc", "mlp", "esn"))
    args = parser.parse_args()
    methods = [
        ("PaperMPC (original paper method)", None, "paper_mpc_dual.gif"),
        ("VMC physics baseline", make_vmc(args.budget, args.vmc_stiffness), "vmc_dual.gif"),
        ("MLP (same 32-D observation)", MLPComplianceController.from_npz(args.mlp), "mlp_dual.gif"),
        ("ESN proposed (same 32-D observation)", load_controller(args.esn), "esn_dual.gif"),
    ]
    if args.only is not None:
        methods = [methods[{"paper": 0, "vmc": 1, "mlp": 2, "esn": 3}[args.only]]]
    results = []
    for label, controller, filename in methods:
        result = render_one(
            args.menagerie, label, controller, args.output_dir / filename,
            seed=args.seed, budget=args.budget, y_offset=args.board_y_offset,
            z_offset=args.board_z_offset, fps=args.fps,
        )
        results.append(result)
        print(json.dumps(result), flush=True)
    manifest = {
        "schema_version": 1, "purpose": "dual-board MuJoCo full-sequence demo",
        "camera": "split global rod_track and fixed dual-board close-up",
        "seed": args.seed, "budget": args.budget,
        "board_y_offset_m": args.board_y_offset, "board_z_offset_m": args.board_z_offset,
        "methods": results,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
