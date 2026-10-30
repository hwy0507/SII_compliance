from pathlib import Path
import json,hashlib,math,time,os
os.environ['MPLBACKEND']='Agg';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import matplotlib.pyplot as plt
os.sched_setaffinity(0,{53});D=Path(__file__).parent;B=D.parents[1];F=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1'
read=lambda p:json.loads(p.read_text())
assert (F/'FINISHED.json').exists(),'Complete86 fixed2514 followup not ready'
for n in ['FINISHED.json','REVIEW.json','SAVED_REVIEW.json']:assert read(F/n)['passed']
r=read(F/'REVIEW.json');fig,axs=plt.subplots(3,2,figsize=(13,12),constrained_layout=True)
for col,m in enumerate(['vmc','admittance']):
 a=r['methods'][m];p=F/(m+'_all2514.jsonl');assert hashlib.sha256(p.read_bytes()).hexdigest()==a['allrows_sha256'];rows=[json.loads(l) for l in p.read_text().splitlines()];assert len(rows)==2514;new=np.array([v['cohort']=='new84' for v in rows]);assert new.sum()==30
 q={cycle:np.array([v['sse'+cycle] for v in rows]) for cycle in ['84','85','86']}
 for cycle,v in q.items():assert np.isfinite(v).all() and np.all(v>=0) and math.isclose(math.fsum(v),a['total_sse'][cycle],rel_tol=1e-12)
 for line,before in enumerate(['84','85']):
  ax=axs[line,col];x=np.log1p(q[before]);y=np.log1p(q['86']);ax.scatter(x[~new],y[~new],s=8,alpha=.3,label='2484 before84');ax.scatter(x[new],y[new],s=28,c='#e67700',label='All30 new84');lim=float(max(x.max(),y.max()));ax.plot([0,lim],[0,lim],ls='--',c='gray');ax.set(title=f'{m}: fixed2514, {before} to86',xlabel=f'log(1 + masked SSE), frozen{before}',ylabel='log(1 + masked SSE), frozen86');ax.legend()
 ax=axs[2,col];cs=a['critics'];assert [v['critic'] for v in cs]==list(range(5));axis=np.arange(5)
 for offset,cycle in zip([-.25,0,.25],['84','85','86']):ax.bar(axis+offset,[v['sse'+cycle] for v in cs],width=.25,label=cycle)
 ax.set(title=f'{m}: all5 critics on unchanged2514',xticks=axis,xlabel='Critic index',ylabel='In-mask squared error sum');ax.legend()
fig.suptitle('Registered fixed terminal cohort: all rows and all critics, no new health threshold');p=F/'fixed2514_84_86.png';assert not p.exists();fig.savefig(p,dpi=140);plt.close(fig)
with (F/'PLOT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),source_review_sha256=hashlib.sha256((F/'REVIEW.json').read_bytes()).hexdigest(),image_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),all_rows=5028,all_critics=10,actual_image_viewed=False),f,indent=2)
print(p)
