"""Reject invalid89 contracts and prove only the two restore seams change."""
from pathlib import Path
import sys,copy,json,os,time,hashlib,gc,difflib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_history_cycle89_20261030_v1';P=B/'runs/parameter_history_cycle88_20261030_v2'
os.sched_setaffinity(0,{11});sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import torch
torch.set_num_threads(1)
from driver import read,sha,put,validate_protocol,validate_parent,validate_actor_rates,transform
results={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];parent=st['parent_registration']['sha256'];validate_protocol(parent,p)
 generated=transform(Path(st['trainer_path']).read_text());old=(P/m/'trainer_registered.py').read_text()
 expected=old.replace("learner.migrate_parent(checkpoint['learner'])","learner.load_state_dict(checkpoint['learner'])").replace("replay.migrate_parent(checkpoint['replay'], protocol['history_critic_amendment']['sidecar']['path'])","replay.load_state_dict(checkpoint['replay'])")
 assert old!=expected and generated==expected
 (D/(m+'_trainer.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),generated.splitlines(True),fromfile='actual88',tofile='registered89')))
 rejections=[]
 def reject(label,fn):
  try:fn()
  except (ValueError,AssertionError,KeyError):rejections.append(label)
  else:raise AssertionError('Bad contract accepted: '+label)
 for key,value in [('parent_cycle',87),('new_cycle',90),('new_cycles',2),('maximum_new_actions',82500),('automatic_followup',True),('optimizer_settings_changed',True),('old_window_continuity_claim',True),('environment_state_saved',True)]:
  bad=copy.deepcopy(p);bad['post_interruption_continuation'][key]=value;reject('stage_'+key,lambda:validate_protocol(parent,bad))
 for key in ['reward','conditions','completed_stage_continuation','history_critic_amendment','replay_capacity_followup_stage']:
  bad=copy.deepcopy(p);bad[key]={'invalid_change':True};reject('contract_'+key,lambda:validate_protocol(parent,bad))
 for actual in [[float('nan')],[float('inf')],[0.],[3e-4],[]]:reject('actor_lr_'+str(actual),lambda:validate_actor_rates(actual,[3e-5]))
 validate_actor_rates([2.9999999999999997e-05],[3e-5])
 ck=torch.load(st['checkpoint']['path'],map_location='cpu',weights_only=False);validate_parent(ck,p)
 for key,value in [('cycle',87),('boundary','partial_condition_cycle'),('environment_state_saved',True),('seed',0),('steps',ck['steps']-1),('controller','invalid'),('history_critic_amendment',{})]:
  bad=dict(ck);bad[key]=value;reject('parent_'+key,lambda:validate_parent(bad,p))
 for key in ['learner','replay']:
  from persisted_history_critic import KEY
  bad=dict(ck);bad[key]=dict(ck[key]);bad[key].pop(KEY);reject('missing_marker_'+key,lambda:validate_parent(bad,p))
 bad=dict(ck);bad['replay']=dict(ck['replay']);bad['replay']['arrays']=dict(ck['replay']['arrays']);bad['replay']['arrays']['observations']=ck['replay']['arrays']['observations'][:,:50];reject('old50_replay',lambda:validate_parent(bad,p))
 result=dict(passed=True,exact_complete88_boundary=True,negative_rejections=rejections,negative_count=len(rejections),native_trainer_only_two_restore_seams_changed=True,trainer_sha256=hashlib.sha256(generated.encode()).hexdigest(),checkpoint_sha256=sha(st['checkpoint']['path']),physical_steps=0,optimizer_updates=0)
 results[m]=result;put(D/(m+'_CONTRACT_REVIEW.json'),result);print(m,len(rejections),flush=True);del ck,bad;gc.collect()
put(D/'CONTRACT_REVIEW.json',dict(passed=True,time=time.time(),methods=results,physical_steps=0,optimizer_updates=0))
