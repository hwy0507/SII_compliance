#!/usr/bin/env python3
"""Render the four frozen methods in an under-table lift collision scene.

This is an exploratory visualization only.  The fixed horizontal board is
placed above the initial approach and grasp path, so the hand starts under the
table, grasps the block, and contacts the board underside only while lifting.
No controller is trained, selected, or tuned by this script, and these GIFs
must not be mixed with the confirmatory held-out hand-proxy statistics.
"""

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
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv  # noqa: E402


BOARD_UNDERSIDE_Z = 0.68
RL_DT = 0.04


def font(size: int) -> ImageFont.ImageFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_vmc(k: float, budget: float) -> VMCTorqueBaseline:
    base = SpringCarriageConfig(k_translation_base=2.2, k_rotation_base=0.18)
    config = replace(base, k_translation_base=k,
                     k_rotation_base=base.k_rotation_base * k / base.k_translation_base)
    return VMCTorqueBaseline(config, TORQUE_LIMITS * budget)


def board_contact_state(model, data, board_id: int, hand_id: int) -> tuple[bool, float, float]:
    """Return board contact, peak normal-force norm, and hand lateral speed."""
    force = 0.0
    touching_hand = False
    wrench = np.zeros(6)
    for index in range(data.ncon):
        contact = data.contact[index]
        ids = {int(contact.geom1), int(contact.geom2)}
        if board_id not in ids:
            continue
        touching_hand = touching_hand or hand_id in {
            int(model.geom_bodyid[contact.geom1]), int(model.geom_bodyid[contact.geom2])
        }
        import mujoco
        mujoco.mj_contactForce(model, data, index, wrench)
        force = max(force, float(np.linalg.norm(wrench[:3])))
    # A nonzero tangential hand speed while the board is active is the visual
    # signature of the natural slide along the underside.
    hand_vel = data.cvel[hand_id, 3:6]
    lateral_speed = float(np.linalg.norm(hand_vel[:2]))
    return bool(touching_hand), force, lateral_speed


def render_one(*, menagerie: Path, seed: int, method: str, controller, budget: float,
               output: Path, fps: int) -> dict:
    import mujoco

    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, seed=seed, robot="fr3",
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", table_board_underside_z=BOARD_UNDERSIDE_Z,
        joint_velocity_noise_std=0.0,
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()

    board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "extraction_board")
    hand_body_id = env._hand_id
    if board_id < 0:
        raise RuntimeError("extraction_board was not found in the MuJoCo scene")
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    render_stride = max(1, round(1.0 / (fps * RL_DT)))
    frames: list[np.ndarray] = []
    step, done, info = 0, False, {}
    peak_force = 0.0
    first_contact = None
    contact_frames = 0
    peak_slide_speed = 0.0
    title_font, info_font = font(22), font(15)

    while not done:
        d = env.diagnostics()
        if controller is None:
            action = np.zeros(7)
        elif hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
            act = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                                 hand_jacobian=d.get("hand_jacobian"),
                                 pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = act.bounded_filter_action
        else:
            act = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                                 pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = act.bounded_filter_action

        touching, force, slide_speed = board_contact_state(env.model, env.data, board_id, hand_body_id)
        time_s = step * RL_DT
        peak_force = max(peak_force, force)
        peak_slide_speed = max(peak_slide_speed, slide_speed if touching else 0.0)
        contact_frames += int(touching)
        if touching and first_contact is None:
            first_contact = time_s

        if step % render_stride == 0:
            renderer.update_scene(env.data, camera="rod_track")
            image = Image.fromarray(renderer.render()).convert("RGB")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, image.width, 82), fill=(12, 17, 27))
            draw.text((12, 7), method, fill=(255, 255, 255), font=title_font)
            draw.text((12, 34), f"under-table lift collision   t={time_s:.2f} s",
                      fill=(202, 218, 238), font=info_font)
            status = "TABLETOP CONTACT / SLIDING" if touching and slide_speed > 0.01 else (
                "TABLETOP CONTACT" if touching else "under board / no contact")
            status_color = (255, 205, 90) if touching else (180, 215, 190)
            draw.text((12, 59), f"{status}   F={force:.1f} N   v_xy={slide_speed:.2f} m/s",
                      fill=status_color, font=info_font)
            frames.append(np.asarray(image))

        _, _, done, _, info = env.step(action)
        step += 1

    renderer.close()
    env.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output, np.stack(frames), duration=1.0 / fps, loop=0)
    return {
        "method": method,
        "budget": budget,
        "task_success": bool(info.get("task_success", False)),
        "first_board_contact_s": first_contact,
        "peak_board_contact_force_n": peak_force,
        "peak_contact_hand_xy_speed_mps": peak_slide_speed,
        "board_contact_frames": contact_frames,
        "peak_torque_nm": float(info.get("peak_torque_nm", np.nan)),
        "hard_limit": bool(info.get("hard_torque_limit", False)),
        "frames": len(frames),
        "gif": str(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261520)
    parser.add_argument("--mlp", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=25)
    args = parser.parse_args()
    if args.fps < 1:
        raise SystemExit("fps must be positive")
    methods = [
        ("paper_mpc_nominal_only", None, 0.05, "paper_mpc_nominal_only.gif"),
        ("vmc_frozen_k1_budget2pct", make_vmc(1.0, 0.02), 0.02, "vmc_frozen_k1_budget2pct.gif"),
        ("mlp_bc_h64_s20261502_selected", MLPComplianceController.from_npz(args.mlp), 0.05,
         "mlp_bc_h64_s20261502_selected.gif"),
        ("esn_proposed_frozen_cem", load_controller(args.esn), 0.05, "esn_proposed_frozen_cem.gif"),
    ]
    manifest = {
        "schema_version": 1,
        "purpose": "exploratory visualization only; new under-table horizontal-board scenario",
        "confirmatory_statistics_excluded": True,
        "no_training_selection_or_tuning": True,
        "seed": args.seed,
        "board": {
            "geom": "extraction_board", "underside_z_m": BOARD_UNDERSIDE_Z,
            "thickness_m": 0.03, "center_m": [0.52, -0.065, BOARD_UNDERSIDE_Z + 0.015],
            "size_m": [0.08, 0.215, 0.015],
            "contact_bits": "board 4/4 with hand 4/4; target 6/7",
            "placement_probe": "PaperMPC nominal: no approach/grasp contact; first hand contact during lift near 3.84 s",
        },
        "methods": [],
    }
    for method, controller, budget, filename in methods:
        result = render_one(menagerie=args.menagerie, seed=args.seed, method=method,
                            controller=controller, budget=budget,
                            output=args.output_dir / filename, fps=args.fps)
        manifest["methods"].append(result)
        print(json.dumps(result), flush=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
