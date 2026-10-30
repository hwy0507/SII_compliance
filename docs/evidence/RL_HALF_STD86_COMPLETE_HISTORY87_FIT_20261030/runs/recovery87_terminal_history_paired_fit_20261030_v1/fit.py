"""Finite terminal-only paired fitting diagnostic, never promotes cloned weights."""
from pathlib import Path
import os,sys,json,time,hashlib,copy,gc,traceback
D=Path(__file__).parent;B=D.parents[1];os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import torch
from torch import nn
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');assert sha(__file__)==plan['sources']['fit.py'];os.sched_setaffinity(0,{plan['cpu']});torch.set_num_threads(1);start=time.monotonic()
sys.path[:0]=[str(B/'runtime/parameter86_half_std_paired_20261030_v3'),str(B/'runtime/source_train17_clock/source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from validate_published_finite_check_20261025 import digest

def budget():assert time.monotonic()-start<plan['budget_seconds'],'Finite fit budget expired'
def predict(model,obs,act):return torch.stack([q(obs,act).reshape(-1) for q in model],dim=1)
def loss_fn(pred,y,mask):return (((pred-y)**2*mask).sum(0)/mask.sum(0)).sum()
def insert_zero(t):return torch.cat([t[:,:50],torch.zeros((t.shape[0],1),device=t.device,dtype=t.dtype),t[:,50:]],dim=1)
try:
 for x in plan['inputs']:assert sha(x['path'])==x['sha256']
 hist=read(B/'runs/recovery87_history_extension_20261030_v1/REVIEW.json');assert read(B/'runs/recovery87_history_extension_20261030_v1/FINISHED.json')['passed'];results={}
 for method in plan['methods']:
  budget();meta=hist['methods'][method];cp=Path(meta['checkpoint87']['path']);assert sha(cp)==meta['checkpoint87']['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);arr=ck['replay']['arrays'];indices=np.flatnonzero(arr['dones'][:,0]==1);assert len(indices)==meta['actual_terminal_rows']
  assert sha(meta['sidecar']['path'])==meta['sidecar']['sha256'];history=np.load(meta['sidecar']['path'],mmap_mode='r');raw_peak=np.array(history[indices,0],copy=True);feature=(raw_peak/(raw_peak+.0002)).astype(np.float32);assert np.isfinite(feature).all() and np.all(feature>=0) and np.all(feature<1)
  obs0=np.array(arr['observations'][indices],copy=True);acts=np.array(arr['actions'][indices],copy=True);ys=np.array(arr['rewards'][indices],copy=True);masks=np.array(arr['masks'][indices],copy=True);assert obs0.shape[1]==50 and np.all(masks.sum(0)>0)
  state=ck['learner'];parent_digest=digest(state);seed=ck['seed'];del ck['replay'],arr;gc.collect()
  dim=acts.shape[1];learner=pair_class(PublishedLearner,'minimum' if method=='impedance' else 'mean')(B/'runtime/source_train17_clock',dimension=dim,direct=False,seed=seed,device=plan['device'],algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);learner.load_state_dict(state);assert digest(learner.state_dict())==parent_digest
  model0=copy.deepcopy(learner.learner.agent.ensemble);model1=copy.deepcopy(model0)
  old_named=list(model0.named_parameters());expanded=set()
  with torch.random.fork_rng(devices=[torch.device(plan['device']).index]):
   for i,q in enumerate(model1):
    old=q.q_net[0];assert isinstance(old,nn.Linear) and old.in_features==50+dim
    new=nn.Linear(old.in_features+1,old.out_features,bias=old.bias is not None,device=old.weight.device,dtype=old.weight.dtype)
    with torch.no_grad():new.weight.copy_(insert_zero(old.weight));new.bias.copy_(old.bias)
    q.q_net[0]=new;expanded.add(f'{i}.q_net.0.weight')
  new_named=dict(model1.named_parameters())
  for name,param in old_named:
   assert torch.equal(new_named[name],insert_zero(param) if name in expanded else param)
  original_opt=copy.deepcopy(learner.learner.q_optimizer.state_dict());opt0=torch.optim.Adam(model0.parameters(),**learner.learner.q_optimizer.defaults);opt0.load_state_dict(copy.deepcopy(original_opt));expanded_opt=copy.deepcopy(original_opt)
  paramids=[k for g in expanded_opt['param_groups'] for k in g['params']];assert len(paramids)==len(old_named)
  for pid,(name,param) in zip(paramids,old_named):
   if name in expanded:
    for key in ['exp_avg','exp_avg_sq']:
     v=expanded_opt['state'][pid][key];assert v.shape==param.shape;expanded_opt['state'][pid][key]=insert_zero(v)
    if 'max_exp_avg_sq' in expanded_opt['state'][pid]:expanded_opt['state'][pid]['max_exp_avg_sq']=insert_zero(expanded_opt['state'][pid]['max_exp_avg_sq'])
  opt1=torch.optim.Adam(model1.parameters(),**learner.learner.q_optimizer.defaults);opt1.load_state_dict(expanded_opt)
  # Verify all old Adam values and counters; only the new column has zero moments.
  s0=opt0.state_dict();s1=opt1.state_dict();assert s0['param_groups']==s1['param_groups']
  for pid,(name,param) in zip(paramids,old_named):
   for key,v in s0['state'][pid].items():
    actual=s1['state'][pid][key];expected=insert_zero(v) if name in expanded and torch.is_tensor(v) and v.ndim==2 else v
    assert torch.equal(actual,expected) if torch.is_tensor(v) else actual==expected
  dev=plan['device'];o0=torch.as_tensor(obs0,device=dev);o1=torch.cat([o0,torch.as_tensor(feature[:,None],device=dev)],1);act=torch.as_tensor(acts,device=dev);y=torch.as_tensor(ys,device=dev);mask=torch.as_tensor(masks,device=dev)
  with torch.no_grad():
   parent_q=predict(learner.learner.agent.ensemble,o0,act);initial0=predict(model0,o0,act);initial1=predict(model1,o1,act)
   assert torch.equal(parent_q,initial0);initial_error=float((initial1-initial0).abs().max());assert initial_error<=plan['initial_q_atol']
  curves=[]
  with (D/(method+'_curve.jsonl')).open('x') as log:
   for step in range(plan['updates_per_arm']+1):
    budget()
    with torch.no_grad():
     pred0=predict(model0,o0,act);pred1=predict(model1,o1,act);row=dict(step=step,control_loss=float(loss_fn(pred0,y,mask)),history_loss=float(loss_fn(pred1,y,mask)),control_sse_by_critic=(((pred0-y)**2)*mask).sum(0).cpu().tolist(),history_sse_by_critic=(((pred1-y)**2)*mask).sum(0).cpu().tolist())
    assert all(np.isfinite(row[k]) for k in ['control_loss','history_loss']);curves.append(row);log.write(json.dumps(row)+'\n');log.flush()
    if step==plan['updates_per_arm']:break
    for model,opt,obs in [(model0,opt0,o0),(model1,opt1,o1)]:
     opt.zero_grad(set_to_none=True);loss=loss_fn(predict(model,obs,act),y,mask);loss.backward();opt.step()
     assert all(torch.isfinite(p).all() for p in model.parameters())
  assert digest(learner.state_dict())==parent_digest and digest(state)==parent_digest and sha(cp)==meta['checkpoint87']['sha256']
  output=D/(method+'_values.npz');np.savez_compressed(output,indices=indices,preaction_peak_m=raw_peak,feature=feature,observations=obs0,actions=acts,rewards=ys,masks=masks,initial_control=initial0.cpu().numpy(),initial_history=initial1.cpu().numpy(),final_control=pred0.cpu().numpy(),final_history=pred1.cpu().numpy())
  results[method]=dict(terminal_rows=len(indices),updates_per_arm=plan['updates_per_arm'],initial_q_max_error=initial_error,initial=curves[0],final=curves[-1],values=ref(output),curve=ref(D/(method+'_curve.jsonl')),original_checkpoint_learner_rng_unchanged=True,original_checkpoint_sha256=meta['checkpoint87']['sha256'],all_original_adam_values_preserved_at_start=True,new_feature_weight_and_moments_initially_zero=True,actor_target_network_and_alpha_updates=0,trained_weights_promoted=False)
  print('FIT',method,curves[-1],flush=True);del learner,model0,model1,opt0,opt1,original_opt,expanded_opt,s0,s1,ck,state;gc.collect();torch.cuda.empty_cache()
 put(D/'REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,methods=results,total_cloned_q_optimizer_steps=len(results)*2*plan['updates_per_arm'],original_checkpoint_optimizer_updates=0,new_physics=0,training88=False,no_weight_promotion=True,limits=plan['limits']))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
