from pathlib import Path
import os,sys,json,time,copy,ast,types,hashlib,gc,traceback,io
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_violation_pipeline_preflight_20261030_v1'
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.sched_setaffinity(0,{11});sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from violation_pipeline import *
from validate_published_finite_check_20261025 import digest
from published_replay_device_cache_20261025 import DeviceReplayCache
from published_exact_pipeline_20261026 import cache_class

def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def reject(out,label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError):out.append(label)
 else:raise AssertionError('Accepted invalid '+label)
torch.set_num_threads(1);start=time.monotonic();plan=read(D/'PLAN.json');results={}
try:
 for n,h in plan['sources'].items():assert sha(D/n)==h,n
 for r in plan['inputs']:assert sha(r['path'])==r['sha256'],r['path']
 for m in plan['methods']:
  assert time.monotonic()-start<plan['budget_seconds'];reg=O/m/'REGISTRATION.json';p=read(reg);a=p['violation_critic_amendment'];b=a['binding'];parent=read(a['parent_registration']['path']);ck=torch.load(a['parent_checkpoint']['path'],map_location='cpu',weights_only=False);validate_parent(ck,p)
  snapshot=torch.load(a['snapshot']['path'],map_location='cpu',weights_only=False);assert snapshot['parent_cycle']==89 and snapshot['online_steps']==snapshot['optimizer_updates']==0 and snapshot['kind']=='interface_only_no_online_approval';before=digest(snapshot['learner']);rd=digest(snapshot['replay'])
  rejected=[]
  for k,v in [('reward',{}),('conditions',[]),('learner_batch_size',256),('learner_updates_per_transition',2),('history_critic_amendment',{}),('replay_capacity_followup_stage',{})]:
   bad=copy.deepcopy(p);bad[k]=v;reject(rejected,'contract_'+k,lambda:validate_registration(bad))
  for k,v in [('scope','finite_online_cycle'),('online_launch',True),('first_cycle',89),('physics_steps',1),('formal_updates',1)]:
   bad=copy.deepcopy(p);bad['violation_critic_amendment'][k]=v;reject(rejected,'scope_'+k,lambda:validate_registration(bad))
  reject(rejected,'unregistered_online_launch',lambda:require_online_launch(p))
  for k,v in [('cycle',88),('boundary','partial'),('environment_state_saved',True),('steps',ck['steps']-1),('seed',0),('controller','direct')]:
   bad=dict(ck);bad[k]=v;reject(rejected,'parent_'+k,lambda:validate_parent(bad,p))
  original_metadata={k:v for k,v in ck.items() if k not in ('learner','replay')};metadata_digest=digest(original_metadata)
  migrated=dict(ck,learner=snapshot['learner'],replay=snapshot['replay'],protocol_sha256=sha(reg),violation_critic_amendment=a);validate_migrated(migrated,p,reg)
  inverse_metadata={k:v for k,v in migrated.items() if k not in ('learner','replay','violation_critic_amendment')};inverse_metadata['protocol_sha256']=ck['protocol_sha256'];assert digest(inverse_metadata)==metadata_digest
  for key in ('learner','replay'):
   for mk in (HK,VK):
    bad=dict(migrated);bad[key]=dict(migrated[key]);bad[key].pop(mk);reject(rejected,'migrated_'+key+'_'+mk,lambda:validate_migrated(bad,p,reg))
  bad=dict(migrated);bad['replay']=dict(migrated['replay']);bad['replay']['arrays']=dict(migrated['replay']['arrays']);bad['replay']['arrays']['observations']=migrated['replay']['arrays']['observations'][:,:51];reject(rejected,'migrated_width51',lambda:validate_migrated(bad,p,reg))
  output=O/'archive'/m/'cycle_00089.pt';torch.save(migrated,output);del ck,snapshot,migrated,bad;gc.collect()
  disk=torch.load(output,map_location='cpu',weights_only=False);validate_migrated(disk,p,reg);assert digest(disk['learner'])==before and digest(disk['replay'])==rd
  # Execute the exact generated trainer AST from learner construction through
  # resume verification. The extracted code contains no sampler/process/physics.
  src=(O/m/'trainer_prepared.py').read_text();tree=ast.parse(src);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  def assign(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
  first=next(i for i,n in enumerate(main.body) if assign(n,'learner'));last=next(i for i,n in enumerate(main.body) if assign(n,'stage'));nodes=main.body[first:last]
  assert len(nodes)>4 and not any(isinstance(n,ast.Attribute) and n.attr in ('Popen','step') for n in ast.walk(ast.Module(body=nodes,type_ignores=[])))
  cls,rcls=classes(p);args=types.SimpleNamespace(controller=m,seed=20261025,algorithm='cheq',device=plan['device'],registration=reg,resume=output)
  def resume_check(checkpoint_digest,protocol,current_digest):
   assert checkpoint_digest==current_digest==sha(reg);validate_registration(protocol)
  def initial_check(learner,replay,checkpoint,out):
   validate_migrated(checkpoint,p,reg);assert digest(learner.state_dict())==before and digest(replay.state_dict())==rd
  namespace=dict(torch=torch,np=np,Path=Path,sha=sha,args=args,protocol=p,root=B/'runtime/source_train17_clock',out=O/m/'unused_no_physics',dim=b['action_dimension'],PublishedLearner=cls,Replay=rcls,validate_resume_protocol=resume_check,_verify_initial_state=initial_check)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(O/m/'trainer_prepared.py'),'exec'),namespace)
  learner=namespace['learner'];replay=namespace['replay'];assert namespace['steps']==b['rows'] and namespace['start_cycle']==90 and namespace['cycles']==disk['cycles'];assert digest(learner.state_dict())==before
  initial=learner.state_dict();rng=copy.deepcopy(replay.rng.bit_generator.state);cache=cache_class(DeviceReplayCache)(replay,plan['device']);batch=cache.sample(65536);sample_digest=digest(batch)
  rates={k:copy.deepcopy(initial[k]['param_groups']) for k in ('actor_optimizer','q_optimizer','alpha_optimizer')};assert initial['terminal_loss_weight']==128
  old_history=[q.q_net[0].weight[:,50].detach().clone() for q in learner.learner.agent.ensemble];assert any(torch.count_nonzero(v)>0 for v in old_history)
  metrics=learner.update(batch);updated=learner.state_dict();assert updated['num_gradient_steps']==initial['num_gradient_steps']+1
  assert all(updated[k]['param_groups']==v for k,v in rates.items());assert all(np.isfinite(v) for v in metrics.values())
  assert any(torch.count_nonzero(q.q_net[0].weight[:,51])>0 for q in learner.learner.agent.ensemble)
  saved=io.BytesIO();torch.save(initial,saved);saved.seek(0);learner.load_state_dict(torch.load(saved,weights_only=False));assert learner.update(batch)==metrics and digest(learner.state_dict())==digest(updated)
  online=list(learner.learner.agent.ensemble.parameters());targets=list(learner.learner.agent.ensemble_targets.parameters())
  with torch.no_grad():online[0][:,51].add_(.25)
  expected=[t.detach().clone().mul_(1-learner.learner.polyak_factor).add_(v,alpha=learner.learner.polyak_factor) for v,t in zip(online,targets)]
  learner.learner.update_target_networks();assert all(torch.equal(t,v) for t,v in zip(targets,expected))
  learner.load_state_dict(initial);replay.rng.bit_generator.state=rng;assert digest(learner.state_dict())==before and digest(replay.state_dict())==rd and digest(batch)==sample_digest
  assert sha(a['parent_checkpoint']['path'])==a['parent_checkpoint']['sha256'] and sha(a['snapshot']['path'])==a['snapshot']['sha256']
  result=dict(passed=True,checkpoint_sha256=sha(output),checkpoint_path=str(output),original_complete89_metadata_inverse_exact=True,metadata_digest=metadata_digest,original_learner_replay_snapshot_exact=True,generated_trainer_restore_AST_executed=True,restore_AST_sha256=hashlib.sha256(ast.dump(ast.Module(body=nodes,type_ignores=[])).encode()).hexdigest(),negative_rejections=rejected,next_cycle=90,online90_launched=False,real_batch=65536,clone_native_updates=2,repeat_update_after_serialization_exact=True,learned_history_weights_preserved=True,bit_column_received_nonzero_gradient=True,target_parameter_references_exact=True,all_state_and_replay_restored=True,actual_formal_updates=0,physics_steps=0,clone_update_metrics=metrics,limits='Only exact trainer restore AST executed, not the full physics/optimizer event loop; clone updates discarded')
  results[m]=result;put(O/(m+'_MIGRATION_REVIEW.json'),result);print('PIPELINE',m,flush=True)
  del namespace,learner,replay,cache,batch,disk,initial,updated,online,targets,expected;gc.collect();torch.cuda.empty_cache()
 put(O/'MIGRATION_REVIEW.json',dict(passed=True,methods=results,elapsed_s=time.monotonic()-start,clone_native_updates=6,formal_updates=0,physics_steps=0,training90=False))
except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
