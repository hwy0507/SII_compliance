from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{54})
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runtime/parameter71_73_condition_churn_20261029_v1';p=O/'REVIEW.json';d=json.loads(p.read_text());errs=[]
for method,v in d['methods'].items():
 rows=v['all30'];assert len(rows)==30 and len({r['condition'] for r in rows})==30
 y=np.asarray([r['rewards'] for r in rows],dtype=np.float64);task=np.asarray([r['task'] for r in rows],dtype=bool);strict=np.asarray([r['strict'] for r in rows],dtype=bool)
 for cycle,col in [(71,0),(72,1),(73,2)]:
  ref=d['inputs'][f'{method}:{cycle}'];src=Path(ref['path']);assert hashlib.sha256(src.read_bytes()).hexdigest()==ref['sha256'];original={r['condition']:r for r in map(json.loads,src.read_text().splitlines())}
  assert set(original)=={r['condition'] for r in rows}
  for r in rows:
   e=original[r['condition']];assert (r['rewards'][col],r['task'][col],r['strict'][col])==(e['reward'],e['task_success'],e['strict_success'])
 for i,j,key in [(0,1,'71_to72'),(1,2,'72_to73'),(0,2,'71_to73')]:
  delta=y[:,j]-y[:,i];changed=(task[:,j]!=task[:,i])|(strict[:,j]!=strict[:,i]);r=v['edges'][key]
  calc=dict(mean_reward_delta=delta.mean(),changed_label_mean_contribution=delta[changed].sum()/30,unchanged_label_mean_contribution=delta[~changed].sum()/30,positive_delta_sum=delta[delta>0].sum(),negative_delta_sum=delta[delta<0].sum(),all30_absolute_delta_sum=np.abs(delta).sum())
  assert r['changed_label_count']==int(changed.sum());assert {c['condition'] for c in r['changed_labels']}=={rows[k]['condition'] for k in np.flatnonzero(changed)}
  for k,x in calc.items():assert math.isclose(float(x),r[k],abs_tol=1e-12,rel_tol=1e-12);errs.append(abs(float(x)-r[k]))
  if j==i+1:
   a,b=71+i,71+j;old=json.loads((B/f'runs/parameter_task_label_audit{b}_20261028_v1/COMPLETE{a}_{b}_SAVED_REVIEW.json').read_text());assert old['passed'];expected={c['condition'] for c in old['methods'][method]['changes'] if set(c['fields']) & {'task','strict'}};assert expected=={c['condition'] for c in r['changed_labels']}
out=dict(passed=True,time=time.time(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),review_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),all270_episode_rewards_and540_labels_exact=True,independent_numpy_arithmetic=True,adjacent_switch_sets_match_original_full_label_reviews=True,maximum_arithmetic_error=max(errs),new_physics=0,optimizer_updates=0,threshold_changed=False)
(O/'SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
