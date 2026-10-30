"""Audit the first2 registered conditions from each method after availability, without new physics."""
from pathlib import Path
import json,time,hashlib,math,os,sys
import numpy as np
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runs/parameter82_frozen_full30_20261030_v1';P=B/'runs/parameter55_frozen_full30_20261028_v1';os.sched_setaffinity(0,{3})
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');assert sha(Path(__file__))==plan['source']['sha256'];cases=plan['case_ids'];assert cases==read(O/'PLAN.json')['case_ids'][:2]
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus
results={};inputs={}
for m in ['impedance','admittance','vmc']:
 reg=read(O/m/'REGISTRATION.json');prior=read(P/m/'REGISTRATION.json');assert reg['action_seed']==prior['action_seed']==2026102638 and reg['case_ids']==prior['case_ids']
 rows=[]
 for case in cases:
  p=O/m/f'{case}_REVIEW.json';r=read(p);a=read(P/m/f'{case}_REVIEW.json');folder=O/m/case
  assert r['passed'] and a['passed'] and r['condition']==a['condition']==case and r['full_learner_state_unchanged'] and r['new_optimizer_updates']==0 and r['native_stochastic_parameter_action_max_error']<=1e-7
  hashed={}
  for kind in ['physical','filter','torque']:
   if kind!='physical':assert r[kind]['passed']
   for n,h in r[kind]['evidence_sha256'].items():
    if n not in hashed:hashed[n]=sha(folder/n)
    assert hashed[n]==h
  raw=np.load(folder/'audit_substeps.npy',mmap_mode='r',allow_pickle=False);count=r['physical']['samples'];raw=raw[:count];assert raw.shape==(count,11) and np.isfinite(raw).all() and (raw[:,0]==.00005).all()
  lim=read(folder/'AUDIT_EXTENSION.json')['actuator_limits_nm'];threshold=[x/2 for x in lim];mask=raw[:,8]>.05;compliant=np.ones(count,dtype=bool);peaks=[]
  for j,th in enumerate(threshold):
   v=abs(raw[:,j+1]);compliant &= v<=th;peaks.append(float(max(v)))
  contact=int(np.count_nonzero(mask))*.00005;below=int(np.count_nonzero(mask & compliant))*.00005;elapsed=count*.00005;row=r['physical']['row'];assert np.allclose(peaks,row['peak_torque_nm_per_joint'],rtol=0,atol=1e-12)
  assert abs(contact-row['human_contact_s'])<1e-8 and abs(below-row['human_below_threshold_s'])<1e-8 and abs(elapsed-row['elapsed_s'])<1e-8
  ratio=below/contact if contact else None;assert ratio==row['human_compliance_ratio'] if ratio is None else math.isclose(ratio,row['human_compliance_ratio'],abs_tol=1e-12)
  assert math.isclose(float(max(raw[:,9]))*1000,r['external_penetration_mm'],abs_tol=1e-10)
  terminal=read(folder/'TERMINAL.json');rollout=read(folder/'rollout.json');journal=[json.loads(l) for l in (folder/'actor_intervals.jsonl').read_text().splitlines()];assert len(journal)==r['actions']<=1375
  vals=[];reward_fn=SPTReward()
  for i,x in enumerate(journal):
   done=i+1==len(journal);nxt=terminal if done else journal[i+1]
   v,_=reward_fn(current_potential=x['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=done,task_success=rollout['task_success'] if done else False,strict_success=rollout['strict_success'] if done else False)
   if done and rollout['strict_success']:v+=completion_bonus(task_success=True,strict_success=True,completion_time_s=terminal['completion_time_s'])
   vals.append(v)
  reward=math.fsum(vals);assert math.isclose(reward,r['reward'],abs_tol=1e-10)
  safety=bool(not rollout['physical_valid'] or rollout['abort_reason'] is not None or any(x>l+1e-8 for x,l in zip(peaks,lim)) or not rollout.get('unexpected_edge_safe',True));assert safety==row['machine_safety_violation']
  assert row['task_success']==rollout['task_success'] and row['strict_success']==rollout['strict_success']
  rows.append(dict(condition=case,actions=r['actions'],physical_samples=count,task=row['task_success'],strict=row['strict_success'],machine_violation=safety,stage=row['final_task_stage'],reward=r['reward'],prior55_reward=a['reward'],reward_delta=r['reward']-a['reward'],prior55_task=a['physical']['row']['task_success'],prior55_strict=a['physical']['row']['strict_success'],human_contact_s=contact,human_compliant_s=below,human_compliance_ratio=ratio,peak_torque_nm_per_joint=peaks,external_penetration_mm=r['external_penetration_mm'],reward_reconstruction_abs_error=abs(reward-r['reward']),full_horizon=row['full_horizon'],abort=row['abort_reason'],evidence_files=len(hashed)))
  inputs[m+':'+case]=dict(current=ref(p),prior55=ref(P/m/f'{case}_REVIEW.json'),raw=ref(folder/'audit_substeps.npy'))
 results[m]=rows
put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,inputs=inputs,total_cases=6,total_substeps=sum(x['physical_samples'] for v in results.values() for x in v),new_physics=0,optimizer_updates=0,new_network_forward=0,convergence_claim=False,limitation='Post-availability first2 registered passive conditions per method; not full30 outcome or success-rate estimate. Exact raw hashes, count-times-dt physical metrics, frozen reward formula with scalar fsum, unchanged saved action/filter/torque receipts; no rerun native action replay or independent physics. Same-seed55 comparison descriptive only. Per-episode state proof does not replace final whole-evaluation learner/replay invariance.'))
saved=read(D/'REVIEW.json');assert saved['methods']==results
put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),all_rows_read_back=True,total_cases=6,total_substeps=saved['total_substeps'],source=ref(Path(__file__)),review=ref(D/'REVIEW.json')))
print(json.dumps(results,indent=2))
