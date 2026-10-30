"""Matched 52-input critic clones on original87 terminals, restored from complete89.

Zero-input control and raw preaction violation-bit intervention have identical
parameter counts, initial weights and Adam states. No learned weight promotion.
"""
from pathlib import Path
import copy,gc,hashlib,json,os,sys,time,traceback
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import torch
from torch import nn
D=Path(__file__).resolve().parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');started=time.monotonic();os.sched_setaffinity(0,{plan['cpu']});torch.set_num_threads(1)
for name,h in plan['sources'].items():assert sha(D/name)==h
for name,h in plan['restore_sources'].items():assert sha(Path(plan['restore_runtime'])/name)==h
for entry in plan['inputs']:assert sha(entry['path'])==entry['sha256']
sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
from history_consumers import restore_learner
from validate_published_finite_check_20261025 import digest
from frozen_helpers import capture_rng

def budget():assert time.monotonic()-started<plan['budget_seconds'],'Registered finite diagnostic expired'
def predict(model,obs,act):return torch.stack([q(obs,act).reshape(-1) for q in model],1)
def loss_fn(pred,y,mask):return (((pred-y)**2*mask).sum(0)/mask.sum(0)).sum()
def insert_zero(t):
 assert t.ndim==2 and t.shape[1] in (56,58)
 return torch.cat((t[:,:51],t.new_zeros((t.shape[0],1)),t[:,51:]),1)
def expand(parent,dim):
 model=copy.deepcopy(parent);old_named=list(parent.named_parameters());expanded=set()
 with torch.random.fork_rng(devices=[torch.device(plan['device']).index]):
  for j,q in enumerate(model):
   old=q.q_net[0];assert isinstance(old,nn.Linear) and old.in_features==51+dim
   new=nn.Linear(old.in_features+1,old.out_features,bias=old.bias is not None,device=old.weight.device,dtype=old.weight.dtype)
   with torch.no_grad():new.weight.copy_(insert_zero(old.weight));new.bias.copy_(old.bias)
   q.q_net[0]=new;expanded.add(f'{j}.q_net.0.weight')
 new_named=dict(model.named_parameters());assert list(new_named)==[k for k,v in old_named]
 for name,value in old_named:
  assert torch.equal(new_named[name],insert_zero(value) if name in expanded else value)
 return model,old_named,expanded

def prepare(method):
 budget();entry=plan['methods'][method];cp=Path(entry['checkpoint']['path']);assert sha(cp)==entry['checkpoint']['sha256']
 ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration']['path']);binding=reg['history_critic_amendment']['binding']
 assert binding==entry['binding'] and ck['cycle']==89 and ck['boundary']=='complete_condition_cycle'
 assert ck['protocol_sha256']==entry['registration']['sha256'] and ck['recovery_continuation']==reg['post_interruption_continuation']
 assert ck['history_critic_amendment']==reg['history_critic_amendment'] and ck['steps']==binding['rows']+82500
 with np.load(entry['values']['path']) as z:values={k:z[k].copy() for k in ('indices','observations51','actions','rewards','masks','complete89')}
 idx=values['indices'];arr=ck['replay']['arrays'];assert len(idx)==entry['terminal_rows']
 np.testing.assert_array_equal(idx,np.flatnonzero(arr['dones'][:binding['rows'],0]==1))
 for name,key in [('observations51','observations'),('actions','actions'),('rewards','rewards'),('masks','masks')]:np.testing.assert_array_equal(values[name],arr[key][idx])
 history=np.load(entry['sidecar']['path'],mmap_mode='r');peak=np.array(history[idx,0],copy=True)
 np.testing.assert_array_equal((peak/(peak+.0002)).astype(np.float32),values['observations51'][:,50])
 bit=(peak>.0002).astype(np.float32);assert np.isfinite(peak).all() and (peak>=0).all()
 state=ck['learner'];initial_digest=digest(state);seed=ck['seed'];del ck,arr,history;gc.collect()
 learner=restore_learner(state,binding,B/'runtime/source_train17_clock',plan['device'],seed)
 assert digest(learner.state_dict())==initial_digest;initial_rng=digest(capture_rng(learner))
 dim=values['actions'].shape[1];model0,old_named,expanded=expand(learner.learner.agent.ensemble,dim);model1=copy.deepcopy(model0)
 original=copy.deepcopy(learner.learner.q_optimizer.state_dict());extended=copy.deepcopy(original)
 ids=[p for g in extended['param_groups'] for p in g['params']];assert len(ids)==len(old_named)
 for pid,(name,param) in zip(ids,old_named):
  if name in expanded:
   for key,v in list(extended['state'][pid].items()):
    if torch.is_tensor(v) and v.ndim==2:
     assert v.shape==param.shape;extended['state'][pid][key]=insert_zero(v)
 opt0=torch.optim.Adam(model0.parameters(),**learner.learner.q_optimizer.defaults);opt0.load_state_dict(copy.deepcopy(extended))
 opt1=torch.optim.Adam(model1.parameters(),**learner.learner.q_optimizer.defaults);opt1.load_state_dict(copy.deepcopy(extended))
 assert digest(model0.state_dict())==digest(model1.state_dict()) and digest(opt0.state_dict())==digest(opt1.state_dict())
 assert opt0.state_dict()['param_groups']==original['param_groups']
 for pid,(name,param) in zip(ids,old_named):
  for key,v in original['state'][pid].items():
   actual=opt0.state_dict()['state'][pid][key];expected=insert_zero(v) if name in expanded and torch.is_tensor(v) and v.ndim==2 else v
   assert torch.equal(actual,expected) if torch.is_tensor(v) else actual==expected
 obs=torch.as_tensor(values['observations51'],device=plan['device']);act=torch.as_tensor(values['actions'],device=plan['device']);y=torch.as_tensor(values['rewards'],device=plan['device']);mask=torch.as_tensor(values['masks'],device=plan['device'])
 assert obs.shape==(len(idx),51) and mask.shape==(len(idx),5) and torch.all(mask.sum(0)>0)
 o0=torch.cat((obs,obs.new_zeros((len(idx),1))),1);o1=torch.cat((obs,torch.as_tensor(bit[:,None],device=plan['device'])),1)
 with torch.no_grad():parent=predict(learner.learner.agent.ensemble,obs,act);p0=predict(model0,o0,act);p1=predict(model1,o1,act)
 assert torch.equal(p0,p1);error=float((p0-parent).abs().max());saved_error=float(np.max(np.abs(parent.cpu().numpy()-values['complete89'])));assert max(error,saved_error)<=plan['initial_q_atol']
 assert digest(learner.state_dict())==initial_digest and digest(capture_rng(learner))==initial_rng
 report=dict(terminal_rows=len(idx),bit_nonzero_rows=int(bit.sum()),matched_expanded_model_and_optimizer_exact=True,old_weights_and_adam_values_preserved=True,new_weight_and_moments_zero=True,all_initial_arms_q_exact=True,parent_q_max_abs_difference=error,saved89_parent_q_max_abs_difference=saved_error,parent_learner_rng_unchanged=True)
 return dict(learner=learner,parent_digest=initial_digest,parent_rng=initial_rng,model0=model0,model1=model1,opt0=opt0,opt1=opt1,o0=o0,o1=o1,act=act,y=y,mask=mask,values=values,peak=peak,bit=bit,initial0=p0.cpu().numpy(),initial1=p1.cpu().numpy(),report=report)

