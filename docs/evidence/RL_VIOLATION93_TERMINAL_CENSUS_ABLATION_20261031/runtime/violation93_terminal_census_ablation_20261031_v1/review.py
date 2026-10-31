"""Independently verify saved original and conditional losses; retain all terminal errors."""
from pathlib import Path
import json,time,hashlib,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_terminal_census_ablation_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def summarize(values):
 a=np.array(values);return dict(mean=float(a.mean()),std=float(a.std()),minimum=float(a.min()),maximum=float(a.max()),maximum_batch=int(a.argmax()))
plan=rd(O/'PLAN.json');results={};large=[];fig,axes=plt.subplots(3,3,figsize=(16,12),constrained_layout=True)
for ri,(m,e) in enumerate(plan['methods'].items()):
 r=rd(O/(m+'_REVIEW.json'));assert r['passed'];assert sha(r['values']['path'])==r['values']['sha256'];zfile=np.load(r['values']['path']);z={k:zfile[k] for k in zfile.files};zfile.close();assert list(z['arms'])==plan['arms'];np.testing.assert_array_equal(z['evaluate_updates'],plan['evaluate_updates']);popcodes=np.array([sum(int(v)*(2**j) for j,v in enumerate(row)) for row in z['masks']]);strata={c:np.flatnonzero(popcodes==c) for c in range(32)};oldfiles=rd(e['raw_manifest']['path'])['files'];outfiles=rd(r['raw_manifest']['path'])['files'];assert len(outfiles)==128;large+=outfiles;lookup={(x['arm'],x['batch']):x for x in outfiles};native={};termstats={};known=[];errors=(z['predictions'].astype(float)-z['rewards'][None,None,:,None])**2;weighted=errors*z['masks'][None,None]
 for ai,arm in enumerate(plan['arms']):
  np.testing.assert_array_equal(z['predictions'][ai,0],z['initial_prediction']);termstats[arm]={}
  for name,sel in [('old85',z['cycles']<=85),('new86_92',(z['cycles']>=86)&(z['cycles']<=92)),('new93',z['cycles']==93),('all',np.ones(len(z['indices']),bool))]:
   ms=np.array([[math.fsum(v[:,j]) for j in range(5)] for v in weighted[ai][:,sel,:]]);us=np.array([[math.fsum(v[:,j]) for j in range(5)] for v in errors[ai][:,sel,:]]);termstats[arm][name]=dict(rows=int(sel.sum()),percritic_masked_sse=ms.tolist(),percritic_unmasked_sse=us.tolist(),total_masked_sse=ms.sum(1).tolist(),total_unmasked_sse=us.sum(1).tolist(),max_masked_row_sse=weighted[ai][:,sel,:].sum(2).max(1).tolist())
 for stage in ['initial']+plan['arms']:
  si=0 if stage=='initial' else -1;ai=0 if stage=='initial' else plan['arms'].index(stage);t_error=errors[ai,si];records=[]
  for bi,item in enumerate(oldfiles):
   assert sha(item['path'])==item['sha256'];f=np.load(item['path']);b={k:f[k] for k in f.files};f.close()
   if stage=='initial':q=b['q'];stored=r['initial_native_batches'][bi]
   else:
    raw=lookup[stage,bi];assert sha(raw['path'])==raw['sha256'];q=np.load(raw['path']);stored=r['arms'][stage]['final_native_batches'][bi]
   assert q.shape==(65536,5);mask=b['masks'].astype(float);done=b['dones'].astype(bool);den=(mask*(1+127*done[:,None])).sum(0);err=(q.astype(float)-b['target'].astype(float)[:,None])**2;contrib=err*mask*(1+127*done[:,None])/den;percritic=contrib.sum(0);perrow=contrib.sum(1);np.testing.assert_allclose(percritic,stored['percritic'],rtol=1e-12,atol=1e-10);assert math.isclose(math.fsum(perrow),stored['original_loss'],rel_tol=1e-12,abs_tol=1e-10)
   codes=np.array([sum(int(v)*(2**j) for j,v in enumerate(row)) for row in b['masks'][done]]);conditional=contrib[~done].sum(0);counts=np.bincount(codes,minlength=32)
   for code,n in enumerate(counts):
    if not n:continue
    rows=strata[code];assert len(rows)>0
    for j in range(5):conditional[j]+=128*int(n)*math.fsum(t_error[rows,j]*z['masks'][rows,j])/(len(rows)*den[j])
   np.testing.assert_array_equal(counts,stored['terminal_pattern_counts']);assert math.isclose(float(conditional.sum()),stored['conditional_loss'],rel_tol=2e-7,abs_tol=2e-7)
   order=np.argsort(-perrow,kind='stable')[:5];records.append(dict(batch=bi,original_loss=float(percritic.sum()),conditional_loss=float(conditional.sum()),top5=[dict(index=int(b['indices'][i]),terminal=bool(done[i]),contribution=float(perrow[i])) for i in order]))
  native[stage]=dict(original=summarize([v['original_loss'] for v in records]),conditional=summarize([v['conditional_loss'] for v in records]),records=records)
 if m=='impedance':
  for idx in plan['known_impedance_indices']:
   where=np.flatnonzero(z['indices']==idx);assert len(where)==1;j=int(where[0]);known.append(dict(index=idx,cycle=int(z['cycles'][j]),condition=str(z['conditions'][j]),reward=float(z['rewards'][j]),mask=z['masks'][j].tolist(),predictions=z['predictions'][:,:,j,:].tolist(),masked_sse=weighted[:,:,j,:].sum(2).tolist()))
 for ai,arm in enumerate(plan['arms']):
  axes[ri,0].plot(np.arange(1,257),z['training_curves'][ai],label=arm);axes[ri,1].plot(range(64),[x['original_loss'] for x in native[arm]['records']],label=arm)
  axes[ri,2].plot(plan['evaluate_updates'],termstats[arm]['all']['total_masked_sse'],marker='o',label=arm+' all');axes[ri,2].plot(plan['evaluate_updates'],termstats[arm]['new93']['total_masked_sse'],ls='--',label=arm+' new93')
 axes[ri,1].plot(range(64),[x['original_loss'] for x in native['initial']['records']],alpha=.4,label='initial full93');axes[ri,0].set(title=m+' objective used for disposable update',xlabel='Update',ylabel='Sampled / conditional estimator');axes[ri,1].set(title=m+' ORIGINAL sampled loss after fixed256',xlabel='Fixed native batch',ylabel='Original masked mixed-batch MSE');axes[ri,2].set(title=m+' all-terminal / new93 error',xlabel='Update',ylabel='Original terminal masked SSE')
 for ax in axes[ri]:ax.legend(fontsize=6);ax.grid(alpha=.2)
 results[m]=dict(native=native,terminals=termstats,known_rows=known,all64_initial_and128_final_raw_q_arithmetic_checked=True,all_terminal_masks_and_unmasked_errors_retained=True,values_sha256=r['values']['sha256'])
fig.suptitle('Conditional terminal census at full93: fixed-target mixed-batch critic-only comparison\nBoth original loss and terminal errors retained; extra census compute; no actor/target update or rollout generalization')
plot=O/'terminal_census_ablation.png';fig.savefig(plot,dpi=150);plt.close(fig);put(O/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),methods=results,plot=dict(path=str(plot),sha256=sha(plot)),formal_updates=0,new_physics=0));put(O/'LARGE_STORAGE_REVIEW.json',dict(passed=True,time=time.time(),files=large,total_bytes=sum(x['bytes'] for x in large),scope='384 final native q arrays verified on SSD; source192 NPZ remain prior SSD archive with verified hashes; large arrays excluded from Git/tar.'));print(json.dumps({m:{s:x['original'] for s,x in r['native'].items()} for m,r in results.items()},indent=2))
