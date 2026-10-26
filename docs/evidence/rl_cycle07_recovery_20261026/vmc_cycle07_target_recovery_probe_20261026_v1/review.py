from pathlib import Path
import json,hashlib,time,os
os.sched_setaffinity(0,{52})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent
reg=json.loads((p/'REGISTRATION.json').read_text());x=json.loads((p/'vmc/FINISHED.json').read_text())
assert x['total_auxiliary_updates']==15000 and x['new_physics']==0 and not x['auxiliary_weights_saved']
assert x['checkpoint_sha256']==reg['checkpoints']['vmc']['sha256']
assert len(x['results'])==3 and len({r['initial_full_state_sha256'] for r in x['results']})==1
assert len({r['sampling_rng_sha256'] for r in x['results']})==1
assert all(r['initial']==x['results'][0]['initial'] and r['parent_unchanged'] for r in x['results'])
summary=[]
fig,axes=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
keys=['terminal_mae','in_bag_terminal_mae','replay_q_mean','replay_q_abs_p95','uncertainty_mean','alpha']
for r in x['results']:
 assert [row['updates'] for row in r['curve']]==list(range(250,5001,250))
 for row in r['curve']:
  assert all(np.isfinite(v) for v in row['metrics'].values()) and all(np.isfinite(v) for v in row['diagnostic'].values())
 for ax,key in zip(axes.flat,keys):
  ax.plot([0]+[row['updates'] for row in r['curve']],[r['initial'][key]]+[row['diagnostic'][key] for row in r['curve']],label=r['arm']['name']);ax.set_title(key);ax.set_xlabel('Auxiliary updates');ax.grid(alpha=.2)
 summary.append(dict(arm=r['arm'],initial=r['initial'],final=r['final'],last_q_loss=r['curve'][-1]['metrics']['agent_train/q_loss']))
axes[0,0].legend();fig.suptitle('VMC cycle7 full-state matched recovery diagnostics; no weight promotion')
fig.savefig(p/'recovery_diagnostics.png',dpi=150)
report=dict(time=time.time(),passed=True,parent_checkpoint=reg['checkpoints']['vmc'],total_auxiliary_updates=15000,full_initial_states_equal=True,replay_sampling_streams_equal=True,parent_state_and_replay_unchanged=True,results=summary,new_physics=0,weights_promoted=False,convergence_claim=False)
(p/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(summary),flush=True)