def main():
 check='--check-only' in sys.argv;results={}
 if not check:
  pre=read(D/'PREFLIGHT_REVIEW.json');assert pre['passed'] and pre['plan_sha256']==sha(D/'PLAN.json') and set(pre['methods'])==set(plan['methods'])
 for method in plan['methods']:
  s=prepare(method);results[method]=s['report'];print('PREFLIGHT',method,json.dumps(s['report']),flush=True)
  if not check:
   curves=[]
   with (D/(method+'_curve.jsonl')).open('x') as f:
    for step in range(plan['updates_per_arm']+1):
     budget()
     with torch.no_grad():
      p0=predict(s['model0'],s['o0'],s['act']);p1=predict(s['model1'],s['o1'],s['act']);row=dict(step=step)
      for arm,p in [('control',p0),('bit',p1)]:
       row[arm+'_loss']=float(loss_fn(p,s['y'],s['mask']));row[arm+'_sse_by_critic']=(((p-s['y'])**2)*s['mask']).sum(0).cpu().tolist()
       assert np.isfinite(row[arm+'_loss']) and np.isfinite(row[arm+'_sse_by_critic']).all()
     curves.append(row);f.write(json.dumps(row)+'\n');f.flush()
     if step==plan['updates_per_arm']:break
     for model,opt,obs in [(s['model0'],s['opt0'],s['o0']),(s['model1'],s['opt1'],s['o1'])]:
      opt.zero_grad(set_to_none=True);loss=loss_fn(predict(model,obs,s['act']),s['y'],s['mask']);loss.backward();opt.step()
      assert all(torch.isfinite(p).all() for p in model.parameters())
   assert digest(s['learner'].state_dict())==s['parent_digest'] and digest(capture_rng(s['learner']))==s['parent_rng']
   output=D/(method+'_values.npz');np.savez_compressed(output,**s['values'],preaction_peak_m=s['peak'],bit=s['bit'],initial_control=s['initial0'],initial_bit=s['initial1'],final_control=p0.cpu().numpy(),final_bit=p1.cpu().numpy())
   results[method].update(initial=curves[0],final=curves[-1],values=ref(output),curve=ref(D/(method+'_curve.jsonl')),updates_per_arm=plan['updates_per_arm'],parent_learner_rng_unchanged_after_fit=True)
   print('FIT',method,json.dumps(curves[-1]),flush=True)
  assert sha(plan['methods'][method]['checkpoint']['path'])==plan['methods'][method]['checkpoint']['sha256']
  del s;gc.collect();torch.cuda.empty_cache()
 put(D/('PREFLIGHT_REVIEW.json' if check else 'REVIEW.json'),dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-started,plan_sha256=sha(D/'PLAN.json'),methods=results,total_cloned_q_optimizer_steps=0 if check else 2*len(results)*plan['updates_per_arm'],original_checkpoint_optimizer_updates=0,actor_alpha_target_updates=0,new_physics=0,no_weight_promotion=True,training90=False,limits=plan['limits']))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(D/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),time=time.time()));raise
