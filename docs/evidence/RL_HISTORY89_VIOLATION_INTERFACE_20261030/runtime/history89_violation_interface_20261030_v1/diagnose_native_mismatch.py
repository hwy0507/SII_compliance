from pathlib import Path
import os,sys,json,time,hashlib,gc
D=Path(__file__).resolve().parent;B=D.parents[1];os.sched_setaffinity(0,{12});os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
plan=json.loads((D/'PLAN.json').read_text());sys.path[:0]=[str(D),plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np,torch
from published_compliance_learner_20261025 import PublishedLearner,OBSERVATION_SCALE
from published_pair_reduction_learner_20261026 import pair_class
from persisted_history_critic import history_class
from persisted_violation_critic import violation_class
from validate_published_finite_check_20261025 import digest
from frozen_helpers import capture_rng
binding=json.loads((D/'impedance_BINDING.json').read_text());cp=B/'runs/parameter_history_cycle89_archive_20261030_v1/impedance/cycle_00089.pt';ck=torch.load(cp,map_location='cpu',weights_only=False);state=ck['learner'];rs=ck['replay'];samples=np.unique(np.r_[np.linspace(0,rs['size']-1,4096,dtype=int),np.flatnonzero(rs['arrays']['dones'][:,0]==1)]);raws=[rs['arrays']['observations'][int(i),:48]*OBSERVATION_SCALE for i in samples[:4]];steps=ck['steps'];del rs,ck;gc.collect();torch.set_num_threads(1)
HC=history_class(pair_class(PublishedLearner,'minimum'),binding['history_binding'])
def make(cls):return cls(B/'runtime/source_train17_clock',dimension=5,direct=False,seed=20261025,device='cuda:1',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
old=make(HC);old.load_state_dict(state);new=make(violation_class(HC,binding));new.migrate_parent(state);initial=new.state_dict();outputs=[];rngs=[];nextweights=[]
for learner,st in [(old,state),(new,initial)]:
 learner.load_state_dict(st);out=[];weights=[]
 for stream in (0,3):learner.reset_episode(stream)
 for j in range(4):
  for stream in (0,3):
   learner.consume_interval(None if j==0 else dict(external_penetration_peak_m=j*.0001),stream)
   o,a,m,c=learner.act(raws[j],step=steps+j,stream=stream);out.append((o[:51].copy(),a.copy(),m.copy(),c));weights.append(learner.hybrid.weight)
 outputs.append(out);rngs.append(digest(capture_rng(learner)));nextweights.append(weights)
rows=[]
for i,(a,b) in enumerate(zip(*outputs)):
 rows.append(dict(step=i//2,stream=(0,3)[i%2],max_abs_by_field=[float(np.max(np.abs(np.asarray(x,dtype=np.float64)-np.asarray(y,dtype=np.float64)))) for x,y in zip(a,b)],exact_by_field=[np.array_equal(x,y) for x,y in zip(a,b)],context_old=a[3],context_new=b[3],next_weight_old=nextweights[0][i],next_weight_new=nextweights[1][i]))
report=dict(time=time.time(),rows=rows,final_rng_equal=rngs[0]==rngs[1],scope='Read-only reproduction of failing native action equality; no tolerance change or training',updates=0,physics=0)
with (D/'NATIVE_MISMATCH_DIAGNOSIS.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
