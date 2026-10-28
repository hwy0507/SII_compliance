import json,os,glob
from collections import defaultdict
import numpy as np, matplotlib.pyplot as plt
base='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009'; out='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013'
runs={
'Direct action | task reward':['campaign_v2/direct_office_task_segment011k','campaign_v2/direct_office_task_extended055000','campaign_v2/direct_office_task_extended110000','recovery_20261011_v1/direct_office_task_step165000'],
'Direct action | task reward + historical entropy':['campaign_v2/direct_office_task_historical_entropy_segment011k','campaign_v2/direct_office_task_historical_entropy_extended055000','recovery_20261011_v1/direct_office_task_historical_entropy_step165000'],
'Parameter | admittance':['campaign_v2/parameter_admittance_segment011k','campaign_v2/parameter_admittance_extended055000','recovery_20261011_v1/parameter_admittance_step165000'],
'Parameter | impedance':['campaign_v2/parameter_impedance_segment011k','campaign_v2/parameter_impedance_extended055000','campaign_v2/parameter_impedance_extended110000','recovery_20261011_v1/parameter_impedance_step165000'],
'Parameter | VMC':['campaign_v2/parameter_vmc_segment011k','campaign_v2/parameter_vmc_extended055000','recovery_20261011_v1/parameter_vmc_step165000'],
'Parameter | impedance + historical entropy':['campaign_v2/parameter_impedance_historical_entropy_segment011k','campaign_v2/parameter_impedance_historical_entropy_extended055000','recovery_20261011_v1/parameter_impedance_historical_entropy_step165000']}
data={}
for label,rels in runs.items():
 ep_by_end={}
 for rel in rels:
  p=os.path.join(base,rel,'training.jsonl')
  if not os.path.exists(p):continue
  e=defaultdict(lambda:[0,0])
  for line in open(p):
   try:x=json.loads(line); ep=int(x['episode']); step=int(x['step']); t=x.get('terms',{}); r=t.get('final_reward',t.get('reward'))
   except:continue
   if r is None:continue
   e[ep][0]+=float(r); e[ep][1]=max(e[ep][1],step)
  # endpoint is the unique identity; keep latest source on overlap
  for ep,(ret,step) in e.items(): ep_by_end[step]=ret
 data[label]=sorted(ep_by_end.items())
colors=plt.cm.tab10(np.linspace(0,1,len(data)))
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
for label,c in zip(data,colors):
 a=data[label]; x=np.array([z[0] for z in a]); y=np.array([z[1] for z in a]); axs[0].plot(x,y,'.-',alpha=.35,lw=.7,color=c,label=label)
 # average every 10 consecutive episodes (actual x at last episode)
 w=10
 if len(y)>=w: axs[1].plot(x[w-1:],np.convolve(y,np.ones(w)/w,mode='valid'),lw=2.2,color=c,label=label)
 axs[1].plot([],[],color=c)
axs[0].set_title('Episode return across training (raw)'); axs[1].set_title('Convergence trend: 10-episode moving average')
for ax in axs: ax.axhline(0,color='k',lw=.6);ax.grid(alpha=.25);ax.set_ylabel('Episode return');ax.legend(fontsize=8,ncol=2)
axs[1].set_xlabel('Actual cumulative training steps')
fig.suptitle('RL reward convergence — direct-action reward standards and parameter output',fontsize=14)
fig.savefig(out+'/reward_convergence_episode_return.png',dpi=180);fig.savefig(out+'/reward_convergence_episode_return.pdf')
print({k:(len(v),v[0][0],v[-1][0]) for k,v in data.items()})
