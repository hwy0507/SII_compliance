"""Plot transition-level reward convergence from existing RL logs; no simulation."""
import json, os
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

base = '/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009'
out = base.rsplit('/outputs/',1)[0] + '/outputs/reward_training_curves_20261013'
os.makedirs(out, exist_ok=True)
# Earlier segment, 55k extension, closed 110k continuation, and 165k recovery.
runs = {
 'Direct action | task reward': [
  'campaign_v2/direct_office_task_segment011k', 'campaign_v2/direct_office_task_extended055000',
  'campaign_v2/direct_office_task_extended110000', 'recovery_20261011_v1/direct_office_task_step165000'],
 'Direct action | task reward + historical entropy': [
  'campaign_v2/direct_office_task_historical_entropy_segment011k', 'campaign_v2/direct_office_task_historical_entropy_extended055000',
  'recovery_20261011_v1/direct_office_task_historical_entropy_step165000'],
 'Parameter | admittance': [
  'campaign_v2/parameter_admittance_segment011k', 'campaign_v2/parameter_admittance_extended055000',
  'recovery_20261011_v1/parameter_admittance_step165000'],
 'Parameter | impedance': [
  'campaign_v2/parameter_impedance_segment011k', 'campaign_v2/parameter_impedance_extended055000',
  'campaign_v2/parameter_impedance_extended110000', 'recovery_20261011_v1/parameter_impedance_step165000'],
 'Parameter | VMC': [
  'campaign_v2/parameter_vmc_segment011k', 'campaign_v2/parameter_vmc_extended055000',
  'recovery_202611_v1/parameter_vmc_step165000'],
 'Parameter | impedance + historical entropy': [
  'campaign_v2/parameter_impedance_historical_entropy_segment011k', 'campaign_v2/parameter_impedance_historical_entropy_extended055000',
  'recovery_20261011_v1/parameter_impedance_historical_entropy_step165000'],
}
# fix typo defensively
runs['Parameter | VMC'][-1] = 'recovery_20261011_v1/parameter_vmc_step165000'
data={}; sources={}
for label, rels in runs.items():
 by_step={}
 for rel in rels:
  p=os.path.join(base,rel,'training.jsonl')
  if not os.path.exists(p): continue
  sources.setdefault(label,[]).append(rel)
  with open(p) as f:
   for line in f:
    try: x=json.loads(line); step=int(x['step']); t=x.get('terms',{}); reward=t.get('final_reward',t.get('reward'))
    except Exception: continue
    if reward is not None: by_step[step]=float(reward)
 data[label]=sorted(by_step.items())
# fixed-step bins; mean immediate reward, then 5-bin moving mean
binw=1000
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
colors=plt.cm.tab10(np.linspace(0,1,len(data)))
for label, c in zip(data,colors):
 vals=data[label]
 bins=defaultdict(list)
 for step,r in vals: bins[(step//binw)*binw].append(r)
 x=np.array(sorted(bins)); y=np.array([np.mean(bins[k]) for k in x])
 axs[0].plot(x,y,'.-',alpha=.3,lw=.7,color=c,label=label)
 w=5
 if len(y)>=w: axs[1].plot(x[w-1:],np.convolve(y,np.ones(w)/w,mode='valid'),lw=2.2,color=c,label=label)
 else: axs[1].plot(x,y,lw=2,color=c,label=label)
axs[0].set_title('Mean immediate reward per 1,000 training transitions (raw bins)')
axs[1].set_title('Reward convergence trend (5,000-transition moving average)')
for ax in axs:
 ax.axhline(0,color='k',lw=.6); ax.grid(alpha=.25); ax.set_ylabel('Mean reward / transition'); ax.legend(fontsize=8,ncol=2)
axs[1].set_xlabel('Actual cumulative training steps')
fig.suptitle('RL reward convergence: direct action reward standards vs parameter output',fontsize=14)
fig.savefig(out+'/reward_convergence_transition_binned.png',dpi=180); fig.savefig(out+'/reward_convergence_transition_binned.pdf')
# Separate panels for readability
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
for ax, labels, title in [(axs[0],[x for x in data if x.startswith('Direct')],'Direct action'),(axs[1],[x for x in data if x.startswith('Parameter')],'Parameter output')]:
 for label in labels:
  vals=data[label]; bins=defaultdict(list)
  for step,r in vals: bins[(step//binw)*binw].append(r)
  x=np.array(sorted(bins)); y=np.array([np.mean(bins[k]) for k in x]); c=colors[list(data).index(label)]
  w=5; yy=np.convolve(y,np.ones(w)/w,mode='valid') if len(y)>=w else y; xx=x[w-1:] if len(y)>=w else x
  ax.plot(xx,yy,lw=2,label=label,color=c)
 ax.axhline(0,color='k',lw=.6);ax.grid(alpha=.25);ax.set_title(title+' — 5,000-transition moving average');ax.set_ylabel('Mean reward / transition');ax.legend(fontsize=8)
axs[1].set_xlabel('Actual cumulative training steps')
fig.savefig(out+'/reward_convergence_by_action_type.png',dpi=180); fig.savefig(out+'/reward_convergence_by_action_type.pdf')
with open(out+'/README.md','w') as f:
 f.write('# RL reward convergence curves (2026-10-13)\n\n')
 f.write('These figures use transition-level `final_reward` from existing `training.jsonl` logs. The raw panel averages every 1,000 recorded training transitions; the trend panel applies a 5,000-transition moving average. Logs from segment/extension/continuation/recovery are joined by their recorded training step and duplicate steps are kept once. No retraining or simulation was run.\n\n')
 for label in data:
  f.write(f'- **{label}**: {len(data[label])} transitions, steps {data[label][0][0] if data[label] else "NA"}–{data[label][-1][0] if data[label] else "NA"}; sources: {", ".join(sources.get(label,[]))}\n')
 f.write('\nThis is the reward objective trend; it is not a task-success or safety convergence proof.\n')
print({k:(len(v),v[0][0] if v else None,v[-1][0] if v else None) for k,v in data.items()})
