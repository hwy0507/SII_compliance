from pathlib import Path
import json,math,time,hashlib
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census100_prefix_terminal_probe_20261031_v1';read=lambda p:json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
r=read(O/'REVIEW.json');assert r['passed'];methods={}
for m,x in r['methods'].items():
 p=O/(m+'_values.npz');assert ref(p)['sha256']==x['values']['sha256']
 with np.load(p) as z:
  old=[];new=[]
  for j in range(len(z['indices'])):
   target=float(z['rewards'][j]);mask=z['masks'][j];old.append(math.fsum((float(v)-target)**2*float(w) for v,w in zip(z['initial_prediction'][j],mask)));new.append(math.fsum((float(v)-target)**2*float(w) for v,w in zip(z['prefix_prediction'][j],mask)))
  assert math.isclose(math.fsum(old),x['old']['total_masked_sse'],abs_tol=1e-8) and math.isclose(math.fsum(new),x['new']['total_masked_sse'],abs_tol=1e-8)
  assert sum(b>a for a,b in zip(old,new))==x['regressions'] and sum(b<a for a,b in zip(old,new))==x['improvements']
  rows=[]
  for j in sorted(range(len(old)),key=lambda j:new[j]-old[j],reverse=True)[:20]:
   rows.append(dict(index=int(z['indices'][j]),step=int(z['indices'][j])+1,cycle=int(z['cycles'][j]),condition=str(z['conditions'][j]),reward=float(z['rewards'][j]),mask=z['masks'][j].tolist(),old_prediction=z['initial_prediction'][j].tolist(),new_prediction=z['prefix_prediction'][j].tolist(),old_sse=old[j],new_sse=new[j],delta=new[j]-old[j]))
  methods[m]=dict(values=ref(p),top20_regressions=rows,all_rows_scalar_recomputed=True)
result=dict(passed=True,time=time.time(),methods=methods,scope='Independent all8893 saved row scalar recomputation and explicit20 largest regressions per method. No causal attribution or convergence claim.',physics_steps=0,optimizer_updates=0)
with (O/'REGRESSION_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({m:v['top20_regressions'][0] for m,v in methods.items()},indent=2))
