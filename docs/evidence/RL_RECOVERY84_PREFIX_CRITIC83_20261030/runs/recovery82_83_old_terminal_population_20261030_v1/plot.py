from pathlib import Path
import json,hashlib,time,os
os.sched_setaffinity(0,{3})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=Path(__file__).parent;r=json.loads((D/'REVIEW.json').read_text());assert json.loads((D/'SAVED_REVIEW.json').read_text())['passed']
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained');series={}
for ax,m in zip(axes,['vmc','admittance']):
 c=r['methods'][m]['critics'];x=np.arange(5);before=[s['sse82'] for s in c];after=[s['sse83'] for s in c]
 ax.bar(x-.19,before,width=.38,label='Complete82',color='#507ca6');ax.bar(x+.19,after,width=.38,label='Complete83',color='#e58d43')
 ax.set_yscale('log');ax.set_xticks(x);ax.set_xlabel('Critic index (all 5 retained)');ax.set_ylabel('Masked SSE on same2454 old terminal rows');ax.set_title(m);ax.grid(axis='y',alpha=.2);ax.legend()
 for j in range(5):ax.text(j,max(before[j],after[j])*1.17,f'{after[j]/before[j]:.2f}x',ha='center',fontsize=9)
 ax.set_ylim(15,max(before+after)*2.3);series[m]=dict(before=before,after=after)
fig.suptitle('Fixed observations/actions/rewards/masks:83 /82 ratios are descriptive\nVMC critic3 worsens while other4 improve; no sampling or causal claim',fontsize=11)
fig.savefig(D/'old_terminal_by_critic.png',dpi=150)
with (D/'PLOT_REVIEW.json').open('x') as f:json.dump(dict(time=time.time(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),data_sha256=hashlib.sha256((D/'REVIEW.json').read_bytes()).hexdigest(),plot_sha256=hashlib.sha256((D/'old_terminal_by_critic.png').read_bytes()).hexdigest(),series=series),f,indent=2);f.write('\n')
