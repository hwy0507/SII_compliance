"""Physical initial arm-state randomization before the first observation."""
import json
import os
from pathlib import Path
import runpy
import sys
import numpy as np
import mujoco
import audited_velocity_env as base


class InitialStateEnv(base.PandaWBCVelocityResidualEnv):
    states=[]
    @property
    def fixed_wbc(self):return getattr(self,'_dataset_wbc',None)
    @fixed_wbc.setter
    def fixed_wbc(self,value):
        self._dataset_wbc=value
        if value is None or type(value).__name__!='ScaledReferenceWBC' or getattr(self,'_dataset_applied',False):return
        self._dataset_applied=True
        delta=np.asarray(json.loads(os.environ.get('DATASET_INITIAL_QDELTA','[0,0,0,0,0,0,0]')))
        if delta.shape!=(7,)or not np.isfinite(delta).all():raise ValueError('Invalid initial state')
        if np.any(delta):
            q=self.data.qpos[:7]+delta
            if np.any(q<self.model.jnt_range[:7,0])or np.any(q>self.model.jnt_range[:7,1]):raise ValueError('Initial joint limit')
            self.data.qpos[:7]=q;mujoco.mj_forward(self.model,self.data)
            robot=self._push_audit_robot_geom_ids
            for c in self.data.contact[:self.data.ncon]:
                if (int(c.geom1)in robot or int(c.geom2)in robot)and c.dist<-.00001:
                    raise ValueError('Randomized initial state overlaps an obstacle or robot body')
            self.previous_torque=self.data.qfrc_bias[:7].copy()
        self.states.append(self.data.qpos[:7].copy())


def main():
    i=sys.argv.index('--entry');entry=sys.argv[i+1];del sys.argv[i:i+2]
    if entry not in ('run_loaded_push_audit_20260918.py','run_primitive_teacher_v7_20260917.py','run_primitive_teacher_v6_20260917.py'):raise ValueError(entry)
    output=Path(sys.argv[sys.argv.index('--output')+1]).with_suffix('.json')
    base.PandaWBCVelocityResidualEnv=InitialStateEnv
    runpy.run_path(str(Path(__file__).with_name(entry)),run_name='__main__')
    d=json.loads(output.read_text());d['dataset_initial_arm_qpos']=InitialStateEnv.states[-1].tolist()
    output.write_text(json.dumps(d,indent=2))


if __name__=='__main__':main()
