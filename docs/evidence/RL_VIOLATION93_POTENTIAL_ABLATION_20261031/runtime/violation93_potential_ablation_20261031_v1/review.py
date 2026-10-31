from pathlib import Path
import json,time,hashlib,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_potential_ablation_20261031_v1';A=B/'runs/violation93_potential_audit_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=rd(O/'PLAN.json');results={};fig,axes=plt.subplots(3,3,figsize=(16,12),constrained_layout=True)
for ri,m in enumerate(plan['methods']):
 r=rd(O/(m+'_REVIEW.json'));assert r['passed'];assert rd(A/(m+'_SAVED_REVIEW.json'))['passed'];p=Path(r['values']['path']);assert sha(p)==r['values']['sha256']
 with np.load(p) as f:z={k:f[k] for k in f.files}
 raw=rd(A/(m+'_REVIEW.json'))['terminal_values'];assert sha(raw['path'])==raw['sha256']
 with np.load(raw['path']) as f:
  for k in f.files:np.testing.assert_array_equal(z[k],f[k])
 fit=z['cycles']<=85;held=~fit;np.testing.assert_array_equal(z['fitting'],fit);np.testing.assert_array_equal(z['feature_mean'],z['features'][fit].mean(0));sd=z['features'][fit].std(0);sd=np.where(sd<=1e-8,1.,sd);np.testing.assert_array_equal(z['feature_scale'],sd);np.testing.assert_array_equal(z['evaluate_updates'],plan['evaluate_updates']);assert list(z['arms'])==plan['arms'];assert z['predictions'].shape==(3,6,len(fit),5)
 allstats={};errors=(z['predictions'].astype(float)-z['rewards'][None,None,:,None])**2;weighted=errors*z['masks'][None,None];records=[]
 for ai,arm in enumerate(plan['arms']):
  np.testing.assert_array_equal(z['predictions'][ai,0],z['initial_prediction']);allstats[arm]={}
  for split,sel in [('fit',fit),('held',held),('all',np.ones(len(fit),bool))]:
   ms=np.array([[math.fsum(row[:,j]) for j in range(5)] for row in weighted[ai][:,sel,:]]);us=np.array([[math.fsum(row[:,j]) for j in range(5)] for row in errors[ai][:,sel,:]]);allstats[arm][split]=dict(per_critic_masked_sse=ms.tolist(),per_critic_unmasked_sse=us.tolist(),total_masked_sse=ms.sum(1).tolist(),max_masked_row_sse=weighted[ai][:,sel,:].sum(2).max(1).tolist());last=r['final'][arm][split];np.testing.assert_allclose(ms[-1],last['masked_sse'],rtol=1e-12,atol=1e-8);np.testing.assert_allclose(us[-1],last['all_row_sse'],rtol=1e-12,atol=1e-8)
  for si,step in enumerate(plan['evaluate_updates']):
   if step<256:
    loss=(weighted[ai,si,fit,:].sum(0)/z['masks'][fit].sum(0)).sum();assert math.isclose(loss,z['training_curves'][ai,step],rel_tol=3e-6,abs_tol=3e-6),(m,arm,step,loss,z['training_curves'][ai,step])
  axes[ri,0].plot(np.arange(1,257),z['training_curves'][ai],label=arm);axes[ri,1].plot(plan['evaluate_updates'],allstats[arm]['held']['total_masked_sse'],marker='o',label=arm)
 if m=='impedance':
  for idx in plan['known_impedance_indices']:
   w=np.flatnonzero(z['indices']==idx);assert len(w)==1;j=int(w[0]);records.append(dict(index=idx,cycle=int(z['cycles'][j]),condition=str(z['conditions'][j]),fitting=bool(fit[j]),reward=float(z['rewards'][j]),features=z['features'][j].tolist(),mask=z['masks'][j].tolist(),predictions=z['predictions'][:,:,j,:].tolist(),masked_sse=weighted[:,:,j,:].sum(2).tolist()))
 held_positions=np.flatnonzero(held);base_sse=weighted[0,-1,held,:].sum(1);worst=held_positions[np.argsort(-base_sse,kind='stable')[:5]]
 for ai,arm in enumerate(plan['arms']):axes[ri,2].bar(np.arange(5)+(ai-1)*.25,weighted[ai,-1,worst,:].sum(1),width=.25,label=arm)
 axes[ri,0].set(title=m+' fitting terminal masked MSE',xlabel='Disposable full-batch updates',ylabel='Sum of five masked means');axes[ri,1].set(title=m+' diagnostic-held terminal SSE',xlabel='Disposable full-batch updates',ylabel='Original masked SSE');axes[ri,2].set(title=m+' baseline-final worst5 held rows',xlabel='Replay index (fixed across arms)',ylabel='Original masked SSE');axes[ri,2].set_xticks(range(5),[str(x) for x in z['indices'][worst]],rotation=30)
 for ax in axes[ri]:ax.legend(fontsize=7);ax.grid(alpha=.2)
 comparisons={}
 for arm in ['potential','potential_history']:
  comparisons[arm]={}
  for split in ['fit','held','all']:
   base=allstats['baseline'][split]['total_masked_sse'][-1];value=allstats[arm][split]['total_masked_sse'][-1];comparisons[arm][split]=dict(baseline=base,candidate=value,relative_change_percent=100*(value-base)/max(abs(base),1e-12))
 results[m]=dict(statistics=allstats,final_vs_matched_baseline=comparisons,known_rows=records,worst5_held_by_baseline_final=z['indices'][worst].tolist(),source_sha256=r['values']['sha256'],all_saved_inputs_initial_predictions_scaling_loss_and_final_statistics_checked=True)
fig.suptitle('Full93 disposable terminal-only information ablation; 256 fixed updates per arm\n86-93 excluded from auxiliary fitting but already seen by source checkpoint; not independent generalization')
plot=O/'potential_ablation.png';fig.savefig(plot,dpi=150);plt.close(fig);put(O/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),methods=results,plot=dict(path=str(plot),sha256=sha(plot)),formal_updates=0,new_physics=0,disposable_updates=2313,scope=plan['diagnostic_holdout']));print(json.dumps({m:x['final_vs_matched_baseline'] for m,x in results.items()},indent=2))
