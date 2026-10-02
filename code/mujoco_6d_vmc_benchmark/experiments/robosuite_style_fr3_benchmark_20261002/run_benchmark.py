#!/usr/bin/env python3
"""Independent FR3 WBC benchmark with a robosuite-style tabletop task layer."""
from __future__ import annotations
import argparse, json, sys, tempfile, subprocess
from pathlib import Path
import mujoco
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
sys.path.insert(0, str(ROOT / "flask_fr3_env_20261002"))
from flask_joint_planner import FlaskJointPlanner, FlaskPlannerConfig, MuJoCoFR3CollisionChecker
from run_sensor_wbc import HOME, GOAL, LOWER, UPPER, VEL_LIMIT, TORQUE_LIMIT, SensorWBC, make_scene

def benchmark_scene(fr3_xml: Path) -> str:
    xml = make_scene(fr3_xml)
    extra = r'''
    <geom name="rs_floor" type="plane" pos="0 0 0" size="3 3 0.01" rgba="0.055 0.065 0.075 1" contype="0" conaffinity="0"/>
    <geom name="rs_table_apron_front" type="box" pos="0.48 -0.57 0.22" size="0.36 0.018 0.06" rgba="0.10 0.12 0.15 1" contype="1" conaffinity="1"/>
    <geom name="rs_table_apron_right" type="box" pos="0.86 0.00 0.22" size="0.018 0.57 0.06" rgba="0.10 0.12 0.15 1" contype="1" conaffinity="1"/>
    <geom name="rs_backboard" type="box" pos="0.89 0.00 0.88" size="0.018 0.60 0.58" rgba="0.19 0.15 0.12 1" contype="1" conaffinity="1"/>
    <body name="rs_storage_bin" pos="0.56 0.24 0.43">
      <geom name="rs_bin_body" type="box" size="0.12 0.15 0.12" rgba="0.08 0.29 0.42 1" contype="1" conaffinity="1"/>
      <geom name="rs_bin_rim_front" type="box" pos="0 -0.16 0.14" size="0.14 0.018 0.025" rgba="0.04 0.16 0.23 1" contype="1" conaffinity="1"/>
      <geom name="rs_bin_rim_back" type="box" pos="0 0.16 0.14" size="0.14 0.018 0.025" rgba="0.04 0.16 0.23 1" contype="1" conaffinity="1"/>
      <geom name="rs_bin_rim_left" type="box" pos="-0.14 0 0.14" size="0.018 0.15 0.025" rgba="0.04 0.16 0.23 1" contype="1" conaffinity="1"/>
      <geom name="rs_bin_rim_right" type="box" pos="0.14 0 0.14" size="0.018 0.15 0.025" rgba="0.04 0.16 0.23 1" contype="1" conaffinity="1"/>
    </body>
    <body name="rs_tool_tray" pos="0.62 -0.28 0.34">
      <geom name="rs_tray_base" type="box" size="0.14 0.16 0.018" rgba="0.12 0.13 0.15 1" contype="1" conaffinity="1"/>
      <geom name="rs_tray_wall_front" type="box" pos="0 -0.15 0.055" size="0.14 0.016 0.055" rgba="0.17 0.18 0.21 1" contype="1" conaffinity="1"/>
      <geom name="rs_tray_wall_back" type="box" pos="0 0.15 0.055" size="0.14 0.016 0.055" rgba="0.17 0.18 0.21 1" contype="1" conaffinity="1"/>
      <geom name="rs_tray_wall_left" type="box" pos="-0.13 0 0.055" size="0.016 0.15 0.055" rgba="0.17 0.18 0.21 1" contype="1" conaffinity="1"/>
      <geom name="rs_tray_wall_right" type="box" pos="0.13 0 0.055" size="0.016 0.15 0.055" rgba="0.17 0.18 0.21 1" contype="1" conaffinity="1"/>
      <geom name="rs_screwdriver_visual" type="capsule" fromto="-0.08 -0.04 0.06 0.08 -0.04 0.06" size="0.012" rgba="0.78 0.23 0.08 1" contype="0" conaffinity="0"/>
      <geom name="rs_hex_tool_visual" type="cylinder" pos="0.00 0.07 0.065" size="0.025 0.012" rgba="0.76 0.78 0.82 1" contype="0" conaffinity="0"/>
    </body>
    <body name="rs_cube_a" pos="0.20 -0.12 0.36"><geom name="rs_cube_a_geom" type="box" size="0.047 0.047 0.047" rgba="0.78 0.12 0.08 1" contype="1" conaffinity="1"/><site name="rs_cube_a_site" pos="0 0 0.055" size="0.012" rgba="1 0.28 0.16 1"/></body>
    <body name="rs_cube_b" pos="0.20 -0.12 0.454"><geom name="rs_cube_b_geom" type="box" size="0.047 0.047 0.047" rgba="0.95 0.64 0.08 1" contype="1" conaffinity="1"/><site name="rs_cube_b_site" pos="0 0 0.055" size="0.012" rgba="1 0.82 0.14 1"/></body>
    <!-- PickPlace pair: deliberately placed in the front open workspace for visual audit -->
    <!-- PickPlace pair: dedicated front tray keeps the task object fully visible -->
    <body name="rs_pick_station" pos="0.62 -0.72 0.32">
      <geom name="rs_pick_station_base" type="box" size="0.16 0.13 0.012" rgba="0.04 0.05 0.06 1" contype="0" conaffinity="0"/>
      <geom name="rs_pick_station_border" type="box" pos="0 0 0.016" size="0.14 0.11 0.004" rgba="1.0 0.48 0.02 1" contype="0" conaffinity="0"/>
    </body>
    <body name="rs_pick_object" pos="0.62 -0.72 0.415">
      <geom name="rs_pick_object_base" type="cylinder" pos="0 0 -0.064" size="0.086 0.006" rgba="0.12 0.02 0.01 0.95" contype="0" conaffinity="0"/>
      <geom name="rs_pick_object_geom" type="box" size="0.095 0.095 0.095" rgba="1.0 0.52 0.015 1" contype="1" conaffinity="1"/>
      <geom name="rs_pick_object_top" type="box" pos="0 0 0.069" size="0.076 0.076 0.010" rgba="1.0 0.92 0.10 1" contype="0" conaffinity="0"/>
      <geom name="rs_pick_object_beacon" type="capsule" fromto="0 0 0.10 0 0 0.30" size="0.022" rgba="1 0.92 0.08 1" contype="0" conaffinity="0"/>
      <site name="rs_pick_object_site" pos="0 0 0.075" size="0.018" rgba="1 0.1 0.02 1"/>
    </body>
    <body name="rs_goal_marker" pos="0.72 -0.50 0.315">
      <geom name="rs_goal_marker_base" type="cylinder" size="0.102 0.008" rgba="0.02 0.16 0.05 0.95" contype="0" conaffinity="0"/>
      <geom name="rs_goal_marker_geom" type="cylinder" pos="0 0 0.010" size="0.090 0.010" rgba="0.05 1.0 0.22 0.98" contype="0" conaffinity="0"/>
      <geom name="rs_goal_marker_inner" type="cylinder" pos="0 0 0.022" size="0.058 0.006" rgba="0.015 0.08 0.025 0.95" contype="0" conaffinity="0"/>
      <geom name="rs_goal_marker_pole" type="capsule" fromto="0 0 0.025 0 0 0.42" size="0.018" rgba="0.10 1.0 0.28 1" contype="0" conaffinity="0"/>
      <geom name="rs_goal_marker_flag" type="box" pos="0 0 0.43" size="0.11 0.020 0.035" rgba="0.10 1.0 0.28 1" contype="0" conaffinity="0"/>
      <site name="rs_goal_site" pos="0 0 0.030" size="0.018" rgba="0.10 1 0.25 1"/>
    </body>
    <geom name="rs_cabinet_side" type="box" pos="0.77 0.40 0.62" size="0.10 0.10 0.30" rgba="0.45 0.27 0.14 1" contype="1" conaffinity="1"/>
    <geom name="rs_cabinet_shelf" type="box" pos="0.67 0.40 0.77" size="0.10 0.10 0.018" rgba="0.55 0.34 0.19 1" contype="1" conaffinity="1"/>
    <light name="rs_fill_light" pos="-1.1 -1.2 2.4" dir="0.25 0.45 -1" diffuse="0.8 0.85 1.0" specular="0.2 0.2 0.2"/>
'''
    return xml.replace("\n  </worldbody>", extra + "\n  </worldbody>", 1)

