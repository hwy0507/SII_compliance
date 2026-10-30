from pathlib import Path
import json,hashlib,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).parent;r=json.loads((D/'REVIEW.json').read_text());assert json.loads((D/'SAVED_REVIEW.json').read_text())['passed']
fig,axs=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
colors={'impedance':'#4263eb','admittance':'#e67700','vmc':'#087f5b'}
for m,x in r['methods'].items():
 for c in x['cases']:
  with np.load(c['derived']['path']) as z:axs[0,0].plot(z['action_time_s'],1000*z['preaction_peak_m'],color=colors[m],alpha=.35,lw=1)
 axs[0,1].scatter([list(r['methods']).index(m)]*30,[1000*c['final_peak_m'] for c in x['cases']],c=colors[m],label=m,alpha=.6)
axs[0,0].set(title='All90: cumulative peak available before each action',xlabel='Action time (s)',ylabel='Pre-action peak (mm)')
axs[0,1].set(title='All30 endpoints per method',xticks=[0,1,2],xticklabels=list(r['methods']),ylabel='Final peak (mm)')
for ax in axs[0]:ax.axhline(.2,color='red',ls='--',label='Existing 0.2 mm gate')
for ax,m in zip(axs[1],['admittance','vmc']):
 cases=[c for c in r['methods'][m]['cases'] if c['final_peak_m']>.0002];assert len(cases)==1;c=cases[0]
 with np.load(c['derived']['path']) as z:
  ax.step(z['action_time_s'],1000*z['preaction_peak_m'],where='post',color=colors[m],label='Available before action')
  ax.axvline(c['first_bad_preaction_time_s'],color='gray',ls=':',label=f"First available violation: {c['first_bad_preaction_time_s']:.2f}s")
 ax.axhline(.2,color='red',ls='--');ax.set(title=f"{m}: {c['condition']}\nTask={c['task']}, Strict={c['strict']}",xlabel='Action time (s)',ylabel='Pre-action peak (mm)');ax.legend(fontsize=8)
fig.suptitle('Saved journal/source availability audit, cycle84; no physics rerun or feature change')
p=D/'causal_history.png';assert not p.exists();fig.savefig(p,dpi=140);plt.close(fig)
with (D/'PLOT_REVIEW.json').open('x') as f:json.dump(dict(time=time.time(),passed=True,episodes=90,rows=123750,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_image_viewed=False),f,indent=2)
