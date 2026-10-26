from pathlib import Path
import os,json,hashlib,math
os.sched_setaffinity(0,{52})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent;reg=json.loads((p/'REGISTRATION.json').read_text())
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return not isinstance(x,float) or math.isfinite(x)
fig,axes=plt.subplots(3,3,figsize=(15,11),constrained_layout=True);report=dict(passed=True,new_physics=0,total_new_auxiliary_updates=0,entry_gate_auxiliary_updates=2,methods={})
for row,m in enumerate(['impedance','admittance','vmc']):
 d=json.loads((p/m/'FINISHED.json').read_text());assert finite(d) and d['parent_unchanged'] and not d['auxiliary_weights_saved']
 assert d['checkpoint_sha256']==sha(reg['checkpoints'][m]['path'])==reg['checkpoints'][m]['sha256'];assert d['registration_sha256']==sha(p/'REGISTRATION.json')
 if m!='vmc':
  ref=reg['completed_controls'][m];assert sha(ref['path'])==ref['sha256'];control=json.loads(Path(ref['path']).read_text());arms=[control]+d['results'];assert d['total_auxiliary_updates']==5000
 else:arms=d['results'];control=arms[0];assert d['total_auxiliary_updates']==10000
 for r in arms:
  assert r['initial']==control['initial'] and r['initial_full_state_sha256']==control['initial_full_state_sha256'];assert r['sampling_rng_sha256']==control['sampling_rng_sha256']
  assert [v['updates'] for v in r['curve']]==list(range(250,5001,250))
  for ax,key in zip(axes[row],['terminal_mae','in_bag_terminal_mae','replay_q_abs_p95']):
   ax.plot([0]+[v['updates'] for v in r['curve']],[r['initial'][key]]+[v['diagnostic'][key] for v in r['curve']],label=r['arm']['name']);ax.set_title(m+': '+key);ax.set_xlabel('Auxiliary critic updates');ax.grid(alpha=.25);ax.legend()
 candidate=arms[-1];assert candidate['final']['in_bag_terminal_mae']<control['final']['in_bag_terminal_mae']
 report['methods'][m]=dict(checkpoint_sha256=d['checkpoint_sha256'],arms=[dict(arm=r['arm'],initial=r['initial'],final=r['final'],patch=r.get('patch')) for r in arms],terminal_fitting_improved=True,q_tail_repaired=False,online_recovery_proven=False)
 report['total_new_auxiliary_updates']+=d['total_auxiliary_updates']
assert report['total_new_auxiliary_updates']==20000
fig.suptitle('Terminal critic weight128; actor/reward/samples unchanged; Q-tail remains abnormal');fig.savefig(p/'terminal_weight.png',dpi=140);report['plot_sha256']=sha(p/'terminal_weight.png');(p/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print('all three terminal fits improve; Q tails remain abnormal; 20000 newupdates and2 gate updates')
