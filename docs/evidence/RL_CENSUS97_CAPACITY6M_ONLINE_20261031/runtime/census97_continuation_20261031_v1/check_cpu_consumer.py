from pathlib import Path
import os,sys,time,json
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
D=Path(__file__).resolve().parent;B=D.parents[1];sys.path.insert(0,str(D))
from driver import read,put,R,restore_consumer
from census_native import KEY,marker
from validate_published_finite_check_20261025 import digest
from frozen_helpers import capture_rng,restore_rng
import torch
os.sched_setaffinity(0,{10});torch.set_num_threads(1);results={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');ck=torch.load(p['post_interruption_continuation']['checkpoint']['path'],map_location='cpu',weights_only=False,mmap=True);state=ck['learner'];assert state[KEY]==marker();l=restore_consumer(state,p,'cpu');initial=digest(l.state_dict());assert initial==digest(state);rng=capture_rng(l);a=ck['replay']['arrays'];obs=torch.tensor(a['observations'][:16]);actions=torch.tensor(a['actions'][:16])
 with torch.no_grad():
  q=torch.stack([net(obs,actions).flatten() for net in l.learner.agent.ensemble],1);action,lp=l.learner.agent.get_action_and_log_prob(obs)
 assert torch.isfinite(q).all() and torch.isfinite(action).all() and torch.isfinite(lp).all();restore_rng(l,rng);assert digest(l.state_dict())==initial and not any(v.grad is not None for v in l.learner.agent.parameters());results[m]=dict(cpu_full_state_exact=True,inference_rng_restored=True,gradients_absent=True)
 del l,ck,state
put(D/'CPU_CONSUMER_REVIEW.json',dict(passed=True,time=time.time(),methods=results,optimizer_updates=0,new_physics=0,scope='CPU diagnostic consumer restores full persisted96 state and preserves it after stochastic inference; not a97 result'))
print('All3 CPU full-state consumers passed',flush=True)
