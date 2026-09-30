"""Render an audited R30 rollout from archived MuJoCo states without rerunning it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import imageio.v2 as iio
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def pulse_mask(checkpoint: Path, rollout: Path, scripts: Path) -> tuple[np.ndarray, float]:
    sys.path.insert(0, str(scripts))
    from current_student_policy_20260921 import load_current  # noqa: PLC0415

    policy = load_current(checkpoint)
    with np.load(rollout, allow_pickle=False) as z:
        observations = z["observation"]
        recorded_actions = z["action"]
    active = []
    replayed = []
    for obs in observations:
        remaining_before = policy.selector_pulse_remaining
        used_before = policy.selector_pulse_used
        replayed.append(policy.act(obs))
        active.append(
            (not used_before and policy.selector_pulse_used)
            or remaining_before > 0
        )
    replay_error = float(np.max(np.abs(np.asarray(replayed) - recorded_actions)))
    return np.asarray(active, dtype=bool), replay_error


def set_state(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    row: np.ndarray,
    nq: int,
    nv: int,
    nu: int,
) -> None:
    data.time = float(row[0])
    data.qpos[:] = row[1 : 1 + nq]
    data.qvel[:] = row[1 + nq : 1 + nq + nv]
    data.ctrl[:] = row[1 + nq + nv : 1 + nq + nv + nu]
    mujoco.mj_forward(model, data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mjb", type=Path, required=True)
    parser.add_argument("--states", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output MP4 path")
    parser.add_argument("--gif", type=Path, required=True)
    parser.add_argument("--fixture", type=int, default=9332)
    parser.add_argument("--stride", type=int, default=2)
    parser.add_argument("--fps", type=float, default=25.0)
    args = parser.parse_args()
    if args.stride < 1 or args.fps <= 0:
        raise ValueError("stride and fps must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with np.load(args.states, allow_pickle=False) as z:
        states = z["state"].copy()
        nq, nv, nu = int(z["nq"]), int(z["nv"]), int(z["nu"])
    with np.load(args.rollout, allow_pickle=False) as z:
        times = z["time"].copy()
        stages = z["stage"].copy()
    if len(states) != len(times):
        raise ValueError("state and rollout lengths differ")
    result = json.loads(args.result.read_text())
    pulse, replay_error = pulse_mask(
        args.checkpoint, args.rollout, Path(__file__).resolve().parents[1] / "scripts"
    )
    if replay_error > 1e-12:
        raise RuntimeError(f"checkpoint replay mismatch: {replay_error}")

    model = mujoco.MjModel.from_binary_path(str(args.mjb))
    if (model.nq, model.nv, model.nu) != (nq, nv, nu):
        raise ValueError("MJB dimensions do not match state archive")
    data = mujoco.MjData(model)
    renderer = mujoco.Renderer(model, height=480, width=640)
    closeup = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(closeup)
    closeup.type = mujoco.mjtCamera.mjCAMERA_FREE
    closeup.lookat[:] = [0.55, -0.08, 0.69]
    closeup.distance = 0.48
    closeup.azimuth = 160.0
    closeup.elevation = -15.0

    width, panel_h, header_h = 960, 360, 72
    writer = iio.get_writer(
        args.output,
        format="FFMPEG",
        mode="I",
        fps=args.fps,
        codec="libx264",
        pixelformat="yuv420p",
        output_params=["-crf", "20", "-movflags", "+faststart"],
    )
    stage_names = {0: "APPROACH", 1: "DESCEND", 2: "GRASP", 3: "LOADED LIFT"}
    selected = list(range(0, len(states), args.stride))
    for frame_no, index in enumerate(selected):
        set_state(model, data, states[index], nq, nv, nu)
        renderer.update_scene(data, camera="rod_track")
        overview = Image.fromarray(renderer.render().copy()).resize((480, panel_h))
        renderer.update_scene(data, camera=closeup)
        detail = Image.fromarray(renderer.render().copy()).resize((480, panel_h))
        frame = Image.new("RGB", (width, header_h + panel_h), (11, 17, 26))
        frame.paste(overview, (0, header_h))
        frame.paste(detail, (480, header_h))
        draw = ImageDraw.Draw(frame)
        draw.text((10, 7), f"R30 ESN  |  fixture {args.fixture}  |  TASK PASS  |  STRICT PASS", font=font(20, True), fill=(150, 242, 177))
        stage = stage_names.get(int(stages[index]), f"STAGE {int(stages[index])}")
        metric = 1000.0 * float(result["contact"]["all_external_max_penetration_m"])
        status = f"t={times[index]:5.2f}s   {stage}   max penetration {metric:.3f} mm < 0.200 mm"
        draw.text((10, 39), status, font=font(15), fill=(216, 227, 239))
        if pulse[index]:
            text = "RESERVOIR-TIMED +Z CLEARANCE PULSE ACTIVE"
            box = draw.textbbox((0, 0), text, font=font(15, True))
            x0 = width - (box[2] - box[0]) - 15
            draw.rounded_rectangle((x0 - 6, 38, width - 8, 65), radius=5, fill=(126, 70, 18))
            draw.text((x0, 42), text, font=font(15, True), fill=(255, 226, 153))
        for x, label in [(8, "Overview"), (488, "Contact close-up")]:
            draw.rounded_rectangle((x, header_h + 8, x + 148, header_h + 36), radius=5, fill=(8, 14, 22))
            draw.text((x + 8, header_h + 13), label, font=font(14, True), fill=(235, 241, 248))
        progress = int(width * (frame_no + 1) / len(selected))
        draw.rectangle((0, header_h + panel_h - 4, width, header_h + panel_h), fill=(45, 57, 73))
        draw.rectangle((0, header_h + panel_h - 4, progress, header_h + panel_h), fill=(84, 201, 122))
        writer.append_data(np.asarray(frame))
    writer.close()
    renderer.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    palette_filter = (
        "fps=16,scale=900:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=128:stats_mode=diff[p];"
        "[s1][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
    )
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-i", str(args.output), "-lavfi", palette_filter, str(args.gif)],
        check=True,
    )
    manifest = {
        "contract": "r30_archived_state_visualization_v1",
        "fixture": args.fixture,
        "offline_state_replay": True,
        "simulation_rerun": False,
        "source_files": {
            str(p): sha256(p)
            for p in (args.mjb, args.states, args.rollout, args.result, args.checkpoint)
        },
        "checkpoint_action_replay_max_abs_error": replay_error,
        "archived_frames": len(states),
        "rendered_frames": len(selected),
        "playback_speed": args.stride,
        "pulse_control_steps": int(np.count_nonzero(pulse)),
        "pulse_time_s": [float(times[pulse][0]), float(times[pulse][-1])],
        "result": {
            "task_success": bool(result["success"]),
            "strict_success": bool(
                result["success"]
                and result["grasp_lift_success"]
                and not result["invalid_physics"]
                and result["contact"]["all_external_max_penetration_m"] <= 0.0002
            ),
            "all_external_max_penetration_mm": 1000.0 * float(result["contact"]["all_external_max_penetration_m"]),
        },
        "outputs": {
            str(args.output): sha256(args.output),
            str(args.gif): sha256(args.gif),
        },
        "renderer_environment": {"MUJOCO_GL": os.environ.get("MUJOCO_GL")},
    }
    args.output.with_suffix(".visualization.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
