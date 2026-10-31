"""Consolidate actual complete96 evidence after separate actual plot inspection."""
from pathlib import Path
import json,time,hashlib,math
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle96_review_20261031_v1';T=B/'runs/census96_fixed95_terminal_20261031_v1';C=B/'runtime/census96_comparison_20261031_v1';W=B/'runs/census96_completion_wait_20261031_v1'
rd=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
checks=[R/'REVIEW.json',D/'FULL_LOSS_SAVED_REVIEW.json',C/'CACHE_POPULATION_FULL_REVIEW.json',C/'INTERPRETATION.json',C/'INTERPRETATION_SAVED_REVIEW.json',C/'CHANGED_CASES_REVIEW.json',T/'REVIEW.json',W/'COMPLETION_REVIEW.json',D/'LIVE_GROWTH_BINDING_REVIEW.json',D/'LIVE_TERMINAL_GROWTH_REVIEW.json']
for p in checks:assert rd(p)['passed'],str(p)
assert rd(R/'FINISHED.json')['completed'] and rd(T/'FINISHED.json')['passed'] and rd(C/'COMPARISON_FINISHED.json')['passed'] and rd(W/'COMPLETION_REVIEW.json')['all_complete']
for root,names in [(R,['loss/loss96.png','health/training_diagnostics.png']),(T,['fixed95_terminal_95_96.png']),(C,['training95_96_all90.png'])]:
 p=root/'PLOT_INSPECTION.json';x=rd(p);assert x['actual_visual_inspection'] and len(x['plots'])==len(names)
 assert {i['path']:i['sha256'] for i in x['plots']}=={str(root/n):sha(root/n) for n in names};assert all(i['inspected'] for i in x['plots']);checks.append(p)
review=rd(R/'REVIEW.json');health=rd(R/'health/DIAGNOSIS.json');loss=rd(D/'FULL_LOSS_SAVED_REVIEW.json');pop=rd(C/'CACHE_POPULATION_FULL_REVIEW.json');comp=rd(C/'INTERPRETATION.json');prefix=rd(D/'LIVE_TERMINAL_GROWTH_REVIEW.json');methods={}
for m,r in review['methods'].items():
 assert 0<r['new_transitions']<=41250 and r['conditions']==30 and r['max_reward_reconstruction_error']==0
 for k in ['retained_replay_all_old_fields_exact','retained_history_features_exact','retained_violation_features_exact','new_current_next52_and_raw_mixed_action_exact','optimizer_and_network_finite']:assert r[k]
 h=health['methods'][m];assert h['full_learner_optimizer_RNG_unchanged'] and h['network_state_unchanged'] and h['checkpoint_sha256']==r['checkpoint_sha256']
 l=loss['methods'][m];assert l['rows']==r['new_transitions'] and l['all_saved_arrays_exact_to_original_log'] and l['all_saved_scalar_stats_exact']
 p=pop['methods'][m];assert p['rows']==r['new_transitions'] and p['new_terminal_rows']==30 and p['checkpoint_sha256']==r['checkpoint_sha256'] and p['online_total_count_checked'] and p['online_new_terminal_growth_observed']
 pre=prefix['methods'][m];assert pre['rows']<=p['rows'] and 0<pre['new_terminal_rows']<=30
 for k in ['optimizer_prefix','transition_prefix']:
  e=pre[k]
  with Path(e['path']).open('rb') as f:data=f.read(e['bytes'])
  assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
 t=rd(T/f'{m}_REVIEW.json');assert t['checkpoint_sha256']==r['checkpoint_sha256'] and t['full_learner_optimizer_replay_rng_unchanged'] and t['saved_scalar_arithmetic_verified'] and sha(T/f'{m}_values.npz')==t['values_sha256']
 groups={}
 for name,g in t['groups'].items():
  a=g['complete95'];b=g['complete96'];assert a['rows']==b['rows'] and a['mask_counts']==b['mask_counts']
  u=[(y-my)-(x-mx) for x,mx,y,my in zip(a['all_row_sse'],a['masked_sse'],b['all_row_sse'],b['masked_sse'])]
  groups[name]=dict(rows=a['rows'],masked_sse95=a['total_masked_sse'],masked_sse96=b['total_masked_sse'],relative_change=b['total_masked_sse']/a['total_masked_sse']-1,masked_per_critic_delta=[y-x for x,y in zip(a['masked_sse'],b['masked_sse'])],all_row_per_critic_delta=[y-x for x,y in zip(a['all_row_sse'],b['all_row_sse'])],unmasked_per_critic_delta=u)
 methods[m]=dict(training=r,loss=l['stats'],terminal_population=p['final_population'],fixed95_terminal_groups=groups,fixed95_regression_rows=t['regression_rows'],fixed95_improved_rows=t['improved_rows'],known_terminal_rows=t['known_rows'],reward_change=comp['methods'][m]['mean_reward_delta'],task_gained=comp['methods'][m]['task_gained'],task_lost=comp['methods'][m]['task_lost'],strict_gained=comp['methods'][m]['strict_gained'],strict_lost=comp['methods'][m]['strict_lost'])
assert sum(x['terminal_population'] for x in methods.values())==8623
assert sum(x['fixed95_terminal_groups']['all']['rows'] for x in methods.values())==8533
put(D/'COMPLETE96_SCIENTIFIC_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,inputs=[dict(path=str(p),sha256=sha(p)) for p in checks],complete96=True,convergence_claim=False,health_acceptance_pending=True,physics_steps=0,optimizer_updates=0,scope='Authoritative complete96 input/array/scalar/plot checks, all90 training comparison, all8533 fixed95 terminal comparisons, every96 update total population and final masks, live prefix bound back to final logs. No online per-stratum tensor observation or independent generalization. Original94–96 fixed-window statistics remain a separate required check; no convergence claim.'))
print(json.dumps({m:dict(task=v['training']['task'],strict=v['training']['strict'],reward=v['training']['reward_mean'],loss=v['loss'],fixed95_terminal_relative_change=v['fixed95_terminal_groups']['all']['relative_change'],regressions=v['fixed95_regression_rows'],task_gained=v['task_gained'],task_lost=v['task_lost'],strict_gained=v['strict_gained'],strict_lost=v['strict_lost']) for m,v in methods.items()},indent=2))
