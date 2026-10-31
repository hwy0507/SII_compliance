"""Read saved actual90 startup bit weights/Adam; no updates or new physics."""
from pathlib import Path
import os,time,json,hashlib
os.sched_setaffinity(0,{12})
import torch
torch.set_num_threads(1)
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle90_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
startup=read(R/'startup/REVIEW.json');assert startup['passed'];result={}
for m,record in startup['methods'].items():
 p=R/'startup'/(m+'.pt');assert sha(p)==record['checkpoint_sha256'];ck=torch.load(p,map_location='cpu',weights_only=False,mmap=True);s=ck['learner'];dim=s['causal_external_penetration_violation_bit']['parent']['action_dimension']
 weights={}
 for name,v in s['agent'].items():
  if name.startswith(('ensemble.','ensemble_targets.')) and name.endswith('.q_net.0.weight'):
   assert v.shape[1]==52+dim and torch.isfinite(v).all();weights[name]=dict(bit_norm=float(torch.linalg.vector_norm(v[:,51])),history_norm=float(torch.linalg.vector_norm(v[:,50])),bit_nonzero=int(torch.count_nonzero(v[:,51])))
 assert len(weights)==10 and all(v['bit_nonzero']>0 for v in weights.values())
 moments=[]
 for pid,state in s['q_optimizer']['state'].items():
  v=state.get('exp_avg')
  if torch.is_tensor(v) and v.ndim==2 and v.shape[1]==52+dim:
   sq=state['exp_avg_sq'];assert torch.isfinite(v).all() and torch.isfinite(sq).all();moments.append(dict(parameter_id=pid,mean_norm=float(torch.linalg.vector_norm(v[:,51])),square_sum=float(sq[:,51].sum()),nonzero=int(torch.count_nonzero(v[:,51]))))
 assert len(moments)==5 and all(x['nonzero']>0 and x['square_sum']>0 for x in moments)
 result[m]=dict(checkpoint_sha256=record['checkpoint_sha256'],actual_new_updates=record['added_steps'],weights=weights,adam=moments)
 del ck,s
with (D/'ACTUAL_STARTUP_BIT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),source_sha256=sha(Path(__file__)),startup_review_sha256=sha(R/'startup/REVIEW.json'),methods=result,new_updates=0,new_physics=0,scope='Actual saved startup only: new bit online/target columns and Adam are nonzero and finite. Does not establish performance improvement or convergence.'),f,indent=2);f.write('\n')
print({m:v['actual_new_updates'] for m,v in result.items()})
