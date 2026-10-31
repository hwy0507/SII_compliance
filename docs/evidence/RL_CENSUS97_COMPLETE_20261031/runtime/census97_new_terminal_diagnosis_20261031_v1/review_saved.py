from pathlib import Path
import json,math,time
import numpy as np
b=Path(__file__).resolve().parents[2];o=b/'runs/census97_new_terminal_diagnosis_20261031_v1';d=json.loads((o/'DIAGNOSIS.json').read_text());out={}
for m,r in d['methods'].items():
 with np.load(o/'reference97'/(m+'_values.npz')) as z:
  idx={int(i):j for j,i in enumerate(z['indices'])};tot=0.;all5=0.
  for x in r['all30_new_terminal_rows']:
   j=idx[x['replay_index']];assert z['cycles'][j]==97 and z['conditions'][j]==x['condition'];q=z['initial_prediction'][j];rw=float(z['rewards'][j]);mask=z['masks'][j]
   terms=[(float(v)-rw)**2 for v in q];s=math.fsum(v*float(w) for v,w in zip(terms,mask));assert math.isclose(s,x['masked_sse'],rel_tol=1e-13,abs_tol=1e-10);assert math.isclose(math.fsum(terms),x['all5_sse'],rel_tol=1e-13,abs_tol=1e-10);tot+=s;all5+=math.fsum(terms)
  assert math.isclose(tot,r['total_new97_masked_sse'],rel_tol=1e-13,abs_tol=1e-10)
  short=r['short0600'];out[m]=dict(new97_rows=30,masked_sse=tot,all5_sse=all5,short0600_fraction_of_new_masked=short['masked_sse']/tot,original_masks_preserved=True)
p=o/'SAVED_ARITHMETIC_REVIEW.json'
with p.open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=out,physics_steps=0,optimizer_updates=0),f,indent=2);f.write('\n')
print(json.dumps(out))
