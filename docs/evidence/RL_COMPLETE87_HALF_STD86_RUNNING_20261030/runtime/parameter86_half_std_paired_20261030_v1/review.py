"""Finite fixed86 sensitivity collector; never launches or repeats science."""
from pathlib import Path
import json,time,os,sys,hashlib,math
R=Path(__file__).parent; O=R.parents[1]/'runs'/R.name
sys.path.insert(0,str(R))
from evaluate_parameter86_half_std_20261030 import validate_design,sha,write

def identity(pid):
 try:
  x=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return dict(start=x[19],state=x[0])
 except FileNotFoundError:return None

def main():
 os.sched_setaffinity(0,{11});os.nice(10)
 plan=json.loads((O/'PLAN.json').read_text());launch=json.loads((O/'LAUNCH.json').read_text())
 assert sha(__file__)==launch['review_source_sha256'] and sha(O/'PLAN.json')==launch['plan_sha256']
 deadline=launch['time']+plan['wall_dispatch_deadline_seconds']
 while True:
  ready=True
  for job in launch['jobs']:
   d=O/job['group'];assert not (d/'FAILURE.json').exists(),str(d)
   if (d/'FINISHED.json').exists():assert json.loads((d/'FINISHED.json').read_text())['passed']
   else:
    ready=False;state=identity(job['pid']);assert state and state['state']!='Z' and state['start']==job['start'],job
  if ready:break
  assert time.time()<deadline,'Original finite wait expired; no automatic restart or extension'
  time.sleep(10)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 groups={};inputs={};fig,axes=plt.subplots(4,2,figsize=(12,12),constrained_layout=True)
 for idx,(key,entry) in enumerate(plan['groups'].items()):
  d=O/key;reg=json.loads((d/'REGISTRATION.json').read_text());validate_design(reg)
  fin=json.loads((d/'FINISHED.json').read_text());stored=json.loads((d/'RESULTS.json').read_text())
  assert fin['passed'] and fin['episodes']==stored['completed']==stored['expected']==len(stored['episodes'])==4
  assert fin['full_learner_state_unchanged'] and fin['full_replay_state_unchanged'] and fin['new_optimizer_updates']==0
  assert fin['initial_learner_digest']==fin['final_learner_digest']
  assert sha(reg['checkpoint'])==reg['checkpoint_sha256']
  for name,expected in reg['source_hashes'].items():assert sha(R/name)==expected,name
  rows=[]
  for seed,original in zip(plan['action_seeds'],stored['episodes']):
   p=d/f'seed_{seed}_REVIEW.json';ev=json.loads(p.read_text());assert ev==original and ev['passed']
   assert ev['action_seed']==seed and ev['condition']==reg['case_ids'][0]
   assert ev['full_learner_state_unchanged'] and ev['new_optimizer_updates']==0
   assert ev['native_stochastic_parameter_action_max_error']<=1e-7
   folder=d/f'seed_{seed}'
   for kind in ['physical','filter','torque']:
    audit=ev[kind]
    if kind!='physical':assert audit['passed']
    for name,expected in audit['evidence_sha256'].items():assert sha(folder/name)==expected,(key,seed,name)
   row=ev['physical']['row'];raw=json.loads((folder/'TERMINAL.json').read_text())
   assert row['task_success']==raw['result']['task_success'] and row['strict_success']==raw['result']['strict_success']
   assert row['full_horizon']==raw['result']['full_task_horizon_completed']
   if row['full_horizon']:assert ev['actions']==1375 and ev['physical']['samples']==1100000
   else:assert row['abort_reason'] and ev['physical']['samples']<1100000
   assert math.isfinite(ev['reward']) and math.isfinite(ev['external_penetration_mm'])
   rows.append(dict(seed=seed,condition=ev['condition'],reward=ev['reward'],task=row['task_success'],strict=row['strict_success'],actions=ev['actions'],substeps=ev['physical']['samples'],penetration_mm=ev['external_penetration_mm'],full_horizon=row['full_horizon'],abort_reason=row['abort_reason'],machine_safety_violation=row['machine_safety_violation'],human_contact_s=row['human_contact_s'],human_compliance_ratio=row['human_compliance_ratio'],peak_torque_nm_per_joint=row['peak_torque_nm_per_joint'],completion_time_s=row['completion_time_s']))
   inputs[str(p)]=sha(p)
  assert [x['seed'] for x in rows]==plan['action_seeds']
  for output,col in [('actions','actions'),('substeps','substeps'),('task','task'),('strict','strict')]:assert sum(x[col] for x in rows)==fin[output]
  assert fin['actions']<=5500 and fin['substeps']<=4400000
  rewards=[x['reward'] for x in rows];peaks=[x['penetration_mm'] for x in rows]
  groups[key]=dict(rows=rows,task=sum(x['task'] for x in rows),strict=sum(x['strict'] for x in rows),task_variation=len(set(x['task'] for x in rows))>1,strict_variation=len(set(x['strict'] for x in rows))>1,reward_mean=math.fsum(rewards)/4,reward_range=[min(rewards),max(rewards)],penetration_range_mm=[min(peaks),max(peaks)],checkpoint_sha256=reg['checkpoint_sha256'],initial_and_final_learner_digest=fin['initial_learner_digest'])
  for j,values in enumerate([rewards,peaks]):
   axes[idx,j].scatter(range(4),values,c=['green' if x['strict'] else 'red' for x in rows]);axes[idx,j].set_xticks(range(4),[str(s) for s in plan['action_seeds']],rotation=15);axes[idx,j].set_title(key+(' return' if j==0 else ' external penetration (mm)'));axes[idx,j].grid(alpha=.2)
  axes[idx,1].axhline(.2,color='black',linestyle='--',label='Original Strict limit');axes[idx,1].legend()
  for name in ['REGISTRATION.json','CHECK_ONLY_REVIEW.json','STARTUP_REVIEW.json','EVALUATION.json','FINISHED.json','RESULTS.json']:inputs[str(d/name)]=sha(d/name)
 fig.suptitle('Frozen86 half-std intervention, same16 pairs; green=Strict success')
 fig.savefig(O/'fixed86_seed_results.png',dpi=140);plt.close(fig)
 report=dict(passed=True,time=time.time(),groups=groups,total_episodes=16,total_actions=sum(x['actions'] for g in groups.values() for x in g['rows']),total_substeps=sum(x['substeps'] for g in groups.values() for x in g['rows']),inputs=inputs,plot_sha256=sha(O/'fixed86_seed_results.png'),plan_sha256=sha(O/'PLAN.json'),new_physics=0,new_optimizer_updates=0,convergence_claim=False,limitations=plan['limits'],prior_evidence=plan['prior_evidence'])
 assert report['total_actions']<=22000 and report['total_substeps']<=17600000
 from pair_review import review_paired
 report['paired_variance_intervention'] = review_paired(O, report, plan)
 write(O/'REVIEW.json',report)
 saved=json.loads((O/'REVIEW.json').read_text());assert saved==report
 for key,g in saved['groups'].items():
  assert g['task']==sum(int(r['task']) for r in g['rows']) and g['strict']==sum(int(r['strict']) for r in g['rows'])
 write(O/'SAVED_REVIEW.json',dict(passed=True,review_sha256=sha(O/'REVIEW.json'),all16_in_declared_order=True,no_dropped_seed=True,raw_evidence_hashes_verified=True,final_full_state_proofs_required=True,new_physics=0,new_optimizer_updates=0))
 write(O/'FINISHED.json',dict(passed=True,time=time.time(),episodes=16,review_sha256=sha(O/'REVIEW.json'),saved_review_sha256=sha(O/'SAVED_REVIEW.json'),plot_sha256=sha(O/'fixed86_seed_results.png'),actual_plot_viewed=False))
if __name__=='__main__':
 try:main()
 except BaseException as e:write(O/'REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
