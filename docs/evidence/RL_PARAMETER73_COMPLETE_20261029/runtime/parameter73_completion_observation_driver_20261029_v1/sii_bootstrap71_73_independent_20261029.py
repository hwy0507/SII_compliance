from pathlib import Path
import json,math,hashlib,time,os
os.sched_setaffinity(0,{54})
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
P=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
O=B/'runtime/parameter71_73_bootstrap_independent_20261029_v1';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
reg=read(P/'REGISTRATION.json');old=read(P/'REVIEW.json');plan=read(P/'PLAN.json')
assert reg['cycles']==[71,72,73] and reg['seed']==2026102855 and reg['bootstrap_replicates']==5000
assert reg['relative_limit']==.05 and reg['near_zero_guard']==1
inputs={n:dict(path=str(P/n),sha256=sha(P/n)) for n in ['PLAN.json','REGISTRATION.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json']}
for key,group in reg['inputs'].items():
 ref=group['episodes'];assert sha(Path(ref['path']))==ref['sha256'];inputs[key]=ref
write(O/'REGISTRATION.json',dict(time=time.time(),inputs=inputs,source_sha256=sha(Path(__file__)),registered_after_results_available=True,cycles=[71,72,73],seed=reg['seed'],replicates=5000,new_physics=0,optimizer_updates=0,old_outputs_unchanged=True))
def quantile(vals,p):
 ordered=sorted(vals);h=(len(ordered)-1)*p;i=math.floor(h);fraction=h-i
 return ordered[i]+fraction*(ordered[min(i+1,len(ordered)-1)]-ordered[i])
results={}
for mi,method in enumerate(['impedance','admittance','vmc']):
 maps=[]
 for cycle in [71,72,73]:
  rows=[json.loads(l) for l in Path(reg['inputs'][f'{method}:{cycle}']['episodes']['path']).read_text().splitlines()]
  assert len(rows)==30;maps.append({r['condition']:r for r in rows})
 ids=sorted(maps[0]);assert all(sorted(m)==ids for m in maps)
 for k in ids:assert len({m[k]['category'] for m in maps})==1
 categories=sorted({maps[0][k]['category'] for k in ids})
 positions=[[i for i,k in enumerate(ids) if maps[0][k]['category']==c] for c in categories]
 assert list(map(len,positions))==[10,10,10]
 # Same registered RNG stream; independent integer-index construction and scalar means.
 rng=np.random.default_rng(reg['seed']+mi)
 blocks=[rng.integers(0,len(v),size=(5000,10)) for v in positions]
 draws=[[positions[c][int(blocks[c][r,j])] for c in range(3) for j in range(10)] for r in range(5000)]
 deltas=[]
 for selected in draws:
  first=math.fsum(maps[0][ids[i]]['reward'] for i in selected)/30
  last=math.fsum(maps[2][ids[i]]['reward'] for i in selected)/30
  deltas.append(last-first)
 intervals=[quantile(deltas,p) for p in [.025,.975]]
 slopes=[quantile([d/2 for d in deltas],p) for p in [.025,.975]]
 expected=old['methods'][method];errors=[]
 for actual,saved in [(intervals,expected['bootstrap_condition_sensitivity95_delta']),(slopes,expected['bootstrap_condition_sensitivity95_slope'])]:
  for a,b in zip(actual,saved):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(method,a,b);errors.append(abs(a-b))
 out=O/(method+'_bootstrap.json');write(out,dict(draws=draws,delta=deltas,slope=[d/2 for d in deltas]))
 reread=read(out);assert reread['draws']==draws and reread['delta']==deltas
 results[method]=dict(seed=reg['seed']+mi,categories=categories,stratum_sizes=[10,10,10],replicates=5000,delta_interval=intervals,slope_interval=slopes,maximum_saved_interval_difference=max(errors),sample_sha256=sha(out),includes_zero=intervals[0]<=0<=intervals[1])
for ref in inputs.values():assert sha(Path(ref['path']))==ref['sha256']
write(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,source_sha256=sha(Path(__file__)),old_inputs_and_outputs_unchanged=True,new_physics=0,optimizer_updates=0,convergence_claim=False,limitation='Independent recomputation of existing stratified condition-composition sensitivity intervals; same registered seed and5000 draws, not independent training seeds or frozen-policy evaluation. Does not alter original5percent/nearzero check or old conclusions.'))
print(json.dumps(results,indent=2))
