"""Independent scalar means/quantile interpolation for the fixed original bootstrap."""
from pathlib import Path
import json,hashlib,math,time,os
import numpy as np
os.sched_setaffinity(0,{54})
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runs/parameter_census97_99_reward_stability_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def quantile(values,p):
 x=sorted(values);position=(len(x)-1)*p;lo=math.floor(position);hi=math.ceil(position)
 return x[lo]+(position-lo)*(x[hi]-x[lo])
reg=read(W/'REGISTRATION.json');review=read(W/'REVIEW.json');assert review['passed']
assert reg['cycles']==[97,98,99] and reg['seed']==2026102861 and reg['bootstrap_replicates']==5000
results={}
for mi,m in enumerate(['impedance','admittance','vmc']):
 maps=[]
 for c in [97,98,99]:
  r=reg['inputs'][f'{m}:{c}']['episodes'];assert sha(Path(r['path']))==r['sha256']
  es=[json.loads(x) for x in Path(r['path']).read_text().splitlines()];assert len(es)==30
  maps.append({e['condition']:e for e in es})
 ids=sorted(maps[0]);groups=[[i for i,k in enumerate(ids) if maps[0][k]['category']==cat] for cat in sorted({e['category'] for e in maps[0].values()})];assert list(map(len,groups))==[10,10,10]
 rng=np.random.default_rng(reg['seed']+mi);draws=np.concatenate([rng.choice(g,size=(5000,10),replace=True) for g in groups],axis=1)
 delta=[]
 for draw in draws:
  before=math.fsum(maps[0][ids[int(i)]]['reward'] for i in draw)/30
  after=math.fsum(maps[2][ids[int(i)]]['reward'] for i in draw)/30
  delta.append(after-before)
 intervals={key:[quantile(values,p) for p in [.025,.975]] for key,values in [('bootstrap_condition_sensitivity95_delta',delta),('bootstrap_condition_sensitivity95_slope',[x/2 for x in delta])]}
 for key,values in intervals.items():
  assert all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12) for a,b in zip(values,review['methods'][m][key]))
 results[m]=intervals
with (D/'WINDOW_BOOTSTRAP_SCALAR_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,original_registration_sha256=sha(W/'REGISTRATION.json'),original_report_sha256=sha(W/'REVIEW.json'),replicates=5000,scalar_mean_and_linear_quantile_checked=True,new_physics=0,optimizer_updates=0,scope='Independent scalar arithmetic on identical originally registered bootstrap draws; condition-composition sensitivity only, not independent training seeds.'),f,indent=2);f.write('\n')
print(json.dumps(results,indent=2))
