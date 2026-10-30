from pathlib import Path
import json,hashlib,math,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;F=B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1'
def read(p):return json.loads(p.read_text())
assert (F/'FINISHED.json').exists(),'Complete fixed2514 input85 result not ready'
assert read(F/'FINISHED.json')['passed'] and read(F/'REVIEW.json')['passed'] and read(F/'SAVED_REVIEW.json')['passed']
r=read(F/'REVIEW.json');fig,axs=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
for col,m in enumerate(['vmc','admittance']):
 a=r['methods'][m];rows=[json.loads(l) for l in (F/(m+'_all2514.jsonl')).read_text().splitlines()];assert len(rows)==2514
 assert hashlib.sha256((F/(m+'_all2514.jsonl')).read_bytes()).hexdigest()==a['allrows_sha256']
 x=np.array([v['sse84'] for v in rows]);y=np.array([v['sse85'] for v in rows]);assert np.isfinite(x).all() and np.isfinite(y).all() and min(x.min(),y.min())>=0
 assert math.isclose(math.fsum(x),a['total_sse84'],rel_tol=1e-12) and math.isclose(math.fsum(y),a['total_sse85'],rel_tol=1e-12)
 ax=axs[0,col];ax.scatter(np.log1p(x[:-30]),np.log1p(y[:-30]),s=8,alpha=.3,label='2484 rows before84');ax.scatter(np.log1p(x[-30:]),np.log1p(y[-30:]),s=26,alpha=.8,c='#e67700',label='All30 new84 rows')
 limit=float(max(np.log1p(x).max(),np.log1p(y).max()));ax.plot([0,limit],[0,limit],ls='--',c='gray');ax.set(title=f'{m}: identical2514 features/actions/rewards/masks',xlabel='log(1 + masked SSE), frozen84',ylabel='log(1 + masked SSE), frozen85');ax.legend(fontsize=8)
 ax=axs[1,col];cs=a['critics'];assert [c['critic'] for c in cs]==list(range(5));axis=np.arange(5)
 ax.bar(axis-.18,[c['sse84'] for c in cs],width=.36,label='84');ax.bar(axis+.18,[c['sse85'] for c in cs],width=.36,label='85');ax.set(title=f'{m}: all5 critics on fixed2514',xticks=axis,xlabel='Critic index',ylabel='In-mask squared error sum');ax.legend()
fig.suptitle('Prospective fixed-input84→85 followup; saved-value diagnosis, no new health gate')
p=D/'fixed2514_inputs84_85.png';assert not p.exists();fig.savefig(p,dpi=140);plt.close(fig)
with (D/'FIXED_INPUT85_PLOT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),source_review_sha256=hashlib.sha256((F/'REVIEW.json').read_bytes()).hexdigest(),all5028_rows=True,all10_critics=True,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_image_viewed=False),f,indent=2);f.write('\n')
print(p)
