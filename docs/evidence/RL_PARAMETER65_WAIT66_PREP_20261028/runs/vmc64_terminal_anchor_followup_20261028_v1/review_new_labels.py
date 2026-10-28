"""Independent saved64 terminal scalar and original all30 label verification."""
from pathlib import Path
import json,math,hashlib,time,os
os.sched_setaffinity(0,{54})
import numpy as np
p=Path(__file__).parent;b=p.parents[1]
def read(x):return json.loads(x.read_text())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def near(a,c):assert math.isclose(a,c,rel_tol=1e-12,abs_tol=1e-12),(a,c)
r=read(p/'NEW_TERMINALS_REVIEW.json');assert r['passed'] and sha(p/'values.npz')==r['values_sha256']
lp=b/'runs/parameter_task_label_audit64_20261028_v1/COMPLETE63_64.json';labels=read(lp);assert labels['passed']
bycondition={x['condition']:next(c for c in x['cases'] if c['cycle']==64) for x in labels['methods']['vmc']['all30']}
ep=b/'runs/parameter_capacity_pool30_cycle64_20261026_v1/vmc/train/episodes.jsonl';assert sha(ep)==r['episodes_sha256']
episodes={x['condition']:x for x in map(json.loads,ep.read_text().splitlines())};rows=[]
assert len(r['all30'])==30 and set(episodes)==set(bycondition)=={x['condition'] for x in r['all30']}
with np.load(p/'values.npz',allow_pickle=False) as v:
 assert len(v['indices'])==1944 and set(map(int,v['indices'][1914:]))=={x['replay_index'] for x in r['all30']}
 totals=[]
 for x in r['all30']:
  k=int(np.flatnonzero(v['indices']==x['replay_index'])[0]);assert 1914<=k<1944
  e=episodes[x['condition']];c=bycondition[x['condition']]
  assert x['replay_index']==e['total_steps']-1 and x['episode_reward']==e['reward']==c['reward']
  assert x['task']==e['task_success']==c['task'] and x['strict']==e['strict_success']==c['strict']
  assert x['q']==list(map(float,v['q_after'][:,k])) and x['masks']==list(map(float,v['masks'][:,k])) and x['terminal_reward']==float(v['rewards'][k])
  parts=[float(v['masks'][h,k])*(float(v['q_after'][h,k])-float(v['rewards'][k]))**2 for h in range(5)]
  assert parts==x['per_critic_sse'];near(math.fsum(parts),x['sse'])
  con=math.fsum(parts[h]*128/float(v['denominator'][h]) for h in range(5));near(con,x['contribution']);totals.append(con)
  for key in ['rollout','model','evaluator']:assert sha(Path(c[key]['path']))==c[key]['sha256']
  roll=read(Path(c['rollout']['path']));physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002
  assert physical==c['physical_valid']==roll['physical_valid'];assert bool(roll['task_success'] and physical)==c['strict']
  assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in Path(c['evaluator']['path']).read_text()
  near(1000*roll['stats']['max_external_penetration_m'],c['penetration_mm'])
  rows.append(dict(condition=x['condition'],replay_index=x['replay_index'],contribution=con,task=c['task'],strict=c['strict'],physical_valid=physical,penetration_mm=c['penetration_mm'],rollout=c['rollout']))
 near(math.fsum(totals),r['new30_contribution']);near(max(totals)/math.fsum(totals),r['largest_fraction'])
assert [x['contribution'] for x in rows]==sorted(totals,reverse=True)
out=p/'NEW_TERMINALS_LABEL_REVIEW.json';assert not out.exists();out.write_text(json.dumps(dict(time=time.time(),passed=True,all30=rows,independent_scalar_recomputation=True,all30_original_labels_verified=True,labels_sha256=sha(lp),values_sha256=sha(p/'values.npz'),source_sha256=sha(Path(__file__)),new_network_forward=0,new_physics=0,optimizer_updates=0,causal_claim=False),indent=2)+'\n');print(json.dumps(rows[:3],indent=2))
