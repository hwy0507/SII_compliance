from pathlib import Path
import sys,json,torch,os,time
B=Path("/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl")
p=json.loads((B/'runs/parameter_partial75_recovery_cycle78_20261029_v1/impedance/REGISTRATION.json').read_text()); st=p['post_interruption_continuation'];root=Path(p['runtime']);sys.path[:0]=[st['original_runtime'],str(root/'source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from validate_published_finite_check_20261025 import digest
torch.set_num_threads(1)
ck=torch.load(st['checkpoint']['path'],map_location='cpu',weights_only=False); cls=pair_class(PublishedLearner,p['batch_size_stage']['reduction'])
learner=cls(root,dimension=ck['replay']['arrays']['actions'].shape[1],direct=False,seed=20261025,device='cpu',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
learner.load_state_dict(ck['learner']);a=learner.state_dict();e=ck['learner'];diff=[]
def compare(x,y,path):
 if digest(x)==digest(y):return
 if isinstance(x,dict) and isinstance(y,dict):
  for k in x.keys()|y.keys():
   if k not in x or k not in y:diff.append(dict(path=path+'/'+str(k),actual=repr(x.get(k)),expected=repr(y.get(k))))
   else:compare(x[k],y[k],path+'/'+str(k))
 elif isinstance(x,(list,tuple)) and isinstance(y,(list,tuple)) and len(x)==len(y):
  for i,(v,w) in enumerate(zip(x,y)):compare(v,w,path+'/'+str(i))
 else:diff.append(dict(path=path,actual=repr(x)[:1500],expected=repr(y)[:1500],actual_hash=digest(x),expected_hash=digest(y)))
compare(a,e,'learner');r=dict(time=time.time(),differences=diff,new_physics=0,optimizer_updates=0);Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
