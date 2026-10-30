"""Prospective teacher-only bounded horizontal cross-track reference feedback.

Uses canonical48 reference error/path direction and estimated wrench only.
Adds no geometry, phase, clock, success flag or test input. The original force
response and z recovery remain; a smooth load gate suppresses the new return
velocity during opposing lateral contact. This active teacher has no claimed
passivity/stability guarantee and must pass registered physical development
checks before collecting training labels. Never used as a deployed student.
"""
import numpy as np
from optimize_tool_contact_20261002 import ParameterTeacher

VERSION='bounded_cross_track_recovery_v1'


class CrossTrackRecoveryTeacher(ParameterTeacher):
    def __init__(self,config):
        c=config.get('cross_track_recovery')
        required={'version','gain_per_s','maximum_speed_mps','load_scale_n'}
        if not isinstance(c,dict) or set(c)!=required or c['version']!=VERSION:
            raise ValueError('Explicit complete cross-track teacher configuration required')
        if not all(np.isfinite(c[k]) and c[k]>0 for k in required-{'version'}):
            raise ValueError('Finite positive feedback constants required')
        if c['maximum_speed_mps']>.02 or c['gain_per_s']>2 or c['load_scale_n']>2:
            raise ValueError('Prospective bounded development envelope exceeded')
        if config.get('teacher_mechanism') is not None:
            raise ValueError('This version extends the original ParameterTeacher only')
        self.cross_track=dict(c)
        super().__init__(config)
        self.last_cross_track_velocity=np.zeros(2)
        self.last_cross_track_load_gate=0.

    def reset(self):
        super().reset()
        self.last_cross_track_velocity=np.zeros(2)
        self.last_cross_track_load_gate=0.

    def act(self,wrench_world,dt=.04):
        if dt!=.04:raise ValueError('Frozen actor clock required')
        wrench=np.asarray(wrench_world,dtype=float)
        if wrench.shape!=(6,) or not np.isfinite(wrench).all():raise ValueError('Finite wrench6 required')
        action=super().act(wrench.copy(),dt)
        obs=self.observation;c=self.cross_track
        path=obs[45:47];norm=float(np.linalg.norm(path))
        if norm<=1e-12:
            self.last_cross_track_velocity=np.zeros(2);self.last_cross_track_load_gate=0.
            return action
        direction=path/norm
        projection=np.eye(2)-np.outer(direction,direction)
        error=projection@obs[20:22]
        force=projection@wrench[:2]
        gate=1./(1.+float(force@force)/c['load_scale_n']**2)
        velocity=c['gain_per_s']*error
        velocity*=min(1.,c['maximum_speed_mps']/max(float(np.linalg.norm(velocity)),1e-12))
        velocity*=gate*min(1.,norm)**2
        self.last_cross_track_velocity=velocity.copy();self.last_cross_track_load_gate=gate
        action[1:3]=np.clip(action[1:3]+velocity/.32,-1.,1.)
        return action
