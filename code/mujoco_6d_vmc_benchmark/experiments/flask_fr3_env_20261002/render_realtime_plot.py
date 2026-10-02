#!/usr/bin/env python3
"""Render the standalone FR3 FLASK simulation with a live right-side plot.

The output is a side-by-side video: MuJoCo on the left and online speed /
acceleration traces on the right, matching the layout of the supplied FLASK
reference video.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import subprocess
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(HERE))
from flask_joint_planner import FlaskJointPlanner, FlaskPlannerConfig, MuJoCoFR3CollisionChecker  # noqa: E402
from run_sensor_wbc import HOME, GOAL, LOWER, UPPER, VEL_LIMIT, TORQUE_LIMIT, SensorWBC, make_scene  # noqa: E402


def draw_live_panel(times, speed, ee_speed, acceleration, torque, now, duration, time_scale):
    """Draw the two online traces without requiring a plotting package."""
    width, height = 720, 360
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 9)
    except OSError:
        font = small = ImageFont.load_default()
    draw.text((12, 8), f'FLASK FR3 WBC | t = {now:.2f} s | time scale = {time_scale:g}x', fill='#222222', font=font)
    panels = [(52, 34, 700, 160, 'Speed + limit'), (52, 205, 700, 331, 'Acceleration + limit')]
    for left, top, right, bottom, title in panels:
        draw.rectangle((left, top, right, bottom), outline='#aaaaaa', width=1)
        draw.text((left + 5, top + 4), title, fill='#222222', font=font)
        for frac in (0.0, 0.5, 1.0):
            y = int(bottom - frac * (bottom - top - 24))
            draw.line((left, y, right, y), fill='#e6e6e6', width=1)
            draw.text((left - 28, y - 6), f'{frac:.1f}', fill='#666666', font=small)
        draw.line((left, bottom - 24, right, bottom - 24), fill='#555555', width=1)
    max_time = max(float(duration) + 0.5, 1.0)
    def points(values, panel):
        left, top, right, bottom, _ = panel
        plot_bottom = bottom - 24
        return [(int(left + (float(x) / max_time) * (right - left)), int(plot_bottom - min(1.25, float(y)) / 1.25 * (plot_bottom - top - 20))) for x, y in zip(times, values)]
    def draw_series(values, panel, color):
        pts = points(values, panel)
        if len(pts) > 1:
            draw.line(pts, fill=color, width=2)
    speed_panel, accel_panel = panels
    draw_series(speed, speed_panel, '#2878b5'); draw_series(ee_speed, speed_panel, '#d77a31')
    draw_series(acceleration, accel_panel, '#c84b4b'); draw_series(torque, accel_panel, '#4c9f70')
    for panel in panels:
        left, top, right, bottom, _ = panel
        y = int((bottom - 24) - 1.0 / 1.25 * (bottom - top - 20))
        for x in range(left, right, 10):
            if (x - left) // 10 % 2 == 0:
                draw.line((x, y, min(x + 5, right), y), fill='#222222', width=1)
        x_now = int(left + min(now, max_time) / max_time * (right - left))
        draw.line((x_now, top, x_now, bottom), fill='#444444', width=1)
    draw.text((530, 42), 'arm speed', fill='#2878b5', font=small)
    draw.text((530, 56), 'EE speed', fill='#d77a31', font=small)
    draw.text((530, 213), 'arm acceleration', fill='#c84b4b', font=small)
    draw.text((530, 227), 'torque usage', fill='#4c9f70', font=small)
    draw.text((left, 339), 'normalized / trajectory time [s]', fill='#555555', font=small)
    return np.asarray(image)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fr3-xml', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--time-scale', type=float, default=3.0, help='retime the planned trajectory for a longer live trace')
    parser.add_argument('--fps', type=int, default=25)
    args = parser.parse_args()
    if args.time_scale <= 0 or args.fps <= 0:
        raise SystemExit('time-scale and fps must be positive')

    with tempfile.TemporaryDirectory(prefix='flask_fr3_plot_scene_') as temp_dir:
        scene_path = Path(temp_dir) / 'scene.xml'
        scene_path.write_text(make_scene(args.fr3_xml))
        model = mujoco.MjModel.from_xml_path(str(scene_path))
        data = mujoco.MjData(model)
        data.qpos[:7] = HOME
        mujoco.mj_forward(model, data)
        robot_names = [model.geom(i).name for i in range(model.ngeom) if (model.geom(i).name or '').startswith('fr3v2_')]
        obstacle_names = [model.geom(i).name for i in range(model.ngeom) if (model.geom(i).name or '').startswith('flask_') and model.geom(i).name != 'flask_target_object_geom']
        checker = MuJoCoFR3CollisionChecker(model, robot_geom_names=robot_names, obstacle_geom_names=obstacle_names)
        config = FlaskPlannerConfig(
            velocity_limits=VEL_LIMIT,
            acceleration_limits=np.full(7, 12.0),
            joint_lower=LOWER,
            joint_upper=UPPER,
            steering_time=0.65,
            min_steering_time=0.10,
            max_steering_time=4.0,
            samples_per_segment=40,
            max_iterations=8000,
            goal_bias=0.30,
            seed=20261002,
        )
        trajectory = FlaskJointPlanner(config, collision_fn=checker).plan(HOME, GOAL)
        if trajectory is None:
            raise SystemExit('planner failed in standalone scene')
        trajectory = trajectory.retime(args.time_scale)
        wbc = SensorWBC(model)
        dynamic_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'flask_dynamic_slide')
        dynamic_qpos_adr = int(model.jnt_qposadr[dynamic_joint_id])
        renderer = mujoco.Renderer(model, height=360, width=480)
        frame_stride = max(1, int(round(1.0 / (model.opt.timestep * args.fps))))
        total_steps = int(np.ceil((trajectory.duration + 0.5) / model.opt.timestep))
        times, speed_ratio, ee_ratio, accel_ratio, torque_ratio = [], [], [], [], []

        try:
            writer = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1200x360', '-r', str(args.fps), '-i', '-', '-an', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(args.output)], stdin=subprocess.PIPE)
            frame_dir = None
        except FileNotFoundError:
            writer = None
            frame_dir = args.output.with_suffix('.frames')
            frame_dir.mkdir(parents=True, exist_ok=True)
        try:
            for step in range(total_steps):
                data.qpos[dynamic_qpos_adr] = 0.22 * np.sin(2.0 * np.pi * float(data.time) / 3.4)
                mujoco.mj_forward(model, data)
                tau = wbc.command(data, trajectory)
                previous_qvel = data.qvel[:7].copy()
                data.ctrl[:] = tau
                mujoco.mj_step(model, data)
                if step % frame_stride != 0 and step + 1 < total_steps:
                    continue
                now = float(data.time)
                current_qvel = data.qvel[:7].copy()
                qacc = (current_qvel - previous_qvel) / model.opt.timestep
                ee_velocity = data.sensor('ee_linear_velocity').data
                times.append(now)
                speed_ratio.append(float(np.max(np.abs(current_qvel) / VEL_LIMIT)))
                ee_ratio.append(float(np.linalg.norm(ee_velocity) / 1.0))
                accel_ratio.append(float(np.max(np.abs(qacc) / 12.0)))
                torque_ratio.append(float(np.max(np.abs(data.ctrl[:7]) / TORQUE_LIMIT)))
                plot_rgb = draw_live_panel(times, speed_ratio, ee_ratio, accel_ratio, torque_ratio, now, trajectory.duration, args.time_scale)
                renderer.update_scene(data)
                robot_rgb = renderer.render()
                frame = np.concatenate([robot_rgb, plot_rgb], axis=1).astype(np.uint8)
                if writer is not None:
                    writer.stdin.write(frame.tobytes())
                else:
                    Image.fromarray(frame).save(frame_dir / f'frame_{len(times):05d}.png')
        finally:
            if writer is not None:
                writer.stdin.close(); writer.wait()
            renderer.close()
    report = {
        'output': str(args.output),
        'frame_dir': None if writer is not None else str(frame_dir),
        'trajectory_duration_s': trajectory.duration,
        'time_scale': args.time_scale,
        'frames': len(times),
        'peak_speed_ratio': max(speed_ratio),
        'peak_acceleration_ratio': max(accel_ratio),
        'peak_torque_ratio': max(torque_ratio),
        'final_q_error_inf': float(np.max(np.abs(data.qpos[:7] - GOAL))),
        'note': 'Live-updated normalized speed and acceleration plots; standalone sensorized FR3 scene.',
    }
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
