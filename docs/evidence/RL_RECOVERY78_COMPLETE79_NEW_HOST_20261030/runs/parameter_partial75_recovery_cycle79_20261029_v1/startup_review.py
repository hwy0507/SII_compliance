from pathlib import Path
import os,sys,json,time,hashlib,shutil,collections
os.sched_setaffinity(0,{52})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent/'startup';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'))
from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER
from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER
from validate_published_finite_check_20261025 import digest
from spt_rl_reward_20261025 import SPTReward

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
jobs=json.loads((OUT.parent/'LAUNCH.json').read_text())['jobs']
for job in jobs:
 m=job['controller'];run=OUT.parent/m/'train';cp=run/'checkpoint_latest.pt';deadline=time.monotonic()+300
 while not cp.exists():
  if time.monotonic()>deadline or (run/'FAILURE.json').exists():raise RuntimeError('Startup checkpoint unavailable: '+m)
  time.sleep(2)
 snapshot=OUT/(m+'.pt')
 with cp.open('rb') as src,snapshot.open('xb') as dst:shutil.copyfileobj(src,dst)
 x=torch.load(snapshot,map_location='cpu',weights_only=False);e=json.loads((run/'EXECUTION.json').read_text());parent=Path(e['resumed_from']);assert sha(parent)==e['resumed_checkpoint_sha256'];old=torch.load(parent,map_location='cpu',weights_only=False);n=old['replay']['size'];a=x['replay']['arrays'];s=x['learner'];original=old['learner']
 assert x['replay']['capacity']==4_000_000 and x['replay']['replay_capacity_followup']==FOLLOWUP_MARKER and x['replay']['replay_capacity_extension']==CAPACITY_MARKER and x['replay']['cursor']==x['replay']['size']
 assert old['replay']['capacity']==4_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER and old['replay']['replay_capacity_followup']==FOLLOWUP_MARKER
 assert x['steps']>old['steps'] and x['replay']['size']==x['steps'] and x['cycles']==old['cycles']
 assert old['boundary']=='complete_condition_cycle' and old['cycle']==78 and x['cycle']==79
 assert x['interruption_recovery']['parent_cycle']==75 and x['interruption_recovery']['new_cycle']==76
 assert not any(c['cycle']==75 for c in x['cycles'])
 assert json.loads((run.parent/'INITIAL_STATE_REVIEW.json').read_text())['passed']
 assert s['num_gradient_steps']-original['num_gradient_steps']==x['steps']-old['steps']
 for k,v in old['replay']['arrays'].items():np.testing.assert_array_equal(v,a[k][:n])
 assert s['terminal_loss_weight']==128 and s.get('bellman_target_count',2)==2 and finite(s)
 assert s['target_pair_reduction']==dict(version=1,target={'impedance':'minimum','admittance':'mean','vmc':'mean'}[m],actor='minimum',sampled_targets=2)
 assert s['finite_target_projection']==dict(version=1,terminal_cap=30.,gamma=.9995,maximum_actions=1375,position='target critic Q before stochastic entropy term',upper_only=True)
 for key in ['actor_optimizer','q_optimizer','alpha_optimizer']:assert s[key]['param_groups']==original[key]['param_groups']
 reg=json.loads((run.parent/'REGISTRATION.json').read_text());assert x['protocol_sha256']==e['protocol_sha256']==sha(run.parent/'REGISTRATION.json');assert e['batch_size']==65536
 assert x['recovery_continuation']==reg['post_interruption_continuation'] and x['recovery_continuation']['parent_cycle']==78 and x['recovery_continuation']['new_cycle']==79
 previous=json.loads(Path(reg['post_interruption_continuation']['parent_registration']['path']).read_text())
 assert old['recovery_continuation']==previous['post_interruption_continuation']
 assert sha(reg['post_interruption_continuation']['parent_registration']['path'])==reg['post_interruption_continuation']['parent_registration']['sha256']
 assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 followup=reg['replay_capacity_followup_stage']
 assert followup['marker']==FOLLOWUP_MARKER and followup['parent_cycle']==47 and old['cycle']==78
 assert followup==previous['replay_capacity_followup_stage']
 assert sha(followup['entry_checkpoint']['path'])==followup['entry_checkpoint']['sha256']
 for name,expected in reg['batch_size_stage']['dependency_hashes'].items():assert sha(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'/name)==expected
 conditions={c['id']:c for c in reg['conditions']};models=0
 for f in run.glob('cycle_*/*/rollout.mjb'):
  assert sha(f)==conditions[f.parent.name]['model_sha256'];models+=1
 assert models==30
 pid=job['pid'];children=[int(v) for v in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()];first={'impedance':13,'admittance':26,'vmc':39}[m];assert len(children)==30 and os.sched_getaffinity(pid)=={first};assert {frozenset(os.sched_getaffinity(v)) for v in children}=={frozenset(range(first+1,first+13))}
 ts=[t for t in lines(run/'transitions.jsonl') if t['step']<=x['steps']];assert [t['step'] for t in ts]==list(range(n+1,x['steps']+1));by=collections.defaultdict(list)
 for t in ts:by[t['condition']].append(t)
 err=0.
 for name,rows in by.items():
  journal=list(lines(run/'cycle_00079'/name/'actor_intervals.jsonl'));reward=SPTReward()
  for i,t in enumerate(rows):
   assert not t['done'];j,nxt=journal[i],journal[i+1];k=t['step']-1
   value,_=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=False,task_success=False,strict_success=False);err=max(err,abs(value-t['reward']));assert err<1e-10
   np.testing.assert_array_equal(a['observations'][k,:48],np.asarray(j['observation'],np.float32)/s['observation_scale']);assert a['observations'][k,48]==np.float32(t['context']);assert a['observations'][k,49]==np.float32((1375-i)/1375)
   np.testing.assert_array_equal(a['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32));executed=np.asarray(j['executed_action'],np.float32);assert executed.shape==(7,) and np.isfinite(executed).all() and np.max(np.abs(executed))<=1.000001
   if m=='impedance':np.testing.assert_array_equal(executed,np.zeros(7,np.float32))
   np.testing.assert_array_equal(a['next_observations'][k,:48],np.asarray(nxt['observation'],np.float32)/s['observation_scale']);assert a['next_observations'][k,49]==np.float32((1374-i)/1375);assert a['rewards'][k,0]==np.float32(t['reward']) and a['dones'][k,0]==0
 report['methods'][m]=dict(steps=x['steps'],updates=s['num_gradient_steps'],added_steps=x['steps']-old['steps'],replay_capacity_extension=CAPACITY_MARKER,replay_capacity_followup=FOLLOWUP_MARKER,current_replay_capacity=4_000_000,historical_entry_cycle=23,parent_sha256=sha(parent),checkpoint_sha256=sha(snapshot),retained_replay_all_fields_exact=True,retained_replay_rows=n,history_retained=True,optimizer_hyperparameters_retained=True,terminal_weight=128,target_projection_marker=s['finite_target_projection'],pair_reduction_marker=s['target_pair_reduction'],model_count=models,actual_sampler_count=30,new_transition_mapping_count=len(ts),max_reward_reconstruction_error=err,terminal_coverage=False,mapping_scope='Raw RL action to mixed parameter-controller input exactly; public seven-channel output shape/finite/bounds checked, impedance zero bridge checked. Not a re-simulation of admittance/VMC internal dynamics.')
 del x,old,a,s,original
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
