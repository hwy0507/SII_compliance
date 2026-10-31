from pathlib import Path
import os,sys,json,time,hashlib,shutil,math,gc,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle100_20261031_v1';O=B/'runs/census100_prefix_terminal_probe_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 os.sched_setaffinity(0,{12});plan=read(D/'PLAN.json');assert sha(__file__)==plan['source_sha256']
 for x in plan['inputs']:assert sha(x['path'])==x['sha256']
 assert not O.exists();O.mkdir();start=time.time()
 sys.path.insert(0,str(B/'runtime/census100_continuation_20261031_v1'))
 from driver import validate_checkpoint,restore_consumer
 from validate_published_finite_check_20261025 import digest
 from frozen_helpers import capture_rng,restore_rng
 sys.path.insert(0,str(B/'runtime/census100_terminal_20261031_v1'))
 from terminal100 import baseline,stats,inputs
 p=inputs(read(B/'runs/census100_fixed99_terminal_20261031_v1/PLAN.json'))
 import torch,numpy as np
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 torch.set_num_threads(1);methods={};fig,axes=plt.subplots(3,2,figsize=(13,11),constrained_layout=True)
 for row,(m,e) in enumerate(p['methods'].items()):
  assert time.time()-start<plan['budget_seconds'];reg=read(R/m/'REGISTRATION.json');source=R/m/'train/checkpoint_latest.pt';dest=O/(m+'_snapshot.pt')
  with source.open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst)
  h=sha(dest);ck=torch.load(dest,map_location='cpu',weights_only=False);validate_checkpoint(ck,reg,complete=False);assert ck['boundary']!='complete_condition_cycle';assert ck['steps']>=e['parent_steps']+5000
  # Every registered old terminal and original mask must still match the actual snapshot.
  a=baseline(e);arr=ck['replay']['arrays'];idx=a['indices'];np.testing.assert_array_equal(idx,np.flatnonzero(arr['dones'][:e['parent_steps'],0]))
  for k in ['observations','actions','masks']:np.testing.assert_array_equal(arr[k][idx],a[k])
  np.testing.assert_array_equal(arr['rewards'][idx,0],a['rewards'])
  l=restore_consumer(ck['learner'],reg,'cpu');before=digest(l.state_dict());assert before==digest(ck['learner']);replay=digest(ck['replay']);rng=capture_rng(l)
  with torch.no_grad():
   pieces=[]
   for lo,hi in zip(e['prediction_block_boundaries'],e['prediction_block_boundaries'][1:]):
    obs=torch.as_tensor(a['observations'][lo:hi]);act=torch.as_tensor(a['actions'][lo:hi]);pieces.append(torch.stack([q(obs,act).reshape(-1) for q in l.learner.agent.ensemble],1).numpy())
   pred=np.concatenate(pieces)
  restore_rng(l,rng);assert np.isfinite(pred).all() and digest(l.state_dict())==before and digest(ck['learner'])==before and digest(ck['replay'])==replay and digest(capture_rng(l))==digest(rng)
  old=stats(a['initial_prediction'],a['rewards'],a['masks']);new=stats(pred,a['rewards'],a['masks']);ow=((a['initial_prediction'].astype(float)-a['rewards'].astype(float)[:,None])**2*a['masks']).sum(1);nw=((pred.astype(float)-a['rewards'].astype(float)[:,None])**2*a['masks']).sum(1)
  values=O/(m+'_values.npz');np.savez_compressed(values,**a,prefix_prediction=pred)
  with np.load(values) as z:
   for k in a:np.testing.assert_array_equal(z[k],a[k])
   np.testing.assert_array_equal(z['prefix_prediction'],pred)
   for k,s in [('initial_prediction',old),('prefix_prediction',new)]:
    for j in range(5):
     err=[(float(v)-float(r))**2 for v,r in zip(z[k][:,j],z['rewards'])];masked=math.fsum(x*float(w) for x,w in zip(err,z['masks'][:,j]));assert math.isclose(masked,s['masked_sse'][j],rel_tol=1e-12,abs_tol=1e-8);assert math.isclose(math.fsum(err),s['all_row_sse'][j],rel_tol=1e-12,abs_tol=1e-8)
  known=[]
  for item in e['known_rows']:
   j=int(np.flatnonzero(idx==item['replay_index'])[0]);known.append(dict(**item,condition=str(a['conditions'][j]),mask=a['masks'][j].tolist(),reward=float(a['rewards'][j]),complete99_prediction=a['initial_prediction'][j].tolist(),prefix100_prediction=pred[j].tolist(),complete99_masked_sse=float(ow[j]),prefix100_masked_sse=float(nw[j])))
  assert sha(dest)==h
  result=dict(passed=True,steps=ck['steps'],new_steps=ck['steps']-e['parent_steps'],cycle=100,boundary=ck['boundary'],snapshot=ref(dest),registration=ref(R/m/'REGISTRATION.json'),baseline_values=ref(e['baseline_values']),values=ref(values),terminal_rows=len(idx),old=old,new=new,masked_sse_change_percent=(new['total_masked_sse']/old['total_masked_sse']-1)*100,improvements=int((nw<ow).sum()),regressions=int((nw>ow).sum()),known_rows=known,full_learner_adam_replay_rng_unchanged=True,saved_scalar_arithmetic_verified=True)
  methods[m]=result;put(O/(m+'_REVIEW.json'),result)
  for off,label,stat in [(-.18,'complete99',old),(.18,'prefix100',new)]:axes[row,0].bar(np.arange(5)+off,stat['masked_sse'],width=.36,label=label)
  axes[row,0].set_title(m+' all retained99 terminal masked SSE');axes[row,0].legend();axes[row,0].grid(alpha=.2)
  axes[row,1].scatter(ow,nw,s=4,alpha=.5);mx=max(float(ow.max()),float(nw.max()),1.);axes[row,1].plot([0,mx],[0,mx],ls='--');axes[row,1].set_xlabel('complete99 masked row SSE');axes[row,1].set_ylabel('prefix100 masked row SSE');axes[row,1].set_title(m+' all rows, including failures');axes[row,1].grid(alpha=.2)
  print(m,result['new_steps'],result['masked_sse_change_percent'],flush=True);del ck,arr,l,obs,act;gc.collect()
 fig.suptitle('Exploratory current100 snapshot on fixed8893 seen99 terminals / zero updates\nDifferent snapshot steps per method; not full100 or independent generalization');fig.savefig(O/'prefix_terminal.png',dpi=150);plt.close(fig)
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=methods,plot=ref(O/'prefix_terminal.png'),plot_inspection_pending=True,physics_steps=0,optimizer_updates=0,convergence_claim=False,scope='Single current partial100 snapshot per method, selected after first5000 loss inspection; fixed8893 old99 terminal population, original masks/all5 critics/prediction blocks. Diagnostic only, not complete100, not an acceptance window, no weights promoted. No sampled indices: cannot causally attribute original-loss spikes.'))
 put(O/'FINISHED.json',dict(passed=True,time=time.time(),elapsed_s=time.time()-start))
if __name__=='__main__':
 try:main()
 except BaseException:
  put(D/'FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
