#!/usr/bin/env python3
"""Render four frozen controllers on one exact matched held-out fixture.

This is a visualization-only replay: it reconstructs the fixture with the
same deterministic generator as the registered four-method test and loads the
already frozen MLP/ESN checkpoints.  It does not select, train, or modify any
policy.
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
from run_multicontact_four_method_benchmark import fixture  # noqa: E402
from vmc_compliance_baseline import SpringCarriageConfig, load_controller  # noqa: E402
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv  # noqa: E402


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


def expected_row(path: Path | None, method: str, seed: int, fixture_index: int) -> dict | None:
    if path is None:
        return None
    data = json.loads(path.read_text())
    matches = [row for row in data["rows"] if row["method"] == method and row["seed"] == seed
               and row["fixture_index"] == fixture_index]
    if len(matches) != 1:
        raise ValueError(f"could not find exactly one registered row for {method}, seed={seed}, fixture={fixture_index}")
    return matches[0]


def render_one(*, menagerie: Path, fx, seed: int, method: str, controller, budget: float,
               fixture_index: int, output: Path, fps: int, expected: dict | None) -> dict:
    import mujoco

    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=True, seed=seed, robot="fr3",
        execution_mode="torque_residual", residual_torque_scale=budget,
        wbc_backend="paper_mpc", fixtures=(fx,), joint_velocity_noise_std=0.0,
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    render_stride = max(1, round(1.0 / (fps * 0.04)))
    frames: list[np.ndarray] = []
    step, done, info, peak_force = 0, False, {}, 0.0
    error_log: list[tuple[float, float]] = []
    title_font, info_font = font(22), font(16)
    while not done:
        d = env.diagnostics()
        error_log.append((step * 0.04, float(np.linalg.norm(d["wbc_pose_error"][:3]))))
        if controller is None:
            action = np.zeros(7)
        elif hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
            act = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                                 hand_jacobian=d.get("hand_jacobian"), pose_error=d["wbc_pose_error"],
                                 twist_error=d["wbc_twist_error"])
            action = act.bounded_filter_action
        else:
            act = controller.act(d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                                 pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = act.bounded_filter_action
        if step % render_stride == 0:
            renderer.update_scene(env.data, camera="rod_track")
            image = Image.fromarray(renderer.render()).convert("RGB")
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, image.width, 58), fill=(12, 17, 27))
            draw.text((12, 8), method, fill=(255, 255, 255), font=title_font)
            draw.text((12, 34), f"matched fixture  seed={seed}, index={fixture_index}   t={step * 0.04:.2f} s",
                      fill=(202, 218, 238), font=info_font)
            frames.append(np.asarray(image))
        _, _, done, _, info = env.step(action)
        peak_force = max(peak_force, float(info.get("peak_contact_force_n", 0.0)))
        step += 1
    renderer.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(output, np.stack(frames), duration=1.0 / fps, loop=0)
    at_grasp_error = min(error_log, key=lambda row: abs(row[0] - fx.grasp_time_s))[1] * 1000.0
    rendered = {"method": method, "seed": seed, "task_success": bool(info.get("task_success", False)),
                "at_grasp_err_mm": at_grasp_error,
                "peak_torque_nm": float(info.get("peak_torque_nm", np.nan)),
                "peak_contact_force_n": peak_force, "hard_limit": bool(info.get("hard_torque_limit", False)),
                "frames": len(frames), "gif": str(output)}
    # Exact metrics are not needed to make a GIF, but this guard catches a
    # mistakenly changed fixture/controller before a visual artifact is shown.
    if expected is not None:
        if rendered["task_success"] != bool(expected["task_success"]):
            raise RuntimeError(f"{method}: replay success differs from registered held-out row")
        if not np.isclose(rendered["at_grasp_err_mm"], float(expected["at_grasp_err_mm"]), atol=1.0e-9):
            raise RuntimeError(f"{method}: replay at-grasp error differs from registered held-out row")
    env.close()
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--fixture-index", type=int, required=True)
    parser.add_argument("--mlp", type=Path, required=True)
    parser.add_argument("--esn", type=Path, required=True)
    parser.add_argument("--registered-results", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=25)
    args = parser.parse_args()
    if args.fixture_index < 0 or args.fps < 1:
        raise SystemExit("fixture-index must be non-negative and fps positive")
    fx = fixture(np.random.default_rng(np.uint64(args.seed) * 6151 + args.fixture_index + 1))
    methods = [
        ("paper_mpc_nominal_only", None, 0.05, "paper_mpc_nominal_only.gif"),
        ("vmc_frozen_k1_budget2pct", make_vmc(1.0, 0.02), 0.02, "vmc_frozen_k1_budget2pct.gif"),
        ("mlp_bc_h64_s20261502_selected", MLPComplianceController.from_npz(args.mlp), 0.05,
         "mlp_bc_h64_s20261502_selected.gif"),
        ("esn_proposed_frozen_cem", load_controller(args.esn), 0.05, "esn_proposed_frozen_cem.gif"),
    ]
    manifest = {"schema_version": 1, "purpose": "visualization-only matched replay; no policy modification",
                "seed": args.seed, "fixture_index": args.fixture_index, "fixture_parameters": fx.__dict__,
                "methods": []}
    for method, controller, budget, filename in methods:
        rendered = render_one(menagerie=args.menagerie, fx=fx, seed=args.seed, method=method,
                              controller=controller, budget=budget, output=args.output_dir / filename,
                              fixture_index=args.fixture_index, fps=args.fps,
                              expected=expected_row(args.registered_results, method, args.seed,
                                                                  args.fixture_index))
        manifest["methods"].append({"budget": budget, **rendered})
        print(json.dumps(manifest["methods"][-1]), flush=True)
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
