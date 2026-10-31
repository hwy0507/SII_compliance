from pathlib import Path
import json,time,hashlib,math
D=Path(__file__).resolve().parent;B=D.parents[1]
R=B/'runs/parameter_census_cycle94_review_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';C=B/'runtime/census94_comparison_20261031_v1'
rd=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def inspect(root,names,notes):
 put(root/'PLOT_INSPECTION.json',dict(actual_visual_inspection=True,time=time.time(),plots=[dict(path=str(root/n),sha256=sha(root/n),inspected=True) for n in names],notes=notes))
inspect(R,['loss/loss94.png','health/training_diagnostics.png'],'Actually viewed all9 loss panels and six health panels during this continuing goal turn before context compaction. I original early high spikes decline but recurring late spikes remain; smoother conditional estimate does not replace original sampled health. I actor increases; A late isolated original spikes and actor rise; V bounded original loss but actor drift. Entropy near targets, I alpha declines. Health4096 is unprojected fixed-min-pair diagnostic, not the projected/I-min/A-V-mean training target. Health top-right title clipped, data visible. No convergence claim.')
inspect(C,['training93_94_all90.png'],'Actually viewed during this continuing turn before compaction. All90 descriptive comparison: reward gains concentrated in I long0000 Task/Strict gain and V short0600 Strict gain. A short0900 gain and short0200 loss cancel in counts. Estimator changes at94, not causal attribution or fixed94–96 stability evidence.')
inspect(T,['fixed93_terminal_93_94.png'],'Actually viewed after compaction. All nine panels: all five masked critic SSE improve in each method. I large old spike residual falls strongly; A all-row critic0 SSE rises. All-row plots mix masked and unmasked values; residual unmasked regressions and per-row regressions retained in report. Plot shows all8353 retained93 terminals, not independent generalization or new94-only performance.')
checks=[R/'REVIEW.json',D/'FULL_LOSS_SAVED_REVIEW.json',C/'CACHE_POPULATION_FULL_REVIEW.json',C/'INTERPRETATION.json',C/'INTERPRETATION_SAVED_REVIEW.json',C/'CHANGED_CASES_REVIEW.json',T/'REVIEW.json',D/'WATCH_REVIEW.json',D/'LIVE_GROWTH_BINDING_REVIEW.json']
for p in checks:assert rd(p)['passed'],str(p)
review=rd(R/'REVIEW.json');health=rd(R/'health/DIAGNOSIS.json');loss=rd(D/'FULL_LOSS_SAVED_REVIEW.json');pop=rd(C/'CACHE_POPULATION_FULL_REVIEW.json');comp=rd(C/'INTERPRETATION.json');snap=rd(D/'TRAINING_FINISH_SNAPSHOT.json')
methods={}
for m,r in review['methods'].items():
 assert r['new_transitions']==41250 and r['conditions']==r['full_horizon_count']==30 and not r['aborts'] and r['max_reward_reconstruction_error']==0
 for k in ['retained_replay_all_old_fields_exact','retained_history_features_exact','retained_violation_features_exact','new_current_next52_and_raw_mixed_action_exact','optimizer_and_network_finite']:assert r[k]
 h=health['methods'][m];assert h['full_learner_optimizer_RNG_unchanged'] and h['network_state_unchanged'] and h['checkpoint_sha256']==r['checkpoint_sha256']
 l=loss['methods'][m];assert l['rows']==41250 and l['all_saved_arrays_exact_to_original_log'] and l['all_saved_scalar_stats_exact']
 p=pop['methods'][m];assert p['rows']==41250 and p['new_terminal_rows']==30 and p['checkpoint_sha256']==r['checkpoint_sha256'] and p['online_total_count_checked'] and p['online_new_terminal_growth_observed']
 t=rd(T/f'{m}_REVIEW.json');assert t['checkpoint_sha256']==r['checkpoint_sha256'] and t['full_learner_optimizer_replay_rng_unchanged'] and t['saved_scalar_arithmetic_verified'] and sha(T/f'{m}_values.npz')==t['values_sha256']
 groups={}
 for name,g in t['groups'].items():
  a=g['complete93'];b=g['complete94'];assert a['rows']==b['rows'] and a['mask_counts']==b['mask_counts']
  u=[(y-my)-(x-mx) for x,mx,y,my in zip(a['all_row_sse'],a['masked_sse'],b['all_row_sse'],b['masked_sse'])]
  groups[name]=dict(rows=a['rows'],masked_sse93=a['total_masked_sse'],masked_sse94=b['total_masked_sse'],relative_change= b['total_masked_sse']/a['total_masked_sse']-1,masked_per_critic_delta=[y-x for x,y in zip(a['masked_sse'],b['masked_sse'])],all_row_per_critic_delta=[y-x for x,y in zip(a['all_row_sse'],b['all_row_sse'])],unmasked_per_critic_delta=u)
 methods[m]=dict(training=r,loss=l['stats'],terminal_population=p['final_population'],fixed93_terminal_groups=groups,fixed93_regression_rows=t['regression_rows'],fixed93_improved_rows=t['improved_rows'],known_terminal_rows=t['known_rows'],reward_change=comp['methods'][m]['mean_reward_delta'],task_gained=comp['methods'][m]['task_gained'],task_lost=comp['methods'][m]['task_lost'],strict_gained=comp['methods'][m]['strict_gained'],strict_lost=comp['methods'][m]['strict_lost'])
assert sum(x['terminal_population'] for x in methods.values())==8443
assert sum(x['fixed93_terminal_groups']['all']['rows'] for x in methods.values())==8353
put(D/'COMPLETE94_SCIENTIFIC_REVIEW.json',dict(passed=True,time=time.time(),methods=methods,inputs=[dict(path=str(p),sha256=sha(p)) for p in checks]+[dict(path=str(p/'PLOT_INSPECTION.json'),sha256=sha(p/'PLOT_INSPECTION.json')) for p in [R,T,C]],complete94=True,convergence_claim=False,health_pass=False,physics_steps=0,optimizer_updates=0,scope='Consolidates authoritative full94 reviews and saved scalar verification. Cache proof covers total population each update and all full-checkpoint terminal masks; online per-stratum tensor values not logged. Historical terminal comparison uses all8353 fixed93 inputs with original masks; not independent generalization. Original online losses retain spikes, actor drifts,94–96 incomplete.'))
put(D/'NEXT_FINITE_DECISION.json',dict(time=time.time(),review=dict(path=str(D/'COMPLETE94_SCIENTIFIC_REVIEW.json'),sha256=sha(D/'COMPLETE94_SCIENTIFIC_REVIEW.json')),decision='Proceed to prepare separately registered single cycle95 from exact archived full94, keeping census estimator and all scientific parameters unchanged; no automatic96 and no Direct34.',reason='All original full states finite; all90 complete without abort; original loss means down and fixed93 masked terminal SSE strongly lower for all methods. Remaining spikes, actor drift, A short0200 regression and unmasked regressions require continued observation within fixed94–96 intent, not a convergence declaration.',max_new_transitions_per_method=41250,full_conditions_per_method=30,horizon_seconds=55,parent_cycle=94,next_cycle=95,required_before_launch=['census-aware exact full94 learner/Adam/replay/RNG restore and both architecture/capacity markers','independent finite registration and source hashes','resource and no-duplicate check','full-state restore tests and actual startup review','archive and full original-loss health review'],cycle95_registered=False,cycle95_launched=False,goal='active',guard_remains_after_science=True))
print({m:(v['terminal_population'],v['fixed93_terminal_groups']['all']['relative_change']) for m,v in methods.items()})
