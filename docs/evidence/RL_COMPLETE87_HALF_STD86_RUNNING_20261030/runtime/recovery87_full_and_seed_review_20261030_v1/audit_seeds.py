from pathlib import Path
import json,time,hashlib,math,os,sys
import numpy as np
D=Path(__file__).parent;B=D.parents[1];S=B/'runs/parameter86_frozen_switches_20261030_v1';os.sched_setaffinity(0,{12})
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
assert read(S/'FINISHED.json')['passed'] and read(S/'REVIEW.json')['total_episodes']==16
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus
plan=read(S/'PLAN.json');report=read(S/'REVIEW.json');rows=[];inputs={}
for group,reg in plan['groups'].items():
 d=S/group;fin=read(d/'FINISHED.json');assert fin['passed'] and fin['episodes']==4 and fin['full_learner_state_unchanged'] and fin['full_replay_state_unchanged'] and fin['initial_learner_digest']==fin['final_learner_digest']
 for seed,original in zip(plan['action_seeds'],report['groups'][group]['rows']):
  folder=d/f'seed_{seed}';p=d/f'seed_{seed}_REVIEW.json';r=read(p);assert r['passed'] and r['action_seed']==original['seed']==seed and r['condition']==reg['case_ids'][0]
  raw=np.load(folder/'audit_substeps.npy',mmap_mode='r',allow_pickle=False)[:r['physical']['samples']];assert raw.shape==(1100000,11) and np.isfinite(raw).all() and (raw[:,0]==.00005).all()
  limits=read(folder/'AUDIT_EXTENSION.json')['actuator_limits_nm'];mask=raw[:,8]>.05;compliant=np.ones(len(raw),bool);peaks=[]
  for j,lim in enumerate(limits):
   v=np.abs(raw[:,j+1]);peaks.append(float(v.max()));compliant &=v<=lim/2
  contact=int(np.count_nonzero(mask))*.00005;below=int(np.count_nonzero(mask & compliant))*.00005
  row=r['physical']['row'];assert np.allclose(peaks,row['peak_torque_nm_per_joint'],rtol=0,atol=1e-12)
  assert math.isclose(contact,row['human_contact_s'],abs_tol=1e-8) and math.isclose(below,row['human_below_threshold_s'],abs_tol=1e-8)
  assert math.isclose(float(raw[:,9].max())*1000,r['external_penetration_mm'],abs_tol=1e-10)
  terminal=read(folder/'TERMINAL.json');journal=[json.loads(l) for l in (folder/'actor_intervals.jsonl').read_text().splitlines()];assert len(journal)==r['actions']==1375
  vals=[];reward=SPTReward()
  for i,x in enumerate(journal):
   done=i==len(journal)-1;y=terminal if done else journal[i+1]
   v,_=reward(current_potential=x['payload_potential'],next_potential=y['payload_potential'],interval=y['interval'],terminated=done,task_success=terminal['result']['task_success'] if done else False,strict_success=terminal['result']['strict_success'] if done else False)
   if done and terminal['result']['strict_success']:v+=completion_bonus(task_success=True,strict_success=True,completion_time_s=terminal['completion_time_s'])
   vals.append(v)
  error=abs(math.fsum(vals)-r['reward']);assert error<1e-10
  assert r['reward']==original['reward'] and row['task_success']==original['task'] and row['strict_success']==original['strict']
  assert r['native_stochastic_parameter_action_max_error']<=1e-7
  rows.append(dict(group=group,seed=seed,condition=r['condition'],actions=1375,substeps=len(raw),reward=r['reward'],reward_error=error,task=row['task_success'],strict=row['strict_success'],stage=row['final_task_stage'],human_contact_s=contact,human_compliant_s=below,human_compliance_ratio=below/contact if contact else None,penetration_mm=r['external_penetration_mm']))
  inputs[str(p)]=sha(p);inputs[str(folder/'audit_substeps.npy')]=sha(folder/'audit_substeps.npy')
assert len(rows)==16
put(D/'SEEDS_RAW_REVIEW.json',dict(passed=True,time=time.time(),rows=rows,inputs=inputs,total_episodes=16,total_actions=22000,total_substeps=17600000,maximum_reward_error=max(r['reward_error'] for r in rows),new_physics=0,new_network_forward=0,new_optimizer_updates=0,convergence_claim=False))
assert read(D/'SEEDS_RAW_REVIEW.json')['rows']==rows
put(D/'SEEDS_RAW_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all16_read_back=True,source_sha256=sha(__file__),review_sha256=sha(D/'SEEDS_RAW_REVIEW.json')))
print('All16 raw review passed',[(r['group'],r['seed'],r['task'],r['strict'],r['stage']) for r in rows])
