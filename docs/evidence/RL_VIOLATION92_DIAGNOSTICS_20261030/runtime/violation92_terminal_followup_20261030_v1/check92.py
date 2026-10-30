from pathlib import Path
import os,sys,json,time,hashlib,gc
os.sched_setaffinity(0,{11})
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';R=B/'runs/parameter_violation_cycle92_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
sys.path[:0]=[str(D),str(B/'runtime/violation90_frozen_preparation_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from compare92 import validate_architecture92,validate_recovery92,sha,put,inputs
import torch
from persisted_violation_critic import KEY as VK
torch.set_num_threads(1);plan=read(O/'PLAN.json');inputs(plan);startup=read(R/'startup/REVIEW.json');result={}
for m,e in plan['methods'].items():
 p=R/'startup'/(m+'.pt');assert sha(p)==startup['methods'][m]['checkpoint_sha256'];ck=torch.load(p,map_location='cpu',weights_only=False);reg=read(R/m/'REGISTRATION.json');validate_architecture92(ck,reg)
 try:validate_recovery92(ck,reg)
 except AssertionError:partial_rejected=True
 else:raise AssertionError('Actual startup partial unexpectedly complete')
 candidates={
 'wrong_cycle':dict(ck,cycle=91),
 'wrong_seed':dict(ck,seed=0),
 'wrong_protocol':dict(ck,protocol_sha256='0'*64),
 'wrong_controller':dict(ck,controller='other'),
 'old89_boundary':dict(ck,steps=reg['violation_critic_amendment']['binding']['rows']),
 'bad_cursor':dict(ck,replay=dict(ck['replay'],cursor=ck['steps']-1)),
 'bad_capacity':dict(ck,replay=dict(ck['replay'],capacity=2000000)),
 'missing_violation_marker':dict(ck,learner={k:v for k,v in ck['learner'].items() if k!=VK}),
 'old_next51':dict(ck,replay=dict(ck['replay'],arrays=dict(ck['replay']['arrays'],next_observations=ck['replay']['arrays']['next_observations'][:,:51])))
 }
 rejected=[]
 for name,candidate in candidates.items():
  try:validate_architecture92(candidate,reg)
  except (AssertionError,KeyError):rejected.append(name)
  else:raise AssertionError('Guard accepted '+name)
 assert sha(p)==startup['methods'][m]['checkpoint_sha256']
 result[m]=dict(actual_partial92_architecture_passed=True,actual_partial_complete_rejected=partial_rejected,negative_cases=rejected,source_sha256=sha(p),actual_parent_steps=read(reg['post_interruption_continuation']['cycle_review']['path'])['methods'][m]['steps'],startup_steps=ck['steps'],no_complete92_validation_claim=True)
 del ck,candidate,candidates;gc.collect()
put(O/'VALIDATOR_REVIEW.json',dict(passed=True,time=time.time(),methods=result,negative_count=sum(len(x['negative_cases']) for x in result.values()),physics_steps=0,neural_forwards=0,optimizer_updates=0,scope='Actual immutable startup92 checkpoints validate architecture and reject complete boundary; no future complete92 state fabricated'))
print('Actual partial92 checked;27 metadata rejects; future complete92 still pending')
