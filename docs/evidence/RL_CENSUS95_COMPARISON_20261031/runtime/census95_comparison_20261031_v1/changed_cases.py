from pathlib import Path
import json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1]
read=lambda p:json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
r=read(D/'INTERPRETATION.json');assert r['passed'];cases=[]
for m,v in r['methods'].items():
 for x in v['rows']:
  if not (x['task_change'] or x['strict_change']):continue
  pair={}
  for c in (94,95):
   run={94:'parameter_census_cycle94_20261031_v1',95:'parameter_census_cycle95_20261031_v1'}[c];p=B/'runs'/run/m/f'train/cycle_{c:05d}'/x['condition']/'rollout.json';s=read(p)
   assert s['task_success']==x['task'+str(c)] and s['strict_success']==x['strict'+str(c)] and s['abort_reason']==x['abort'+str(c)] and s['final_task_stage']==x['stage'+str(c)]
   pair[str(c)]=dict(source=ref(p),task=s['task_success'],strict=s['strict_success'],abort=s['abort_reason'],stage=s['final_task_stage'],full_horizon=s['full_task_horizon_completed'],external_peak_mm=s['stats']['max_external_penetration_m']*1000,global_peak_mm=s['stats']['max_penetration_m']*1000,worst_external_pair=s['stats']['worst_external_pair'],model_sha256=s['model_sha256'])
  assert pair['94']['model_sha256']==pair['95']['model_sha256'];cases.append(dict(method=m,condition=x['condition'],pair=pair))
assert len(cases)==sum(bool(x['task_change'] or x['strict_change']) for v in r['methods'].values() for x in v['rows'])
result=dict(passed=True,time=time.time(),cases=cases,scope='All condition/method pairs with changed Task or Strict labels, bound to saved rollout summaries. No independent dynamics replay or causal attribution.',physics_steps=0,optimizer_updates=0)
with (D/'CHANGED_CASES_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(cases,indent=2))
