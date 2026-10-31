"""Paired full93 frozen-target mixed-batch critic updates, disposable clones only."""
from pathlib import Path
import os,sys,time,json,copy,hashlib,gc,traceback
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_terminal_census_ablation_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main(m):
 import numpy as np
 import torch
 from conditional import weights
 plan=rd(O/'PLAN.json');e=plan['methods'][m];start=time.monotonic();os.sched_setaffinity(0,{e['cpu']});torch.set_num_threads(1);lock=rd(O/'SOURCE_LOCK.json');assert sha(__file__)==lock['ablate.py'] and sha(D/'conditional.py')==lock['conditional.py'];assert rd(O/'MATH_PREFLIGHT.json')['passed']
 for p,h in plan['dependencies'].items():assert sha(p)==h
 for name in ['raw_manifest','raw_review','terminal_values']:assert sha(e[name]['path'])==e[name]['sha256']
 sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1')]
 from violation_consumers import restore_learner
 from compare93 import validate_complete93
 from validate_published_finite_check_20261025 import digest
 from frozen_helpers import capture_rng
 cp=Path(e['checkpoint']);assert sha(cp)==e['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=rd(e['registration']);validate_complete93(ck,reg);arr=ck['replay']['arrays'];learner=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',e['device'],ck['seed']);initial=digest(learner.state_dict());assert initial==digest(ck['learner']);rdigest=digest(ck['replay']);rng=digest(capture_rng(learner));grads=digest([p.grad for p in learner.learner.agent.parameters()]);old=learner.learner.agent.ensemble;oldopt=learner.learner.q_optimizer
 tf=np.load(e['terminal_values']['path']);td={k:tf[k] for k in ['indices','observations','actions','rewards','masks','cycles','conditions','initial_prediction']};tf.close();ti=td['indices'];np.testing.assert_array_equal(ti,np.flatnonzero(arr['dones'][:,0]==1))
 for key in ['observations','actions','masks']:np.testing.assert_array_equal(td[key],arr[key][ti])
 np.testing.assert_array_equal(td['rewards'],arr['rewards'][ti,0]);obs=torch.as_tensor(arr['observations'],device=learner.device);actions=torch.as_tensor(arr['actions'],device=learner.device);tobs=obs[ti];tactions=actions[ti];ty=torch.as_tensor(td['rewards'],device=learner.device);tm=torch.as_tensor(td['masks'],device=learner.device)
 def predict(model,x,a):return torch.stack([q(x,a).reshape(-1) for q in model],1)
 with torch.no_grad():tinitial=predict(old,tobs,tactions).cpu().numpy()
 np.testing.assert_array_equal(tinitial,td['initial_prediction']);batches=[];allsource=rd(e['raw_manifest']['path'])['files'];assert len(allsource)==64
 for bi,item in enumerate(allsource):
  assert sha(item['path'])==item['sha256'];z=np.load(item['path']);v={k:z[k] for k in z.files};z.close();idx=v['indices'].astype(np.int64);assert len(idx)==65536
  for key,native in [('masks','masks'),('dones','dones'),('rewards','rewards')]:np.testing.assert_array_equal(v[key],arr[native][idx] if key=='masks' else arr[native][idx,0])
  np.testing.assert_array_equal(v['target'][v['dones']==1],v['rewards'][v['dones']==1]);w,den,pop,counts=weights(td['masks'],v['masks'],v['dones']);batches.append(dict(index=torch.as_tensor(idx,device=learner.device),target=torch.as_tensor(v['target'],device=learner.device),mask=torch.as_tensor(v['masks'].astype(np.float32),device=learner.device),done=torch.as_tensor(v['dones'].astype(np.float32),device=learner.device),den=torch.as_tensor(den.astype(np.float32),device=learner.device),cw=torch.as_tensor(w.astype(np.float32),device=learner.device),raw=v,counts=counts,population=pop))
  with torch.no_grad():q=predict(old,obs[idx],actions[idx]).cpu().numpy()
  np.testing.assert_array_equal(q,v['q'])
 (O/m).mkdir();(O/m/'raw').mkdir();raw_manifest=[]
 def objective(model,b,arm):
  q=predict(model,obs[b['index']],actions[b['index']]);error=(q-b['target'][:,None])**2
  if arm=='sampled_terminal':return ((error*b['mask']*(1+127*b['done'][:,None])).sum(0)/b['den']).sum()
  nt=((error*b['mask']*(1-b['done'][:,None])).sum(0)/b['den']).sum();terr=(predict(model,tobs,tactions)-ty[:,None])**2;return nt+(terr*b['cw']).sum()
 def make():
  model=copy.deepcopy(old);opt=torch.optim.Adam([p for q in model for p in q.parameters()],**oldopt.defaults);opt.load_state_dict(copy.deepcopy(oldopt.state_dict()));assert digest(opt.state_dict())==digest(oldopt.state_dict());return model,opt
 def stats(q,v):
  er=(q.astype(float)-v['target'].astype(float)[:,None])**2;w=v['masks'].astype(float)*(1+127*v['dones'].astype(float))[:,None];den=w.sum(0);contrib=er*w/den;loss=contrib.sum(0);return loss,contrib.sum(1)
 def evaluate(model,arm,save):
  with torch.no_grad():tq=predict(model,tobs,tactions).cpu().numpy()
  terr=(tq.astype(float)-td['rewards'][:,None])**2;records=[]
  for bi,b in enumerate(batches):
   with torch.no_grad():q=predict(model,obs[b['index']],actions[b['index']]).cpu().numpy()
   v=b['raw'];ls,perrow=stats(q,v);w,den,_,_=weights(td['masks'],v['masks'],v['dones']);cl=perrow[v['dones']==0].sum()+(terr*w).sum();groups={}
   idx=v['indices'];done=v['dones']==1
   for name,sel in [('terminal',done),('nonterminal',~done),('old85',idx<e['steps85']),('new86_92',(idx>=e['steps85'])&(idx<e['parent_steps'])),('new93',idx>=e['parent_steps'])]:groups[name]=dict(count=int(sel.sum()),original_loss=float(perrow[sel].sum()))
   records.append(dict(batch=bi,original_loss=float(ls.sum()),percritic=ls.tolist(),conditional_loss=float(cl),groups=groups,denominators=den.tolist(),terminal_pattern_counts=b['counts'].tolist()))
   if save:
    file=O/m/'raw'/f'{arm}_batch_{bi:03d}.npy';np.save(file,q);raw_manifest.append(dict(arm=arm,batch=bi,**ref(file)))
  return tq,records
 results={};terminal_predictions=[];curves=[];native_initial=None
 for arm in plan['arms']:
  model,opt=make();tq,ini=evaluate(model,arm,False);np.testing.assert_array_equal(tq,tinitial)
  if native_initial is None:native_initial=ini
  else:assert ini==native_initial
  if arm=='sampled_terminal':
   for b,rec in zip(batches,ini):np.testing.assert_allclose(rec['percritic'],b['raw']['native_losses'],rtol=3e-6,atol=1e-6)
  clone,copt=make();curve=[];snapshots=[tq];updates=[0]
  for step in range(1,257):
   assert time.monotonic()-start<plan['budget_seconds_per_method'];b=batches[(step-1)%64];opt.zero_grad(set_to_none=True);loss=objective(model,b,arm);assert torch.isfinite(loss);loss.backward();assert all(p.grad is None or torch.isfinite(p.grad).all() for q in model for p in q.parameters());opt.step();curve.append(float(loss.detach().cpu()))
   if step==1:
    copt.zero_grad(set_to_none=True);repeat=objective(clone,b,arm);assert torch.equal(loss.detach(),repeat.detach());repeat.backward();copt.step();assert digest(model.state_dict())==digest(clone.state_dict()) and digest(opt.state_dict())==digest(copt.state_dict());del clone,copt
   if step in plan['evaluate_updates']:
    with torch.no_grad():snapshots.append(predict(model,tobs,tactions).cpu().numpy())
    updates.append(step)
   if step%16==0:(O/(m+'_PROGRESS.json')).write_text(json.dumps(dict(time=time.time(),arm=arm,step=step,loss=curve[-1]))+'\n')
  tq,final=evaluate(model,arm,True);np.testing.assert_array_equal(tq,snapshots[-1]);assert updates==plan['evaluate_updates'];terminal_predictions.append(np.array(snapshots));curves.append(curve);results[arm]=dict(updates=256,first_update_repeat_exact=True,initial_original_Adam_exact=True,model_final_digest=digest(model.state_dict()),optimizer_final_digest=digest(opt.state_dict()),training_loss=dict(first=curve[0],last=curve[-1],mean=float(np.mean(curve)),maximum=max(curve)),final_native_batches=final);del model,opt;gc.collect();torch.cuda.empty_cache()
 assert digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng and digest([p.grad for p in learner.learner.agent.parameters()])==grads and digest(ck['replay'])==rdigest and sha(cp)==e['checkpoint_sha256']
 file=O/(m+'_values.npz');np.savez_compressed(file,**td,predictions=np.array(terminal_predictions),training_curves=np.array(curves),arms=np.array(plan['arms']),evaluate_updates=np.array(plan['evaluate_updates']));put(O/m/'RAW_MANIFEST.json',dict(files=raw_manifest));put(O/(m+'_REVIEW.json'),dict(passed=True,time=time.time(),method=m,terminal_rows=len(ti),all64_initial_q_exact=True,all64_initial_original_loss_exact_tolerance=True,all_raw_sources_and_terminal_inputs_bound=True,all_original_learner_Adam_replay_RNG_grads_unchanged=True,initial_native_batches=native_initial,arms=results,values=ref(file),raw_manifest=ref(O/m/'RAW_MANIFEST.json'),additional_census_rows_per_candidate_update=len(ti),formal_updates=0,main_disposable_updates=512,repeat_updates=2,new_physics=0,elapsed_s=time.monotonic()-start,scope=plan['schedule']))
 print(json.dumps(dict(method=m,passed=True,elapsed=time.monotonic()-start,loss={k:v['training_loss'] for k,v in results.items()})),flush=True)
if __name__=='__main__':
 m=sys.argv[1]
 try:main(m)
 except BaseException:put(O/(m+'_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
