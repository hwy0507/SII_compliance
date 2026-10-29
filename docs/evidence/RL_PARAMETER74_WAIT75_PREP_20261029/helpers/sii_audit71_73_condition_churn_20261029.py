from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');W=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1';O=B/'runtime/parameter71_73_condition_churn_20261029_v1';O.mkdir(exist_ok=False)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
reg=read(W/'REGISTRATION.json');review=read(W/'REVIEW.json');assert read(W/'SAVED_ARITHMETIC_REVIEW.json')['passed'];methods={};inputs={}
for method in ['impedance','admittance','vmc']:
 maps={}
 for cycle in [71,72,73]:
  ref=reg['inputs'][f'{method}:{cycle}']['episodes'];p=Path(ref['path']);assert sha(p)==ref['sha256'];inputs[f'{method}:{cycle}']=ref
  rows=[json.loads(l) for l in p.read_text().splitlines()];assert len(rows)==30;maps[cycle]={r['condition']:r for r in rows};assert len(maps[cycle])==30
 ids=sorted(maps[71]);assert all(sorted(m)==ids for m in maps.values())
 rows=[]
 for cid in ids:
  es=[maps[c][cid] for c in [71,72,73]];assert len({r['category'] for r in es})==1
  rows.append(dict(condition=cid,category=es[0]['category'],rewards=[e['reward'] for e in es],task=[e['task_success'] for e in es],strict=[e['strict_success'] for e in es],aborts=[e['abort_reason'] for e in es]))
 def summary(i,j):
  pairs=[dict(condition=r['condition'],delta=r['rewards'][j]-r['rewards'][i],task_changed=r['task'][j]!=r['task'][i],strict_changed=r['strict'][j]!=r['strict'][i],before_task=r['task'][i],after_task=r['task'][j],before_strict=r['strict'][i],after_strict=r['strict'][j]) for r in rows]
  changed=[p for p in pairs if p['task_changed'] or p['strict_changed']];same=[p for p in pairs if not(p['task_changed'] or p['strict_changed'])]
  values=[p['delta'] for p in pairs];delta=math.fsum(values)/30
  expected=review['methods'][method]['cycles'][j]['reward_mean']-review['methods'][method]['cycles'][i]['reward_mean'];assert math.isclose(delta,expected,abs_tol=1e-12,rel_tol=1e-12)
  ch=math.fsum(p['delta'] for p in changed)/30;no=math.fsum(p['delta'] for p in same)/30;assert math.isclose(ch+no,delta,abs_tol=1e-12)
  return dict(mean_reward_delta=delta,changed_label_count=len(changed),task_changed_count=sum(p['task_changed'] for p in pairs),strict_changed_count=sum(p['strict_changed'] for p in pairs),changed_label_mean_contribution=ch,unchanged_label_mean_contribution=no,positive_delta_sum=math.fsum(v for v in values if v>0),negative_delta_sum=math.fsum(v for v in values if v<0),all30_absolute_delta_sum=math.fsum(abs(v) for v in values),changed_labels=changed)
 reverted=[r['condition'] for r in rows if (r['task'][0],r['strict'][0])==(r['task'][2],r['strict'][2]) and (r['task'][0],r['strict'][0])!=(r['task'][1],r['strict'][1])]
 methods[method]=dict(all30=rows,edges={'71_to72':summary(0,1),'72_to73':summary(1,2),'71_to73':summary(0,2)},intermediate_label_reversions=reverted)
for ref in inputs.values():assert sha(Path(ref['path']))==ref['sha256']
write(O/'REVIEW.json',dict(passed=True,time=time.time(),source_sha256=sha(Path(__file__)),registered_after_results=True,inputs=inputs,original_window_review_sha256=sha(W/'REVIEW.json'),methods=methods,new_physics=0,optimizer_updates=0,convergence_claim=False,limitation='Descriptive arithmetic on all original270 saved training episodes and both task/strict labels. Not a new statistical gate, causal attribution, re-simulation, independent-seed study or frozen-policy evaluation; original5percent verdict and windows unchanged.'))
for m,v in methods.items():print(m,json.dumps({k:v for k,v in v.items() if k!='all30'},indent=2))
