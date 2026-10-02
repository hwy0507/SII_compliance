"""Read-only native-substep ball probe around the immutable campaign worker."""
import importlib.util,json,sys,traceback
from pathlib import Path
import mujoco
import numpy as np
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
spec=importlib.util.spec_from_file_location('frozen_baseline_worker',ROOT/'frozen_adapter01/primitive_baselines_20261002/worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
original_save=mujoco.mj_saveModel;original_step=mujoco.mj_step
active=None;rows=[];poses=[];qadr=None;dadr=None;ballbody=None;ballgeoms=set()
def save(model,*args,**kwargs):
 global active,qadr,dadr,ballbody,ballgeoms
 result=original_save(model,*args,**kwargs)
 j=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,'primitive_free_ball_joint')
 if j>=0:
  active=model;qadr=int(model.jnt_qposadr[j]);dadr=int(model.jnt_dofadr[j]);ballbody=int(model.jnt_bodyid[j]);ballgeoms={g for g in range(model.ngeom) if model.geom_bodyid[g]==ballbody}
 return result

def step(model,data,*args,**kwargs):
 if model is not active:return original_step(model,data,*args,**kwargs)
 before=data.qvel[dadr:dadr+3].copy()
 result=original_step(model,data,*args,**kwargs)
 force=np.zeros(3);peak=0.;n=0;pen=0.
 for ci in range(data.ncon):
  c=data.contact[ci];g1,g2=int(c.geom1),int(c.geom2)
  if (g1 in ballgeoms)==(g2 in ballgeoms):continue
  f=np.zeros(6);mujoco.mj_contactForce(model,data,ci,f)
  force+=(c.frame.reshape(3,3).T@f[:3])*(1 if g2 in ballgeoms else -1)
  peak=max(peak,float(np.linalg.norm(f[:3])));n+=int(np.linalg.norm(f[:3])>.05);pen=max(pen,-float(c.dist))
 rows.append(np.r_[data.time,model.opt.timestep,data.qpos[qadr:qadr+3],before,data.qvel[dadr:dadr+3],force,peak,n,pen,model.body_gravcomp[ballbody]])
 if not poses or data.time-poses[-1][0]>=.001-1e-8:poses.append((float(data.time),data.qpos.copy(),data.qvel.copy(),data.ctrl.copy()))
 return result

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--request',type=Path,required=True);a=p.parse_args();request=json.loads(a.request.read_text())
 mujoco.mj_saveModel=save;mujoco.mj_step=step
 try:worker.execute(request,sys.stdout)
 except BaseException:
  error=traceback.format_exc();out=Path(request['output']);out.mkdir(parents=True,exist_ok=True);(out/'ERROR.txt').write_text(error);print(json.dumps(dict(kind='error',error=error)),flush=True);raise
 finally:
  mujoco.mj_step=original_step;mujoco.mj_saveModel=original_save
  if rows:
   out=Path(request['output']);columns=['time','dt','ball_x','ball_y','ball_z','vx_before','vy_before','vz_before','vx_after','vy_after','vz_after','contact_fx','contact_fy','contact_fz','peak_pair_force_n','forceful_contacts','penetration_m','gravcomp']
   np.savez_compressed(out/'ball_native_substeps.npz',values=np.asarray(rows),columns=np.asarray(columns))
   np.savez_compressed(out/'ball_1khz_states.npz',time=np.array([v[0] for v in poses]),qpos=np.array([v[1] for v in poses]),qvel=np.array([v[2] for v in poses]),ctrl=np.array([v[3] for v in poses]))
   (out/'BALL_PROBE.json').write_text(json.dumps(dict(native_substeps=len(rows),read_only=True,ball_body_id=ballbody,ball_geom_ids=sorted(ballgeoms),all_ball_contacts=True,physics_or_policy_modified=False,force_time='completed MuJoCo substep force, corresponding to preintegration contact configuration'),indent=2))
if __name__=='__main__':main()
