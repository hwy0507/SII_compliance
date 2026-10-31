from pathlib import Path
import sys,copy,json,time,hashlib,os,math,textwrap
os.sched_setaffinity(0,{54});D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/parameter_census94_96_reward_stability_20261031_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1';sys.path.insert(0,str(O))
from binding_rules import locked,protocol,validate_registration,read,sha,ref
from bind_inputs import build
import numpy as np
plan=locked(O);original=read(S/'REGISTRATION.json');report=read(S/'REVIEW.json');assert report['passed']
old=(S/'audit.py').read_text();new=(O/'audit.py').read_text()
def kernel(text):return textwrap.dedent(text[text.index('        ids = sorted(maps[0])'):text.index('        axes[mi, 0].plot(')])
assert kernel(old)==kernel(new).replace('paired94_to96_mean_delta','paired90_to92_mean_delta')
results={}
for mi,m in enumerate(['impedance','admittance','vmc']):
 maps=[]
 for c in [90,91,92]:
  item=original['inputs'][f'{m}:{c}']['episodes'];assert sha(item['path'])==item['sha256'];es=[json.loads(l) for l in Path(item['path']).read_text().splitlines()];assert len(es)==30 and all(e['cycle']==c for e in es);maps.append({e['condition']:e for e in es})
 ns=dict(np=np,maps=maps,reg=original,mi=mi,method=m,summaries=report['methods'][m]['cycles'],results={});exec(kernel(new),ns);computed=ns['results'][m];normalized={k.replace('paired94_to96_mean_delta','paired90_to92_mean_delta'):v for k,v in computed.items()};assert normalized==report['methods'][m]
 # Independently recompute each bootstrap mean by scalar fsum on the actual old90–92 data.
 matrix=ns['matrix'];draws=ns['draws'];deltas=[math.fsum(float(matrix[2,j]) for j in draw)/30-math.fsum(float(matrix[0,j]) for j in draw)/30 for draw in draws]
 ci=np.quantile(deltas,[.025,.975]);np.testing.assert_allclose(ci,computed['bootstrap_condition_sensitivity95_delta'],rtol=1e-12,atol=1e-12);np.testing.assert_allclose(ci/2,computed['bootstrap_condition_sensitivity95_slope'],rtol=1e-12,atol=1e-12)
 p=read(plan['protocol94'][m]['path']);protocol(p,m,94,plan);rejected=[]
 for case in ['controller','new_cycle','parent_cycle','cycles','budget','automatic','census_marker','health_metric','physics','batch','actor_lr']:
  bad=copy.deepcopy(p);st=bad['post_interruption_continuation']
  if case=='controller':st['controller']='other'
  elif case=='new_cycle':st['new_cycle']=95
  elif case=='parent_cycle':st['parent_cycle']=92
  elif case=='cycles':st['new_cycles']=2
  elif case=='budget':st['maximum_new_actions']=41251
  elif case=='automatic':st['automatic_followup']=True
  elif case=='census_marker':bad['conditional_terminal_amendment']['marker']['terminal_weight']=64
  elif case=='health_metric':bad['conditional_terminal_amendment']['health_metric']='agent_train/q_loss'
  elif case=='physics':bad['physics_dt_s']=.0001
  elif case=='batch':bad['learner_batch_size']=32768
  elif case=='actor_lr':bad['completed_stage_continuation']['actor_learning_rate_factor']=.5
  try:protocol(bad,m,94,plan)
  except ValueError:rejected.append(case)
  else:raise AssertionError('Accepted corrupt '+case)
 results[m]=dict(actual_historical_cycles=[90,91,92],statistical_kernel_exact_except_output_key=True,all_original_saved_results_reproduced_exact=True,independent_scalar_bootstrap_delta95=ci.tolist(),original_five_percent_passed=computed['descriptive_five_percent_check'],actual94_protocol_passed=True,negative_cases=rejected)
try:validate_registration(O,build({}))
except ValueError as e:assert str(e)=='All nine complete input groups required'
else:raise AssertionError('Accepted empty fullwindow inputs')
try:read(B/'runs/parameter_census_cycle94_review_20261031_v1/FINISHED.json')
except FileNotFoundError:missing94=True
else:raise AssertionError('Complete94 unexpectedly ready, inspect actual result')
assert not (O/'REGISTRATION.json').exists() and not (O/'REVIEW.json').exists()
r=dict(passed=True,time=time.time(),methods=results,negative_count=33,missing_full94_verified=missing94,empty_fullwindow_binding_rejected=True,source_lock=ref(O/'SOURCE_LOCK.json'),scope='Arithmetic compatibility on real historical90–92 ONLY, preserving I/A failures and V reward-only pass. No94–96 statistics, no complete94 binding or95/96 registration. Actual94 protocol and33 corruptions checked; all future data must be complete and bound.',new_physics=0,optimizer_updates=0)
with (D/'PREPARATION_REVIEW.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({m:dict(historical_five_percent=x['original_five_percent_passed'],negative_cases=len(x['negative_cases'])) for m,x in results.items()}))
