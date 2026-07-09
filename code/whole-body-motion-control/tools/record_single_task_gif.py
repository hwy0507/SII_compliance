#!/usr/bin/env python3
"""
Run one ManiSkill benchmark task and record a third-person GIF.

This is meant for quick visual demos, not for full benchmark scoring.
It reuses the same Fetch, scheduler, benchmark JSON, and perception service
paths as experiments/run_maniskill_benchmark.py.
"""

import argparse
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional


os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
for cache_dir in [os.environ["MPLCONFIGDIR"], os.environ["XDG_CACHE_HOME"]]:
    try:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

if "CONDA_PREFIX" in os.environ:
    conda_lib = os.path.join(os.environ["CONDA_PREFIX"], "lib")
    current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if conda_lib not in current_ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{conda_lib}:{current_ld_path}"
        os.execv(sys.executable, [sys.executable] + sys.argv)


import imageio.v2 as imageio
import numpy as np
import sapien
import trimesh.transformations as tra
import yaml
from mani_skill.utils.building import actors


def get_camera_pose(target_pos, dist=4.8, pitch=-0.95, yaw=-2.25):
    z = dist * np.sin(-pitch)
    xy = dist * np.cos(-pitch)
    x = xy * np.cos(yaw)
    y = xy * np.sin(yaw)
    cam_pos = target_pos + np.array([x, y, z], dtype=np.float32)

    forward = target_pos - cam_pos
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    if abs(float(np.dot(forward, world_up))) > 0.99:
        cam_x = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        cam_z = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        cam_y = np.cross(cam_z, cam_x)
    else:
        cam_x = forward
        cam_y = np.cross(world_up, forward)
        cam_y = cam_y / np.linalg.norm(cam_y)
        cam_z = np.cross(cam_x, cam_y)

    mat44 = np.eye(4)
    mat44[:3, 0] = cam_x
    mat44[:3, 1] = cam_y
    mat44[:3, 2] = cam_z
    mat44[:3, 3] = cam_pos
    quat = tra.quaternion_from_matrix(mat44)
    return sapien.Pose(p=mat44[:3, 3], q=quat)


def rgba_to_rgb_array(rgba):
    if hasattr(rgba, "cpu"):
        rgba = rgba.cpu().numpy()
    elif isinstance(rgba, list):
        if len(rgba) > 0 and hasattr(rgba[0], "cpu"):
            rgba = [x.cpu().numpy() for x in rgba]
        rgba = np.array(rgba)

    while rgba.ndim > 3 and rgba.shape[0] == 1:
        rgba = rgba[0]

    if rgba.dtype.kind == "f":
        rgb = np.clip(rgba[..., :3] * 255.0, 0, 255).astype(np.uint8)
    else:
        rgb = rgba[..., :3].astype(np.uint8)
    return rgb


class ThirdPersonRecorder:
    def __init__(self, sim_env, target_pos, width, height, fps, max_frames):
        self.sim_env = sim_env
        self.target_pos = np.asarray(target_pos, dtype=np.float32)
        self.width = int(width)
        self.height = int(height)
        self.fps = float(fps)
        self.max_frames = int(max_frames)
        self.frames = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._camera = None

    def _ensure_camera(self):
        scene = self.sim_env.env.unwrapped.scene
        if self._camera is not None:
            return

        pose = get_camera_pose(self.target_pos)
        self._camera = scene.add_camera(
            name=f"record_cam_{uuid.uuid4().hex[:6]}",
            width=self.width,
            height=self.height,
            fovy=np.deg2rad(60),
            near=0.1,
            far=100,
            pose=pose,
        )

        scene.set_ambient_light([0.5, 0.5, 0.5])
        scene.add_directional_light([1, 1, -1], [0.9, 0.9, 0.9], shadow=True)
        scene.add_directional_light([-1, -0.5, -1], [0.5, 0.5, 0.6], shadow=True)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def _loop(self):
        dt = 1.0 / max(self.fps, 1.0)
        while self._running and len(self.frames) < self.max_frames:
            try:
                with self.sim_env._env_lock:
                    self._ensure_camera()
                    scene = self.sim_env.env.unwrapped.scene
                    scene.update_render()
                    self._camera.take_picture()
                    self.frames.append(rgba_to_rgb_array(self._camera.get_picture("Color")))
            except Exception as exc:
                print(f"[Recorder] frame capture failed: {exc}")
                time.sleep(dt)
                continue
            time.sleep(dt)

    def save(self, output_path):
        if not self.frames:
            raise RuntimeError("No frames captured; cannot save GIF.")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(str(output_path), self.frames, fps=self.fps)
        return output_path


def make_scheduler(scheduler_type, fetch_robot, config_path):
    from grasp_anywhere.core.closed_loop_scheduler import ClosedLoopScheduler
    from grasp_anywhere.core.nav_manip_scheduler import NavManipScheduler
    from grasp_anywhere.core.nav_prepose_scheduler import NavPreposeScheduler
    from grasp_anywhere.core.scheduler import Scheduler
    from grasp_anywhere.core.sequential_scheduler import SequentialScheduler

    if scheduler_type == "sequential":
        return SequentialScheduler(robot=fetch_robot, config_path=config_path)
    if scheduler_type == "nav_manip":
        return NavManipScheduler(robot=fetch_robot, config_path=config_path)
    if scheduler_type == "nav_prepose":
        return NavPreposeScheduler(robot=fetch_robot, config_path=config_path)
    if scheduler_type == "closed_loop":
        return ClosedLoopScheduler(robot=fetch_robot, config_path=config_path)
    return Scheduler(robot=fetch_robot, config_path=config_path)


