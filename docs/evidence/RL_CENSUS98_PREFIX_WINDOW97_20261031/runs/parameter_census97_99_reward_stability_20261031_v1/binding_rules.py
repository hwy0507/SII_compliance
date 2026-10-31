"""Fail closed on missing complete cycles, changed census rules or substituted health loss."""
from pathlib import Path
import json,hashlib,math
METHODS=['impedance','admittance','vmc'];CYCLES=[97,98,99]
KEYS={'protocol','review','health','finished','episodes','optimizer','loss_plot','health_plot','loss_review','plot_inspection','checkpoint'}
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def check_ref(r):
 if set(r)!={'path','sha256'} or sha(r['path'])!=r['sha256']:raise ValueError('Bound artifact changed')
def locked(root):
 lock=read(root/'SOURCE_LOCK.json')
 for n,h in lock['files'].items():
  if sha(root/n)!=h:raise ValueError('Prepared analysis source drift: '+n)
 p=read(root/'PLAN.json');check_ref(p['intent']);intent=read(p['intent']['path'])
 for k,v in [('cycles',CYCLES),('bootstrap_seed',2026102861),('replicates',5000),('near_zero_guard',1.),('relative_limit',.05)]:
  if p[k]!=v or intent[k]!=v:raise ValueError('Fixed census window rule changed: '+k)
 if p['conditional_amendment']!=intent['amendments']:raise ValueError('Census estimator intent changed')
 for k in ['original_plan','original_failed_report','original_saved_review','original_early_failure']:check_ref(p[k])
 check_ref(p['previous94_96_failed_report'])
 for group in ['protocol97','anchor_protocol55']:
  for r in p[group].values():check_ref(r)
 return p

def protocol(p,m,c,plan):
 st=p['post_interruption_continuation']
 anchor=read(plan['anchor_protocol55'][m]['path'])
 for key in ['conditions','runtime_sha256','reference_plan_sha256','physics_dt_s','actor_period_s','horizon_s','actor','reward','critic_clock','learner_batch_size','learner_updates_per_transition','critic_layer_norm','numerical_amendments','terminal_weight_stage','target_projection_stage','exact_pipeline_stage','pair_reduction_stage','sampler_pool','shared_sampler_stage','replay_capacity_stage','replay_capacity_followup_stage']:
  if p[key]!=anchor[key]:raise ValueError('Frozen scientific setting changed: '+key)
 for key in ['projection','weight','reduction','dependency_hashes']:
  if p['batch_size_stage'][key]!=anchor['batch_size_stage'][key]:raise ValueError('Frozen batch dependency changed')
 for key in ['actor_learning_rate_factor','parent_actor_learning_rates','bellman_target_count']:
  if p['completed_stage_continuation'][key]!=anchor['completed_stage_continuation'][key]:raise ValueError('Frozen optimizer setting changed')
 if (st['controller'],st['new_cycle'],st['parent_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'])!=(m,c,c-1,1,41250,False):raise ValueError('Wrong finite cycle identity')
 if p['conditional_terminal_amendment']!=plan['conditional_amendment'][m]:raise ValueError('Estimator revision changed inside window')
 if p['history_critic_amendment']!=plan['history_amendment'][m] or p['violation_critic_amendment']!=plan['violation_amendment'][m]:raise ValueError('Critic architecture changed inside window')
 if (p['conditional_terminal_amendment']['health_metric'],p['conditional_terminal_amendment']['update_metric'])!=('agent_train/original_sampled_q_loss','agent_train/conditional_terminal_q_loss'):raise ValueError('Original health loss substituted')
 if p.get('replay_capacity_third_stage')!=plan['third_capacity_stage'][m]:raise ValueError('Third capacity stage changed')
 if st['optimizer_settings_changed'] is not False:raise ValueError('Optimizer settings changed')
 for k in ['cycle_review','scientific_decision','parent_registration']:check_ref(st[k])
 decision=read(st['scientific_decision']['path'])
 if (decision['parent_cycle'],decision['new_cycle'],decision['new_cycles'],decision['maximum_new_actions_per_method'],decision['automatic_followup'])!=(c-1,c,1,41250,False):raise ValueError('Finite decision changed')
 return st

