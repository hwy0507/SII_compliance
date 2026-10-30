from pathlib import Path
import json,time,hashlib,math,os
import numpy as np
os.sched_setaffinity(0,{53})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).parent;read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
plan=read(D/'PLAN.json');r=read(D/'REVIEW.json');assert r['passed'];fig,axes=plt.subplots(3,2,figsize=(13,11),constrained_layout=True);methods={}
for i,(m,x) in enumerate(r['methods'].items()):
 assert sha(x['values']['path'])==x['values']['sha256'];z=np.load(x['values']['path']);mask=z['masks'].astype(float);y=z['rewards'].astype(float);n=len(y);assert n==x['terminal_rows'];assert np.array_equal(z['feature'],(z['preaction_peak_m']/(z['preaction_peak_m']+.0002)).astype(np.float32))
 curves=[json.loads(l) for l in Path(x['curve']['path']).read_text().splitlines()];assert sha(x['curve']['path'])==x['curve']['sha256'] and len(curves)==plan['updates_per_arm']+1 and [v['step'] for v in curves]==list(range(len(curves)))
 stats={}
 for phase in ['initial','final']:
  stats[phase]={}
  for arm in ['control','history']:
   q=z[phase+'_'+arm].astype(float);assert q.shape==mask.shape and np.isfinite(q).all();sse=np.array([math.fsum(float((q[k,c]-y[k,0])**2*mask[k,c]) for k in range(n)) for c in range(5)]);loss=math.fsum(float(sse[c]/mask[:,c].sum()) for c in range(5));log=curves[0 if phase=='initial' else -1]
   np.testing.assert_allclose(sse,log[arm+'_sse_by_critic'],rtol=1e-5,atol=1e-6);assert math.isclose(loss,log[arm+'_loss'],rel_tol=1e-5,abs_tol=1e-6)
   stats[phase][arm]=dict(masked_loss=loss,total_masked_sse=float(sse.sum()),sse_by_critic=sse.tolist(),inmask_sign_disagreements=int(((q*y<0)&(mask==1)).sum()))
 delta=stats['final']['history']['masked_loss']-stats['final']['control']['masked_loss'];methods[m]=dict(terminal_rows=n,stats=stats,history_minus_control_final_loss=delta,history_better_in_sample=delta<0,feature_nonzero_rows=int((z['feature']>0).sum()),known_preaction_penetration_failure_rows=int((z['preaction_peak_m']>.0002).sum()))
 for arm in ['control','history']:axes[i,0].plot([v['step'] for v in curves],[v[arm+'_loss'] for v in curves],label=arm)
 axes[i,0].set_title(m+' terminal-only fit');axes[i,0].set_yscale('log');axes[i,0].set_xlabel('Matched cloned critic update');axes[i,0].legend();axes[i,0].grid(alpha=.2)
 v0=stats['final']['control']['sse_by_critic'];v1=stats['final']['history']['sse_by_critic'];axes[i,1].plot(range(5),v0,'o-',label='control');axes[i,1].plot(range(5),v1,'o-',label='history');axes[i,1].set_title(m+' final masked SSE/all5');axes[i,1].legend();axes[i,1].grid(alpha=.2)
fig.suptitle('Fixed87 terminal in-sample fitting only; no actor update or policy promotion');fig.savefig(D/'paired_terminal_history_fit.png',dpi=140);plt.close(fig)
out=dict(passed=True,time=time.time(),methods=methods,all_endpoints_independently_recomputed=True,original_review_sha256=sha(D/'REVIEW.json'),source_sha256=sha(__file__),plot_sha256=sha(D/'paired_terminal_history_fit.png'),new_physics=0,new_network_forward=0,new_optimizer_updates=0,fit_is_not_reward_convergence=True)
p=D/'SAVED_REVIEW.json';p.write_text(json.dumps(out,indent=2)+'\n');assert read(p)==out
(D/'FINISHED.json').write_text(json.dumps(dict(passed=True,time=time.time(),saved_review_sha256=sha(p)),indent=2)+'\n');print(json.dumps({m:x['history_minus_control_final_loss'] for m,x in methods.items()}))
