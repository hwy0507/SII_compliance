"""Plot recorded RL optimizer metrics; read-only analysis, no training/simulation."""
import json, os
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

ROOT='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark'
BASE=os.path.join(ROOT,'outputs/baseline_local_rl_20261009')
OUT=os.path.join(ROOT,'outputs/reward_training_curves_20261013')
os.makedirs(OUT,exist_ok=True)
RUNS={
 'Direct | task reward':['recovery_20261011_v1/direct_office_task_step165000','campaign_v2/direct_office_task_extended110000','campaign_v2/direct_office_task_extended055000','campaign_v2/direct_office_task_segment011k'],
 'Direct | task + historical entropy':['recovery_20261011_v1/direct_office_task_historical_entropy_step165000','campaign_v2/direct_office_task_historical_entropy_extended055000','campaign_v2/direct_office_task_historical_entropy_segment011k'],
 'Parameter | admittance':['recovery_20261011_v1/parameter_admittance_step165000','campaign_v2/parameter_admittance_extended055000','campaign_v2/parameter_admittance_segment011k'],
 'Parameter | impedance':['recovery_20261011_v1/parameter_impedance_step165000','campaign_v2/parameter_impedance_extended110000','campaign_v2/parameter_impedance_extended055000','campaign_v2/parameter_impedance_segment011k'],
 'Parameter | VMC':['recovery_20261011_v1/parameter_vmc_step165000','campaign_v2/parameter_vmc_extended055000','campaign_v2/parameter_vmc_segment011k'],
 'Parameter | impedance + historical entropy':['recovery_20261011_v1/parameter_impedance_historical_entropy_step165000','campaign_v2/parameter_impedance_historical_entropy_extended055000','campaign_v2/parameter_impedance_historical_entropy_segment011k'],
}
METRICS=[('actor/loss','Actor loss'),('critic/loss','Critic loss'),('actor/entropy','Actor entropy'),('temperature/value','Temperature value')]
data={}; sources={}
for label,rels in RUNS.items():
 raw=defaultdict(lambda:defaultdict(list))
 for rel in rels:
  p=os.path.join(BASE,rel,'optimizer.jsonl')
  if not os.path.exists(p): continue
  sources.setdefault(label,[]).append(rel)
  with open(p) as f:
   for line in f:
    try:x=json.loads(line); step=int(x['step']); m=x['metrics']
    except Exception: continue
    for key,_ in METRICS:
     if key in m: raw[step][key].append(float(m[key]))
 # mean duplicate optimizer records at same step, then bin by 1000 steps
 bins=defaultdict(lambda:defaultdict(list))
 for step,mm in raw.items():
  b=(step//1000)*1000
  for k,vals in mm.items(): bins[b][k].extend(vals)
 data[label]={k:(np.array(sorted(bins)),np.array([np.mean(bins[b][k]) if bins[b][k] else np.nan for b in sorted(bins)])) for k,_ in METRICS}
colors=plt.cm.tab10(np.linspace(0,1,len(data)))
# Main plot with actor/critic losses
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
for ax,(key,title) in zip(axs,METRICS[:2]):
 for (label,dd),c in zip(data.items(),colors):
  x,y=dd[key]; ax.plot(x,y,alpha=.22,lw=.6,color=c)
  w=5
  if len(y)>=w: ax.plot(x[w-1:],np.convolve(y,np.ones(w)/w,mode='valid'),lw=2,color=c,label=label)
  else: ax.plot(x,y,lw=2,color=c,label=label)
 ax.set_title(title+' (1,000-step bins; thick line = 5-bin moving average)');ax.set_ylabel(title);ax.grid(alpha=.25);ax.legend(fontsize=8,ncol=2)
axs[1].set_xlabel('Actual cumulative training steps')
fig.suptitle('RL optimizer loss convergence from recorded logs',fontsize=14)
fig.savefig(os.path.join(OUT,'loss_convergence_actor_critic.png'),dpi=180);fig.savefig(os.path.join(OUT,'loss_convergence_actor_critic.pdf'))
# Auxiliary entropy/temp
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
for ax,(key,title) in zip(axs,METRICS[2:]):
 for (label,dd),c in zip(data.items(),colors):
  x,y=dd[key]; w=5; yy=np.convolve(y,np.ones(w)/w,mode='valid') if len(y)>=w else y; xx=x[w-1:] if len(y)>=w else x
  ax.plot(xx,yy,lw=1.8,color=c,label=label)
 ax.set_title(title+' (5-bin moving average of 1,000-step bins)');ax.set_ylabel(title);ax.grid(alpha=.25);ax.legend(fontsize=8,ncol=2)
axs[1].set_xlabel('Actual cumulative training steps')
fig.suptitle('RL auxiliary optimizer diagnostics',fontsize=14)
fig.savefig(os.path.join(OUT,'loss_convergence_auxiliary.png'),dpi=180);fig.savefig(os.path.join(OUT,'loss_convergence_auxiliary.pdf'))
with open(os.path.join(OUT,'LOSS_README.md'),'w') as f:
 f.write('# RL loss convergence plots\n\n')
 f.write('Metrics are read from existing `optimizer.jsonl` files. Duplicate optimizer records at the same training step are averaged; values are then averaged in 1,000-step bins. Thick lines use a 5-bin moving average (about 5,000 training steps). No retraining or simulation was run.\n\n')
 f.write('Main figure: actor/loss and critic/loss. Auxiliary figure: actor/entropy and temperature/value. Losses are optimizer diagnostics and do not by themselves establish task success or policy convergence.\n\n')
 for label in data:
  f.write(f'- **{label}**: {sources.get(label,[])}; steps {int(data[label]["actor/loss"][0][0]) if len(data[label]["actor/loss"][0]) else "NA"}–{int(data[label]["actor/loss"][0][-1]) if len(data[label]["actor/loss"][0]) else "NA"}.\n')
 f.write('\nLegacy PPO/SAC pilot directories contain monitor.csv and TensorBoard event files but use a different old protocol and are not merged into the main loss plot.\n')
print({k:{m:int(len(v[0])) for m,(v) in dd.items()} for k,dd in data.items()})
