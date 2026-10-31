"""Finite terminal-only information ablation on disposable full93 critic clones."""
from pathlib import Path
import os,sys,json,time,hashlib,copy,gc,traceback
os.environ['OMP_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_potential_ablation_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main(m):
 import numpy as np
 import torch
 from torch import nn
 plan=rd(O/'PLAN.json');start=time.monotonic();e=plan['methods'][m];os.sched_setaffinity(0,{e['cpu']});torch.set_num_threads(1);assert sha(__file__)==rd(O/'SOURCE_LOCK.json')['ablate.py']
 for p,h in plan['dependencies'].items():assert sha(p)==h
 A=Path(plan['input_directory']);audit=rd(A/(m+'_REVIEW.json'));assert audit['passed'] and audit['rows']==e['rows'];source=Path(audit['terminal_values']['path']);assert sha(source)==audit['terminal_values']['sha256'];datafile=np.load(source);data={k:datafile[k] for k in datafile.files};datafile.close()
 sys.path[:0]=[str(B/'runtime/violation90_frozen_preparation_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1')]
 from violation_consumers import restore_learner
 from compare93 import validate_complete93
 from validate_published_finite_check_20261025 import digest
 from frozen_helpers import capture_rng
 cp=Path(e['checkpoint']['path']);assert sha(cp)==e['checkpoint']['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=rd(e['registration']);validate_complete93(ck,reg);idx=data['indices'];arr=ck['replay']['arrays'];np.testing.assert_array_equal(idx,np.flatnonzero(arr['dones'][:,0]==1))
 for k in ['observations','actions','masks']:np.testing.assert_array_equal(arr[k][idx],data[k])
 np.testing.assert_array_equal(arr['rewards'][idx,0],data['rewards']);learner=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',e['device'],ck['seed']);original=digest(learner.state_dict());assert original==digest(ck['learner']);replay=digest(ck['replay']);rng=digest(capture_rng(learner));original_grads=digest([p.grad for p in learner.learner.agent.parameters()]);agent=learner.learner.agent;oldopt=learner.learner.q_optimizer
 fit=data['cycles']<=85;held=~fit;assert fit.any() and held.sum()==240 and np.all((data['cycles'][held]>=86)&(data['cycles'][held]<=93));mu=data['features'][fit].mean(0);sd=data['features'][fit].std(0);sd=np.where(sd<=1e-8,1.,sd);scaled=((data['features']-mu)/sd).astype(np.float32);assert np.isfinite(scaled).all()
 obs=torch.as_tensor(data['observations'],device=learner.device);act=torch.as_tensor(data['actions'],device=learner.device);target=torch.as_tensor(data['rewards'],device=learner.device);mask=torch.as_tensor(data['masks'],device=learner.device);select=torch.as_tensor(fit,device=learner.device)
 with torch.no_grad():initial=torch.stack([q(obs,act).reshape(-1) for q in agent.ensemble],1).cpu().numpy()
 class Clone(nn.Module):
  def __init__(self):
   super().__init__();self.qs=copy.deepcopy(agent.ensemble);self.branches=nn.ParameterList([nn.Parameter(torch.zeros(q.q_net[0].out_features,3,device=learner.device)) for q in self.qs])
  def forward(self,x,a,f):
   inp=torch.cat([x,a],-1);outputs=[]
   for q,w in zip(self.qs,self.branches):
    h=q.q_net[0](inp)+torch.nn.functional.linear(f,w)
    for layer in list(q.q_net.children())[1:]:h=layer(h)
    outputs.append(h.reshape(-1))
   return torch.stack(outputs,1)
 def create():
  model=Clone();baseparams=[p for q in model.qs for p in q.parameters()];opt=torch.optim.Adam(baseparams,**oldopt.defaults);opt.load_state_dict(copy.deepcopy(oldopt.state_dict()));assert digest(opt.state_dict())==digest(oldopt.state_dict());opt.add_param_group(dict(params=list(model.branches)));return model,opt
 def objective(pred):return (((pred-target[select,None])**2*mask[select]).sum(0)/mask[select].sum(0)).sum()
 results={};predictions=[];training_curves=[];repeated=False
 for arm in plan['arms']:
  model,opt=create();feats=scaled.copy()
  if arm=='baseline':feats[:]=0
  elif arm=='potential':feats[:,1:]=0
  f=torch.as_tensor(feats,device=learner.device)
  with torch.no_grad():pred=model(obs,act,f).cpu().numpy()
  np.testing.assert_array_equal(pred,initial);saved=[pred];curve=[];checkpoints=[0]
  # Exactly repeat the first full-batch update on an independent clone for each arm.
  duplicate,dopt=create()
  for step in range(1,plan['fullbatch_updates']+1):
   assert time.monotonic()-start<plan['budget_seconds_per_method'];opt.zero_grad(set_to_none=True);loss=objective(model(obs[select],act[select],f[select]));assert torch.isfinite(loss);loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters());opt.step();curve.append(float(loss.detach().cpu()))
   if step==1:
    dopt.zero_grad(set_to_none=True);repeat=objective(duplicate(obs[select],act[select],f[select]));assert torch.equal(loss.detach(),repeat.detach());repeat.backward();dopt.step();assert digest(model.state_dict())==digest(duplicate.state_dict()) and digest(opt.state_dict())==digest(dopt.state_dict());del duplicate,dopt;repeated=True
   if step in plan['evaluate_updates']:
    with torch.no_grad():p=model(obs,act,f).cpu().numpy()
    assert np.isfinite(p).all();saved.append(p);checkpoints.append(step)
   if step%64==0:(O/(m+'_PROGRESS.json')).write_text(json.dumps(dict(time=time.time(),method=m,arm=arm,step=step,loss=curve[-1]))+'\n')
  assert checkpoints==plan['evaluate_updates'];predictions.append(np.array(saved));training_curves.append(curve);results[arm]=dict(initial_prediction_exact=True,first_update_repeat_exact=True,original_Adam_state_exact_at_start=True,clone_final_digest=digest(model.state_dict()),clone_optimizer_final_digest=digest(opt.state_dict()),updates=256,training_loss_first=curve[0],training_loss_last=curve[-1],training_loss_max=max(curve));del model,opt,f;gc.collect();torch.cuda.empty_cache()
 assert repeated and digest(learner.state_dict())==original and digest(capture_rng(learner))==rng and digest([p.grad for p in agent.parameters()])==original_grads and digest(ck['replay'])==replay and sha(cp)==e['checkpoint']['sha256']
 file=O/(m+'_values.npz');np.savez_compressed(file,**data,predictions=np.array(predictions),training_curves=np.array(training_curves),feature_mean=mu,feature_scale=sd,fitting=fit,initial_prediction=initial,evaluate_updates=np.array(plan['evaluate_updates']),arms=np.array(plan['arms']))
 stats={}
 for ai,arm in enumerate(plan['arms']):
  stats[arm]={}
  for split,sel in [('fit',fit),('held',held),('all',np.ones(len(fit),bool))]:
   pred=predictions[ai][-1][sel].astype(float);err=(pred-data['rewards'][sel,None])**2;stats[arm][split]=dict(rows=int(sel.sum()),masked_sse=(err*data['masks'][sel]).sum(0).tolist(),all_row_sse=err.sum(0).tolist(),total_masked_sse=float((err*data['masks'][sel]).sum()),max_masked_row_sse=float((err*data['masks'][sel]).sum(1).max()))
 put(O/(m+'_REVIEW.json'),dict(passed=True,time=time.time(),method=m,terminal_rows=len(idx),fitting_rows=int(fit.sum()),held_rows=int(held.sum()),arms=results,final=stats,full_original_learner_optimizer_replay_rng_grads_unchanged=True,checkpoint_sha256=e['checkpoint']['sha256'],values=dict(path=str(file),bytes=file.stat().st_size,sha256=sha(file)),formal_updates=0,disposable_main_updates=768,disposable_first_update_repeats=3,new_physics=0,elapsed_s=time.monotonic()-start,scope=plan['diagnostic_holdout']))
 print(json.dumps(dict(method=m,final=stats,elapsed_s=time.monotonic()-start)),flush=True)
if __name__=='__main__':
 m=sys.argv[1]
 try:main(m)
 except BaseException:put(O/(m+'_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
