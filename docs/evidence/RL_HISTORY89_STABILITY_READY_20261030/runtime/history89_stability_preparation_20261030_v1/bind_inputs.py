"""Bind complete88-90 inputs to the original prospective protocol; no training."""
from pathlib import Path
import argparse,hashlib,json,time,math
D=Path(__file__).resolve().parent;B=D.parents[1];S=B/'runs/parameter_history88_90_reward_stability_20261030_v2';OLD=B/'runs/parameter_history88_90_reward_stability_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def setup():
 correction=read(S/'LABEL_CORRECTION.json');assert correction['passed'] and sha(OLD/'PLAN.json')==correction['original_plan_sha256']==sha(S/'ORIGINAL_PLAN.json')
 for file in correction['files']:assert sha(S/file['name'])==file['sha256'] and sha(OLD/file['name'])==file['parent_sha256']
 plan=read(OLD/'PLAN.json');assert plan['cycles']==[88,89,90] and plan['bootstrap_seed']==2026102861 and plan['replicates']==5000 and plan['near_zero_guard']==1 and plan['relative_limit']==.05 and not plan['automatic_training']
 previous=read(B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/REGISTRATION.json')
 for x in previous['anchor_protocol55'].values():assert sha(x['path'])==x['sha256']
 return plan,previous

def bind_cycle(cycle,run,review,plan,previous):
 full=read(review/'REVIEW.json');health=read(review/'health/DIAGNOSIS.json');loss=read(review/'loss/REVIEW.json');finished=read(review/'FINISHED.json');inspection=read(review/'PLOT_INSPECTION.json')
 assert full['passed'] and loss['passed'] and finished['completed'] and inspection['actual_visual_inspection']
 result={}
 for m in ['impedance','admittance','vmc']:
  p=read(run/m/'REGISTRATION.json');row=full['methods'][m];anchor=read(previous['anchor_protocol55'][m]['path'])
  assert p['history_critic_amendment']==plan['history_amendment'][m]
  assert p['post_interruption_continuation']['new_cycle']==cycle and p['post_interruption_continuation']['parent_cycle']==cycle-1
  for key in ['conditions','runtime_sha256','reference_plan_sha256','physics_dt_s','actor_period_s','horizon_s','actor','reward','critic_clock','learner_batch_size','learner_updates_per_transition','critic_layer_norm','numerical_amendments','terminal_weight_stage','target_projection_stage','exact_pipeline_stage','pair_reduction_stage','sampler_pool','shared_sampler_stage','replay_capacity_stage']:assert p[key]==anchor[key],(m,key)
  for key in ['projection','weight','reduction','dependency_hashes']:assert p['batch_size_stage'][key]==anchor['batch_size_stage'][key]
  for key in ['actor_learning_rate_factor','parent_actor_learning_rates','bellman_target_count']:assert p['completed_stage_continuation'][key]==anchor['completed_stage_continuation'][key]
  assert p['replay_capacity_followup_stage']==anchor['replay_capacity_followup_stage'] and row['replay_capacity_followup']==previous['followup_marker']
  assert row['optimizer_and_network_finite'] and row['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256'] and health['methods'][m]['network_state_unchanged']
  assert row['steps']==p['history_critic_amendment']['binding']['rows']+(cycle-87)*41250 and row['new_transitions']==41250
  episodes=run/m/'train/episodes.jsonl';optimizer=run/m/'train/optimizer.jsonl';es=[json.loads(line) for line in episodes.read_text().splitlines()]
  cs={c['id']:c for c in p['conditions']};assert len(es)==len({e['condition'] for e in es})==len(cs)==30 and {e['condition'] for e in es}==set(cs)
  assert all(e['cycle']==cycle and e['model_sha256']==cs[e['condition']]['model_sha256'] for e in es)
  assert abs(math.fsum(e['reward'] for e in es)/30-row['reward_mean'])<1e-10 and sum(e['steps'] for e in es)==row['new_transitions']
  assert sha(optimizer)==loss['methods'][m]['optimizer_log_sha256']
  result[f'{m}:{cycle}']={name:ref(path) for name,path in dict(protocol=run/m/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'health/DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=episodes,optimizer=optimizer).items()}
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');parser.add_argument('--cycle90-run',type=Path);parser.add_argument('--cycle90-review',type=Path);args=parser.parse_args();plan,previous=setup()
 inputs=bind_cycle(88,B/'runs/parameter_history_cycle88_20261030_v2',B/'runs/parameter_history_cycle88_review_20261030_v2',plan,previous)
 if args.check_only:
  try:bind_cycle(89,B/'runs/parameter_history_cycle89_20261030_v1',B/'runs/parameter_history_cycle89_review_20261030_v1',plan,previous)
  except FileNotFoundError:missing=True
  else:raise AssertionError('89 already complete; inspect before changing preparation status')
  put(D/'INPUT88_REVIEW.json',dict(passed=True,time=time.time(),inputs88=inputs,exact_history_revision=True,scientific_contract55_exact=True,actual_incomplete89_rejected=missing,original_plan_sha256=sha(OLD/'PLAN.json'),binding_source_sha256=sha(__file__),physical_steps=0,optimizer_updates=0,statistics_evaluated=False));print('Actual complete88 schema/bindings passed; incomplete89 rejected; no full88-90 statistics')
 else:
  if args.cycle90_run is None or args.cycle90_review is None:raise ValueError('Actual separately registered and reviewed complete90 paths required')
  inputs.update(bind_cycle(89,B/'runs/parameter_history_cycle89_20261030_v1',B/'runs/parameter_history_cycle89_review_20261030_v1',plan,previous));inputs.update(bind_cycle(90,args.cycle90_run,args.cycle90_review,plan,previous))
  registration=dict(cycles=plan['cycles'],seed=plan['bootstrap_seed'],bootstrap_replicates=plan['replicates'],near_zero_guard=plan['near_zero_guard'],relative_limit=plan['relative_limit'],source_sha256=sha(S/'audit.py'),followup_marker=previous['followup_marker'],anchor_protocol55=previous['anchor_protocol55'],history_amendment=plan['history_amendment'],inputs=inputs,original_prospective_plan=ref(OLD/'PLAN.json'),label_correction=ref(S/'LABEL_CORRECTION.json'),binding_source=ref(Path(__file__)),automatic_training=False)
  put(S/'REGISTRATION.json',registration);print('All complete88-90 bound; run audit.py --root and review_saved.py, then inspect actual plot. No training launched.')
