from pathlib import Path
import json,os,sys,time,hashlib,math,gc,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census100_impedance_gradient_probe_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 os.sched_setaffinity(0,{10});p=rd(D/'PLAN.json');assert sha(__file__)==p['source_sha256'];start=time.time();O.mkdir()
 for x in p['inputs']:assert sha(x['path'])==x['sha256']
 sys.path.insert(0,str(B/'runtime/census100_continuation_20261031_v1'))
 from driver import restore_consumer,validate_parent,validate_checkpoint
 from frozen_helpers import capture_rng,restore_rng
 from validate_published_finite_check_20261025 import digest
 import torch,numpy as np
 torch.set_num_threads(1);reg=rd(p['registration']['path'])
 with np.load(p['values']['path']) as z:a={k:z[k].copy() for k in z.files}
 indices=[int(np.flatnonzero(a['indices']==i)[0]) for i in p['replay_indices']];assert a['cycles'][indices].tolist()==[92,99];assert a['masks'][indices,4].tolist()==[1.,1.]
 meta=[dict(index=int(a['indices'][j]),cycle=int(a['cycles'][j]),condition=str(a['conditions'][j]),reward=float(a['rewards'][j]),mask=a['masks'][j].tolist(),context_history_violation=a['observations'][j,48:].tolist(),action=a['actions'][j].tolist()) for j in indices];results={}
 for label,entry in p['snapshots'].items():
  assert time.time()-start<p['budget_seconds'];cp=Path(entry['path']);assert sha(cp)==entry['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True)
  if label=='complete99':validate_parent(ck,reg)
  else:validate_checkpoint(ck,reg,complete=False)
  l=restore_consumer(ck['learner'],reg,'cpu');before=digest(l.state_dict());assert before==digest(ck['learner']);rb=digest(ck['replay']);rng=capture_rng(l);net=l.learner.agent.ensemble[4];params=[q for q in net.parameters() if q.requires_grad];names=[n for n,q in net.named_parameters() if q.requires_grad]
  expected=a['initial_prediction' if label=='complete99' else 'prefix_prediction'][:,4];vectors={};losses={};predictions={};selected={}
  allmask=a['masks'][:,4]==1
  for group in ['old92','new99','other_mask1_terminals']:
   if group=='old92':sel=np.array([indices[0]])
   elif group=='new99':sel=np.array([indices[1]])
   else:sel=np.flatnonzero(allmask);sel=sel[~np.isin(sel,indices)]
   obs=torch.as_tensor(a['observations'][sel]);act=torch.as_tensor(a['actions'][sel]);target=torch.as_tensor(a['rewards'][sel]);q=net(obs,act).flatten();np.testing.assert_allclose(q.detach().numpy(),expected[sel],rtol=1e-5,atol=1e-5)
   loss=((q-target)**2).mean();grads=torch.autograd.grad(loss,params,allow_unused=True);flat=torch.cat([(torch.zeros_like(par) if g is None else g).reshape(-1) for par,g in zip(params,grads)]).detach().numpy().copy();assert np.isfinite(flat).all();vectors[group]=flat;losses[group]=float(loss.detach());predictions[group]=q.detach().numpy().copy();selected[group]=a['indices'][sel].copy();assert all(x.grad is None for x in l.learner.agent.parameters())
  restore_rng(l,rng);assert digest(l.state_dict())==before==digest(ck['learner']) and digest(ck['replay'])==rb and digest(capture_rng(l))==digest(rng) and sha(cp)==entry['sha256']
  out=O/(label+'_gradients.npz');np.savez_compressed(out,**vectors,**{k+'_prediction':v for k,v in predictions.items()},**{k+'_replay_indices':v for k,v in selected.items()})
  pairs={}
  with np.load(out) as z:
   for k,v in vectors.items():np.testing.assert_array_equal(z[k],v)
   for left,right in [('old92','new99'),('old92','other_mask1_terminals'),('new99','other_mask1_terminals')]:
    x=z[left].astype(float);y=z[right].astype(float);dot=math.fsum(float(a)*float(b) for a,b in zip(x,y));nx=math.sqrt(math.fsum(float(a)*float(a) for a in x));ny=math.sqrt(math.fsum(float(a)*float(a) for a in y));assert nx>0 and ny>0
    cosine=dot/(nx*ny);assert math.isclose(dot,float(np.dot(x,y)),rel_tol=1e-10,abs_tol=1e-7);assert -1.000001<=cosine<=1.000001;pairs[left+'__'+right]=dict(dot=dot,left_norm=nx,right_norm=ny,cosine=cosine,local_steepest_descent_conflict=dot<0)
  result=dict(checkpoint=entry,steps=ck['steps'],gradient_parameters=names,gradient_dimension=len(vectors['old92']),groups={k:dict(rows=len(selected[k]),mse=losses[k]) for k in vectors},two_predictions={k:predictions[k].tolist() for k in ['old92','new99']},pairs=pairs,values=ref(out),learner_adam_replay_rng_unchanged=True,parameter_grad_buffers_absent=True)
  results[label]=result;put(O/(label+'_REVIEW.json'),result);print(label,json.dumps(pairs),flush=True);del ck,l,net,params,obs,act,q,loss,grads;gc.collect()
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,samples=meta,critic_index=4,critic_index_base=0,source=ref(__file__),physics_steps=0,optimizer_updates=0,weight_promotion=False,scope='Exploratory local gradients of original-mask critic4 mean terminal SSE at saved complete99 and partial100+7000. Includes two failed terminal samples and mean of all other critic4 mask1 retained99 terminals. No nonterminal TD, sampled denominator, other critics, optimizer preconditioning or actor update included; gradient cosine is only local first-order geometry and does not establish cause of observed online regression. Forward batch shapes differ from baseline blocks; predictions checked within1e-5, not claimed bit-exact. All original masks preserved.'))
 put(O/'FINISHED.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start))
if __name__=='__main__':
 try:main()
 except BaseException:put(D/'FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
