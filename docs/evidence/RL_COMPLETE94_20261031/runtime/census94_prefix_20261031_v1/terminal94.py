"""Read-only complete94 comparison on every retained full93 terminal, all five critics."""
from pathlib import Path
import gc,hashlib,json,math,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census94_fixed93_terminal_20261031_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stats(pred,reward,mask):
 import numpy as np
 err=(pred.astype(np.float64)-reward.astype(np.float64)[:,None])**2;w=err*mask
 return dict(rows=len(reward),masked_sse=[math.fsum(w[:,j]) for j in range(5)],all_row_sse=[math.fsum(err[:,j]) for j in range(5)],mask_counts=mask.sum(0).tolist(),total_masked_sse=math.fsum(w.reshape(-1)))
def inputs(p):
 for item in p['inputs']:assert sha(item['path'])==item['sha256'],item['path']
 for n,h in p['source_hashes'].items():assert sha(D/n)==h,n
 for n,h in p['runtime_hashes'].items():assert sha(Path(p['restore_runtime'])/n)==h,n
 return p

def baseline(e):
 import numpy as np
 assert sha(e['baseline_values'])==e['baseline_sha256'];r=read(e['baseline_review']);assert r['passed'] and r['values']['sha256']==e['baseline_sha256'] and r['checkpoint_sha256']==e['parent_sha256']
 with np.load(e['baseline_values']) as z:a={k:z[k].copy() for k in ['indices','observations','actions','rewards','masks','cycles','conditions','initial_prediction']}
 n=e['terminal_rows'];assert a['observations'].shape==(n,52) and a['initial_prediction'].shape==(n,5) and len(a['indices'])==n and np.all(np.diff(a['indices'])>0)
 assert np.isfinite(a['initial_prediction']).all() and set(np.unique(a['masks']))<={0.,1.} and np.all(a['cycles']<=93) and np.count_nonzero(a['cycles']==93)==30
 for row in e['known_rows']:assert np.count_nonzero(a['indices']==row['replay_index'])==1
 return a

def complete(p):
 V=Path(p['complete_review']);finish=read(V/'FINISHED.json');r=read(V/'REVIEW.json');loss=read(V/'loss/REVIEW.json');health=read(V/'health/DIAGNOSIS.json')
 assert finish['completed'] and r['passed'] and loss['passed'] and health['cycle']==94 and health['optimizer_updates_performed']==0
 for m in p['methods']:
  x=r['methods'][m];assert x['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256'] and 0<x['new_transitions']<=41250 and x['new_transitions']==loss['methods'][m]['rows']
 return r

def preflight(p):
 import numpy as np
 results={}
 for m,e in p['methods'].items():
  a=baseline(e);s=stats(a['initial_prediction'],a['rewards'],a['masks']);weighted=(a['initial_prediction'].astype(float)-a['rewards'].astype(float)[:,None])**2*a['masks']
  np.testing.assert_allclose(s['masked_sse'],weighted.sum(0),rtol=1e-12,atol=1e-8)
  results[m]=dict(terminal_rows=len(a['indices']),initial_full93_only=True,stats=s,known_rows=e['known_rows'])
 try:complete(p)
 except FileNotFoundError:missing=True
 else:raise AssertionError('Expected still incomplete94 at registration')
 put(O/'PREFLIGHT_REVIEW.json',dict(passed=True,time=time.time(),methods=results,missing_complete94_rejected=missing,physics_steps=0,optimizer_updates=0,neural_forwards=0))

