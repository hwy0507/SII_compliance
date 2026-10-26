from pathlib import Path
import os,json,hashlib,math,sys
os.sched_setaffinity(0,{52})
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(sys.argv[1]);reg=json.loads((p/'REGISTRATION.json').read_text());d=json.loads((p/'result/FINISHED.json').read_text())
def sha(f):
 with Path(f).open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()
def finite(v):
 if isinstance(v,dict):return all(finite(x) for x in v.values())
 if isinstance(v,list):return all(finite(x) for x in v)
 return not isinstance(v,float) or math.isfinite(v)
assert finite(d) and d['passed'] and d['parent_unchanged'] and not d['auxiliary_weights_saved']
assert d['checkpoint_sha256']==sha(reg['checkpoint']['path'])==reg['checkpoint']['sha256']
assert d['registration_sha256']==sha(p/'REGISTRATION.json')
assert d['auxiliary_critic_updates']==32000 and d['auxiliary_actor_updates']==4000
from validate_serl_state_20261026 import digest
ck=torch.load(reg['checkpoint']['path'],map_location='cpu',weights_only=False);assert ck['cycle']==9
arms=d['results'];assert arms[0]['initial']==arms[1]['initial'] and arms[0]['sampling_rng_sha256']==arms[1]['sampling_rng_sha256']
fig,axes=plt.subplots(2,3,figsize=(15,8),constrained_layout=True)
for a in arms:
 assert a['initial_full_state_sha256']==digest(ck['learner'])
 assert [v['outer_updates'] for v in a['curve']]==list(range(100,2001,100))
 for ax,key in zip(axes.flat,['terminal_mae','terminal_max','replay_q_mean','td_mae_1','td_mae_32','temperature']):
  ax.plot([0]+[v['outer_updates'] for v in a['curve']],[a['initial'][key]]+[v['diagnostic'][key] for v in a['curve']],label=str(a['horizon'])+' step');ax.set_title(key);ax.grid(alpha=.25);ax.legend()
gate=json.loads((p/'result/REPLAY_GATE.json').read_text());assert gate['passed'] and gate['rows']==400935 and gate['episodes']==300
for j in gate['journals']:assert sha(j['path'])==j['sha256']
fig.suptitle('Formal clock9, matched historical rows; off-policy multistep target comparison; no online claim');fig.savefig(p/'multistep.png',dpi=130)
(p/'REVIEW.json').write_text(json.dumps(dict(passed=True,checkpoint_sha256=d['checkpoint_sha256'],results=[dict(horizon=a['horizon'],final=a['final']) for a in arms],auxiliary_critic_updates=32000,auxiliary_actor_updates=4000,previous_failed_attempt_updates=0,new_physics=0,formal_state_unchanged=True,plot_sha256=sha(p/'multistep.png'),online_recovery_proven=False),indent=2)+'\n')
