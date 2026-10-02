# Standalone sensorized FR3 FLASK environment

This directory is a fresh MuJoCo environment for reproducing the FLASK-style
planner plus a torque-level fixed-base WBC. It does not load any SII benchmark
scene. At runtime `run_sensor_wbc.py` reads an upstream `fr3v2.xml` robot
asset, writes a temporary wrapper model, replaces the position actuators with
seven torque motors, and adds two box/cylinder obstacles.

The wrapper adds these sensors:

- end-effector frame position, quaternion, linear velocity, and angular velocity;
- end-effector force and torque at `flask_ee_site`;
- joint position and joint velocity for all seven FR3 joints.

The WBC uses the FLASK trajectory's `q`, `q_dot`, and `q_ddot` with computed
torque `tau = M(q)(q_ddot + Kp(q_ref-q) + Kd(qdot_ref-qdot)) + bias(q,qdot)`,
then applies the FR3 actuator limits. The planner's collision callback checks
only the explicitly named FR3 and obstacle geometries in this new model.

Example on `arm1`:

```bash
PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts \
  /home/arm1/vmc_mujoco_runtime/simba_v2_venv/bin/python \
  code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002/run_sensor_wbc.py \
  --fr3-xml /home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3_v2/fr3v2.xml \
  --duration 4.0 \
  --output /home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_sensor_wbc.json
```

The development run on 2026-10-02 produced a two-segment collision-free plan
in 3.86 ms, simulated for 4.0 s / 2000 steps, with peak command torque
48.57 Nm, zero contacts, zero measured end-effector force/torque in this
non-contact scene, and final joint error 0.0644 rad. These are simulated
development measurements, not hardware or real-time certification.

## Reference-style live plot

To render the MuJoCo view beside the online speed and acceleration plots, run:

```bash
MUJOCO_GL=egl PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts:code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002 \
  python code/mujoco_6d_vmc_benchmark/experiments/flask_fr3_env_20261002/render_realtime_plot.py \
  --fr3-xml /home/arm1/vmc_mujoco_runtime/mujoco_menagerie/franka_fr3_v2/fr3v2.xml \
  --time-scale 3 --output /home/arm1/vmc_mujoco_runtime/flask_fr3_env_20261002_realtime_plot.mp4
```

The default time scale makes the planned path about 6.25 s long. The right
panel updates every rendered frame and shows normalized arm/EE speed above
and normalized arm acceleration/torque usage below, each with a dashed limit.
If ffmpeg is unavailable, the script writes the same live frames to a `.frames`
directory for later encoding.
