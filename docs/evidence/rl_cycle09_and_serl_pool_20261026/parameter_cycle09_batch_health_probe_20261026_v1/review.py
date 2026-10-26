from pathlib import Path
import os,json,hashlib,math
os.sched_setaffinity(0,{52})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent
registration=json.loads((p/'REGISTRATION.json').read_text())
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return not isinstance(x,float) or math.isfinite(x)
fig,axes=plt.subplots(2,3,figsize=(15,8),constrained_layout=True)
report=dict(passed=True,total_auxiliary_updates=0,new_physics=0,auxiliary_weights_promoted=False,methods={})
for row,m in enumerate(['impedance','admittance']):
 d=json.loads((p/m/'FINISHED.json').read_text());assert finite(d)
 assert d['total_auxiliary_updates']==10000 and not d['auxiliary_weights_saved'] and d['parent_unchanged']
 assert d['checkpoint_sha256']==registration['checkpoints'][m]['sha256']==sha(registration['checkpoints'][m]['path'])
 assert d['registration_sha256']==sha(p/'REGISTRATION.json')
 assert len(d['results'])==2 and len({r['initial_full_state_sha256'] for r in d['results']})==1
 assert d['results'][0]['initial']==d['results'][1]['initial']
 values=[]
 for r in d['results']:
  assert [x['updates'] for x in r['curve']]==list(range(250,5001,250))
  assert r['parent_unchanged']
  updates=[0]+[x['updates'] for x in r['curve']]
  for ax,key in zip(axes[row],['terminal_mae','in_bag_terminal_mae','replay_q_abs_p95']):
   ax.plot(updates,[r['initial'][key]]+[x['diagnostic'][key] for x in r['curve']],label=r['arm']['name'])
   ax.set_title(m+': '+key);ax.set_xlabel('Auxiliary optimizer updates');ax.grid(alpha=.25);ax.legend()
  values.append(dict(arm=r['arm'],initial=r['initial'],final=r['final'],last_recorded_q_loss=r['curve'][-1]['metrics']['agent_train/q_loss']))
 report['methods'][m]=values;report['total_auxiliary_updates']+=d['total_auxiliary_updates']
assert report['total_auxiliary_updates']==20000
fig.suptitle('Exact cycle9 states: equal updates, unequal sampled rows; no online recovery claim')
fig.savefig(p/'batch_health.png',dpi=140)
report['plot_sha256']=sha(p/'batch_health.png')
(p/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print('passed; 20000 total auxiliary updates; original checkpoints unchanged')