def validate_registration(root,reg,check_checkpoints=False):
 plan=locked(root)
 required=dict(cycles=CYCLES,seed=2026102861,bootstrap_replicates=5000,near_zero_guard=1.,relative_limit=.05,automatic_training=False,source_sha256=sha(root/'audit.py'),review_source_sha256=sha(root/'review_saved.py'),binding_source=ref(root/'bind_inputs.py'),original_prospective_plan=plan['intent'],original_failed_window=plan['original_failed_report'],original_early_failure=plan['original_early_failure'],history_amendment=plan['history_amendment'],violation_amendment=plan['violation_amendment'],conditional_amendment=plan['conditional_amendment'],anchor_protocol55=plan['anchor_protocol55'],followup_marker=plan['followup_marker'],third_capacity_stage=plan['third_capacity_stage'],previous94_96_failed_report=plan['previous94_96_failed_report'])
 if set(reg)!=set(required)|{'inputs'}:raise ValueError('Exact window registration fields required')
 for k,v in required.items():
  if reg[k]!=v:raise ValueError('Wrong registration '+k)
 if set(reg['inputs'])!={f'{m}:{c}' for m in METHODS for c in CYCLES}:raise ValueError('All nine complete input groups required')
 for m in METHODS:
  for c in CYCLES:
   refs=reg['inputs'][f'{m}:{c}']
   if set(refs)!=KEYS:raise ValueError('Complete raw/loss/plot/checkpoint bindings required')
   for item in refs.values():check_ref(item)
   r={k:read(refs[k]['path']) for k in ['protocol','review','health','finished','loss_review','plot_inspection']};p=r['protocol'];st=protocol(p,m,c,plan);row=r['review']['methods'][m];health=r['health']['methods'][m]
   if not r['review']['passed'] or not r['finished']['completed'] or not r['loss_review']['passed'] or r['health']['cycle']!=c:raise ValueError('Incomplete cycle evidence')
   if row['checkpoint_sha256']!=health['checkpoint_sha256'] or row['checkpoint_sha256']!=refs['checkpoint']['sha256']:raise ValueError('Checkpoint identity mismatch')
   if not 0<row['new_transitions']<=41250 or row['new_transitions']!=r['loss_review']['methods'][m]['rows']:raise ValueError('Actual cycle length mismatch')
   if 'agent_train/original_sampled_q_loss' not in r['loss_review']['methods'][m]['stats']:raise ValueError('Original loss review missing')
   if not row['optimizer_and_network_finite'] or not health['network_state_unchanged'] or r['health']['optimizer_updates_performed']!=0:raise ValueError('Full health evidence required')
   prior=read(st['cycle_review']['path'])
   if not prior['passed'] or prior['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or row['retained_replay_rows']!=prior['methods'][m]['steps'] or row['steps']!=prior['methods'][m]['steps']+row['new_transitions']:raise ValueError('Full parent review/counters mismatch')
   inspection=r['plot_inspection'];plots=inspection['plots']
   if inspection['actual_visual_inspection'] is not True or len(plots)!=2 or any(x['inspected'] is not True for x in plots):raise ValueError('Actual two-plot inspection required')
   expected={str(Path(refs[k]['path']).resolve()):refs[k]['sha256'] for k in ['loss_plot','health_plot']}
   if len(expected)!=2 or {str(Path(x['path']).resolve()):x['sha256'] for x in plots}!=expected:raise ValueError('Plot inspection binding mismatch')
   if refs['loss_plot']['sha256']!=r['loss_review']['plot_sha256']:raise ValueError('Loss plot mismatch')
   if refs['optimizer']['sha256']!=r['loss_review']['methods'][m]['optimizer_log_sha256']:raise ValueError('Original optimizer log mismatch')
   logs=[json.loads(x) for x in Path(refs['optimizer']['path']).read_text().splitlines()]
   if len(logs)!=row['new_transitions'] or [x['step'] for x in logs]!=list(range(st['parent_steps']+1,row['steps']+1)):raise ValueError('Missing actual updates')
   if any(x['update_index']!=0 or x['agent_train/q_loss']!=x['agent_train/conditional_terminal_q_loss'] or not math.isfinite(x['agent_train/original_sampled_q_loss']) or x['agent_train/original_sampled_q_loss']<0 for x in logs):raise ValueError('Dual-loss/update identity invalid')

   episodes=[json.loads(x) for x in Path(refs['episodes']['path']).read_text().splitlines()]
   if len(episodes)!=30 or len({e['condition'] for e in episodes})!=30 or any(e['cycle']!=c for e in episodes):raise ValueError('All30 actual cycle episodes required')
   conditions={x['id']:x for x in p['conditions']}
   if {e['condition'] for e in episodes}!=set(conditions) or any(e['model_sha256']!=conditions[e['condition']]['model_sha256'] for e in episodes):raise ValueError('Frozen conditions/models changed')
   if sum(e['steps'] for e in episodes)!=row['new_transitions'] or any(not 0<e['steps']<=1375 for e in episodes) or sum(e['full_task_horizon_completed'] for e in episodes)!=row['full_horizon_count']:raise ValueError('Actual episode lengths changed')
   if [e for e in episodes if e.get('abort_reason')]!=row['aborts'] or sum(e['task_success'] for e in episodes)!=row['task'] or sum(e['strict_success'] for e in episodes)!=row['strict']:raise ValueError('Task/Strict/aborts changed')
   if not math.isclose(math.fsum(e['reward'] for e in episodes)/30,row['reward_mean'],abs_tol=1e-10):raise ValueError('Reward summary mismatch')

   if c==97:
    if p!=read(plan['protocol97'][m]['path']):raise ValueError('Initial94 registration changed')
   else:
    prev=reg['inputs'][f'{m}:{c-1}'];parent=read(prev['review']['path'])['methods'][m]
    if st['checkpoint']['sha256']!=prev['checkpoint']['sha256'] or st['parent_registration']['sha256']!=prev['protocol']['sha256'] or st['parent_steps']!=parent['steps']:raise ValueError('Noncontiguous formal parent chain')
   if check_checkpoints:
    import torch
    torch.set_num_threads(1);ck=torch.load(refs['checkpoint']['path'],map_location='cpu',weights_only=False)
    if (ck['controller'],ck['cycle'],ck['boundary'],ck['protocol_sha256'])!=(m,c,'complete_condition_cycle',refs['protocol']['sha256']):raise ValueError('Actual saved boundary/identity mismatch')
    if ck['conditional_terminal_amendment']!=p['conditional_terminal_amendment'] or ck['learner']['conditional_terminal_census']!=p['conditional_terminal_amendment']['marker']:raise ValueError('Persisted estimator marker missing')
    if ck['history_critic_amendment']!=p['history_critic_amendment'] or ck['violation_critic_amendment']!=p['violation_critic_amendment']:raise ValueError('Saved architecture metadata changed')
    if ck['steps']!=row['steps'] or ck['replay']['size']!=row['steps'] or ck['replay']['cursor']!=row['steps'] or ck['replay']['capacity']!=6000000:raise ValueError('Saved replay counters/capacity changed')
    if ck.get('replay_capacity_third_stage')!=plan['third_capacity_stage'][m] or ck['replay'].get('replay_capacity_third')!=plan['third_capacity_stage'][m]['marker']:raise ValueError('Saved third capacity marker missing')
    if any(ck['replay']['arrays'][k].shape!=(row['steps'],52) for k in ['observations','next_observations']):raise ValueError('Full52 replay required')
    del ck
 return True
