# Mechanism Run

Results directory: `results/20260819_092205_mechanism`

## Command used

```bash
/home/arm1/vmc_mujoco_runtime/.venv/bin/python mujoco_bridge/franka_cutting_vm_sim_mechanism.py --sim-time 10.0 --record cutting_mechanism.mp4
```

## Resolved simulation settings

- `sim_time = 10`
- `dt = 0.001`
- `load_snapshot_txt = None`
- `load_snapshot_start_at_zero = False`
- `knife_in_air = False`
- `nullspace_posture = False`
- `joint4_anchor_xyz = None`
- `joint4_spring_kp = 0`
- `joint4_spring_kd = 0`
- `gravity_comp_mode = robot_only`
- `joint_kd = None`
- `trace_npz = results/20260819_092205_mechanism/trace.npz`
- `snapshot_txt = results/20260819_092205_mechanism/cut_state.txt`
- `record_path = results/20260819_092205_mechanism/cutting_mechanism.mp4`

Resolved nullspace values used by the simulator:

- `q_pref = -1.08998578 0.881800735 -0.258898269 -1.411888077 0.294467747 2.051399292 -1.440580354`
- `kp = 0.5 0.5 0.35 0.2 0.35 0.25 0.2`
- `kd = 0.08 0.08 0.06 0.03 0.06 0.04 0.03`
