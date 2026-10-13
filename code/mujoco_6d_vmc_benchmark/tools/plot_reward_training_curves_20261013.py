import json, os, glob
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
root='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/recovery_20261011_v1'
out='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013'
os.makedirs(out,exist_ok=True)
# Keep complete/current train logs; closed runs are still useful but label endpoint.
paths={
'Direct action | task reward':'direct_office_task_step165000',
'Direct action | task reward + historical entropy':'direct_office_task_historical_entropy_step165000',
'Parameter | admittance':'parameter_admittance_step165000',
'Parameter | impedance':'parameter_impedance_step165000',
'Parameter | VMC':'parameter_vmc_step165000',
'Parameter | impedance + historical entropy':'parameter_impedance_historical_entropy_step165000',
}
all_data={}; meta=[]
for label,dn in paths.items():
 p=os.path.join(root,dn,'training.jsonl'); eps=defaultdict(lambda:[0,0,0])
 if not os.path.exists(p): continue
 with open(p) as f:
  for line in f:
   try:x=json.loads(line)
   except:continue
   t=x.get('terms',{}); r=t.get('final_reward',t.get('reward'))
   if r is None:continue
   e=int(x.get('episode',-1)); step=int(x.get('step',0)); eps[e][0]+=float(r); eps[e][1]=step; eps[e][2]+=1
 rows=sorted((v[1],v[0],e,v[2]) for e,v in eps.items() if v[2]>=1)
 all_data[label]=rows
 meta.append((label,dn,len(rows),rows[-1][0] if rows else 0))
# combined overview, separate y scales
fig,axs=plt.subplots(2,1,figsize=(13,10),sharex=True,constrained_layout=True)
colors=plt.cm.tab10(np.linspace(0,1,len(all_data)))
for ax, smooth in zip(axs,[False,True]):
 for (label,rows),c in zip(all_data.items(),colors):
  x=np.array([r[0] for r in rows]); y=np.array([r[1] for r in rows])
  ax.plot(x,y,marker='.',lw=.8,alpha=.25 if smooth else .6,color=c,label=label)
  if smooth and len(y)>=5:
   w=min(15,len(y)); ys=np.convolve(y,np.ones(w)/w,mode='valid'); xs=x[w-1:]
   ax.plot(xs,ys,lw=2,color=c)
 ax.axhline(0,color='k',lw=.5); ax.grid(alpha=.25)
 axs[0].set_title('RL training episode return (raw)')
 axs[1].set_title('RL training episode return (15-episode moving average)')
axs[1].set_xlabel('Recorded training steps')
axs[0].set_ylabel('Episode return'); axs[1].set_ylabel('Episode return')
axs[0].legend(fontsize=8,ncol=2,loc='best')
fig.suptitle('Reward curves: direct action vs parameter output; reward standards separated',fontsize=14)
fig.savefig(out+'/reward_curves_overview.png',dpi=180); fig.savefig(out+'/reward_curves_overview.pdf')
# individual panels grouped to avoid scale clutter
fig,axs=plt.subplots(2,1,figsize=(13,10),sharex=False,constrained_layout=True)
for ax, group, title in [(axs[0],[k for k in all_data if k.startswith('Direct')],'Direct action'),(axs[1],[k for k in all_data if k.startswith('Parameter')],'Parameter output')]:
 for label in group:
  rows=all_data[label]; x=np.array([r[0] for r in rows]); y=np.array([r[1] for r in rows]); c=colors[list(all_data).index(label)]
  ax.plot(x,y,marker='.',lw=.7,alpha=.2,color=c); w=min(15,len(y));
  if len(y)>=w: ax.plot(x[w-1:],np.convolve(y,np.ones(w)/w,mode='valid'),lw=2,color=c,label=label)
 ax.axhline(0,color='k',lw=.5);ax.grid(alpha=.25);ax.set_title(title);ax.set_ylabel('Episode return');ax.legend(fontsize=8)
axs[1].set_xlabel('Recorded training steps')
fig.savefig(out+'/reward_curves_by_action_type.png',dpi=180); fig.savefig(out+'/reward_curves_by_action_type.pdf')
with open(out+'/README.md','w') as f:
 f.write('# Reward training curves (2026-10-13)\n\n')
 f.write('Episode return is the sum of recorded `final_reward` over each training episode; x is the maximum recorded `step` in that episode. Solid lines are 15-episode moving averages; faint points/lines are raw episode returns. Reward standards are separated by labels. This is an offline plot of existing logs; no retraining or simulation was run.\n\n')
 for m in meta:f.write(f'- {m[0]}: `{m[1]}/training.jsonl`, {m[2]} episodes, last recorded step {m[3]}\n')
 f.write('\nSome runs end before 165k because the archived log itself ends there; curves show available data only. Episode return is not a task-success metric.\n')
print(meta)
