from pathlib import Path
import os,json,math,hashlib
os.sched_setaffinity(0,{52})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent
reg=json.loads((p/'REGISTRATION.json').read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return not isinstance(x,float) or math.isfinite(x)
fig,axes=plt.subplots(2,3,figsize=(15,8),constrained_layout=True);report=dict(passed=True,total_new_auxiliary_updates=0,reused_control_updates=10000,new_physics=0,methods={})
for row,m in enumerate(['impedance','admittance']):
 d=json.loads((p/m/'FINISHED.json').read_text());assert finite(d)
 control=json.loads(Path(reg['completed_controls'][m]['path']).read_text());assert sha(reg['completed_controls'][m]['path'])==reg['completed_controls'][m]['sha256']
 assert d['total_auxiliary_updates']==10000 and not d['auxiliary_weights_saved'] and d['parent_unchanged']
 assert d['checkpoint_sha256']==sha(reg['checkpoints'][m]['path'])==reg['checkpoints'][m]['sha256'];assert d['registration_sha256']==sha(p/'REGISTRATION.json')
 for r in d['results']:
  assert r['initial']==control['initial'] and r['initial_full_state_sha256']==control['initial_full_state_sha256']
  assert r['sampling_rng_sha256']==control['sampling_rng_sha256']
  assert r['frozen_component_digests_before']['targets']==r['frozen_component_digests_after']['targets']
  if r['arm']['freeze_actor']:assert r['frozen_component_digests_before']==r['frozen_component_digests_after']
 for r in [control]+d['results']:
  assert [v['updates'] for v in r['curve']]==list(range(250,5001,250))
  for ax,key in zip(axes[row],['terminal_mae','replay_q_abs_p95','replay_q_mean']):
   ax.plot([0]+[v['updates'] for v in r['curve']],[r['initial'][key]]+[v['diagnostic'][key] for v in r['curve']],label=r['arm']['name']);ax.set_title(m+': '+key);ax.set_xlabel('Auxiliary critic updates');ax.grid(alpha=.25);ax.legend()
 report['methods'][m]=[dict(arm=r['arm'],final=r['final']) for r in [control]+d['results']];report['total_new_auxiliary_updates']+=d['total_auxiliary_updates']
fig.suptitle('Matched full states and replay draws; existing uniform control reused; no online recovery claim');fig.savefig(p/'target_drift.png',dpi=140);report['plot_sha256']=sha(p/'target_drift.png');(p/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print('verified20000 newupdates, exact frozen components and reused control streams')