def main():
    parser = argparse.ArgumentParser(description="Record one ManiSkill grasp task to GIF.")
    parser.add_argument("--benchmark", default="resources/grasp_benchmark.json")
    parser.add_argument("-c", "--config", default="grasp_anywhere/configs/maniskill_fetch.yaml")
    parser.add_argument("--scene", default="scene_0")
    parser.add_argument("--task", type=int, default=0)
    parser.add_argument("--output", default="outputs/task_recordings/scene_0_task000.gif")
    parser.add_argument("--fps", type=float, default=8.0)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--max-seconds", type=float, default=180.0)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--no-trajectory", action="store_true")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
    with open(args.benchmark, "r") as f:
        benchmark = json.load(f)

    if args.scene not in benchmark:
        raise KeyError(f"Scene {args.scene!r} not found in {args.benchmark}")

    scene_data = benchmark[args.scene]
    grasp_tasks = scene_data.get("grasp_tasks", [])
    if not (0 <= args.task < len(grasp_tasks)):
        raise IndexError(f"Task index {args.task} out of range for {args.scene}")

    canonical_map_path = scene_data.get("canonical_map_path")
    if not canonical_map_path:
        raise ValueError(f"{args.scene} has no canonical_map_path")
    canonical_map_path = os.path.expanduser(canonical_map_path)
    if not os.path.isabs(canonical_map_path):
        canonical_map_path = os.path.abspath(canonical_map_path)
    if not os.path.exists(canonical_map_path):
        raise FileNotFoundError(
            f"Canonical map not found: {canonical_map_path}\n"
            "Generate it first with tools/build_scene_pointclouds.py."
        )

    from grasp_anywhere.envs.maniskill.maniskill_env_mpc import ManiSkillEnv
    from grasp_anywhere.robot.fetch import Fetch

    render_mode = None
    sim_env = ManiSkillEnv(
        env_id="ReplicaCAD_SceneManipulation-v1",
        robot_uids="fetch",
        render_mode=render_mode,
        camera_width=320,
        camera_height=240,
    )

    try:
        seed = scene_data.get("seed", 0)
        sim_env.reset(seed=seed)
        scene = sim_env.env.unwrapped.scene

        object_actors = {}
        for i, task in enumerate(grasp_tasks):
            model_id = task["model_id"]
            position = np.asarray(task["position"], dtype=np.float32).reshape(-1, 3)[0]
            orientation = np.asarray(task["orientation"], dtype=np.float32).reshape(-1, 4)[0]

            builder = actors.get_actor_builder(scene, id=f"ycb:{model_id}")
            builder.initial_pose = sapien.Pose(p=position, q=orientation)
            actor_name = f"ycb_{model_id}_{uuid.uuid4().hex[:8]}"
            builder.build(name=actor_name)

            if i == args.task:
                object_actors[model_id] = actor_name

        task = grasp_tasks[args.task]
        target_actor_name = object_actors[task["model_id"]]
        target_pos = np.asarray(task["position"], dtype=np.float32).reshape(-1, 3)[0]

        fetch_robot = Fetch(
            config_path=args.config,
            robot_env=sim_env,
            static_pcd_paths=[canonical_map_path],
        )
        scheduler_type = config.get("planning", {}).get("scheduler_type", "default")
        scheduler = make_scheduler(scheduler_type, fetch_robot, args.config)

        monitor_cfg = config.get("monitor", {})
        sim_env.start_monitoring(
            target_actor_name,
            hold_seconds=float(monitor_cfg.get("hold_seconds", 0.0)),
            contact_force_threshold=float(monitor_cfg.get("contact_force_threshold", 0.001)),
        )

        if not args.no_trajectory:
            sim_env.start_trajectory_recording()

        recorder = ThirdPersonRecorder(
            sim_env=sim_env,
            target_pos=target_pos,
            width=args.width,
            height=args.height,
            fps=args.fps,
            max_frames=int(args.max_seconds * args.fps),
        )
        recorder.start()

        print(f"Running {args.scene} task {args.task}: {task['model_id']}")
        success, message = scheduler.grasp_anywhere(
            target_pos.reshape(1, 3),
            max_attempts=args.max_attempts,
            target_model_id=target_actor_name,
        )

        sim_env.arm_hold_monitoring()
        time.sleep(
            float(
                monitor_cfg.get(
                    "post_grasp_wait_s",
                    float(monitor_cfg.get("hold_seconds", 0.0)) + 0.2,
                )
            )
        )

        recorder.stop()
        gif_path = recorder.save(args.output)

        sim_env.stop_monitoring()
        has_collision, has_success, has_hold_success, collision_pairs = (
            sim_env.get_hold_monitoring_results()
        )

        trajectory_file = None
        if not args.no_trajectory:
            trajectory = sim_env.stop_trajectory_recording()
            if trajectory is not None:
                trajectory_file = str(Path(args.output).with_suffix(".npy"))
                np.save(trajectory_file, trajectory)

        result = {
            "scene": args.scene,
            "task": args.task,
            "model_id": task["model_id"],
            "scheduler_success": bool(success),
            "scheduler_message": message,
            "collision_detected": bool(has_collision),
            "gripper_touched_object": bool(has_success),
            "hold_success": bool(has_hold_success),
            "collision_pairs": collision_pairs,
            "gif": str(gif_path),
            "trajectory": trajectory_file,
            "frames": len(recorder.frames),
        }
        result_path = str(Path(args.output).with_suffix(".json"))
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2)

        print(json.dumps(result, indent=2))
        print(f"Saved GIF: {gif_path}")
        print(f"Saved result: {result_path}")

    finally:
        sim_env.close()


if __name__ == "__main__":
    main()
