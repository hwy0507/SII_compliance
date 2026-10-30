"""Independent scalar endpoint arithmetic for the registered matched bit fit."""
from pathlib import Path
import hashlib,json,math,os,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');assert sha(__file__)==plan['sources']['review_saved.py'];os.sched_setaffinity(0,{plan['cpu']})
r=read(D/'REVIEW.json');assert r['passed'] and r['plan_sha256']==sha(D/'PLAN.json')
fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True);methods={}
for i,(m,x) in enumerate(r['methods'].items()):
 entry=plan['methods'][m];assert sha(x['values']['path'])==x['values']['sha256'] and sha(x['curve']['path'])==x['curve']['sha256']
 with np.load(x['values']['path']) as z:arrays={k:z[k].copy() for k in z.files}
 with np.load(entry['values']['path']) as old:
  for k in ('indices','observations51','actions','rewards','masks','complete89'):np.testing.assert_array_equal(old[k],arrays[k])
 raw=np.load(entry['sidecar']['path'],mmap_mode='r');np.testing.assert_array_equal(raw[arrays['indices'],0],arrays['preaction_peak_m']);np.testing.assert_array_equal(arrays['bit'],(arrays['preaction_peak_m']>.0002).astype(np.float32))
 np.testing.assert_array_equal(arrays['initial_control'],arrays['initial_bit'])
 mask=arrays['masks'].astype(float);y=arrays['rewards'].astype(float);n=len(y);assert n==entry['terminal_rows']==x['terminal_rows']
 curves=[json.loads(l) for l in Path(x['curve']['path']).read_text().splitlines()];assert len(curves)==plan['updates_per_arm']+1 and [c['step'] for c in curves]==list(range(len(curves)))
 for c in curves:
  for arm in ('control','bit'):assert np.isfinite(c[arm+'_loss']) and np.isfinite(c[arm+'_sse_by_critic']).all()
 stats={}
 for phase in ('initial','final'):
  stats[phase]={}
  for arm in ('control','bit'):
   q=arrays[phase+'_'+arm].astype(float);assert q.shape==mask.shape and np.isfinite(q).all();sse=[math.fsum((float(q[k,j])-float(y[k,0]))**2*float(mask[k,j]) for k in range(n)) for j in range(5)]
   loss=math.fsum(sse[j]/math.fsum(mask[:,j]) for j in range(5));logged=curves[0 if phase=='initial' else -1]
   np.testing.assert_allclose(sse,logged[arm+'_sse_by_critic'],rtol=1e-5,atol=1e-6);assert math.isclose(loss,logged[arm+'_loss'],rel_tol=1e-5,abs_tol=1e-6)
   stats[phase][arm]=dict(masked_loss=loss,total_masked_sse=math.fsum(sse),sse_by_critic=sse,inmask_sign_disagreements=int(((q*y<0)&(mask==1)).sum()))
 delta=stats['final']['bit']['masked_loss']-stats['final']['control']['masked_loss'];methods[m]=dict(terminal_rows=n,stats=stats,bit_minus_control_final_loss=delta,bit_better_in_sample=delta<0,bit_nonzero_rows=int(arrays['bit'].sum()),bit_minus_control_final_sse_by_critic=(np.array(stats['final']['bit']['sse_by_critic'])-np.array(stats['final']['control']['sse_by_critic'])).tolist())
 for arm in ('control','bit'):axes[i,0].plot([c['step'] for c in curves],[c[arm+'_loss'] for c in curves],label=arm);axes[i,1].plot(range(5),stats['final'][arm]['sse_by_critic'],'o-',label=arm)
 axes[i,0].set_title(m+' fixed87 terminal fit from89');axes[i,0].set_yscale('log');axes[i,0].set_xlabel('Matched clone update')
 axes[i,1].set_title(m+' final masked SSE, all5 critics');axes[i,1].set_xticks(range(5))
 for ax in axes[i]:ax.legend();ax.grid(alpha=.2)
fig.suptitle('Matched 52-input clones: zero control vs causal violation bit; seen terminals only');fig.savefig(D/'paired_violation_bit_fit.png',dpi=150);plt.close(fig)
report=dict(passed=True,time=time.time(),methods=methods,all_endpoints_independently_recomputed=True,original_review_sha256=sha(D/'REVIEW.json'),source_sha256=sha(__file__),plan_sha256=sha(D/'PLAN.json'),plot_sha256=sha(D/'paired_violation_bit_fit.png'),new_physics=0,new_network_forward=0,new_optimizer_updates=0,fit_is_not_reward_convergence=True)
put(D/'SAVED_REVIEW.json',report);put(D/'FINISHED.json',dict(passed=True,time=time.time(),saved_review_sha256=sha(D/'SAVED_REVIEW.json')))
print(json.dumps({m:x['bit_minus_control_final_loss'] for m,x in methods.items()}))
