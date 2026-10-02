"""Read-only native ball momentum probe; no physics/actor changes."""
import json
import mujoco
import numpy as np

class NativeBallProbe:
 def __init__(self,out):
  self.out=out;self.rows=[];self.poses=[];self.active=None;self.save=mujoco.mj_saveModel;self.step=mujoco.mj_step
 def install(self):
  mujoco.mj_saveModel=self.capture_model;mujoco.mj_step=self.capture_step
 def capture_model(self,m,*args,**kwargs):
  result=self.save(m,*args,**kwargs);j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'primitive_free_ball_joint')
  if j>=0:
   self.active=m;self.qadr=int(m.jnt_qposadr[j]);self.dadr=int(m.jnt_dofadr[j]);self.body=int(m.jnt_bodyid[j]);self.geoms={g for g in range(m.ngeom) if m.geom_bodyid[g]==self.body}
  return result
 def capture_step(self,m,d,*args,**kwargs):
  if m is not self.active:return self.step(m,d,*args,**kwargs)
  before=d.qvel[self.dadr:self.dadr+3].copy();result=self.step(m,d,*args,**kwargs);force=np.zeros(3);peak=0.;n=0;pen=0.
  for ci in range(d.ncon):
   c=d.contact[ci];g1,g2=int(c.geom1),int(c.geom2)
   if (g1 in self.geoms)==(g2 in self.geoms):continue
   f=np.zeros(6);mujoco.mj_contactForce(m,d,ci,f);force+=(c.frame.reshape(3,3).T@f[:3])*(1 if g2 in self.geoms else -1);peak=max(peak,float(np.linalg.norm(f[:3])));n+=int(np.linalg.norm(f[:3])>.05);pen=max(pen,-float(c.dist))
  self.rows.append(np.r_[d.time,m.opt.timestep,d.qpos[self.qadr:self.qadr+3],before,d.qvel[self.dadr:self.dadr+3],force,peak,n,pen,m.body_gravcomp[self.body]])
  if not self.poses or d.time-self.poses[-1][0]>=.001-1e-8:self.poses.append((float(d.time),d.qpos.copy(),d.qvel.copy(),d.ctrl.copy()))
  return result
 def close(self):
  mujoco.mj_step=self.step;mujoco.mj_saveModel=self.save
  if self.rows:
   np.savez_compressed(self.out/'ball_1khz_states.npz',time=np.array([v[0] for v in self.poses]),qpos=np.array([v[1] for v in self.poses]),qvel=np.array([v[2] for v in self.poses]),ctrl=np.array([v[3] for v in self.poses]))
   columns=['time','dt','ball_x','ball_y','ball_z','vx_before','vy_before','vz_before','vx_after','vy_after','vz_after','contact_fx','contact_fy','contact_fz','peak_pair_force_n','forceful_contacts','penetration_m','gravcomp']
   np.savez_compressed(self.out/'ball_native_substeps.npz',values=np.asarray(self.rows),columns=np.asarray(columns));(self.out/'BALL_PROBE.json').write_text(json.dumps(dict(native_substeps=len(self.rows),read_only=True,ball_body_id=self.body,all_ball_contacts=True),indent=2))
