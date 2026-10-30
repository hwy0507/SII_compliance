"""Descriptive complete87->88 comparison on every registered training condition."""
from pathlib import Path
import os,json,hashlib,time,math
D=Path(__file__).resolve().parent;B=D.parents[1]
O=B/'runs/parameter_history_cycle88_review_20261030_v2'
P=B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1'
os.sched_setaffinity(0,{10})
read=lambda p:json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
assert read(O/'FINISHED.json')['completed']
old,new=read(P/'REVIEW.json'),read(O/'REVIEW.json')
a,b=read(P/'health/DIAGNOSIS.json'),read(O/'health/DIAGNOSIS.json')
loss=read(O/'loss/REVIEW.json');assert old['passed'] and new['passed'] and loss['passed']
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(3,1,figsize=(15,11),constrained_layout=True);results={}
for i,m in enumerate(['impedance','admittance','vmc']):
    before={x['condition']:x for x in a['methods'][m]['episodes'] if x['cycle']==87}
    after={x['condition']:x for x in b['methods'][m]['episodes'] if x['cycle']==88}
    reg=read(B/'runs/parameter_history_cycle88_20261030_v2'/m/'REGISTRATION.json')
    cases=[c['id'] for c in reg['conditions']]
    assert set(before)==set(after)==set(cases) and len(cases)==30
    assert new['methods'][m]['checkpoint_sha256']==b['methods'][m]['checkpoint_sha256']
    rows=[]
    for c in cases:
        x,y=before[c],after[c]
        terms={k:y['reward_terms'][k]-x['reward_terms'][k] for k in x['reward_terms']}
        delta=y['reward']-x['reward'];assert math.isclose(math.fsum(terms.values()),delta,abs_tol=1e-7)
        rows.append(dict(condition=c,reward87=x['reward'],reward88=y['reward'],reward_delta=delta,
            task87=x['task_success'],task88=y['task_success'],strict87=x['strict_success'],strict88=y['strict_success'],
            task_change=int(y['task_success'])-int(x['task_success']),strict_change=int(y['strict_success'])-int(x['strict_success']),
            abort87=x['abort_reason'],abort88=y['abort_reason'],stage87=x['final_task_stage'],stage88=y['final_task_stage'],reward_term_deltas=terms))
    for stage,report in [(87,old),(88,new)]:
        assert sum(r['task'+str(stage)] for r in rows)==report['methods'][m]['task']
        assert sum(r['strict'+str(stage)] for r in rows)==report['methods'][m]['strict']
        assert math.isclose(math.fsum(r['reward'+str(stage)] for r in rows)/30,report['methods'][m]['reward_mean'],abs_tol=1e-12)
    terms={k:math.fsum(r['reward_term_deltas'][k] for r in rows)/30 for k in rows[0]['reward_term_deltas']}
    mean=math.fsum(r['reward_delta'] for r in rows)/30;assert math.isclose(mean,math.fsum(terms.values()),abs_tol=1e-8)
    results[m]=dict(rows=rows,mean_reward_delta=mean,reward_terms_mean_delta=terms,
        task_gained=[r['condition'] for r in rows if r['task_change']>0],task_lost=[r['condition'] for r in rows if r['task_change']<0],
        strict_gained=[r['condition'] for r in rows if r['strict_change']>0],strict_lost=[r['condition'] for r in rows if r['strict_change']<0],
        q_loss=loss['methods'][m]['stats']['agent_train/q_loss'],actor_loss=loss['methods'][m]['stats']['agent_train/actor_loss'])
    ax=axes[i];xs=np.arange(30);ax.bar(xs,[r['reward_delta'] for r in rows],color=['green' if r['strict_change']>0 else 'red' if r['strict_change']<0 else 'steelblue' for r in rows]);ax.axhline(0,color='black',lw=.5)
    ax.set_xticks(xs,[c.replace('passive_corner_train_','p').replace('active_short_train_','s').replace('active_long_train_','l') for c in cases],rotation=90,fontsize=8)
    ax.set_title(m+' complete training88 minus87; mean '+str(round(mean,6)));ax.set_ylabel('Return difference');ax.grid(axis='y',alpha=.2)
fig.suptitle('All90 training conditions retained; Strict gains green/losses red\nIncludes additional online updates and history critic revision, not a causal comparison')
fig.savefig(D/'training87_88_all90.png',dpi=150);plt.close(fig)
put(D/'INTERPRETATION.json',dict(passed=True,time=time.time(),methods=results,inputs=[ref(p) for p in [P/'REVIEW.json',P/'health/DIAGNOSIS.json',O/'REVIEW.json',O/'health/DIAGNOSIS.json',O/'loss/REVIEW.json']],plot=ref(D/'training87_88_all90.png'),physical_steps=0,optimizer_updates=0,convergence_claim=False,scope='Descriptive all-condition online87->88 comparison; per-term decomposition is arithmetic, not causal. No stable-window claim across revisions.'))
print(json.dumps({m:{k:v for k,v in r.items() if k!='rows'} for m,r in results.items()},indent=2))
