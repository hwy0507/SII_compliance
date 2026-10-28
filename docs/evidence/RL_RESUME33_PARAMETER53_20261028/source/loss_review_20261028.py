from pathlib import Path
import json,os
os.sched_setaffinity(0,{54})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=b/'runs/resume_loss_review_20261028_v1';out.mkdir(exist_ok=True)
fig,axes=plt.subplots(4,2,figsize=(15,12)); result={}
for row,m in enumerate(['direct','impedance','admittance','vmc']):
 run=b/'runs/serl_take_cycle32_20261027_v1/direct' if m=='direct' else b/f'runs/parameter_capacity_pool30_cycle52_20261026_v1/{m}/train'
 rec=[json.loads(l) for l in (run/'optimizer.jsonl').open()]; names=['serl/critic/critic_loss','serl/actor/actor_loss'] if m=='direct' else ['agent_train/q_loss','agent_train/actor_loss']
 stats={}
 for col,k in enumerate(names):
  v=np.array([r[k] for r in rec]);stats[k]=dict(count=len(v),nonfinite=int((~np.isfinite(v)).sum()),first1000_mean=float(v[:1000].mean()),last1000_mean=float(v[-1000:].mean()),minimum=float(v.min()),maximum=float(v.max()))
  ax=axes[row,col];ax.plot(np.arange(len(v))[::20],v[::20],alpha=.2,lw=.5);w=1000;av=np.convolve(v,np.ones(w)/w,mode='valid');ax.plot(np.arange(len(av))+w-1,av,lw=1);ax.set_title(m+' '+k);ax.set_xlabel('optimizer row');ax.grid(alpha=.2)
 result[m]=stats
fig.tight_layout();fig.savefig(out/'loss.png',dpi=120);(out/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
