"""Read-only physical-substep audit shared by every panel controller.

Velocity/error use post-integration qpos/qvel and a separate kinematic MjData.
Actuator forces are the live dynamics evaluation retained by the completed
mj_step, generally from an earlier evaluation time within that same step.
They are deliberately not advertised as perfectly synchronous samples.
"""
from __future__ import annotations
from contextlib import AbstractContextManager
from pathlib import Path
import json
import mujoco
import numpy as np


class EpisodeMetrics:
    def __init__(self, env, capacity=None):
        self.env = env
        self.timestep_s = float(env.model.opt.timestep)
        self.stage_names = tuple(env.reference.names)
        self.scratch = mujoco.MjData(env.model)
        self.jp = np.zeros((3, env.model.nv))
        self.jr = np.zeros_like(self.jp)
        self.capacity = max(1024, int(np.ceil(env.simulation_time_s / env.model.opt.timestep)) + 16 if capacity is None else int(capacity))
        self.arrays = dict(time=np.empty(self.capacity), dt=np.empty(self.capacity), stage=np.empty(self.capacity, dtype=np.int16),
                           error=np.empty((self.capacity,3), dtype=np.float32),
                           twist=np.empty((self.capacity,6), dtype=np.float32),
                           qfrc_actuator=np.empty((self.capacity,7), dtype=np.float32),
                           actuator_force=np.empty((self.capacity,7), dtype=np.float32))
        self.count = 0
        self.stages = {}
        self.speed_peak = 0.
        self.qfrc_peak = np.zeros(7)
        self.force_peak = np.zeros(7)
        self.timestep_counts = {}

    def sample(self):
        env, scratch = self.env, self.scratch
        model, data = env.model, env.data
        if self.count >= self.capacity:
            raise RuntimeError('Physical audit capacity exceeded planned simulation duration')
        scratch.qpos[:] = data.qpos
        scratch.qvel[:] = data.qvel
        scratch.mocap_pos[:] = data.mocap_pos
        scratch.mocap_quat[:] = data.mocap_quat
        # No mj_forward, collision detection, or write to live model/data.
        mujoco.mj_kinematics(model, scratch)
        mujoco.mj_comPos(model, scratch)
        mujoco.mj_jacBody(model, scratch, self.jp, self.jr, env._hand_id)
        twist = np.r_[self.jp @ scratch.qvel, self.jr @ scratch.qvel]
        stage = int(env.reference.index)
        target = np.asarray(env.reference.goals[stage])
        error = scratch.xpos[env._hand_id] - target
        torque = data.qfrc_actuator[:7].copy()
        force = data.actuator_force[:7].copy()
        speed = float(np.linalg.norm(twist[:3]))
        dt=float(model.opt.timestep)
        self.timestep_counts[dt]=self.timestep_counts.get(dt,0)+1
        self.speed_peak = max(self.speed_peak, speed)
        self.qfrc_peak = np.maximum(self.qfrc_peak, np.abs(torque))
        self.force_peak = np.maximum(self.force_peak, np.abs(force))
        row = self.stages.setdefault(stage, dict(count=0, sum_squared_xyz=np.zeros(3),
                    time_integral_squared_xyz=np.zeros(3),duration_s=0.,
                    error_peak_m=0., speed_peak_mps=0., qfrc_peak_nm=0.,
                    first_s=float(data.time), last_s=float(data.time)))
        row['count'] += 1
        row['sum_squared_xyz'] += error * error
        row['time_integral_squared_xyz'] += dt * error * error
        row['duration_s'] += dt
        row['error_peak_m'] = max(row['error_peak_m'],float(np.linalg.norm(error)))
        row['speed_peak_mps'] = max(row['speed_peak_mps'],speed)
        row['qfrc_peak_nm'] = max(row['qfrc_peak_nm'],float(np.abs(torque).max()))
        row['last_s'] = float(data.time)
        for key, value in dict(time=float(data.time), dt=dt, stage=stage, error=error, twist=twist,
                               qfrc_actuator=torque, actuator_force=force).items():
            self.arrays[key][self.count] = value
        self.count += 1

    def summary(self):
        by_stage = {}
        mixed=len(self.timestep_counts)>1
        for index, values in self.stages.items():
            row = {k:v for k,v in values.items() if k not in ('sum_squared_xyz','time_integral_squared_xyz')}
            mean_squared = (values['time_integral_squared_xyz']/values['duration_s'] if mixed
                            else values['sum_squared_xyz']/values['count'])
            row['position_rmse_xyz_m'] = np.sqrt(mean_squared).tolist()
            row['position_rmse_3d_m'] = float(np.sqrt(mean_squared.sum()))
            row['name'] = str(self.stage_names[index])
            by_stage[str(index)] = row
        squared = sum((r['time_integral_squared_xyz' if mixed else 'sum_squared_xyz'] for r in self.stages.values()), np.zeros(3))
        denominator=sum(r['duration_s'] for r in self.stages.values()) if mixed else max(1,self.count)
        return dict(samples=self.count, timestep_s=None if mixed else self.timestep_s,
                    timestep_sample_counts={str(dt):n for dt,n in self.timestep_counts.items()},
                    rmse_weighting='physical time integral' if mixed else 'uniform physical samples (equivalent to time integral)',
                    velocity_semantics='post-integration J(qpos)@qvel on scratch kinematics',
                    torque_semantics='live qfrc_actuator/actuator_force retained from completed mj_step dynamics evaluation',
                    timestamp_caveat='force evaluation may precede post-integration state within the same physical step',
                    raw_float_precision='time float64; stage int16; raw vectors float32; peak/sum accumulators float64',
                    linear_speed_peak_mps=self.speed_peak,
                    generalized_actuator_torque_peak_nm=float(self.qfrc_peak.max()),
                    generalized_actuator_torque_peak_by_joint_nm=self.qfrc_peak.tolist(),
                    actuator_force_peak_by_actuator=self.force_peak.tolist(),
                    position_rmse_xyz_m=np.sqrt(squared/denominator).tolist(),
                    position_rmse_3d_m=float(np.sqrt(squared.sum()/denominator)),
                    stages=by_stage)

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        summary = self.summary()
        (directory/'substep_metrics.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
        np.savez_compressed(directory/'substep_metrics.npz', **{k:v[:self.count] for k,v in self.arrays.items()})
        return summary


class Instrumentation(AbstractContextManager):
    def __init__(self):
        self.current = None
        self.episodes = []
        self._by_id = {}

    def __enter__(self):
        import audited_velocity_env
        self.env_class = audited_velocity_env.PandaWBCVelocityResidualEnv
        self.original_physics = self.env_class._physics_step
        self.original_step = mujoco.mj_step
        owner = self

        def physics(env, *args, **kwargs):
            if id(env) not in owner._by_id:
                metric = EpisodeMetrics(env)
                owner._by_id[id(env)] = metric
                owner.episodes.append(metric)
            previous = owner.current
            owner.current = owner._by_id[id(env)]
            try:
                return owner.original_physics(env, *args, **kwargs)
            finally:
                owner.current = previous

        def step(model, data, *args, **kwargs):
            result = owner.original_step(model, data, *args, **kwargs)
            metric = owner.current
            if metric is not None and data is metric.env.data:
                if args or kwargs.get('nstep',1) != 1:
                    raise ValueError('Instrumentation requires one physical step per mj_step call')
                metric.sample()
            return result

        self.env_class._physics_step = physics
        mujoco.mj_step = step
        return self

    def __exit__(self, *args):
        self.env_class._physics_step = self.original_physics
        mujoco.mj_step = self.original_step
        return False
