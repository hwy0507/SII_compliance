"""Reward convergence plot in the same raw/faint + smoothed/thick style as loss plots."""
import json, os
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

ROOT='/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark'
BASE=os.path.join(ROOT,'outputs/baseline_local_rl_20261009')
OUT=os.path.join(ROOT,'outputs/reward_training_curves_20261013')
os.makedirs(OUT,exist_ok=True)
RUNS={
'Direct | task reward':['campaign_v2/direct_office_task_segment011k','campaign_v2/direct_office_task_extended055000','campaign_v2/direct_office_task_extended110000','recovery_20261011_v1/direct_office_task_step165000'],
'Direct | task + historical entropy':['campaign_v2/direct_office_task_historical_entropy_segment011k','campaign_v2/direct_office_task_historical_entropy_extended055000','recovery_20261011_v1/direct_office_task_historical_entropy_step165000'],
'Parameter | admittance':['campaign_v2/parameter_admittance_segment011k','campaign_v2/parameter_admittance_extended055000','recovery_20261011_v1/parameter_admittance_step165000'],
'Parameter | impedance':['campaign_v2/parameter_impedance_segment011k','campaign_v2/parameter_impedance_extended055000','campaign_v2/parameter_impedance_extended110000','recovery_20261011_v1/parameter_impedance_step165000'],
'Parameter | VMC':['campaign_v2/parameter_vmc_segment011k','campaign_v2/parameter_vmc_extended055000','recovery_20261011_v1/parameter_vmc_step165000'],
'Parameter | impedance + historical entropy':['campaign_v2/parameter_impedance_historical_entropy_segment011k','campaign_v2/parameter_impedance_historical_entropy_extended055000','recovery_20261011_v1/parameter_impedance_historical_entropy_step165000']}
data={}
for label,rels in RUNS.items():
    ep_by_end={}
    for rel in rels:
        p=os.path.join(BASE,rel,'training.jsonl')
        if not os.path.exists(p): continue
        episodes=defaultdict(lambda:[0,0])
        with open(p) as f:
            for line in f:
                try:
                    x=json.loads(line); step=int(x['step']); t=x.get('terms',{}); r=t.get('final_reward',t.get('reward')); ep=int(x['episode'])
                except Exception: continue
                if r is not None:
                    episodes[ep][0]+=float(r); episodes[ep][1]=max(episodes[ep][1],step)
        for ep,(ret,step) in episodes.items(): ep_by_end[step]=ret
    data[label]=sorted(ep_by_end.items())
colors=plt.cm.tab10(np.linspace(0,1,len(data)))
# Main figure exactly mirrors the loss layout: raw panel, smoothed panel.
fig,axs=plt.subplots(2,1,figsize=(14,10),sharex=True,constrained_layout=True)
for label,c in zip(data,colors):
    a=data[label]; x=np.array([z[0] for z in a]); y=np.array([z[1] for z in a])
    axs[0].plot(x,y,'.-',alpha=.24,lw=.65,color=c)
    w=10
    if len(y)>=w:
        axs[1].plot(x[w-1:],np.convolve(y,np.ones(w)/w,mode='valid'),lw=2.2,color=c,label=label)
    else: axs[1].plot(x,y,lw=2.2,color=c,label=label)
axs[0].set_title('Episode return (raw; one point per completed training episode)')
axs[1].set_title('Episode return convergence (10-episode moving average)')
for ax in axs:
    ax.axhline(0,color='k',lw=.6); ax.grid(alpha=.25); ax.set_ylabel('Episode return')
axs[1].set_xlabel('Actual cumulative training steps')
axs[1].legend(fontsize=8,ncol=2,loc='best')
fig.suptitle('RL reward convergence — loss-style view',fontsize=14)
fig.savefig(os.path.join(OUT,'reward_convergence_loss_style.png'),dpi=180)
fig.savefig(os.path.join(OUT,'reward_convergence_loss_style.pdf'))
# Grouped figure: same visual treatment, separate y-axis ranges for direct and parameter outputs.
fig,axs=plt.subplots(2,2,figsize=(15,10),sharex='col',constrained_layout=True)
for col,(title,labels) in enumerate([('Direct action',[k for k in data if k.startswith('Direct')]),('Parameter output',[k for k in data if k.startswith('Parameter')])]):
    for label,c in zip(labels,[colors[list(data).index(k)] for k in labels]):
        a=data[label]; x=np.array([z[0] for z in a]); y=np.array([z[1] for z in a]); axs[0,col].plot(x,y,'.-',alpha=.24,lw=.65,color=c)
        w=10; yy=np.convolve(y,np.ones(w)/w,mode='valid') if len(y)>=w else y; xx=x[w-1:] if len(y)>=w else x
        axs[1,col].plot(xx,yy,lw=2.2,color=c,label=label)
    axs[0,col].set_title(title+' — raw'); axs[1,col].set_title(title+' — 10-episode moving average')
    for row in (0,1): axs[row,col].axhline(0,color='k',lw=.6); axs[row,col].grid(alpha=.25); axs[row,col].set_ylabel('Episode return')
    axs[1,col].set_xlabel('Actual cumulative training steps'); axs[1,col].legend(fontsize=8)
fig.suptitle('RL reward convergence by action type — loss-style view',fontsize=14)
fig.savefig(os.path.join(OUT,'reward_convergence_loss_style_by_action_type.png'),dpi=180)
fig.savefig(os.path.join(OUT,'reward_convergence_loss_style_by_action_type.pdf'))
# Small machine-readable export.
with open(os.path.join(OUT,'reward_episode_returns.csv'),'w') as f:
    f.write('method,training_step,episode_return\n')
    for label,rows in data.items():
        for step,r in rows: f.write(f'{label},{step},{r:.12g}\n')
print({k:(len(v),v[0][0],v[-1][0]) for k,v in data.items()})
