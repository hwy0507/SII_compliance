from pathlib import Path
import os,sys,json,time,hashlib,shutil,collections
os.sched_setaffinity(0,{52})
os.nice(15)
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent/'startup';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(v):
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,(list,tuple)):return all(finite(x) for x in v)
 if torch.is_tensor(v):return bool(torch.isfinite(v).all())
 if isinstance(v,(float,np.ndarray)):return bool(np.isfinite(v).all())
 return True
def lines(p):
 with p.open() as f:
  for line in f:
   if line.endswith('\n'):yield json.loads(line)
report=dict(time=time.time(),passed=True,methods={},new_physics=0,optimizer_updates=0)
launch=json.loads((OUT.parent/'LAUNCH.json').read_text());jobs=[dict(controller='direct',pid=launch['pid'])]
for job in jobs:
 m=job['controller'];run=OUT.parent/'direct';cp=run/'checkpoint_latest.pt';deadline=time.monotonic()+300
 while not cp.exists():
  if time.monotonic()>deadline or (run/'FAILURE.json').exists():raise RuntimeError('Startup checkpoint unavailable: '+m)
  time.sleep(2)
 snapshot=OUT/(m+'.pt')
 with cp.open('rb') as src,snapshot.open('xb') as dst:shutil.copyfileobj(src,dst)
 x=torch.load(snapshot,map_location='cpu',weights_only=False);e=json.loads((run/'EXECUTION.json').read_text());parent=Path(e['resumed_from']);assert sha(parent)==e['resumed_checkpoint_sha256'];old=torch.load(parent,map_location='cpu',weights_only=False);n=old['replay']['size'];a=x['replay']['arrays'];s=x['learner'];original=old['learner']
 assert x['steps']>old['steps'] and x['replay']['size']==x['steps'] and x['cycles']==old['cycles']
 assert s['num_gradient_steps']-original['num_gradient_steps']==8*(x['steps']-old['steps'])
 for k,v in old['replay']['arrays'].items():np.testing.assert_array_equal(v,a[k][:n])
 assert finite(s) and s['critic_actor_ratio']==8 and s['config']==original['config']
 assert s['critic_clock_extension']==original['critic_clock_extension']
 assert s['critic_clock_extension']['actor_features']==48 and s['critic_clock_extension']['critic_observation_features']==49
 reg=json.loads((OUT.parent/'REGISTRATION.json').read_text());assert x['protocol_sha256']==e['protocol_sha256']==sha(OUT.parent/'REGISTRATION.json');assert e['batch_size']==65536
 sys.path.insert(0,str(B/'runtime/serl_recovery26_take27_20261027_v1'))
 from serl_replay_capacity_20261027 import MARKER as CAPACITY_MARKER
 assert reg['replay_capacity_stage']['marker']==CAPACITY_MARKER
 assert x['replay']['replay_capacity_extension']==CAPACITY_MARKER
 assert x['replay']['capacity']==2_000_000 and x['replay']['cursor']==x['replay']['size']==x['steps']
 assert old['cycle']==26 and old['boundary']=='complete_condition_cycle'
 assert old['replay']['capacity']==2_000_000 and old['replay']['size']==old['replay']['cursor']==old['steps']
 assert old['replay']['replay_capacity_extension']==CAPACITY_MARKER
 parent_ref=reg['recovery_continuation_stage']['parent_registration'];parent_reg_path=Path(parent_ref['path'])
 assert sha(parent_reg_path)==parent_ref['sha256']==old['protocol_sha256']
 parent_reg=json.loads(parent_reg_path.read_text())
 assert reg['replay_capacity_stage']==parent_reg['replay_capacity_stage']
 assert reg['replay_capacity_stage']['parent_cycle']==23
 assert reg['recovery_continuation_stage']['parent_cycle']==26
 assert x['interruption_recovery']==old['interruption_recovery']==reg['interrupted_stream_recovery']
 assert x['recovery_continuation']==reg['recovery_continuation_stage']
 assert reg['recovery_continuation_stage']['checkpoint']==dict(path=str(parent),sha256=sha(parent))
 entry=reg['replay_capacity_stage']['entry_checkpoint'];assert sha(entry['path'])==entry['sha256']
 capacity_review=dict(passed=True,historical_entry_cycle=23,inherited_stage_exact=True,old_capacity=2_000_000,new_capacity=2_000_000,marker=CAPACITY_MARKER,
     old_size=old['replay']['size'],current_size=x['steps'],cursor=x['replay']['cursor'],crossed_old_capacity=x['steps']>1_000_000)
 report['replay_capacity']=capacity_review
 conditions={c['id']:c for c in reg['conditions']};models=0
 for f in run.glob('cycle_*/*/rollout.mjb'):
  assert sha(f)==conditions[f.parent.name]['model_sha256'];models+=1
 assert models==30
 pid=job['pid'];children=[int(v) for v in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()]
 finished_episodes=list(lines(run/'episodes.jsonl'))
 assert len(children)+len(finished_episodes)==30 and os.sched_getaffinity(pid)=={0} and all(os.sched_getaffinity(v)==set(range(1,13)) for v in children)
 ts=[t for t in lines(run/'transitions.jsonl') if t['step']<=x['steps']];assert [t['step'] for t in ts]==list(range(n+1,x['steps']+1));by=collections.defaultdict(list)
 for t in ts:by[t['condition']].append(t)
 err=0.
 for name,rows in by.items():
  journal=list(lines(run/'cycle_00027'/name/'actor_intervals.jsonl'));reward=SPTReward()
  for i,t in enumerate(rows):
   j=journal[i];nxt=json.loads((run/'cycle_00027'/name/'TERMINAL.json').read_text()) if t['done'] else journal[i+1];k=t['step']-1
   labels=nxt['result'] if t['done'] else dict(task_success=False,strict_success=False)
   value,_=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=t['done'],task_success=labels['task_success'],strict_success=labels['strict_success'])
   if t['done'] and labels['strict_success']:value+=completion_bonus(task_success=True,strict_success=True,completion_time_s=nxt['completion_time_s'])
   err=max(err,abs(value-t['reward']));assert err<1e-10
   np.testing.assert_array_equal(a['observations'][k,:48],np.asarray(j['observation'],np.float32)/s['observation_scale']);assert a['observations'][k,48]==np.float32((1375-i)/1375)
   expected=a['actions'][k].copy();expected[0]=np.float32(.5)*(expected[0]+np.float32(1.))
   np.testing.assert_array_equal(expected,np.asarray(j['action'],np.float32));np.testing.assert_array_equal(expected,np.asarray(j['executed_action'],np.float32));assert t['context'] is None
   np.testing.assert_array_equal(a['next_observations'][k,:48],(a['observations'][k,:48] if t['done'] else np.asarray(nxt['observation'],np.float32)/s['observation_scale']));assert a['next_observations'][k,48]==np.float32((1374-i)/1375);assert a['rewards'][k,0]==np.float32(t['reward']) and a['dones'][k,0]==float(t['done'])
 sys.path.insert(0,str(B/'runtime/serl_recovery26_take27_20261027_v1'))
 sys.path.insert(0,'/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_recovery26_take27_20261027_v1/audit_source')
 from audit_serl_recovery27_replay_20261027 import audit
 multistep=audit(x,old,ts)
 report['multistep_replay']=multistep
 report['methods'][m]=dict(steps=x['steps'],updates=s['num_gradient_steps'],added_steps=x['steps']-old['steps'],parent_sha256=sha(parent),checkpoint_sha256=sha(snapshot),retained_replay_all_fields_exact=True,retained_replay_rows=n,history_retained=True,optimizer_hyperparameters_retained=True,critic_clock_marker=s['critic_clock_extension'],model_count=models,actual_live_sampler_count=len(children),completed_at_affinity_observation=len(finished_episodes),registered_samplers=30,new_transition_mapping_count=len(ts),max_reward_reconstruction_error=err,terminal_coverage_count=sum(t['done'] for t in ts),aborts=[e for e in finished_episodes if e['abort_reason']],mapping_scope='All new canonical48 scaling, critic remaining-time current/next clocks, raw7-to-public7 mapping and journal rewards verified. Prepared replay prefix exact; not raw-substep dynamics replay.')
 del x,old,a,s,original
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
