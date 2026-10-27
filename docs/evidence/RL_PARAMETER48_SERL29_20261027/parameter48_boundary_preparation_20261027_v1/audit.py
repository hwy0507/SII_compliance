from pathlib import Path
import os,sys,json,time,hashlib,shutil,collections
os.sched_setaffinity(0,{52})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');RUN=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1';OUT=Path(__file__).parent/'evidence';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(B/'runtime/parameter_capacity_pool30_cycle48_20261026_v1'))
from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus
from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER
from validate_published_finite_check_20261025 import digest

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
jobs=json.loads((RUN/'LAUNCH.json').read_text())['jobs']
for job in jobs:
 m=job['controller'];run=RUN/m/'train';cp=run/'checkpoint_latest.pt';deadline=time.monotonic()+7200;threshold=2_001_000
 while True:
  if time.monotonic()>deadline or (run/'FAILURE.json').exists():raise RuntimeError('Bounded second-capacity observation failed: '+m)
  progress=run/'PROGRESS.json'
  if cp.exists() and progress.exists() and json.loads(progress.read_text())['steps']>=threshold:
   candidate=OUT/(m+'.tmp')
   with cp.open('rb') as src,candidate.open('wb') as dst:shutil.copyfileobj(src,dst)
   probe=torch.load(candidate,map_location='cpu',weights_only=False);reached=probe['steps']>=threshold;del probe
   if reached:snapshot=OUT/(m+'.pt');candidate.rename(snapshot);break
   candidate.unlink()
  if (run/'FINISHED.json').exists():
   report['methods'][m]=dict(boundary_observed=False,threshold=threshold,reason='Finite48 ended before threshold');snapshot=None;break
  time.sleep(5)
 if snapshot is None:continue
 x=torch.load(snapshot,map_location='cpu',weights_only=False);e=json.loads((run/'EXECUTION.json').read_text());parent=Path(e['resumed_from']);assert sha(parent)==e['resumed_checkpoint_sha256'];old=torch.load(parent,map_location='cpu',weights_only=False);n=old['replay']['size'];a=x['replay']['arrays'];s=x['learner'];original=old['learner']
 assert x['replay']['capacity']==4_000_000 and x['replay']['replay_capacity_followup']==FOLLOWUP_MARKER and x['replay']['replay_capacity_extension']==CAPACITY_MARKER and x['replay']['cursor']==x['replay']['size']
 assert old['replay']['capacity']==2_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER and 'replay_capacity_followup' not in old['replay']
 assert old['cycle']==47 and old['boundary']=='complete_condition_cycle'
 assert x['steps']>=threshold
 assert x['steps']>old['steps'] and x['replay']['size']==x['steps'] and (x['cycles']==old['cycles'] or (x['cycles'][:-1]==old['cycles'] and x['cycles'][-1]['cycle']==48))
 assert s['num_gradient_steps']-original['num_gradient_steps']==x['steps']-old['steps']
 for k,v in old['replay']['arrays'].items():np.testing.assert_array_equal(v,a[k][:n])
 assert s['terminal_loss_weight']==128 and s.get('bellman_target_count',2)==2 and finite(s)
 assert s['target_pair_reduction']==dict(version=1,target={'impedance':'minimum','admittance':'mean','vmc':'mean'}[m],actor='minimum',sampled_targets=2)
 assert s['finite_target_projection']==dict(version=1,terminal_cap=30.,gamma=.9995,maximum_actions=1375,position='target critic Q before stochastic entropy term',upper_only=True)
 for key in ['actor_optimizer','q_optimizer','alpha_optimizer']:assert s[key]['param_groups']==original[key]['param_groups']
 reg=json.loads((run.parent/'REGISTRATION.json').read_text());assert x['protocol_sha256']==e['protocol_sha256']==sha(run.parent/'REGISTRATION.json');assert e['batch_size']==65536
 followup=reg['replay_capacity_followup_stage'];assert followup['parent_cycle']==47 and followup['marker']==FOLLOWUP_MARKER
 assert followup['entry_checkpoint']==dict(path=str(parent),sha256=sha(parent)) and followup['entry_replay_digest']==digest(old['replay'])
 previous=json.loads(Path(reg['resume_parent_registration']['path']).read_text());assert sha(reg['resume_parent_registration']['path'])==reg['resume_parent_registration']['sha256']
 assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 for name,expected in reg['batch_size_stage']['dependency_hashes'].items():assert sha(B/'runtime/parameter_capacity_pool30_cycle48_20261026_v1'/name)==expected
 conditions={c['id']:c for c in reg['conditions']};models=0
 for f in run.glob('cycle_*/*/rollout.mjb'):
  assert sha(f)==conditions[f.parent.name]['model_sha256'];models+=1
 assert models==30
 pid=job['pid'];process=Path(f'/proc/{pid}');children=[]
 if process.exists():
  assert RUN.name.encode() in (process/'cmdline').read_bytes()
  children=[int(v) for v in (process/f'task/{pid}/children').read_text().split()]
  first={'impedance':13,'admittance':26,'vmc':39}[m];assert os.sched_getaffinity(pid)=={first}
  for child in children:
   try:assert os.sched_getaffinity(child)==set(range(first+1,first+13))
   except ProcessLookupError:pass
 startup=json.loads((RUN/'startup/REVIEW.json').read_text());assert startup['passed'] and startup['methods'][m]['actual_sampler_count']==30
 rng=np.random.default_rng();rng.bit_generator.state=x['replay']['rng']
 while True:
  draws=rng.integers(x['replay']['size'],size=65536)
  if not np.any(a['masks'][draws].sum(axis=0)==0):break
 retained_draws=int(np.sum(draws<n));beyond_draws=int(np.sum(draws>=2_000_000));assert retained_draws>0 and beyond_draws>0
 ts=[t for t in lines(run/'transitions.jsonl') if t['step']<=x['steps']];assert [t['step'] for t in ts]==list(range(n+1,x['steps']+1));by=collections.defaultdict(list)
 for t in ts:by[t['condition']].append(t)
 err=0.
 for name,rows in by.items():
  journal=list(lines(run/'cycle_00048'/name/'actor_intervals.jsonl'));reward=SPTReward()
  for i,t in enumerate(rows):
   j=journal[i];nxt=json.loads((run/'cycle_00048'/name/'TERMINAL.json').read_text()) if t['done'] else journal[i+1];k=t['step']-1
   labels=nxt['result'] if t['done'] else dict(task_success=False,strict_success=False)
   value,_=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=t['done'],task_success=labels['task_success'],strict_success=labels['strict_success'])
   if t['done'] and labels['strict_success']:value+=completion_bonus(task_success=True,strict_success=True,completion_time_s=nxt['completion_time_s'])
   err=max(err,abs(value-t['reward']));assert err<1e-10
   np.testing.assert_array_equal(a['observations'][k,:48],np.asarray(j['observation'],np.float32)/s['observation_scale']);assert a['observations'][k,48]==np.float32(t['context']);assert a['observations'][k,49]==np.float32((1375-i)/1375)
   np.testing.assert_array_equal(a['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32));executed=np.asarray(j['executed_action'],np.float32);assert executed.shape==(7,) and np.isfinite(executed).all() and np.max(np.abs(executed))<=1.000001
   if m=='impedance':np.testing.assert_array_equal(executed,np.zeros(7,np.float32))
   np.testing.assert_array_equal(a['next_observations'][k,:48],(a['observations'][k,:48] if t['done'] else np.asarray(nxt['observation'],np.float32)/s['observation_scale']));assert a['next_observations'][k,49]==np.float32((1374-i)/1375);assert a['rewards'][k,0]==np.float32(t['reward']) and a['dones'][k,0]==float(t['done'])
 report['methods'][m]=dict(boundary_observed=True,threshold=threshold,current_replay_capacity=4_000_000,replay_capacity_followup=FOLLOWUP_MARKER,rows_beyond_old_capacity=x['steps']-2_000_000,saved_next65536_retained_draws=retained_draws,saved_next65536_beyond_old_capacity_draws=beyond_draws,sampling_scope='Read-only clone of saved RNG including original mask-rejection rule; not a live learner sample log',steps=x['steps'],updates=s['num_gradient_steps'],added_steps=x['steps']-old['steps'],replay_capacity_extension=CAPACITY_MARKER,parent_sha256=sha(parent),checkpoint_sha256=sha(snapshot),retained_replay_all_fields_exact=True,retained_replay_rows=n,history_retained=True,optimizer_hyperparameters_retained=True,terminal_weight=128,target_projection_marker=s['finite_target_projection'],pair_reduction_marker=s['target_pair_reduction'],model_count=models,registered_sampler_count=30,observed_live_sampler_count=len(children),startup_sampler_count_verified=True,new_transition_mapping_count=len(ts),max_reward_reconstruction_error=err,terminal_coverage_count=sum(t['done'] for t in ts),mapping_scope='Raw RL action to mixed parameter-controller input exactly; public seven-channel output shape/finite/bounds checked, impedance zero bridge checked. Not a re-simulation of admittance/VMC internal dynamics.')
 del x,old,a,s,original
report['passed']=all(v['boundary_observed'] for v in report['methods'].values())
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