def run(p):
 import numpy as np
 os.sched_setaffinity(0,{11});sys.path.insert(0,p['restore_runtime'])
 from driver import validate_checkpoint,restore_consumer
 from frozen_helpers import capture_rng,restore_rng
 from validate_published_finite_check_20261025 import digest
 import torch
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 torch.set_num_threads(1);full=complete(p);results={};fig,axes=plt.subplots(3,3,figsize=(17,11),constrained_layout=True)
 for row,(m,e) in enumerate(p['methods'].items()):
  cp=Path(e['checkpoint']);h=full['methods'][m]['checkpoint_sha256'];assert sha(cp)==h
  ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(e['registration']);validate_checkpoint(ck,reg,complete=True)
  a=baseline(e);idx=a['indices'];arr=ck['replay']['arrays'];assert np.array_equal(idx,np.flatnonzero(arr['dones'][:e['parent_steps'],0]==1))
  for k in ['observations','actions','masks']:np.testing.assert_array_equal(arr[k][idx],a[k])
  np.testing.assert_array_equal(arr['rewards'][idx,0],a['rewards'])
  learner=restore_consumer(ck['learner'],reg,'cpu');before=digest(ck['learner']);replay_before=digest(ck['replay']);assert digest(learner.state_dict())==before;saved_rng=capture_rng(learner)
  with torch.no_grad():
   obs=torch.as_tensor(a['observations']);act=torch.as_tensor(a['actions']);pred=torch.stack([q(obs,act).reshape(-1) for q in learner.learner.agent.ensemble],1).numpy()
  restore_rng(learner,saved_rng)
  assert np.isfinite(pred).all() and digest(learner.state_dict())==before and digest(ck['learner'])==before and digest(ck['replay'])==replay_before and digest(capture_rng(learner))==digest(saved_rng) and sha(cp)==h
  groups={};selectors={'all':np.ones(len(idx),bool),'old_through92':a['cycles']<=92,'new93':a['cycles']==93}
  for group,sel in selectors.items():groups[group]={label:stats(q[sel],a['rewards'][sel],a['masks'][sel]) for label,q in [('complete93',a['initial_prediction']),('complete94',pred)]}
  old=((a['initial_prediction'].astype(float)-a['rewards'].astype(float)[:,None])**2*a['masks']).sum(1);new=((pred.astype(float)-a['rewards'].astype(float)[:,None])**2*a['masks']).sum(1)
  records=[]
  for known in e['known_rows']:
   j=int(np.flatnonzero(idx==known['replay_index'])[0]);records.append(dict(**known,mask=a['masks'][j].tolist(),reward=float(a['rewards'][j]),q93=a['initial_prediction'][j].tolist(),q94=pred[j].tolist(),masked_sse93=float(old[j]),masked_sse94=float(new[j])))
  out=O/(m+'_values.npz');np.savez_compressed(out,**a,complete94=pred)
  # Reopen persisted artifact, calculate independently using scalar fsum, retain every regression.
  with np.load(out) as z:
   for k in a:np.testing.assert_array_equal(z[k],a[k])
   np.testing.assert_array_equal(z['complete94'],pred)
   for group,sel in selectors.items():
    for label,key in [('complete93','initial_prediction'),('complete94','complete94')]:
     q=z[key][sel];rw=z['rewards'][sel];mask=z['masks'][sel]
     for j in range(5):
      err=[(float(v)-float(r))**2 for v,r in zip(q[:,j],rw)]
      np.testing.assert_allclose(math.fsum(x*float(w) for x,w in zip(err,mask[:,j])),groups[group][label]['masked_sse'][j],rtol=1e-12,atol=1e-8)
      np.testing.assert_allclose(math.fsum(err),groups[group][label]['all_row_sse'][j],rtol=1e-12,atol=1e-8)
  for col,key in enumerate(['masked_sse','all_row_sse']):
   ax=axes[row,col]
   for offset,label in [(-.18,'complete93'),(.18,'complete94')]:ax.bar(np.arange(5)+offset,groups['all'][label][key],width=.36,label=label)
   ax.set_title(m+' '+key);ax.legend();ax.grid(alpha=.2)
  ax=axes[row,2];ax.scatter(old,new,s=4,alpha=.5);maximum=max(float(old.max()),float(new.max()),1.);ax.plot([0,maximum],[0,maximum],ls='--');ax.set_xlabel('full93 masked row SSE');ax.set_ylabel('full94 masked row SSE');ax.set_title(m+' all retained full93 terminals');ax.grid(alpha=.2)
  result=dict(terminal_rows=len(idx),groups=groups,known_rows=records,regression_rows=int((new>old).sum()),improved_rows=int((new<old).sum()),largest20_regressions=[dict(index=int(idx[j]),cycle=int(a['cycles'][j]),old=float(old[j]),new=float(new[j]),change=float(new[j]-old[j])) for j in np.argsort(new-old)[-20:][::-1]],checkpoint_sha256=h,values_sha256=sha(out),full_learner_optimizer_replay_rng_unchanged=True,saved_scalar_arithmetic_verified=True,physics_steps=0,optimizer_updates=0)
  results[m]=result;put(O/(m+'_REVIEW.json'),result);del learner,ck,arr,obs,act;gc.collect()
 fig.suptitle('All8353 seen full93 terminals / original masks / five critics / zero updates\nNot independent generalization or a convergence gate');fig.savefig(O/'fixed93_terminal_93_94.png',dpi=150);plt.close(fig)
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,plot_sha256=sha(O/'fixed93_terminal_93_94.png'),actual_plot_inspection_pending=True,optimizer_updates=0,physics_steps=0,convergence_claim=False))
if __name__=='__main__':
 try:
  p=inputs(read(O/'PLAN.json'))
  if '--preflight' in sys.argv:preflight(p)
  else:run(p)
 except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
