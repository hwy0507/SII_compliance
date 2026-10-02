#!/usr/bin/env python3
"""Render a robosuite 1.5.2 Stack reference scene with telemetry.

This is a reference benchmark artifact: it deliberately uses robosuite's
official arena / object / Panda asset so the visual and contact model can be
compared with the hand-built FR3 scene.
"""
from pathlib import Path
import time
import cv2
import numpy as np
import robosuite as suite
from robosuite.controllers import load_composite_controller_config

OUT = Path("/home/arm1/vmc_mujoco_runtime/robosuite_wbc_reference_20261002")
OUT.mkdir(parents=True, exist_ok=True)
VIDEO = OUT / "robosuite_stack_reference.mp4"
META = OUT / "robosuite_stack_reference_metrics.npz"

cfg = load_composite_controller_config(controller="BASIC", robot="Panda")
env = suite.make(
    env_name="Stack",
    robots="Panda",
    controller_configs=cfg,
    has_renderer=False,
    has_offscreen_renderer=True,
    use_camera_obs=False,
    ignore_done=True,
    reward_shaping=True,
    control_freq=20,
)
obs = env.reset()
frame_w, frame_h = 960, 540
writer = cv2.VideoWriter(
    str(VIDEO),
    cv2.VideoWriter_fourcc(*"mp4v"),
    20.0,
    (frame_w, frame_h),
)
if not writer.isOpened():
    raise RuntimeError(f"could not open {VIDEO}")

cube_a = np.array(obs["cubeA_pos"], dtype=float)
cube_b = np.array(obs["cubeB_pos"], dtype=float)
# Waypoints make the contact sequence legible without relying on a learned policy.
waypoints = [
    ("hover A", cube_a + [0.0, 0.0, 0.16], -1.0, 45),
    ("approach A", cube_a + [0.0, 0.0, 0.065], -1.0, 30),
    ("grasp A", cube_a + [0.0, 0.0, 0.065], 1.0, 24),
    ("lift A", cube_a + [0.0, 0.0, 0.20], 1.0, 42),
    ("move to B", cube_b + [0.0, 0.0, 0.17], 1.0, 52),
    ("place A", cube_b + [0.0, 0.0, 0.105], 1.0, 34),
    ("release", cube_b + [0.0, 0.0, 0.105], -1.0, 25),
    ("retreat", np.array([-0.10, -0.12, 1.08]), -1.0, 36),
]
errors, rewards, stages, contacts, eef_trace = [], [], [], [], []
total_steps = sum(n for _, _, _, n in waypoints)
step_idx = 0
for stage_name, target, grip, count in waypoints:
    for _ in range(count):
        eef = np.asarray(obs["robot0_eef_pos"], dtype=float)
        err = np.asarray(target) - eef
        action = np.zeros(7, dtype=float)
        action[:3] = np.clip(err / 0.05, -1.0, 1.0)
        action[3:6] = 0.0
        action[6] = grip
        obs, reward, _, _ = env.step(action)
        # Count contacts involving the robot or either cube at this frame.
        ncon = int(env.sim.data.ncon)
        errors.append(float(np.linalg.norm(err)))
        rewards.append(float(reward))
        stages.append(stage_name)
        contacts.append(ncon)
        eef_trace.append(np.asarray(obs["robot0_eef_pos"], dtype=float))
        rgb = env.sim.render(camera_name="agentview", width=640, height=540)
        frame = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
        panel = np.full((540, 320, 3), (22, 27, 35), dtype=np.uint8)
        cv2.putText(panel, "robosuite 1.5.2 / Stack", (16, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.72, (235, 240, 245), 2, cv2.LINE_AA)
        cv2.putText(panel, "official arena + Panda + OSC_POSE", (16, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (165, 185, 205), 1, cv2.LINE_AA)
        cv2.putText(panel, f"stage: {stage_name}", (16, 102),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (80, 210, 255), 2, cv2.LINE_AA)
        cv2.putText(panel, f"step: {step_idx:03d}/{total_steps}", (16, 132),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (215, 220, 225), 1, cv2.LINE_AA)
        cv2.putText(panel, f"eef error: {errors[-1]*1000:6.1f} mm", (16, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (215, 220, 225), 1, cv2.LINE_AA)
        cv2.putText(panel, f"reward: {rewards[-1]:6.3f}", (16, 186),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (215, 220, 225), 1, cv2.LINE_AA)
        cv2.putText(panel, f"MuJoCo contacts: {ncon:02d}", (16, 212),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 235, 150), 1, cv2.LINE_AA)
        cv2.putText(panel, "scene contents", (16, 252),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 200, 100), 1, cv2.LINE_AA)
        for i, line in enumerate([
            "wood worktable / arena",
            "two textured cubes",
            "Panda arm + parallel gripper",
            "collision contacts + reward",
            "optional RGB/depth cameras",
        ]):
            cv2.putText(panel, "• " + line, (22, 280 + 28*i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46, (205, 210, 215), 1, cv2.LINE_AA)
        # A compact error trace on the right panel.
        x0, y0, w, h = 18, 448, 284, 72
        cv2.rectangle(panel, (x0, y0), (x0+w, y0+h), (45, 52, 65), -1)
        cv2.putText(panel, "tracking error (last 90 frames)", (x0+7, y0+18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 190, 205), 1, cv2.LINE_AA)
        hist = np.asarray(errors[-90:], dtype=float)
        if hist.size > 1:
            scale = max(float(hist.max()), 1e-4)
            pts = []
            for j, value in enumerate(hist):
                px = x0 + 5 + int(j * (w-10) / max(len(hist)-1, 1))
                py = y0 + h - 6 - int(min(value/scale, 1.0) * (h-28))
                pts.append((px, py))
            cv2.polylines(panel, [np.asarray(pts, dtype=np.int32)], False, (90, 220, 255), 2)
        writer.write(np.hstack([frame, panel]))
        step_idx += 1

writer.release()
np.savez(
    META,
    eef_error_m=np.asarray(errors),
    reward=np.asarray(rewards),
    contacts=np.asarray(contacts),
    eef_pos=np.asarray(eef_trace),
    waypoint_names=np.asarray([x[0] for x in waypoints]),
)
env.close()
print(f"video={VIDEO}")
print(f"metrics={META}")
print(f"frames={step_idx}")
print(f"max_eef_error_mm={max(errors)*1000:.3f}")
print(f"mean_eef_error_mm={np.mean(errors)*1000:.3f}")
print(f"max_contacts={max(contacts)}")
print(f"max_reward={max(rewards):.4f}")