def wbc_command_compat(model, data, trajectory, mass):
    q_ref, qdot_ref, qddot_ref = trajectory.sample(float(data.time))
    mujoco.mj_fullM(model, mass, data.qM)
    q_error = q_ref - data.qpos[:7]
    qdot_error = qdot_ref - data.qvel[:7]
    desired_acceleration = qddot_ref + 110.0 * q_error + 24.0 * qdot_error
    torque = mass[:7, :7] @ desired_acceleration + data.qfrc_bias[:7]
    return np.clip(torque, -TORQUE_LIMIT, TORQUE_LIMIT)

def draw_panel(qerr, torques, contacts, now, duration, segments):
    im = Image.new("RGB", (400, 480), "#151a21")
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
        s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    except OSError:
        f = s = ImageFont.load_default()
    d.text((14, 12), "FR3 robosuite-style benchmark", fill="#f0f3f5", font=f)
    d.text((14, 36), "FLASK route + computed-torque WBC", fill="#9dc9e8", font=s)
    d.text((14, 66), f"t = {now:5.2f} / {duration:5.2f} s", fill="#d8dde2", font=s)
    d.text((14, 88), f"route segments: {segments}", fill="#69dcff", font=s)
    d.text((14, 110), f"q error: {qerr[-1]:7.4f} rad", fill="#d8dde2", font=s)
    d.text((14, 132), f"command torque: {torques[-1]:7.2f} Nm", fill="#d8dde2", font=s)
    d.text((14, 154), f"MuJoCo contacts: {contacts[-1]:02d}", fill="#8ff0aa", font=s)
    d.text((14, 194), "task layout", fill="#f2c879", font=f)
    for i, txt in enumerate(["robosuite-style tabletop arena", "storage bin + raised rim", "tool tray + visual tools", "Stack cubes A / B", "PICK  orange cube on front tray  ->  PLACE  green flag", "front-edge task pair kept in view", "FR3 sensors + collision audit"]):
        d.text((20, 222 + 25*i), "• " + txt, fill="#c6cbd0", font=s)
    d.rectangle((20, 391, 34, 405), fill="#ff8a12", outline="#ffd34e")
    d.text((40, 389), "PICK OBJECT", fill="#ffd34e", font=s)
    d.rectangle((165, 391, 179, 405), fill="#18f06a", outline="#b8ffca")
    d.text((185, 389), "PLACE TARGET", fill="#9dffb6", font=s)
    left, top, right, bottom = 16, 412, 384, 464
    d.rectangle((left, top, right, bottom), outline="#3d4653", width=1)
    d.text((left+6, top+5), "q error trace", fill="#aeb8c4", font=s)
    vals = np.asarray(qerr[-110:], dtype=float)
    if vals.size > 1:
        scale = max(float(vals.max()), 1e-5)
        pts = [(left+5+int(i*(right-left-10)/max(len(vals)-1,1)), bottom-5-int(min(v/scale,1)* (bottom-top-25))) for i,v in enumerate(vals)]
        d.line(pts, fill="#63d7ff", width=2)
    return np.asarray(im)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fr3-xml", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--time-scale", type=float, default=3.0)
    ap.add_argument("--fps", type=int, default=20)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="robosuite_style_fr3_") as td:
        scene = Path(td) / "scene.xml"
        scene.write_text(benchmark_scene(a.fr3_xml))
        model = mujoco.MjModel.from_xml_path(str(scene))
        data = mujoco.MjData(model)
        data.qpos[:7] = HOME
        for finger_name in ('fr3v2_finger_joint1', 'fr3v2_finger_joint2'):
            finger_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, finger_name)
            if finger_id >= 0:
                data.qpos[int(model.jnt_qposadr[finger_id])] = 0.04
        mujoco.mj_forward(model, data)
        robot = [model.geom(i).name for i in range(model.ngeom) if (model.geom(i).name or "").startswith("fr3v2_") and model.geom_contype[i] != 0]
        obstacles = [model.geom(i).name for i in range(model.ngeom) if (model.geom(i).name or "").startswith(("flask_", "rs_")) and model.geom_contype[i] != 0 and model.geom(i).name != "rs_floor" and model.geom(i).name != "flask_target_object_geom"]
        checker = MuJoCoFR3CollisionChecker(model, robot_geom_names=robot, obstacle_geom_names=obstacles)
        cfg = FlaskPlannerConfig(velocity_limits=VEL_LIMIT, acceleration_limits=np.full(7,12.0), joint_lower=LOWER, joint_upper=UPPER, steering_time=0.65, min_steering_time=0.10, max_steering_time=4.0, samples_per_segment=45, max_iterations=10000, goal_bias=0.25, seed=20261002)
        planner = FlaskJointPlanner(cfg, collision_fn=checker)
        direct = planner.steer(HOME, np.zeros(7), GOAL, np.zeros(7))
        traj = planner.plan(HOME, GOAL)
        if traj is None:
            raise SystemExit("planner failed in robosuite-style scene")
        traj = traj.retime(a.time_scale)
        mass = np.zeros((model.nv, model.nv))
        renderer = mujoco.Renderer(model, height=480, width=640)
        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(cam)
        cam.lookat[:] = [0.42, -0.10, 0.55]
        cam.distance, cam.azimuth, cam.elevation = 2.05, -58, -20
        stride = max(1, int(round(1.0/(model.opt.timestep*a.fps))))
        total = int(np.ceil((traj.duration+0.6)/model.opt.timestep))
        qerr, torques, contacts, times = [], [], [], []
        a.output.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(a.output), cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (1040, 480))
        if not writer.isOpened():
            raise RuntimeError("could not open video writer")
        try:
            for step in range(total):
                ref = traj.sample(float(data.time))[0]
                data.ctrl[:] = wbc_command_compat(model, data, traj, mass)
                mujoco.mj_step(model, data)
                if step % stride and step+1 < total:
                    continue
                now = float(data.time)
                qerr.append(float(np.max(np.abs(ref-data.qpos[:7]))))
                torques.append(float(np.max(np.abs(data.ctrl[:7]))))
                contacts.append(int(data.ncon))
                times.append(now)
                renderer.update_scene(data, camera=cam)
                left = renderer.render()
                right = draw_panel(qerr, torques, contacts, now, traj.duration, len(traj.segments))
                writer.write(cv2.cvtColor(np.hstack([left, right]).astype(np.uint8), cv2.COLOR_RGB2BGR))
        finally:
            writer.release(); renderer.close()
        report = {"protocol":"robosuite_style_fr3_flask_wbc","scene":"independent FR3 wrapper with robosuite-style tabletop task layer","fr3_xml":str(a.fr3_xml),"direct_edge_available":direct is not None,"trajectory_segments":len(traj.segments),"trajectory_duration_s":traj.duration,"time_scale":a.time_scale,"frames":len(times),"scene_obstacle_count":len(obstacles),"max_contacts_seen":max(contacts),"peak_tracking_error_rad":max(qerr),"peak_command_torque_nm":max(torques),"final_q_error_inf":float(np.max(np.abs(data.qpos[:7]-GOAL))),"sensor_count":int(model.nsensor),"task_objects":["rs_cube_a","rs_cube_b","rs_pick_object","rs_goal_marker"],"obstacle_names":obstacles,"limitations":"development-only; task objects are static and this is not a grasp-success claim"}
        a.output.with_suffix(".json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
if __name__ == "__main__":
    main()

