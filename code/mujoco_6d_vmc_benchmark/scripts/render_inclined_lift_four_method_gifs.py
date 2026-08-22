#!/usr/bin/env python3
"""Render the four methods against the physical inclined lift board."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mlp_compliance_baseline import MLPComplianceController  # noqa: E402
from run_benchmark import TORQUE_LIMITS  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture  # noqa: E402


def make_vmc(budget):
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    cfg = replace(base, k_translation_base=1.0,
                  k_rotation_base=base.k_rotation_base / base.k_translation_base)
    return VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget)


def fixture(seed):
    rng = np.random.default_rng(seed)
    return VelocityResidualFixture(float(rng.uniform(.165, .175)),
                                   float(rng.uniform(.539, .542)), 99.0,
                                   grasp_time_s=2.4, contact_time_constant_s=.015)


def font(size):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size) if Path(path).is_file() else ImageFont.load_default()


def render_one(menagerie, seed, tilt, yaw, board_y_offset, label, controller, budget, output, fps, camera_mode="rod_track", contact_mode="side_slide"):
    import mujoco
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, seed=seed, robot="fr3",
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fixture(seed),), lift_board_tilt_deg=tilt,
        lift_board_yaw_deg=yaw, lift_board_y_offset_m=board_y_offset,
        lift_board_contact_mode=contact_mode)
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    close_camera = None
    if camera_mode == "close":
        # Free camera centered on the physical board.  This is deliberately
        # scene-derived only for visualization; it never enters control.
        close_camera = mujoco.MjvCamera()
        close_camera.type = mujoco.mjtCamera.mjCAMERA_FREE
        close_camera.lookat[:] = np.asarray(env.model.geom_pos[board_id], dtype=float)
        close_camera.distance = 0.58
        close_camera.azimuth = 135.0
        close_camera.elevation = -18.0
    frames, done, info, step = [], False, {}, 0
    peak_force, peak_slide, first_contact = 0.0, 0.0, None
    stride = max(1, round(1.0 / (fps * .04)))
    while not done:
        d = env.diagnostics()
        touching, force = env._lift_board_contact_diagnostics()
        hand_v = np.asarray(d["ee_twist"][:3])
        slide = float(np.linalg.norm(hand_v[:2]))
        t = step * .04
        peak_force, peak_slide = max(peak_force, force), max(peak_slide, slide if touching else 0.0)
        if touching and first_contact is None: first_contact = t
        if step % stride == 0:
            renderer.update_scene(env.data, camera=close_camera if close_camera is not None else camera_mode)
            image = Image.fromarray(renderer.render()).convert("RGB")
            draw, title, small = ImageDraw.Draw(image), font(22), font(15)
            draw.rectangle((0, 0, image.width, 86), fill=(12, 17, 27))
            draw.text((12, 7), label, fill="white", font=title)
            draw.text((12, 34), f"inclined-board lift   tilt={tilt:.0f} deg   yaw={yaw:.0f} deg   t={t:.2f} s", fill=(202,218,238), font=small)
            status = "CONTACT / SLIDING" if touching and slide > .01 else ("CONTACT" if touching else "NO CONTACT")
            color = (255,205,90) if touching else (180,215,190)
            draw.text((12, 60), f"{status}   F={force:.1f} N   v_xy={slide:.2f} m/s", fill=color, font=small)
            frames.append(np.asarray(image))
        if controller is None: action = np.zeros(7)
        elif hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
            action = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"], hand_jacobian=d["hand_jacobian"], pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]).bounded_filter_action
        else:
            action = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"], pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]).bounded_filter_action
        _, _, done, _, info = env.step(action)
        step += 1
    renderer.close(); env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output, np.stack(frames), duration=1.0 / fps, loop=0)
    return {"method": label, "tilt_deg": tilt, "yaw_deg": yaw,
            "board_y_offset_m": board_y_offset, "seed": seed, "gif": str(output),
            "task_success": bool(info.get("task_success", False)), "first_contact_s": first_contact,
            "peak_board_force_n": peak_force, "peak_slide_speed_mps": peak_slide,
            "board_contact_duration_s": float(info.get("lift_board_contact_duration_s", 0.0)),
            "board_contact_impulse_ns": float(info.get("lift_board_contact_impulse_ns", 0.0))}


def main():
    p = argparse.ArgumentParser(); p.add_argument("--menagerie", type=Path, required=True)
    p.add_argument("--mlp", type=Path, required=True); p.add_argument("--esn", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True); p.add_argument("--seed", type=int, default=20262201)
    p.add_argument("--tilt", type=float, default=40.0); p.add_argument("--yaw", type=float, default=0.0)
    p.add_argument("--board-y-offset", type=float, default=0.0)
    p.add_argument("--contact-mode", choices=["side_slide", "front_face"], default="side_slide")
    p.add_argument("--fps", type=int, default=25)
    p.add_argument("--only", choices=["paper", "vmc", "mlp", "esn"], default=None,
                   help="render one method only; useful for avoiding long-lived renderer resource buildup")
    p.add_argument("--camera", choices=["rod_track", "close"], default="rod_track")
    a = p.parse_args()
    methods = [("PaperMPC", None, .02, "paper_mpc_inclined.gif"),
               ("VMC", make_vmc(.02), .02, "vmc_inclined.gif"),
               ("MLP trained on inclined-board traces", MLPComplianceController.from_npz(a.mlp), .02, "mlp_inclined.gif"),
               ("ESN trained on inclined-board traces", load_controller(a.esn), .02, "esn_inclined.gif")]
    if a.only is not None:
        methods = [methods[{"paper": 0, "vmc": 1, "mlp": 2, "esn": 3}[a.only]]]
    manifest = {"schema_version": 1, "purpose": "physical MuJoCo inclined-board demo",
                "tilt_deg": a.tilt, "yaw_deg": a.yaw,
                "board_y_offset_m": a.board_y_offset, "seed": a.seed, "methods": []}
    for label, ctrl, budget, name in methods:
        result = render_one(a.menagerie, a.seed, a.tilt, a.yaw, a.board_y_offset,
                            label, ctrl, budget, a.output_dir / name, a.fps, a.camera,
                            a.contact_mode)
        manifest["methods"].append(result); print(json.dumps(result), flush=True)
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__": main()
