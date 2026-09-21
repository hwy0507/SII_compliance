"""Observe post-grasp release at physics rate; no audit truth enters policy."""
import json
from pathlib import Path
import runpy
import sys
import mujoco
import numpy as np
import audited_velocity_env as env_module


class ReleaseAuditEnv(env_module.PandaWBCVelocityResidualEnv):
    instances=[]
    def __init__(self,*args,**kwargs):
        self.release_audit=dict(last_contact_s=None,postgrasp_contact_s=0.,
            postgrasp_peak_point_force_n=0.,postgrasp_max_penetration_m=0.,bodies=set())
        self.rod_trace=[]
        self.geometry_trace=[]
        super().__init__(*args,**kwargs)
        self.instances.append(self)

    @property
    def substep_observer(self):return getattr(self,'_release_observer',None)

    @substep_observer.setter
    def substep_observer(self,callback):
        if callback is None:self._release_observer=None;return
        def observe(time_s):
            callback(time_s)
            m,d=self.model,self.data
            if not hasattr(self,'reference')or getattr(self.reference,'index',0)<3:return
            touching=False
            for i in range(d.ncon):
                c=d.contact[i];pair=(int(c.geom1),int(c.geom2))
                if self._push_rod_geom_id not in pair:continue
                other=pair[1]if pair[0]==self._push_rod_geom_id else pair[0]
                if other not in self._push_audit_robot_geom_ids and int(m.geom_bodyid[other])!=self._target_body_id:continue
                f=np.zeros(6);mujoco.mj_contactForce(m,d,i,f)
                mag=float(np.linalg.norm(f[:3]))
                self.release_audit['postgrasp_peak_point_force_n']=max(self.release_audit['postgrasp_peak_point_force_n'],mag)
                self.release_audit['postgrasp_max_penetration_m']=max(self.release_audit['postgrasp_max_penetration_m'],-float(c.dist))
                if mag>.05:
                    touching=True
                    self.release_audit['bodies'].add(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[other])))
            if touching:
                self.release_audit['last_contact_s']=float(d.time)
                self.release_audit['postgrasp_contact_s']+=m.opt.timestep
        self._release_observer=observe

    def step(self,action):
        value=super().step(action)
        self.rod_trace.append([float(self.data.time),float(self.data.qpos[self._push_rod_qpos]),float(self.data.ctrl[self._push_rod_ctrl])])
        if getattr(self.reference,'index',0)>=3:
            m,d=self.model,self.data;rod=self._push_rod_geom_id
            ids=[g for g in range(m.ngeom)if (g in self._push_audit_robot_geom_ids or int(m.geom_bodyid[g])==self._target_body_id)
                 and ((int(m.geom_contype[g])&int(m.geom_conaffinity[rod])) or (int(m.geom_contype[rod])&int(m.geom_conaffinity[g])))]
            legacy=min(float(mujoco.mj_geomDistance(m,d,rod,g,.2,None))for g in ids)
            flags=int(m.opt.disableflags)
            try:
                m.opt.disableflags=flags&~int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
                native=min(float(mujoco.mj_geomDistance(m,d,rod,g,.2,None))for g in ids)
            finally:m.opt.disableflags=flags
            self.geometry_trace.append([float(d.time),legacy,native])
        return value

    def close(self):
        if self.model is not None:
            self._audit_model,self._audit_data=self.model,self.data
        super().close()


def main():
    output=Path(sys.argv[sys.argv.index('--output')+1])
    env_module.PandaWBCVelocityResidualEnv=ReleaseAuditEnv
    runpy.run_path(str(Path(__file__).with_name('run_core_vmc_push_20260918.py')),run_name='__main__')
    env=ReleaseAuditEnv.instances[-1];m,d=env._audit_model,env._audit_data
    target_geoms=[i for i in range(m.ngeom)if int(m.geom_bodyid[i])==env._target_body_id]
    checked=list(env._push_audit_robot_geom_ids)+target_geoms
    rod=env._push_rod_geom_id
    checked=[g for g in checked if (int(m.geom_contype[g])&int(m.geom_conaffinity[rod])) or (int(m.geom_contype[rod])&int(m.geom_conaffinity[g]))]
    gaps=[float(mujoco.mj_geomDistance(m,d,rod,g,.20,None))for g in checked]
    finger_bodies=set()
    for i in range(d.ncon):
        pair=(int(d.contact[i].geom1),int(d.contact[i].geom2))
        if any(g in target_geoms for g in pair):
            other=pair[1]if pair[0]in target_geoms else pair[0]
            name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[other]))
            if name in ('left_finger','right_finger'):finger_bodies.add(name)
    audit=env.release_audit.copy();audit['bodies']=sorted(audit['bodies'])
    audit.update(final_min_gap_m=min(gaps),finger_contacts=sorted(finger_bodies),
                 final_nearby_geometries=sorted([dict(geom=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g),
                    body=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[g])),gap_m=gap)
                    for g,gap in zip(checked,gaps)],key=lambda r:r['gap_m'])[:4],
                 bilateral_grasp=len(finger_bodies)==2,final_rod_qpos_m=float(d.qpos[env._push_rod_qpos]),
                 final_rod_command_m=float(d.ctrl[env._push_rod_ctrl]),
                 no_contact_final_two_seconds=audit['last_contact_s']is None or float(d.time)-audit['last_contact_s']>=2.)
    geometry=np.asarray(env.geometry_trace)
    if len(geometry):
        audit['loaded_geometry_min_gap_legacy_m']=float(geometry[:,1].min())
        audit['loaded_geometry_min_gap_native_m']=float(geometry[:,2].min())
    path=output.with_suffix('.json');result=json.loads(path.read_text());result['postgrasp_release']=audit
    path.write_text(json.dumps(result,indent=2))
    np.savez_compressed(output.with_name('rod_audit.npz'),rod_state=np.asarray(env.rod_trace))
    np.savez_compressed(output.with_name('geometry_audit.npz'),geometry=geometry)
    print(json.dumps(dict(postgrasp_release=audit)),flush=True)


if __name__=='__main__':main()
