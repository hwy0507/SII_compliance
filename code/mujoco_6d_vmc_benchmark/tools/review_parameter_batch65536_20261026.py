"""Read-only independent audit of the finite cycle13 batch-size probe."""
from pathlib import Path
import os,json,hashlib,math,time
os.sched_setaffinity(0,{52})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse,sys,torch
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);p=parser.parse_args().root
reg=json.loads((p/'REGISTRATION.json').read_text())
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,list):return all(finite(v) for v in x)
 return not isinstance(x,float) or math.isfinite(x)
deadline=time.monotonic()+1800
for m in ['impedance','admittance','vmc']:
 while not (p/m/'FINISHED.json').exists():
  if (p/m/'FAILURE.json').exists() or time.monotonic()>deadline:raise RuntimeError('Missing finite probe result '+m)
  time.sleep(2)
fig,axes=plt.subplots(3,4,figsize=(18,11),constrained_layout=True)
assert reg['expected_cycle']==13 and reg['optimizer']=='batch65536'
report=dict(passed=True,new_physics=0,total_new_auxiliary_updates=0,entry_gate_auxiliary_updates=0,previous_failed_gate_auxiliary_updates=0,methods={})
for row,m in enumerate(['impedance','admittance','vmc']):
 d=json.loads((p/m/'FINISHED.json').read_text());assert finite(d) and d['parent_unchanged'] and not d['auxiliary_weights_saved']
 assert d['checkpoint_sha256']==sha(reg['checkpoints'][m]['path'])==reg['checkpoints'][m]['sha256']
 assert d['registration_sha256']==sha(p/'REGISTRATION.json') and d['total_auxiliary_updates']==10000
 arms=d['results'];control=arms[0]
 from validate_published_finite_check_20261025 import digest
 ck=torch.load(reg['checkpoints'][m]['path'],map_location='cpu',weights_only=False);assert ck['cycle']==13
 assert digest(ck['learner'])==control['initial_full_state_sha256'];del ck
 assert [r['arm'] for r in arms]==reg['arms']
 assert len({r['sampling_rng_sha256'] for r in arms})==2
 for r in arms:
  assert r['initial']==control['initial'] and r['initial_full_state_sha256']==control['initial_full_state_sha256']
  assert r['patch']['target_pair_reduction']['target']==('minimum' if m=='impedance' else 'mean')
  assert [v['updates'] for v in r['curve']]==list(range(250,5001,250))
  for ax,key in zip(axes[row],['terminal_mae','in_bag_terminal_mae','replay_q_abs_p95','replay_q_mean']):
   ax.plot([0]+[v['updates'] for v in r['curve']],[r['initial'][key]]+[v['diagnostic'][key] for v in r['curve']],label=r['arm']['name'])
   ax.set_title(m+': '+key);ax.set_xlabel('Auxiliary critic updates');ax.grid(alpha=.25);ax.legend()
 report['methods'][m]=dict(checkpoint_sha256=d['checkpoint_sha256'],arms=[dict(arm=r['arm'],initial=r['initial'],final=r['final'],patch=r['patch'],elapsed_s=r['elapsed_s'],updates_per_second=5000/r['elapsed_s']) for r in arms],online_recovery_proven=False,convergence_claim=False)
 report['total_new_auxiliary_updates']+=d['total_auxiliary_updates']
assert report['total_new_auxiliary_updates']==30000
fig.suptitle('Batch32768 vs65536, identical formal13 initial state; differing sample counts; no online claim')
fig.savefig(p/'batch_size.png',dpi=140);report['plot_sha256']=sha(p/'batch_size.png')
(p/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
