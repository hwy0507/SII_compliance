"""Bind complete90-92 inputs to the original prospective protocol; no training."""
from pathlib import Path
import argparse,hashlib,json,time,math
D=Path(__file__).resolve().parent;B=D.parents[1];S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1';OLD=S
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def bind_visual_evidence(cycle,review,inspection,loss):
 assert inspection['actual_visual_inspection'] is True
 expected={'loss_plot':review/'loss'/f'loss{cycle}.png','health_plot':review/'health/training_diagnostics.png'}
 items=inspection['plots'];assert len(items)==2
 by_path={Path(x['path']).resolve():x for x in items}
 assert len(by_path)==2 and set(by_path)=={p.resolve() for p in expected.values()}
 for p in expected.values():
  item=by_path[p.resolve()];assert item['inspected'] is True and sha(p)==item['sha256']
 assert sha(expected['loss_plot'])==loss['plot_sha256']
 return {k:ref(p) for k,p in expected.items()}

def setup():
 binding=read(D/'BINDING_PLAN.json');assert sha(__file__)==binding['binding_sha256'] and sha(S/'EARLY_WINDOW_FAILURE_91.json')==binding['original_early_failure_sha256']
 plan=read(S/'PLAN.json');assert plan['cycles']==[90,91,92] and plan['bootstrap_seed']==2026102861 and plan['replicates']==5000 and plan['near_zero_guard']==1 and plan['relative_limit']==.05 and not plan['automatic_training']
 assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256']
 for k in ['original88_90_plan','original_failure','revision_boundary']:assert sha(plan[k]['path'])==plan[k]['sha256']
 previous=read(B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/REGISTRATION.json')
 for x in previous['anchor_protocol55'].values():assert sha(x['path'])==x['sha256']
 return plan,previous

def bind_cycle(cycle,run,review,plan,previous):
 full=read(review/'REVIEW.json');health=read(review/'health/DIAGNOSIS.json');loss=read(review/'loss/REVIEW.json');finished=read(review/'FINISHED.json');inspection=read(review/'PLOT_INSPECTION.json')
 assert full['passed'] and loss['passed'] and finished['completed'] and inspection['actual_visual_inspection']
 visual_refs=bind_visual_evidence(cycle,review,inspection,loss)
 result={}
 for m in ['impedance','admittance','vmc']:
  p=read(run/m/'REGISTRATION.json');row=full['methods'][m];anchor=read(previous['anchor_protocol55'][m]['path'])
  assert cycle in plan['cycles'] and p['history_critic_amendment']==plan['history_amendment'][m] and p['violation_critic_amendment']==plan['violation_amendment'][m]
  assert p['post_interruption_continuation']['new_cycle']==cycle and p['post_interruption_continuation']['parent_cycle']==cycle-1
  for key in ['conditions','runtime_sha256','reference_plan_sha256','physics_dt_s','actor_period_s','horizon_s','actor','reward','critic_clock','learner_batch_size','learner_updates_per_transition','critic_layer_norm','numerical_amendments','terminal_weight_stage','target_projection_stage','exact_pipeline_stage','pair_reduction_stage','sampler_pool','shared_sampler_stage','replay_capacity_stage']:assert p[key]==anchor[key],(m,key)
  for key in ['projection','weight','reduction','dependency_hashes']:assert p['batch_size_stage'][key]==anchor['batch_size_stage'][key]
  for key in ['actor_learning_rate_factor','parent_actor_learning_rates','bellman_target_count']:assert p['completed_stage_continuation'][key]==anchor['completed_stage_continuation'][key]
  assert p['replay_capacity_followup_stage']==anchor['replay_capacity_followup_stage'] and row['replay_capacity_followup']==previous['followup_marker']
  assert row['optimizer_and_network_finite'] and row['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256'] and health['methods'][m]['network_state_unchanged']
  st=p['post_interruption_continuation']
  for k in ['cycle_review','scientific_decision']:assert sha(st[k]['path'])==st[k]['sha256']
  prior=read(st['cycle_review']['path']);assert prior['passed'];parent=prior['methods'][m]
  decision=read(st['scientific_decision']['path']);assert decision['parent_cycle']==cycle-1 and decision['new_cycle']==cycle and decision['new_cycles']==1 and decision['maximum_new_actions_per_method']==41250 and decision['automatic_followup'] is False
  assert st['new_cycles']==1 and st['maximum_new_actions']==41250 and st['automatic_followup'] is False and st['optimizer_settings_changed'] is False
  if cycle==90:assert parent['steps']==p['violation_critic_amendment']['binding']['rows']
  else:assert parent['checkpoint_sha256']==st['checkpoint']['sha256']
  assert row['retained_replay_rows']==parent['steps'] and row['steps']==parent['steps']+row['new_transitions'] and 0<row['new_transitions']<=41250
  assert health['cycle']==cycle and health['optimizer_updates_performed']==0 and loss['methods'][m]['rows']==row['new_transitions']
  episodes=run/m/'train/episodes.jsonl';optimizer=run/m/'train/optimizer.jsonl';es=[json.loads(line) for line in episodes.read_text().splitlines()]
  cs={c['id']:c for c in p['conditions']};assert len(es)==len({e['condition'] for e in es})==len(cs)==30 and {e['condition'] for e in es}==set(cs)
  assert all(e['cycle']==cycle and e['model_sha256']==cs[e['condition']]['model_sha256'] for e in es)
  assert abs(math.fsum(e['reward'] for e in es)/30-row['reward_mean'])<1e-10 and sum(e['steps'] for e in es)==row['new_transitions']
  assert sum(e['task_success'] for e in es)==row['task'] and sum(e['strict_success'] for e in es)==row['strict']
  assert all(0<e['steps']<=1375 for e in es) and sum(e['full_task_horizon_completed'] for e in es)==row['full_horizon_count']
  assert [e for e in es if e.get('abort_reason')]==row['aborts']
  assert sha(optimizer)==loss['methods'][m]['optimizer_log_sha256']
  records=[json.loads(line) for line in optimizer.read_text().splitlines()]
  assert len(records)==row['new_transitions'] and [x['step'] for x in records]==list(range(parent['steps']+1,row['steps']+1))
  assert all(math.isfinite(v) for x in records for v in x.values() if isinstance(v,(float,int)))
  result[f'{m}:{cycle}']={name:ref(path) for name,path in dict(protocol=run/m/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'health/DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=episodes,optimizer=optimizer).items()}
  result[f'{m}:{cycle}'].update(visual_refs,loss_review=ref(review/'loss/REVIEW.json'),plot_inspection=ref(review/'PLOT_INSPECTION.json'),window_plan=ref(S/'PLAN.json'),early_window_failure=ref(S/'EARLY_WINDOW_FAILURE_91.json'))
 return result
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');parser.add_argument('--cycle92-run',type=Path);parser.add_argument('--cycle92-review',type=Path);args=parser.parse_args();plan,previous=setup()
 inputs=bind_cycle(90,B/'runs/parameter_violation_cycle90_20261030_v1',B/'runs/parameter_violation_cycle90_review_20261030_v1',plan,previous)
 if args.check_only:
  inputs.update(bind_cycle(91,B/'runs/parameter_violation_cycle91_20261030_v1',B/'runs/parameter_violation_cycle91_review_20261030_v1',plan,previous))
  try:bind_cycle(92,B/'runs/parameter_violation_cycle92_20261030_v1',B/'runs/parameter_violation_cycle92_review_20261030_v1',plan,previous)
  except FileNotFoundError:missing=True
  else:raise AssertionError('92 already complete; inspect before changing preparation status')
  original=read(B/'runtime/violation91_completion_20261030_v1/COMPLETE91_BINDING_REVIEW.json');assert original['passed']
  for key,group in original['inputs90_91'].items():
   assert all(inputs[key][k]==v for k,v in group.items())
  early=read(S/'EARLY_WINDOW_FAILURE_91.json');assert early['original_plan_sha256']==sha(S/'PLAN.json') and early['failed_methods']==['impedance','admittance']
  assert sha(early['source_report']['path'])==early['source_report']['sha256']
  put(D/'INPUT90_91_READY_REVIEW.json',dict(passed=True,time=time.time(),inputs90_91=inputs,previous_six_input_groups_exact=True,actual_missing_complete92_rejected=missing,actual_plots_and_loss_receipts_bound=True,original_plan_sha256=sha(S/'PLAN.json'),original_early_failure_sha256=sha(S/'EARLY_WINDOW_FAILURE_91.json'),binding_source_sha256=sha(__file__),physical_steps=0,optimizer_updates=0,statistics_evaluated=False,automatic_training=False));print('Complete90/91 core refs unchanged; plots/loss/plan/failure now bound; actual incomplete92 rejected; no full statistics')
 else:
  if args.cycle92_run is None or args.cycle92_review is None:raise ValueError('Actual separately registered and reviewed complete92 paths required')
  inputs.update(bind_cycle(91,B/'runs/parameter_violation_cycle91_20261030_v1',B/'runs/parameter_violation_cycle91_review_20261030_v1',plan,previous));inputs.update(bind_cycle(92,args.cycle92_run,args.cycle92_review,plan,previous))
  registration=dict(cycles=plan['cycles'],seed=plan['bootstrap_seed'],bootstrap_replicates=plan['replicates'],near_zero_guard=plan['near_zero_guard'],relative_limit=plan['relative_limit'],source_sha256=sha(S/'audit.py'),followup_marker=previous['followup_marker'],anchor_protocol55=previous['anchor_protocol55'],history_amendment=plan['history_amendment'],violation_amendment=plan['violation_amendment'],inputs=inputs,original_prospective_plan=ref(S/'PLAN.json'),binding_source=ref(Path(__file__)),original_early_failure=ref(S/'EARLY_WINDOW_FAILURE_91.json'),automatic_training=False)
  put(S/'REGISTRATION.json',registration);print('All complete90-92 bound; run original audit/review_saved then inspect actual plot. No training launched.')
