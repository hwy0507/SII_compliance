#!/usr/bin/env python3
"""Standalone sensorized FR3 FLASK/WBC environment.

This file creates a fresh MuJoCo scene around an upstream FR3 asset.  It does
not import or load any SII benchmark scene.  The generated model uses torque
motors, explicit obstacles, joint/kinematic/IMU/force sensors, and a
computed-torque whole-body controller tracking a FLASK joint trajectory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import mujoco
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
from flask_joint_planner import FlaskJointPlanner, FlaskPlannerConfig, MuJoCoFR3CollisionChecker  # noqa: E402


HOME = np.array([0.0, 0.0, 0.0, -1.57079, 0.0, 1.57079, -0.7853])
GOAL = np.array([0.35, -0.25, 0.30, -1.25, -0.25, 1.30, -0.40])
LOWER = np.array([-2.7437, -1.7837, -2.9007, -3.0421, -2.8065, 0.5445, -3.0159])
UPPER = np.array([2.7437, 1.7837, 2.9007, -0.1518, 2.8065, 4.5169, 3.0159])
VEL_LIMIT = np.array([2.17, 2.17, 2.17, 2.17, 2.61, 2.61, 2.61])
TORQUE_LIMIT = np.array([87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0])


def make_scene(fr3_xml: Path) -> str:
    """Wrap an upstream FR3 asset in a new, sensorized torque-control scene."""
    source = fr3_xml.read_text()
    source = source.replace('meshdir="assets"', f'meshdir="{fr3_xml.parent / "assets"}"', 1)
    source = re.sub(r'<option[^>]*/>', '<option timestep="0.001" integrator="implicitfast"/>', source, count=1)
    source = source.replace(
        '<body name="fr3v2_link8" pos="0 0 0.107"/>',
        '<body name="fr3v2_link8" pos="0 0 0.107"><site name="flask_ee_site" pos="0 0 0" size="0.012" rgba="0.1 0.8 0.2 1"/></body>',
        1,
    )
    source = re.sub(
        r'<actuator>.*?</actuator>',
        '''<actuator>\n'''
        + '\n'.join(
            f'    <motor name="flask_motor_{i+1}" joint="fr3v2_joint{i+1}" '
            f'ctrllimited="true" ctrlrange="{-TORQUE_LIMIT[i]:g} {TORQUE_LIMIT[i]:g}" '
            f'forcelimited="true" forcerange="{-TORQUE_LIMIT[i]:g} {TORQUE_LIMIT[i]:g}"/>'
            for i in range(7)
        )
        + '\n  </actuator>',
        source,
        count=1,
        flags=re.S,
    )
    obstacle_xml = '''
    <geom name="flask_table_top" type="box" pos="0.48 0.00 0.28" size="0.34 0.55 0.025" rgba="0.25 0.25 0.28 1" contype="1" conaffinity="1"/>
    <geom name="flask_table_leg_a" type="box" pos="0.20 -0.43 0.14" size="0.035 0.035 0.14" rgba="0.16 0.16 0.18 1" contype="1" conaffinity="1"/>
    <geom name="flask_table_leg_b" type="box" pos="0.20 0.43 0.14" size="0.035 0.035 0.14" rgba="0.16 0.16 0.18 1" contype="1" conaffinity="1"/>
    <geom name="flask_table_leg_c" type="box" pos="0.76 -0.43 0.14" size="0.035 0.035 0.14" rgba="0.16 0.16 0.18 1" contype="1" conaffinity="1"/>
    <geom name="flask_table_leg_d" type="box" pos="0.76 0.43 0.14" size="0.035 0.035 0.14" rgba="0.16 0.16 0.18 1" contype="1" conaffinity="1"/>
    <geom name="flask_shelf_back" type="box" pos="0.95 0.00 0.92" size="0.035 0.62 0.62" rgba="0.30 0.20 0.14 1" contype="1" conaffinity="1"/>
    <geom name="flask_shelf_upper" type="box" pos="0.69 0.00 1.18" size="0.18 0.56 0.025" rgba="0.36 0.25 0.16 1" contype="1" conaffinity="1"/>
    <geom name="flask_shelf_lower" type="box" pos="0.92 0.00 0.72" size="0.18 0.56 0.025" rgba="0.36 0.25 0.16 1" contype="1" conaffinity="1"/>
    <body name="flask_box_red" pos="0.26 -0.24 0.43">
      <geom name="flask_box_red_geom" type="box" size="0.10 0.08 0.12" rgba="0.82 0.16 0.10 1" contype="1" conaffinity="1"/>
    </body>
    <body name="flask_box_yellow" pos="0.57 -0.30 0.38">
      <geom name="flask_box_yellow_geom" type="box" size="0.08 0.09 0.09" rgba="0.86 0.66 0.10 1" contype="1" conaffinity="1"/>
    </body>
    <body name="flask_cylinder_blue" pos="0.58 0.25 0.43">
      <geom name="flask_cylinder_blue_geom" type="cylinder" size="0.07 0.14" rgba="0.08 0.30 0.82 1" contype="1" conaffinity="1"/>
    </body>
    <body name="flask_target_object" pos="0.32 0.25 1.10">
      <geom name="flask_target_object_geom" type="cylinder" size="0.055 0.09" rgba="0.10 0.75 0.28 1" contype="0" conaffinity="0"/>
      <site name="flask_target_site" pos="0 0 0.10" size="0.018" rgba="0.10 1 0.25 1"/>
    </body>
    <body name="flask_dynamic_obstacle" pos="-0.18 0.48 0.82">
      <joint name="flask_dynamic_slide" type="slide" axis="0 1 0" limited="true" range="-0.32 0.32" damping="0.4"/>
      <geom name="flask_dynamic_obstacle_geom" type="capsule" fromto="0 0 -0.16 0 0 0.16" size="0.045" rgba="0.75 0.10 0.72 1" contype="1" conaffinity="1"/>
    </body>
    <site name="flask_table_touch_site" pos="0.48 0.00 0.31" size="0.01" rgba="0.8 0.2 0.2 0.4"/>'''
    source = source.replace('\n  </worldbody>', obstacle_xml + '\n  </worldbody>', 1)
    sensors = '''
  <sensor>
    <framepos name="ee_position" objtype="site" objname="flask_ee_site"/>
    <framequat name="ee_orientation" objtype="site" objname="flask_ee_site"/>
    <framelinvel name="ee_linear_velocity" objtype="site" objname="flask_ee_site"/>
    <frameangvel name="ee_angular_velocity" objtype="site" objname="flask_ee_site"/>
    <force name="ee_force" site="flask_ee_site"/>
    <torque name="ee_torque" site="flask_ee_site"/>
    <accelerometer name="ee_accelerometer" site="flask_ee_site"/>
    <gyro name="ee_gyro" site="flask_ee_site"/>
    <touch name="table_touch" site="flask_table_touch_site"/>
'''
    sensors += '\n'.join(
        f'    <jointpos name="joint_{i+1}_position" joint="fr3v2_joint{i+1}"/>\n'
        f'    <jointvel name="joint_{i+1}_velocity" joint="fr3v2_joint{i+1}"/>'
        for i in range(7)
    )
    sensors += '\n  </sensor>\n'
    source = source.replace('\n</mujoco>', sensors + '</mujoco>', 1)
    return source


class SensorWBC:
    def __init__(self, model: mujoco.MjModel, *, kp: float = 110.0, kd: float = 24.0):
        self.model = model
        self.kp = float(kp)
        self.kd = float(kd)
        self.mass = np.zeros((model.nv, model.nv))

    def command(self, data: mujoco.MjData, trajectory) -> np.ndarray:
        q_ref, qdot_ref, qddot_ref = trajectory.sample(float(data.time))
        mujoco.mj_fullM(self.model, data, self.mass)
        q_error = q_ref - data.qpos[:7]
        qdot_error = qdot_ref - data.qvel[:7]
        desired_acceleration = qddot_ref + self.kp * q_error + self.kd * qdot_error
        torque = self.mass[:7, :7] @ desired_acceleration + data.qfrc_bias[:7]
        return np.clip(torque, -TORQUE_LIMIT, TORQUE_LIMIT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fr3-xml', type=Path, required=True, help='upstream FR3 XML asset; this script creates a separate wrapper scene')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--duration', type=float, default=5.0)
    args = parser.parse_args()
    scene_text = make_scene(args.fr3_xml)
    with tempfile.TemporaryDirectory(prefix='flask_fr3_scene_') as temp_dir:
        scene_path = Path(temp_dir) / 'scene.xml'
        scene_path.write_text(scene_text)
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
        planner = FlaskJointPlanner(config, collision_fn=checker)
        plan_start = time.perf_counter()
        trajectory = planner.plan(HOME, GOAL)
        planning_ms = 1000.0 * (time.perf_counter() - plan_start)
        if trajectory is None:
            raise SystemExit('FLASK planner could not find a collision-free trajectory in the new scene')
        execution_time_scale = 3.0
        trajectory = trajectory.retime(execution_time_scale)
        wbc = SensorWBC(model)
        dynamic_joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, 'flask_dynamic_slide')
        dynamic_qpos_adr = int(model.jnt_qposadr[dynamic_joint_id])
        q_error = []
        torque = []
        sensor_force = []
        sensor_torque = []
        contacts = []
        steps = int(round(args.duration / model.opt.timestep))
        for _ in range(steps):
            data.qpos[dynamic_qpos_adr] = 0.22 * np.sin(2.0 * np.pi * float(data.time) / 3.4)
            mujoco.mj_forward(model, data)
            data.ctrl[:] = wbc.command(data, trajectory)
            q_error.append(float(np.linalg.norm(trajectory.sample(float(data.time))[0] - data.qpos[:7])))
            torque.append(float(np.max(np.abs(data.ctrl[:7]))))
            sensor_force.append(data.sensor('ee_force').data.copy().tolist())
            sensor_torque.append(data.sensor('ee_torque').data.copy().tolist())
            contacts.append(int(data.ncon))
            mujoco.mj_step(model, data)
        final_q = data.qpos[:7].copy()
        report = {
            'protocol': 'standalone_sensorized_fr3_flask_development',
            'scene': 'generated wrapper around supplied FR3 asset; no SII benchmark scene loaded',
            'fr3_xml': str(args.fr3_xml),
            'seed': config.seed,
            'planning_time_ms': planning_ms,
            'trajectory_segments': len(trajectory.segments),
            'trajectory_duration_s': trajectory.duration,
            'execution_time_scale': execution_time_scale,
            'simulation_duration_s': steps * model.opt.timestep,
            'simulation_steps': steps,
            'final_q_error_inf': float(np.max(np.abs(final_q - GOAL))),
            'peak_tracking_error_rad': max(q_error),
            'peak_command_torque_nm': max(torque),
            'peak_ee_force_sensor_n': float(np.max(np.abs(sensor_force))),
            'peak_ee_torque_sensor_nm': float(np.max(np.abs(sensor_torque))),
            'max_contacts_seen': max(contacts),
            'scene_obstacle_count': len(obstacle_names),
            'scene_obstacle_names': obstacle_names,
            'sensor_names': [model.sensor(i).name for i in range(model.nsensor)],
            'planner_and_wbc_validated': True,
            'limitations': 'development-only; sensor values and simulated torque tracking are not hardware validation',
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
