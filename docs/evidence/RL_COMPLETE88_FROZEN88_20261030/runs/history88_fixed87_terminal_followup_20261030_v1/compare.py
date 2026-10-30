"""Compare complete88 to untouched87 on the prospectively fixed87 terminal set."""
from pathlib import Path
import gc, json, os, sys, time, traceback
D=Path(__file__).resolve().parent; B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
    import hashlib
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json'); os.sched_setaffinity(0,{plan['cpu']})
os.environ['OMP_NUM_THREADS']=os.environ['OPENBLAS_NUM_THREADS']='1'
sys.path[:0]=[plan['runtime'],str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from history_consumers import restore_learner
from validate_published_finite_check_20261025 import digest
from frozen_helpers import capture_rng
started=time.monotonic(); torch.set_num_threads(1)
try:
    assert sha(__file__)==plan['script_sha256']
    for n,h in plan['sources'].items():assert sha(Path(plan['runtime'])/n)==h
    for x in plan['inputs']:assert sha(x['path'])==x['sha256']
    for name in ['REVIEW.json','FINISHED.json','loss/REVIEW.json']:
        report=read(Path(plan['complete88_review'])/name)
        assert report.get('passed',report.get('completed',False))
    full=read(Path(plan['complete88_review'])/'REVIEW.json')
    results={}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(13,11))
    for i,(method,reg) in enumerate(plan['methods'].items()):
        assert time.monotonic()-started<plan['budget_seconds']
        cp=Path(reg['checkpoint']); expected=full['methods'][method]['checkpoint_sha256']
        assert sha(cp)==expected
        ck=torch.load(cp,map_location='cpu',weights_only=False)
        assert ck['cycle']==88 and ck['boundary']=='complete_condition_cycle'
        assert ck['steps']==reg['binding']['rows']+41250
        with np.load(reg['baseline_values']) as saved:
            old={k:saved[k].copy() for k in ['indices','feature','observations','actions','rewards','masks','initial_control']}
        idx=old['indices']; arr=ck['replay']['arrays']
        assert len(idx)==reg['terminal_rows']
        assert np.array_equal(idx,np.flatnonzero(arr['dones'][:reg['binding']['rows'],0]==1))
        assert np.array_equal(arr['observations'][idx,:50],old['observations'])
        assert np.array_equal(arr['observations'][idx,50],old['feature'])
        for k in ['actions','rewards','masks']:assert np.array_equal(arr[k][idx],old[k])
        obs_np=arr['observations'][idx].copy()
        learner=restore_learner(ck['learner'],reg['binding'],B/'runtime/source_train17_clock',plan['device'],ck['seed'])
        initial=digest(ck['learner']); assert digest(learner.state_dict())==initial
        rng=digest(capture_rng(learner))
        obs=torch.as_tensor(obs_np,device=learner.device)
        acts=torch.as_tensor(old['actions'],device=learner.device)
        with torch.no_grad():
            current=torch.stack([q(obs,acts).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
            zero=obs.clone();zero[:,50]=0
            zero_values=torch.stack([q(zero,acts).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
        assert np.isfinite(current).all() and np.isfinite(zero_values).all()
        assert digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng
        out=D/(method+'_values.npz')
        np.savez_compressed(out,**old,observations51=obs_np,complete88=current,complete88_history_zero=zero_values)
        # Independent scalar arithmetic on saved predictions, not a second forward.
        stats={}
        with np.load(out) as saved:
            import math
            for label in ['initial_control','complete88','complete88_history_zero']:
                errors=(saved[label].astype(np.float64)-saved['rewards'].astype(np.float64))**2
                masks=saved['masks'].astype(np.float64)
                sse=[math.fsum(float(e)*float(m) for e,m in zip(errors[:,j],masks[:,j])) for j in range(5)]
                np.testing.assert_allclose(sse,(errors*masks).sum(0),rtol=1e-12,atol=1e-8)
                counts=masks.sum(0)
                stats[label]=dict(masked_sse=sse,masked_mse=(np.array(sse)/counts).tolist(),
                    all_row_sse=errors.sum(0).tolist(),mask_counts=counts.tolist())
        for col,(key,title) in enumerate([('masked_mse','Original-mask terminal MSE'),('all_row_sse','All-row terminal SSE')]):
            ax=axes[i,col]
            for shift,label in [(-.22,'initial_control'),(0,'complete88'),(.22,'complete88_history_zero')]:
                ax.bar(np.arange(5)+shift,stats[label][key],width=.22,label=label)
            ax.set_title(method+' '+title);ax.set_xticks(range(5));ax.set_xlabel('Critic');ax.legend(fontsize=7)
        result=dict(terminal_rows=len(idx),baseline_role='Untouched87 initial_control only; no fitted final weights',
            checkpoint_sha256=expected,values_sha256=sha(out),stats=stats,
            complete88_minus87_masked_sse=(np.array(stats['complete88']['masked_sse'])-stats['initial_control']['masked_sse']).tolist(),
            learner_and_rng_unchanged=True,original_terminal_inputs_exact=True)
        results[method]=result;put(D/(method+'_REVIEW.json'),result)
        assert sha(cp)==expected
        del ck,arr,learner,obs,acts,zero;gc.collect();torch.cuda.empty_cache()
    fig.tight_layout();fig.savefig(D/'fixed87_terminal_followup.png',dpi=150);plt.close(fig)
    put(D/'REVIEW.json',dict(passed=True,methods=results,elapsed_s=time.monotonic()-started,
        plot_sha256=sha(D/'fixed87_terminal_followup.png'),plot_viewed=False,
        physical_steps=0,optimizer_updates=0,limits=plan['limits']))
except BaseException as e:
    put(D/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
