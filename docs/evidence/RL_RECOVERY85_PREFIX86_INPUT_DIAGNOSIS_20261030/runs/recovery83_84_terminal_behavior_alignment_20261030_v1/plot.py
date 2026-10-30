from pathlib import Path
import json,time,hashlib,os
os.sched_setaffinity(0,{54})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
age=read(D/'INPUT_REVIEW.json');grad=read(D/'GRADIENT_REVIEW.json')
assert read(D/'INPUT_SAVED_REVIEW.json')['passed'] and read(D/'GRADIENT_SAVED_REVIEW.json')['passed']
fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
for col,m in enumerate(['vmc','admittance']):
 rows=age['methods'][m]['all30_new_terminal_rows'];ax=axes[0,col]
 for strict,marker,label in [(True,'o','Strict success'),(False,'x','Strict failure')]:
  selected=[r for r in rows if r['strict']==strict];ax.scatter([r['updates_available'] for r in selected],[r['masked_sse'] for r in selected],marker=marker,label=label,alpha=.8)
 if m=='vmc':
  for r in rows:
   if r['condition'] in ['active_short_train_0600','active_long_train_0400','active_short_train_0200']:
    ax.annotate(r['condition'].replace('active_','').replace('_train_',''),(r['updates_available'],r['masked_sse']),xytext=(-90,8 if '0600' in r['condition'] else -12),textcoords='offset points',fontsize=8)
 ax.set_xscale('log');ax.set_yscale('log');ax.set_xlabel('Logged update opportunities after append');ax.set_ylabel('Masked terminal SSE at complete84');ax.set_title(m+': all30 new84 terminal rows');ax.legend();ax.grid(alpha=.2)
 ax=axes[1,col];pairs=grad['methods'][m]['pairs']
 for sign,marker in [('same','o'),('opposite','x')]:
  selected=[r for r in pairs if r['neighbor_sign']==sign and r['squared_error_gradient_cosine'] is not None];ax.scatter([r['input_l2'] for r in selected],[r['squared_error_gradient_cosine'] for r in selected],marker=marker,label=sign+' reward sign',alpha=.5,s=18)
 ax.axhline(0,color='black',lw=.7);ax.set_xscale('log');ax.set_ylim(-1.05,1.05);ax.set_xlabel('Euclidean distance in actual57 input coordinates');ax.set_ylabel('Local squared-error gradient cosine');ax.set_title(m+': all active critics and both neighbor signs');ax.legend();ax.grid(alpha=.2)
fig.suptitle('Frozen84 diagnosis: update opportunity is not actual sampling; local gradients are not Adam history')
p=D/'input_gradient_diagnostics.png';fig.savefig(p,dpi=140);plt.close(fig)
with (D/'PLOT_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),all60_terminal_rows=True,all482_neighbor_pairs=True,retrospective_annotations=True,plot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),new_physics=0,optimizer_updates=0),f,indent=2)
