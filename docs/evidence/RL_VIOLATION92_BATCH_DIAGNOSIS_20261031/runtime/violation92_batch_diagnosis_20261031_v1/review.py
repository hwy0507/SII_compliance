"""Independent saved-array arithmetic for all fixed64 native batches/method."""
from pathlib import Path
import os,json,hashlib,time,math,traceback
os.sched_setaffinity(0,{14})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_frozen_batch_diagnosis_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 plan=read(O/'PLAN.json');assert read(O/'FINISHED.json')['passed'];assert sha(__file__)==read(O/'REVIEW_PLAN.json')['source_sha256'];fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True);result={}
 for mi,(m,entry) in enumerate(plan['methods'].items()):
  root=O/m;r=read(root/'REVIEW.json');manifest=read(root/'RAW_MANIFEST.json')['files'];assert r['passed'] and r['first_batch_exact_repeat'] and r['full_learner_optimizer_replay_rng_restored'] and r['optimizer_updates']==r['backward_calls']==r['new_physics']==0
  assert len(r['records'])==len(manifest)==plan['batches']==64
  groups={};records=[]
  for n,(record,ref) in enumerate(zip(r['records'],manifest)):
   p=Path(ref['path']);assert sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes'] and record['batch']==n
   with np.load(p,allow_pickle=False) as z:
    idx=z['indices'];done=z['dones'].astype(bool);bits=z['bits'];q=z['q'].astype(np.float64);target=z['target'].astype(np.float64);mask=z['masks'].astype(np.float64);weights=mask*(1+127*done)[:,None];den=weights.sum(0);res=(q-target[:,None])**2*weights/den;perrow=res.sum(1);percritic=res.sum(0)
    assert len(idx)==65536 and q.shape==mask.shape==(65536,5) and np.isfinite(res).all();np.testing.assert_array_equal(target[done],z['rewards'][done].astype(np.float64));np.testing.assert_array_equal(den,record['denominators'])
    np.testing.assert_allclose(percritic,z['native_losses'],rtol=3e-6,atol=1e-6);np.testing.assert_allclose(percritic,record['native_losses'],rtol=3e-6,atol=1e-6);assert math.isclose(float(perrow.sum()),record['native_loss'],rel_tol=3e-6,abs_tol=1e-6)
    for key,sel in [('terminal',done),('nonterminal',~done),('old',idx<entry['parent_steps']),('new92',idx>=entry['parent_steps']),('bit0',bits==0),('bit1',bits==1)]:
     x=record['groups'][key];assert int(sel.sum())==x['count'];assert math.isclose(float(perrow[sel].sum()),x['loss'],rel_tol=1e-12,abs_tol=1e-12);np.testing.assert_allclose(res[sel].sum(0),x['per_critic'],rtol=1e-12,atol=1e-12)
    order=np.argsort(-perrow)[:20]
    for j,x in zip(order,record['top20']):
     assert int(idx[j])==x['replay_index'] and bool(done[j])==x['terminal'];assert math.isclose(float(perrow[j]),x['contribution'],rel_tol=1e-12,abs_tol=1e-12)
    pair=tuple(sorted(map(int,z['pair'])));assert list(z['pair'])==record['pair'];groups.setdefault(pair,[]).append(record['native_loss']);records.append(dict(batch=n,loss=record['native_loss'],terminal=record['groups']['terminal']['loss'],nonterminal=record['groups']['nonterminal']['loss'],top1_fraction=float(perrow[order[0]]/perrow.sum()),top20_fraction=float(perrow[order].sum()/perrow.sum())))
  losses=np.array([x['loss'] for x in records]);summary=dict(mean=float(losses.mean()),minimum=float(losses.min()),maximum=float(losses.max()),std=float(losses.std()),quantiles=np.quantile(losses,[.5,.9,.95,.99]).tolist(),mean_terminal_loss=float(np.mean([x['terminal'] for x in records])),mean_nonterminal_loss=float(np.mean([x['nonterminal'] for x in records])),target_pairs=[list(k) for k in sorted(groups)],maximum_batch=int(losses.argmax()))
  assert summary==r['summary'];maximum=r['records'][summary['maximum_batch']];pair_stats={','.join(map(str,k)):dict(count=len(v),mean=float(np.mean(v)),minimum=float(min(v)),maximum=float(max(v))) for k,v in sorted(groups.items())}
  result[m]=dict(summary=summary,mean_terminal_fraction=summary['mean_terminal_loss']/summary['mean'],pair_stats=pair_stats,maximum_batch=dict(index=maximum['batch'],loss=maximum['native_loss'],pair=maximum['pair'],groups=maximum['groups'],top20=maximum['top20']),max_top1_fraction=max(x['top1_fraction'] for x in records),mean_top1_fraction=float(np.mean([x['top1_fraction'] for x in records])),records=records,all_saved_raw_scalar_and_group_arithmetic_checked=True,source_review_sha256=sha(root/'REVIEW.json'),raw_manifest_sha256=sha(root/'RAW_MANIFEST.json'))
  ax=axes[mi,0];ax.plot(losses,label='Native total');ax.plot([x['terminal'] for x in records],label='Terminal');ax.plot([x['nonterminal'] for x in records],label='Nonterminal');ax.set_title(m+' frozen batch loss');ax.set_xlabel('Batch');ax.legend();ax.grid(alpha=.2)
  ax=axes[mi,1];pairs=sorted(groups);ax.boxplot([groups[k] for k in pairs],tick_labels=[','.join(map(str,k)) for k in pairs]);ax.set_title(m+' loss by sampled target pair');ax.set_xlabel('Zero-based critic pair; unequal observed counts');ax.grid(axis='y',alpha=.2)
 fig.suptitle('Full92 fixed-state native65536 batches;64 per method; zero updates\nSampling/target randomness diagnostic, not historical online spike replay')
 plot=O/'native_batch_decomposition.png';fig.savefig(plot,dpi=150);plt.close(fig)
 put(O/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),methods=result,source_sha256=sha(__file__),plot_sha256=sha(plot),all192_batches_retained=True,optimizer_updates=0,new_physics=0,actual_plot_inspection_pending=True,convergence_claim=False))
 print(json.dumps({m:{k:v for k,v in x.items() if k in ['summary','mean_terminal_fraction','pair_stats','max_top1_fraction']} for m,x in result.items()},indent=2))
try:main()
except BaseException as e:put(O/'REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
