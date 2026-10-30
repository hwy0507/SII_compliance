from pathlib import Path
import json,time,hashlib,os,importlib.util,sys
os.sched_setaffinity(0,{7})
import numpy as np
import mujoco
O=Path(__file__).parent;B=O.parents[1];RT=B/'runtime/source_train17_clock'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
plan=read(O/'PLAN.json')
for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
sys.path[:0]=[str(RT/'parameter'),str(RT/'source/tools'),str(RT/'source/scripts')]
from controllers import ParameterShield
helper=B/'runs/parameter_cycle_audit_v1/audit_published_parameter_cycle_20261025.py';spec=importlib.util.spec_from_file_location('original_parameter_audit',helper);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);prior=read(RT/'parameter/PRIORS.json')['methods']['impedance']
results={};arrays={}
for c in [78,79]:
 folder=Path(plan['inputs'][f'{c}:rollout.json']['path']).parent;rollout=read(folder/'rollout.json');terminal=read(folder/'TERMINAL.json');shield=mod.episode(folder,'impedance',prior,ParameterShield)
 with np.load(folder/'rollout.npz',allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
 assert len(a['time'])==(675 if c==79 else 1375);assert np.isfinite(a['qpos']).all() and np.isfinite(a['qvel']).all();assert np.max(abs(np.diff(a['time'])-.04))<1e-8
 m=mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'));d=mujoco.MjData(m);assert m.opt.timestep==5e-5
 maxima=[];pairs=[];target=[];dpos=[]
 tg=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom');tb=int(m.geom_bodyid[tg]);names=lambda g:mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g))
 for i in range(675):
  mujoco.mj_resetData(m,d);d.time=float(a['time'][i]);d.qpos[:]=a['qpos'][i];d.qvel[:]=a['qvel'][i];d.ctrl[:]=a['ctrl'][i];d.mocap_pos[:]=a['mocap_pos'][i];d.mocap_quat[:]=a['mocap_quat'][i];mujoco.mj_forward(m,d)
  contacts=[(max(0.,-float(x.dist)),int(x.geom1),int(x.geom2)) for x in d.contact if m.geom_bodyid[x.geom1]!=m.geom_bodyid[x.geom2]]
  q=max(contacts,default=(0.,-1,-1));maxima.append(q[0]);pairs.append([names(q[1]),names(q[2])] if q[1]>=0 else [])
  target.append(max([v for v,g1,g2 in contacts if tg in [g1,g2]],default=0.));dpos.append(float(np.linalg.norm(d.xpos[tb]-a['object_position'][i])))
 values=np.array(maxima);index=int(values.argmax());arrays[str(c)+'_time']=a['time'][:675];arrays[str(c)+'_penetration']=values;arrays[str(c)+'_object']=a['object_position'][:675];arrays[str(c)+'_max_abs_qvel']=np.max(abs(a['qvel'][:675]),axis=1)
 results[str(c)]=dict(original_frames=len(a['time']),geometry_frames=675,maximum_saved_frame_global_penetration_m=float(values.max()),maximum_saved_frame_pair=pairs[index],maximum_saved_frame_time=float(a['time'][index]),saved_frames_above2mm=int((values>.002).sum()),last_frame_global_penetration_m=float(values[-1]),last_frame_pair=pairs[-1],maximum_saved_frame_target_penetration_m=max(target),stored_full_substep_max_penetration_m=rollout['stats']['max_penetration_m'],stored_full_substep_worst_pair=rollout['stats']['worst_pair'],maximum_body_position_reconstruction_difference_m=max(dpos),last_saved_object_position=a['object_position'][674].tolist(),last_saved_max_abs_qvel=float(np.max(abs(a['qvel'][674]))),task=rollout['task_success'],strict=rollout['strict_success'],abort_reason=rollout['abort_reason'],terminal_time_s=terminal['terminal_time_s'],shield=shield)
assert results['79']['abort_reason']=='global_penetration_exceeded_2mm' and not results['79']['task'] and not results['79']['strict'];assert results['78']['task'] and results['78']['strict'];assert plan['inputs']['78:rollout.mjb']['sha256']==plan['inputs']['79:rollout.mjb']['sha256']
assert plan['inputs']['78:executed_evaluator.py.txt']['sha256']==plan['inputs']['79:executed_evaluator.py.txt']['sha256']
np.savez_compressed(O/'geometry_values.npz',**arrays)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(3,1,figsize=(9,9),constrained_layout=True)
for c in ['78','79']:
 t=arrays[c+'_time'];axes[0].plot(t,1000*arrays[c+'_penetration'],label=c);axes[1].plot(t,arrays[c+'_object'][:,2],label=c);axes[2].plot(t,arrays[c+'_max_abs_qvel'],label=c)
axes[0].axhline(2,color='red',ls='--',label='2mm original stop threshold');axes[0].set_ylabel('Saved-frame geometry penetration (mm)');axes[1].set_ylabel('Saved object z (m)');axes[2].set_ylabel('Max abs generalized velocity');axes[2].set_xlabel('Time (s); first27s of each saved rollout')
for ax in axes:ax.legend();ax.grid(alpha=.2)
fig.suptitle('Impedance active_long_train_0000: retained78 vs aborted79\n25Hz saved geometry; not the full-substep97.689mm statistic')
fig.savefig(O/'abort_geometry.png',dpi=130)
for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
report=dict(passed=True,time=time.time(),cycles=results,model_and_executed_evaluator_exactly_same=True,mujoco_version=mujoco.__version__,geometry_forward_calls=1350,new_mj_steps=0,new_optimizer_updates=0,plot_sha256=sha(O/'abort_geometry.png'),values_sha256=sha(O/'geometry_values.npz'),source_sha256=sha(Path(__file__)),original_parameter_audit_sha256=sha(helper),scope=plan['scope'],causal_claim=False,physics_pass_claim=False,convergence_claim=False)
(O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({c:{k:v for k,v in row.items() if k!='shield'} for c,row in results.items()},indent=2))
