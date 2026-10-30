from pathlib import Path
import os,sys,copy,gc,time,json,difflib,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_violation_cycle91_20261030_v1'
os.sched_setaffinity(0,{11});sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import torch
torch.set_num_threads(1)
from driver import read,sha,put,validate_protocol,validate_parent,validate_actor_rates,transform
from persisted_history_critic import KEY as HK
from persisted_violation_critic import KEY as VK
results={}
for m in ('impedance','admittance','vmc'):
 p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];parent=st['parent_registration']['sha256'];validate_protocol(parent,p);old=Path(st['trainer_path']).read_text();s=transform(old)
 assert s==old and s.count("learner.consume_interval(event['interval'], stream=slot)")==1
 (D/(m+'_trainer.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='actual90',tofile='finite91')))
 rejections=[]
 def reject(label,fn):
  try:fn()
  except (ValueError,AssertionError,KeyError):rejections.append(label)
  else:raise AssertionError('Invalid contract accepted: '+label)
 for k,v in [('parent_cycle',89),('new_cycle',92),('new_cycles',2),('maximum_new_actions',82500),('automatic_followup',True),('optimizer_settings_changed',True),('old_window_continuity_claim',True),('environment_state_saved',True)]:
  bad=copy.deepcopy(p);bad['post_interruption_continuation'][k]=v;reject('stage_'+k,lambda:validate_protocol(parent,bad))
 for k in ('reward','conditions','completed_stage_continuation','history_critic_amendment','violation_critic_amendment','replay_capacity_followup_stage'):
  bad=copy.deepcopy(p);bad[k]={};reject('contract_'+k,lambda:validate_protocol(parent,bad))
 for actual in [[float('nan')],[float('inf')],[0.],[3e-4],[]]:reject('actor_lr_'+str(actual),lambda:validate_actor_rates(actual,[3e-5]))
 validate_actor_rates([2.9999999999999997e-05],[3e-5]);ck=torch.load(st['checkpoint']['path'],map_location='cpu',weights_only=False);validate_parent(ck,p)
 for k,v in [('cycle',89),('boundary','partial'),('environment_state_saved',True),('seed',0),('steps',ck['steps']-1),('controller','invalid'),('history_critic_amendment',{})]:
  bad=dict(ck);bad[k]=v;reject('parent_'+k,lambda:validate_parent(bad,p))
 for k in ('learner','replay'):
  for marker in (HK,VK):
   bad=dict(ck);bad[k]=dict(ck[k]);bad[k].pop(marker);reject('missing_'+k+'_'+marker,lambda:validate_parent(bad,p))
 bad=dict(ck);bad['replay']=dict(ck['replay']);bad['replay']['arrays']=dict(ck['replay']['arrays']);bad['replay']['arrays']['observations']=ck['replay']['arrays']['observations'][:,:51];reject('old51_replay',lambda:validate_parent(bad,p))
 bad=dict(ck);bad['replay']=dict(ck['replay']);bad['replay']['arrays']=dict(ck['replay']['arrays']);bad['replay']['arrays']['next_observations']=ck['replay']['arrays']['next_observations'][:,:51];reject('old51_next_replay',lambda:validate_parent(bad,p))
 for key,value in [('cursor',ck['steps']-1),('capacity',2_000_000)]:
  bad=dict(ck);bad['replay']=dict(ck['replay']);bad['replay'][key]=value;reject('replay_'+key,lambda:validate_parent(bad,p))
 bad=dict(ck);bad['learner']=dict(ck['learner']);bad['learner']['num_gradient_steps']-=1;reject('optimizer_counter',lambda:validate_parent(bad,p))
 bad=dict(ck);bad['violation_critic_amendment']={};reject('violation_amendment',lambda:validate_parent(bad,p))
 assert len(rejections)==36
 result=dict(passed=True,exact_trained90_boundary=True,negative_count=len(rejections),negative_rejections=rejections,actual90_trainer_bytes_unchanged=True,interval_consumer_once=True,trainer_sha256=hashlib.sha256(s.encode()).hexdigest(),checkpoint_sha256=sha(st['checkpoint']['path']),physical_steps=0,optimizer_updates=0);results[m]=result;put(D/(m+'_CONTRACT_REVIEW.json'),result);print(m,len(rejections),flush=True);del ck,bad;gc.collect()
put(D/'CONTRACT_REVIEW.json',dict(passed=True,time=time.time(),methods=results,physical_steps=0,optimizer_updates=0))
