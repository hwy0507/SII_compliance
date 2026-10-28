"""Render the archived R30 office-v5 rollout without rerunning physics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import imageio.v2 as iio
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gif", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=2)
    parser.add_argument("--fps", type=float, default=25.0)
    args = parser.parse_args()
    result_path = args.rollout.with_suffix(".json")
    trace_path = args.rollout.with_suffix(".npz")
    result = json.loads(result_path.read_text())
    for name, expected in result["source_sha256"].items():
        source = ROOT / "scripts" / name
        if digest(source) != expected:
            raise RuntimeError(f"source changed after rollout: {name}")

    from audit_office_complex_scene_v5_20260917 import make  # noqa: PLC0415

    env, _, _ = make(result["fixture"])
    model, data = env.model, env.data
    data.mocap_pos[env._obstacle_mocap] = [3.0, 3.0, 3.0]
    model.vis.global_.offwidth = 640
    model.vis.global_.offheight = 480
    model.vis.headlight.ambient[:] = [0.65, 0.65, 0.65]
    model.vis.headlight.diffuse[:] = [0.8, 0.8, 0.8]
    renderer = mujoco.Renderer(model, height=480, width=640)
    overview = mujoco.MjvCamera()
    overview.lookat[:] = [0.64, -0.02, 0.45]
    overview.distance = 2.5
    overview.azimuth = 135
    overview.elevation = -20
    detail = mujoco.MjvCamera()
    detail.lookat[:] = [0.60, -0.18, 0.64]
    detail.distance = 1.05
    detail.azimuth = 105
    detail.elevation = -20

    with np.load(trace_path, allow_pickle=False) as z:
        trace = {key: z[key].copy() for key in z.files}
    chosen = list(range(0, len(trace["time"]), args.stride))
    width, header, panel_h = 1280, 74, 480
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = iio.get_writer(
        args.output,
        format="FFMPEG",
        mode="I",
        fps=args.fps,
        codec="libx264",
        pixelformat="yuv420p",
        output_params=["-crf", "20", "-movflags", "+faststart"],
    )
    names = ["approach", "align", "grasp", "lift", "carry", "load transfer", "release", "retreat"]
    for frame_no, index in enumerate(chosen):
        data.qpos[:] = trace["qpos"][index]
        data.time = float(trace["time"][index])
        mujoco.mj_forward(model, data)
        renderer.update_scene(data, camera=overview)
        left = Image.fromarray(renderer.render().copy())
        renderer.update_scene(data, camera=detail)
        right = Image.fromarray(renderer.render().copy())
        frame = Image.new("RGB", (width, header + panel_h), (12, 17, 25))
        frame.paste(left, (0, header))
        frame.paste(right, (640, header))
        draw = ImageDraw.Draw(frame)
        task_ok = bool(result["task_success"])
        strict_ok = bool(result["strict_success"])
        outcome = f"TASK {'PASS' if task_ok else 'FAIL'}  |  STRICT {'PASS' if strict_ok else 'FAIL'}"
        color = (151, 242, 178) if strict_ok else (255, 132, 119)
        draw.text((12, 7), f"R30 ESN | full office-v5: person hand + ball + rod + obstacles | {outcome}", font=font(20, True), fill=color)
        stage = names[int(trace["stage"][index])]
        penetration = 1000.0 * float(result["stats"]["max_external_penetration_m"])
        event = "PERSON PUSH" if 3 <= data.time < 10 else "ROD PUSH" if 11 <= data.time < 17.5 else ""
        line = f"t={data.time:5.2f}s   stage={stage}   external penetration={penetration:.3f} mm < 0.200 mm   {event}"
        draw.text((12, 40), line, font=font(16), fill=(218, 228, 239))
        if bool(trace["selector_pulse_active"][index]):
            label = "R30 RESERVOIR PULSE ACTIVE (EARLY FALSE TRIGGER)"
            box = draw.textbbox((0, 0), label, font=font(15, True))
            x = width - (box[2] - box[0]) - 18
            draw.rounded_rectangle((x - 7, 38, width - 9, 66), radius=5, fill=(129, 67, 20))
            draw.text((x, 43), label, font=font(15, True), fill=(255, 226, 153))
        for x, label in [(8, "Full office scene"), (648, "Person-hand / robot close-up")]:
            draw.rounded_rectangle((x, header + 8, x + 246, header + 37), radius=5, fill=(8, 14, 22))
            draw.text((x + 8, header + 14), label, font=font(14, True), fill=(238, 243, 249))
        progress = int(width * (frame_no + 1) / len(chosen))
        draw.rectangle((0, header + panel_h - 4, width, header + panel_h), fill=(50, 60, 74))
        draw.rectangle((0, header + panel_h - 4, progress, header + panel_h), fill=color)
        writer.append_data(np.asarray(frame))
    writer.close()
    renderer.close()
    env.close()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    filters = (
        "fps=16,scale=1000:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=128:stats_mode=diff[p];"
        "[s1][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle"
    )
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(args.output), "-lavfi", filters, str(args.gif)], check=True)
    manifest = {
        "contract": "r30_office_v5_archived_state_visualization_v1",
        "simulation_rerun": False,
        "playback_speed": args.stride,
        "source": {str(result_path): digest(result_path), str(trace_path): digest(trace_path)},
        "result": {
            "task_success": task_ok,
            "strict_success": strict_ok,
            "final_stage": result["final_task_stage"],
            "max_external_penetration_mm": penetration,
            "person_hand_contact_present": "person_hand" in result["stats"]["events"],
            "pulse_steps": int(np.count_nonzero(trace["selector_pulse_active"])),
            "pulse_time_s": [
                float(trace["time"][trace["selector_pulse_active"]][0]),
                float(trace["time"][trace["selector_pulse_active"]][-1]),
            ],
        },
        "outputs": {str(args.output): digest(args.output), str(args.gif): digest(args.gif)},
        "renderer_environment": {"MUJOCO_GL": os.environ.get("MUJOCO_GL")},
    }
    args.output.with_suffix(".visualization.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
