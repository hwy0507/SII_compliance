"""Read-only causal necessary-gate audit; never equate upper bound with true dwell."""
from pathlib import Path
import os,time,json,hashlib,traceback,sys
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
import mujoco
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_placement_audit_20261031_v1';S=B/'runtime/source_train17_clock/source'
sys.path.insert(0,str(S/'tools'))
from payload_reward_potential_20261014 import payload_potential
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,r):
 with Path(p).open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
def ref(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def run():
 start=time.monotonic();plan=rd(O/'PLAN.json');sources=rd(O/'SOURCE_LOCK.json');assert all(sha(Path(p))==h for p,h in sources.items());os.sched_setaffinity(0,{10})
 results=[];manifest=[]
 for ei,e in enumerate(plan['selected']):
  assert time.monotonic()-start<plan['budget']['wall_seconds'];p=Path(e['episode']);r=rd(p/'rollout.json');term=rd(p/'TERMINAL.json');ad=rd(p/'ADAPTER.json');model=mujoco.MjModel.from_binary_path(str(p/'rollout.mjb'))
  assert sha(p/'rollout.mjb')==r['model_sha256'];assert ad['arguments']['planned_hand_corner'];assert model.opt.timestep==5e-5
  with np.load(p/'rollout.npz',allow_pickle=False) as z:a={k:z[k] for k in ['time','neuron_time','qpos','neuron_qpos','qvel','object_position','hand','observation']};keys=list(z.files)
  n=len(a['time']);assert n<=1375;assert all(len(v)==n for v in a.values());assert all(np.isfinite(v).all() for v in a.values())
  np.testing.assert_array_equal(a['qpos'][:-1],a['neuron_qpos'][1:]);np.testing.assert_array_equal(a['time'][:-1],a['neuron_time'][1:]);np.testing.assert_allclose(a['time']-a['neuron_time'],.04,rtol=0,atol=2e-10)
  gid=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom');assert gid>=0;body=int(model.geom_bodyid[gid]);joint=int(model.body_jntadr[body]);qa=int(model.jnt_qposadr[joint]);va=int(model.jnt_dofadr[joint]);fingers=[int(model.joint(k).qposadr[0]) for k in ['finger_joint1','finger_joint2']]
  dest=np.asarray(r['placement_destination']);pos=a['object_position'];linear=np.linalg.norm(a['qvel'][:,va:va+3],axis=1);angular=np.linalg.norm(a['qvel'][:,va+3:va+6],axis=1);opening=a['qpos'][:,fingers].sum(1);xy=np.linalg.norm(pos[:,:2]-dest[:2],axis=1);height=abs(pos[:,2]-dest[2]);values=np.column_stack([xy,linear,opening,height,angular]);gates=np.column_stack([xy<.025,linear<.015,opening>.075,height<.015,angular<.15]);eligible=gates.all(1);counts=np.empty(n,np.int64);count=0
  for i,ok in enumerate(eligible):count=count+1 if ok else 0;counts[i]=count
  bound=counts*.04;pre=np.r_[0.,bound[:-1]];hold=float(r['placement_hold_s']);assert hold==term['placement_hold_s'];assert hold<=bound[-1]+1e-10
  np.testing.assert_allclose(max(0.,float((pos[:,2]-.425).max())),r['max_lift_m'],rtol=0,atol=1e-12)
  # Initial physical state is not synthesized: the first action's history is explicitly initialized at zero.
  journal=[json.loads(l) for l in (p/'actor_intervals.jsonl').read_text().splitlines()];assert len(journal)==n and journal[0]['interval'] is None
  np.testing.assert_array_equal(np.asarray([j['observation'] for j in journal]),a['observation'])
  potential=np.array([payload_potential(h,x,dest) for h,x in zip(a['hand'],pos)])
  np.testing.assert_array_equal(potential[:-1],np.array([j['payload_potential'] for j in journal[1:]]));np.testing.assert_array_equal(potential[:-1],np.array([j['interval']['payload_potential'] for j in journal[1:]]));assert potential[-1]==term['payload_potential']
  pos_phase_error=np.max(abs(pos-a['qpos'][:,qa:qa+3]),axis=1);inverse_error=np.max(abs(pos-(a['qpos'][:,qa:qa+3]-model.opt.timestep*a['qvel'][:,va:va+3])),axis=1)
  out=O/f'episode_{ei:03d}.npz';np.savez_compressed(out,time=a['time'],preaction_time=a['neuron_time'],necessary_values=values,necessary_gates=gates,post_upper_s=bound,pre_upper_s=pre,post_potential=potential,post_qpos_position_error=pos_phase_error,inverse_translation_error=inverse_error)
  last_fail=np.flatnonzero(~eligible);lf=int(last_fail[-1]) if len(last_fail) else None
  row=dict(**e,rows=n,task=bool(r['task_success']),strict=bool(r['strict_success']),abort=r['abort_reason'],full_horizon=r['full_task_horizon_completed'],actual_final_hold_s=hold,post_final_upper_s=float(bound[-1]),pre_final_upper_s=float(pre[-1]),final_upper_equals_hold=bool(abs(hold-bound[-1])<1e-10),last_necessary_failure_index=lf,last_necessary_failure_time_s=None if lf is None else float(a['time'][lf]),last_necessary_failed_gates=[] if lf is None else [k for k,x in zip(['xy','linear_speed','finger_opening','height','angular_speed'],gates[lf]) if not x],final_values=values[-1].tolist(),preaction_final_values=None if n<2 else values[-2].tolist(),integrator=int(model.opt.integrator),max_post_qpos_position_error=float(pos_phase_error.max()),max_inverse_translation_error=float(inverse_error.max()),zero_bound_rows=int((counts==0).sum()),raw_keys=keys,explicit_hold_in_raw=any('hold' in k or 'placement' in k for k in keys),explicit_hold_in_journal=any('hold' in k or 'placement' in k for j in journal for k in j),saved=ref(out),exact_observation_time_qpos_and_potential_alignment=True)
  results.append(row)
  for name in ['rollout.npz','rollout.json','rollout.mjb','actor_intervals.jsonl','TERMINAL.json','ADAPTER.json','executed_evaluator.py.txt']:manifest.append(ref(p/name))
  print(json.dumps(dict(episode=ei,method=e['method'],cycle=e['cycle'],condition=p.name,hold=hold,upper=bound[-1],pre=pre[-1],last_fail=row['last_necessary_failed_gates'])),flush=True)
 # Availability inventory uses the exact earlier validated replay episode list, including interrupted prefixes.
 inv=[];inventory_summary={}
 for m in ['impedance','admittance','vmc']:
  ep=B/'runs/recovery85_history_reconstruction_20261030_v1'/(m+'_episodes.jsonl');prev=rd(ep.with_name(m+'_REVIEW.json'));assert sha(ep)==prev['episode_review']['sha256'];manifest.append(ref(ep));rows=[json.loads(l) for l in ep.read_text().splitlines()];assert len(rows)<plan['budget']['history85_inventory_max'];counts={k:0 for k in ['rollout.npz','rollout.mjb','rollout.json','actor_intervals.jsonl','TERMINAL.json','executed_evaluator.py.txt']};retained=0;missing=[]
  for row in rows:
   path=Path(row['journal']['path']).parent;exists={k:(path/k).is_file() for k in counts};retained+=row['retained_transitions']
   for k,v in exists.items():counts[k]+=v
   item=dict(method=m,episode=str(path),retained_transitions=row['retained_transitions'],terminal_retained=row['terminal_retained'],exists=exists);inv.append(item)
   if not all(exists.values()):missing.append(item)
  assert retained==prev['retained_rows'];inventory_summary[m]=dict(episode_cohorts=len(rows),retained_rows=retained,files_present=counts,missing_cases=missing,scope='Existence only for original complete85 retained cohorts; no all-file contents or new full93 replay equality claim')
 with (O/'HISTORY85_INVENTORY.jsonl').open('x') as f:
  for row in inv:f.write(json.dumps(row)+'\n')
 put(O/'SOURCE_MANIFEST.json',dict(files=manifest))
 summary={}
 for m in ['impedance','admittance','vmc']:
  group=[x for x in results if x['method']==m and x['selection']=='all_complete93'];assert len(group)==30;summary[m]=dict(episodes=30,rows=sum(x['rows'] for x in group),task=sum(x['task'] for x in group),strict=sum(x['strict'] for x in group),final_bound_exact_count=sum(x['final_upper_equals_hold'] for x in group),failed_task_with_final_bound_below_gate=sum(not x['task'] and x['post_final_upper_s']<.5 for x in group),failed_task_with_preaction_bound_plus_one_period_below_gate=sum(not x['task'] and x['pre_final_upper_s']+.04<.5 for x in group))
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,episodes=results,complete93=summary,history85_inventory=inventory_summary,new_physics=0,optimizer_updates=0,checkpoint_loads=0,replay_writes=0,conclusion='Saved necessary gates give causal upper bounds, not exact force-supported dwell. Exact phase and potential/observation binding checked; contact force state remains unrecorded. Missing historical raw, if any, blocks universal raw-derived feature migration. No convergence or feature deployment claim.'))
 for item in manifest:assert sha(item['path'])==item['sha256']
 put(O/'FINISHED.json',dict(passed=True,time=time.time(),source_hashes_verified=True,all_input_files_unchanged=True,episodes=len(results),elapsed_s=time.monotonic()-start))
if __name__=='__main__':
 try:run()
 except BaseException:
  put(O/'FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
