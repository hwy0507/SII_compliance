"""Instrument accepted legacy corner without changing its actions or physics.

Proprioceptive observations are captured before each action. Observer updates
use encoder velocity, model terms and actuator torque only. Contact truth is
not an input. Normalized actions retain both native and canonical coordinates.
"""
import json
from pathlib import Path
import runpy
import sys
import numpy as np
import mujoco
import audited_velocity_env as module
from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
from run_benchmark import body_jacobian,body_twist


class CaptureEnv(module.PandaWBCVelocityResidualEnv):
    instances=[]
    def __init__(self,*a,**kw):
        self.capture=[];self.load_observer=None;self.mass_matrix=None
        super().__init__(*a,**kw);self.instances.append(self)

    @property
    def substep_observer(self):
        return self.capture_substep

    @substep_observer.setter
    def substep_observer(self,value):self.extra_observer=value

    def capture_substep(self,t):
        if self.extra_observer is not None:self.extra_observer(t)
        if self.load_observer is not None:
            m,d=self.model,self.data;mujoco.mj_fullM(m,d,self.mass_matrix)
            self.load_observer.update(d.qvel.copy(),self.mass_matrix,d.qfrc_bias.copy(),
                                     d.qfrc_passive.copy(),d.qfrc_actuator.copy(),m.opt.timestep)

    def diagnostics(self):
        value=super().diagnostics();self._source_diagnostics=value;return value

    def step(self,action):
        m,d=self.model,self.data
        if self.load_observer is None:
            self.load_observer=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss)
            self.mass_matrix=np.zeros((m.nv,m.nv))
        diag=self._source_diagnostics;J=body_jacobian(m,d,self._hand_id)
        wrench=equivalent_tool_wrench(J,self.load_observer.filtered)
        nominal=np.asarray(diag['nominal_twist'])
        direction=nominal[:3].copy()
        if np.linalg.norm(direction)<1e-8:direction=np.asarray(diag['wbc_pose_error'])[:3].copy()
        direction/=max(np.linalg.norm(direction),1e-9)
        obs=np.r_[d.qpos[:7],d.qvel[:7],nominal,diag['wbc_pose_error'],diag['wbc_twist_error'],
                  self.load_observer.filtered,wrench[:3],direction]
        native=np.asarray(action,dtype=float).copy();canonical=native.copy()
        canonical[0]=native[0]*(1-self.safety_config.minimum_wbc_scale)/.8
        canonical[1:4]*=self.safety_config.maximum_linear_yield_mps/.32
        canonical[4:7]*=self.safety_config.maximum_angular_yield_radps/.6
        limits=np.array([self.safety_config.minimum_wbc_scale,self.safety_config.maximum_linear_yield_mps,
                         self.safety_config.maximum_angular_yield_radps])
        # Inverse adapter must preserve the exact command for later replay.
        back=canonical.copy();back[0]*=.8/(1-limits[0]);back[1:4]*=.32/limits[1];back[4:7]*=.6/limits[2]
        np.testing.assert_allclose(back,native,atol=1e-12,rtol=0)
        row=dict(time=float(d.time),observation=obs,teacher_action=canonical,native_action=native,
                 native_limits=limits,jacobian=J.copy(),target=np.asarray(diag['nominal_position']).copy())
        output=super().step(action)
        row.update(position=d.xpos[self._hand_id].copy(),torque=d.qfrc_actuator[:7].copy(),
                   object_position=d.xpos[self._target_body_id].copy(),twist=body_twist(m,d,self._hand_id))
        self.capture.append(row)
        return output


def main():
    output=Path(sys.argv[sys.argv.index('--output')+1]).with_suffix('.canonical.npz')
    module.PandaWBCVelocityResidualEnv=CaptureEnv
    runpy.run_path(str(Path(__file__).with_name('render_compliance_audited.py')),run_name='__main__')
    rows=CaptureEnv.instances[-1].capture
    if not rows:raise RuntimeError('No captured teacher samples')
    np.savez_compressed(output,**{k:np.asarray([r[k]for r in rows])for k in rows[0]})


if __name__=='__main__':main()
