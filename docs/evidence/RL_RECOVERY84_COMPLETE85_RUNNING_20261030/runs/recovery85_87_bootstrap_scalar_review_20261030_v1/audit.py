from pathlib import Path
import json,hashlib,math,time,os
import numpy as np
D=Path(__file__).parent;os.sched_setaffinity(0,{54})
def read(p):return json.loads(Path(p).read_text())
def ref(p):
 with Path(p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),(a,b)
def quantile(x,p):
 y=sorted(x);a=(len(y)-1)*p;i=int(a);return y[i]+(a-i)*(y[min(i+1,len(y)-1)]-y[i])
plan=read(D/'PLAN.json')
for r in plan['inputs']:assert ref(r['path'])==r
result={}
for window,root in plan['windows'].items():
 root=Path(root);reg=read(root/'REGISTRATION.json');report=read(root/'REVIEW.json');saved=read(root/'SAVED_ARITHMETIC_REVIEW.json');assert report['passed'] and saved['passed']
 assert reg['bootstrap_replicates']==5000 and reg['seed']==2026102858 and reg['relative_limit']==.05 and reg['near_zero_guard']==1
 methods={}
 for mi,m in enumerate(['impedance','admittance','vmc']):
  maps=[]
  for cycle in reg['cycles']:
   r=reg['inputs'][f'{m}:{cycle}']['episodes'];assert ref(r['path'])==r
   rows=[json.loads(l) for l in Path(r['path']).read_text().splitlines() if json.loads(l)['cycle']==cycle]
   assert len(rows)==30 and len({r['condition'] for r in rows})==30;maps.append({r['condition']:r for r in rows})
  ids=sorted(maps[0]);assert all(sorted(v)==ids for v in maps)
  categories=sorted({maps[0][k]['category'] for k in ids});groups=[[i for i,k in enumerate(ids) if maps[0][k]['category']==c] for c in categories];assert [len(v) for v in groups]==[10,10,10]
  assert all(maps[j][k]['category']==maps[0][k]['category'] for k in ids for j in [1,2])
  rng=np.random.default_rng(reg['seed']+mi);draws=[]
  for positions in groups:
   positions=np.asarray(positions);draws.append(positions[rng.integers(0,10,size=(5000,10))])
  draws=np.concatenate(draws,axis=1)
  # Separate RNG API consistency check; estimator and quantiles below do not call original audit or vectorized mean/quantile.
  check=np.random.default_rng(reg['seed']+mi);oracle=np.concatenate([check.choice(v,size=(5000,10),replace=True) for v in groups],axis=1);assert np.array_equal(draws,oracle)
  means=[];deltas=[];slopes=[]
  for draw in draws:
   mu=[math.fsum(float(v[ids[int(i)]]['reward']) for i in draw)/30 for v in maps];means.append(mu);deltas.append(mu[-1]-mu[0]);slopes.append((mu[-1]-mu[0])/2)
  intervals={}
  for key,values in [('delta',deltas),('slope',slopes)]:
   ci=[quantile(values,p) for p in [.025,.975]];existing=report['methods'][m]['bootstrap_condition_sensitivity95_'+key]
   for a,b in zip(ci,existing):close(a,b)
   intervals[key]=ci
  p=D/f'{window}_{m}_draws_values.npz';np.savez_compressed(p,draws=draws,means=np.asarray(means),delta=np.asarray(deltas),slope=np.asarray(slopes))
  with np.load(p,allow_pickle=False) as z:
   assert np.array_equal(z['draws'],draws) and np.array_equal(z['means'],means) and np.array_equal(z['delta'],deltas) and np.array_equal(z['slope'],slopes)
   for key in ['delta','slope']:
    for a,b in zip([quantile(z[key].tolist(),p) for p in [.025,.975]],intervals[key]):close(a,b)
  methods[m]=dict(condition_order=ids,categories=categories,replicates=5000,all5000_means_computed_with_math_fsum=True,independent_sorted_linear_quantile=True,original_intervals_match=True,intervals95=intervals,saved_arrays=ref(p),original_descriptive_five_percent_check=report['methods'][m]['descriptive_five_percent_check'],original_near_zero_guard=report['methods'][m]['near_zero_guard_triggered'],actual_episode_lengths=[[maps[j][k]['steps'] for k in ids] for j in range(3)])
 result[window]=dict(methods=methods,registration=ref(root/'REGISTRATION.json'),original_review=ref(root/'REVIEW.json'),original_saved_review=ref(root/'SAVED_ARITHMETIC_REVIEW.json'))
for r in plan['inputs']:assert ref(r['path'])==r
out=dict(passed=True,time=time.time(),windows=result,new_network_forward=0,new_physics=0,optimizer_updates=0,original_reports_unchanged=True,convergence_claim=False,limitation=plan['limitation'])
with (D/'REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for w,r in result.items():
 for m,v in r['methods'].items():print(w,m,v['intervals95'])
