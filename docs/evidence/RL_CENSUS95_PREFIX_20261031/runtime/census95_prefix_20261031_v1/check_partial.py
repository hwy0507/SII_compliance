from pathlib import Path
import os,sys,gc,time
from terminal95 import B,D,O,read,put,inputs,sha
os.sched_setaffinity(0,{11});p=inputs(read(O/'PLAN.json'));sys.path.insert(0,p['restore_runtime'])
from driver import validate_checkpoint
import torch
torch.set_num_threads(1);R=Path(p['run']);startup=read(R/'startup/REVIEW.json');results={}
for m,e in p['methods'].items():
 f=R/'startup'/(m+'.pt');assert sha(f)==startup['methods'][m]['checkpoint_sha256'];ck=torch.load(f,map_location='cpu',weights_only=False);reg=read(e['registration']);validate_checkpoint(ck,reg)
 try:validate_checkpoint(ck,reg,complete=True)
 except ValueError as err:assert str(err)=='Complete95 required'
 else:raise AssertionError('Accepted actual partial95')
 assert sha(f)==startup['methods'][m]['checkpoint_sha256'];results[m]=dict(actual_partial_architecture_passed=True,actual_partial_complete_rejected=True,checkpoint_sha256=sha(f),steps=ck['steps']);del ck;gc.collect()
put(O/'PARTIAL_REJECTION_REVIEW.json',dict(passed=True,time=time.time(),methods=results,prior111_negative_contract_review=str(Path(p['restore_runtime'])/'CONTRACT_REVIEW.json'),physics_steps=0,optimizer_updates=0,neural_forwards=0))
