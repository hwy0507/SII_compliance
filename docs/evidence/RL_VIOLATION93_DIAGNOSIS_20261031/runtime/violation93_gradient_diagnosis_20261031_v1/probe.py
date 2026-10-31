"""Fixed92 impedance terminal gradient geometry at full92/full93; no optimizer operations."""
from pathlib import Path
import gc,hashlib,json,math,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_gradient_diagnosis_20261031_v1';read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 plan=read(O/'PLAN.json');start=time.monotonic();os.sched_setaffinity(0,{10});assert sha(__file__)==plan['sources']['probe.py']
 for p,h in plan['dependencies'].items():assert sha(p)==h,p
 for x in plan['inputs']:assert sha(x['path'])==x['sha256'],x
 sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1'),str(B/'runtime/violation92_terminal_followup_20261030_v1')]
 import numpy as np
 import torch
 from violation_consumers import restore_learner
 from compare93 import validate_complete93
 from compare92 import validate_recovery92
 from frozen_helpers import capture_rng
 from validate_published_finite_check_20261025 import digest
 torch.set_num_threads(1)
 with np.load(plan['fixed_values']) as z:data={k:z[k].copy() for k in z.files}
 idx=data['indices'];assert len(idx)==2755;flags=np.isin(idx,plan['known_abort_indices']);assert flags.sum()==3;results={}
 def relation(g,h):
  g=g.astype(np.float64);h=h.astype(np.float64);dot=float(g@h);ng=float(np.linalg.norm(g));nh=float(np.linalg.norm(h));return dict(dot=dot,norm_left=ng,norm_right=nh,cosine=None if ng==0 or nh==0 else dot/(ng*nh))
 for cycle in ['92','93']:
  assert time.monotonic()-start<plan['budget_seconds'];entry=plan['cycles'][cycle];cp=Path(entry['checkpoint']);assert sha(cp)==entry['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration'])
  (validate_recovery92 if cycle=='92' else validate_complete93)(ck,reg);assert ck['boundary']=='complete_condition_cycle' and ck['steps']==entry['steps']
  arr=ck['replay']['arrays'];np.testing.assert_array_equal(idx,np.flatnonzero(arr['dones'][:plan['fixed_parent_steps'],0]==1))
  for key in ['observations','actions','masks']:np.testing.assert_array_equal(arr[key][idx],data[key])
  np.testing.assert_array_equal(arr['rewards'][idx,0],data['rewards'])
  learner=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',plan['device'],ck['seed']);initial=digest(ck['learner']);replay_digest=digest(ck['replay']);assert digest(learner.state_dict())==initial;rng=digest(capture_rng(learner));params=list(learner.learner.agent.parameters());before_grad=digest([p.grad for p in params])
  obs=torch.as_tensor(data['observations'],device=learner.device);act=torch.as_tensor(data['actions'],device=learner.device);target=torch.as_tensor(data['rewards'],device=learner.device);mask=torch.as_tensor(data['masks'],device=learner.device);selected=torch.as_tensor(flags,device=learner.device)
  with torch.no_grad():pred=torch.stack([q(obs,act).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
  np.testing.assert_array_equal(pred,data['complete'+cycle]);critics=[];all_groups=[]
  for j,q in enumerate(learner.learner.agent.ensemble):
   qp=list(q.parameters());names=[n for n,p in q.named_parameters()];den=mask[:,j].sum();assert den>0
   def grads(group):
    prediction=q(obs,act).reshape(-1);errors=(prediction-target)**2*mask[:,j];loss=errors[group].sum()/den
    gs=torch.autograd.grad(loss,qp);return torch.cat([g.reshape(-1) for g in gs]).detach().cpu().numpy(),float(loss.detach().cpu())
   ga,la=grads(selected);go,lo=grads(~selected);gt,lt=grads(torch.ones(len(idx),dtype=torch.bool,device=learner.device));repeat,lr=grads(selected);np.testing.assert_array_equal(ga,repeat);assert la==lr
   residual=float(np.linalg.norm(gt.astype(float)-ga.astype(float)-go.astype(float)));assert residual<=2e-5*max(1.,float(np.linalg.norm(gt.astype(float))))
   assert math.isclose(la+lo,lt,rel_tol=2e-6,abs_tol=2e-6)
   file=O/f'cycle{cycle}_critic{j}_gradients.npz';np.savez_compressed(file,known_aborts=ga,other_terminals=go,all_terminals=gt)
   record=dict(critic=j,parameter_names=names,parameter_sizes=[p.numel() for p in qp],loss_known_aborts=la,loss_other_terminals=lo,loss_all_terminals=lt,mask_count=float(den.cpu()),known_abort_mask_count=float(mask[selected,j].sum().cpu()),other_mask_count=float(mask[~selected,j].sum().cpu()),relation=relation(ga,go),gradient_sum_residual_norm=residual,exact_repeat=True,gradients=dict(path=str(file),bytes=file.stat().st_size,sha256=sha(file)))
   critics.append(record);all_groups.append((ga,go));(O/'PROGRESS.json').write_text(json.dumps(dict(time=time.time(),cycle=cycle,critic=j))+'\n')
  aggregate=relation(np.concatenate([g for g,h in all_groups]),np.concatenate([h for g,h in all_groups]));assert digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng and digest([p.grad for p in params])==before_grad and digest(ck['replay'])==replay_digest and sha(cp)==entry['checkpoint_sha256']
  results[cycle]=dict(critics=critics,aggregate=aggregate,checkpoint_sha256=entry['checkpoint_sha256'],exact_saved_predictions=True,full_learner_optimizer_replay_rng_and_parameter_grads_unchanged=True)
  del ck,arr,learner,params,qp,q,obs,act,target,mask,selected,all_groups;gc.collect();torch.cuda.empty_cache()
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),cycles=results,terminal_rows=2755,known_abort_rows=3,other_rows=2752,optimizer_updates=0,new_physics=0,neural_gradient_calls=40,elapsed_s=time.monotonic()-start,scope=plan['scope'],convergence_claim=False))
 print(json.dumps({c:dict(aggregate=r['aggregate'],cosines=[v['relation']['cosine'] for v in r['critics']]) for c,r in results.items()},indent=2))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(O/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
