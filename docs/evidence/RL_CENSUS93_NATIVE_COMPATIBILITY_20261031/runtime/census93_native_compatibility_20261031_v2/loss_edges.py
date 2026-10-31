from pathlib import Path
import os,sys,json,time,copy,types
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import torch,numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).resolve().parent;O=B/'runs/census93_native_compatibility_20261031_v2';sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from census_native import CensusCache,census_class,losses
from violation_pipeline import classes
from train_published_compliance_20261025 import Replay
from validate_published_finite_check_20261025 import digest
os.sched_setaffinity(0,{10});torch.set_num_threads(1);e=json.loads((O/'PLAN.json').read_text())['methods']['impedance'];ck=torch.load(e['checkpoint'],map_location='cpu',weights_only=False,mmap=True);reg=json.loads(Path(e['registration']).read_text());base,_=classes(reg);dim=reg['violation_critic_amendment']['binding']['action_dimension'];l=census_class(base)(B/'runtime/source_train17_clock',dimension=dim,direct=False,seed=ck['seed'],device='cuda:0',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);l.migrate_parent(ck['learner']);initial=digest(l.state_dict());r=Replay(dim,52,123,capacity=64);c=CensusCache(r,'cuda:0')
idx=np.flatnonzero(ck['replay']['arrays']['dones'][:,0]==0)[:16];batch={k:torch.tensor(v[idx],device=l.device) for k,v in ck['replay']['arrays'].items()};batch['masks']=torch.ones((16,5),device=l.device);d=types.SimpleNamespace(**batch);target=d.rewards.flatten();q=[l.learner.agent.get_q_value(state=d.observations,action=d.actions,q_net=j,target=False).flatten() for j in range(5)];ls=losses(l.learner,d,q,target,c);native=[((v-target)**2).mean() for v in q];assert all(torch.equal(a,b) for a,b in zip(ls,native))
rejected=[]
def reject(name,fn):
 try:fn()
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
bad=types.SimpleNamespace(**dict(batch,dones=torch.ones_like(d.dones)));reject('absent_terminal_pattern',lambda:losses(l.learner,bad,q,target,c))
bad=types.SimpleNamespace(**dict(batch,masks=torch.zeros_like(d.masks)));reject('zero_denominator',lambda:losses(l.learner,bad,q,target,c))
bad=types.SimpleNamespace(**dict(batch,masks=torch.full_like(d.masks,.5)));reject('invalid_mask',lambda:losses(l.learner,bad,q,target,c))
bad=types.SimpleNamespace(**dict(batch,dones=torch.full_like(d.dones,.5)));reject('invalid_done',lambda:losses(l.learner,bad,q,target,c))
assert digest(l.state_dict())==initial
result=dict(passed=True,time=time.time(),empty_terminal_native_loss_exact=True,negative_guards=rejected,full_learner_state_unchanged=True,optimizer_updates=0,new_physics=0)
(O/'LOSS_EDGE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
