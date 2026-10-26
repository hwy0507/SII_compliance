from pathlib import Path
import os,json,time,hashlib,subprocess
os.sched_setaffinity(0,{54})
out=Path(__file__).parent;pid=json.loads((out/'LAUNCH.json').read_text())['pid'];deadline=time.monotonic()+1800
while not (out/'REVIEW.json').exists():
 if not Path(f'/proc/{pid}').exists():raise RuntimeError('Original probe exited without report; retain evidence')
 if time.monotonic()>deadline:raise RuntimeError('Observation window ended; inspect original handle without restarting')
 time.sleep(2)
reg=json.loads((out/'REGISTRATION.json').read_text());d=json.loads((out/'REVIEW.json').read_text())
assert d['passed'] and d['formal_state_unchanged'] and d['new_physics']==0 and not d['weights_saved']
assert d['checkpoint']==reg['checkpoint']
with Path(reg['checkpoint']['path']).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==reg['checkpoint']['sha256']
assert d['total_critic_updates']==32000 and d['total_actor_updates']==4000
assert [r['batch_size'] for r in d['results']]==[32768,65536]
import numpy as np
for r in d['results']:
 assert r['outer_updates']==2000 and r['critic_updates']==16000 and r['actor_updates']==2000
 assert r['sampled_rows']==r['batch_size']*2000 and not r['weights_saved']
 assert [p['outer_updates'] for p in r['points']]==list(range(100,2001,100))
 for p in r['points']:
  assert p['critic_updates']==p['outer_updates']*8
  assert all(np.isfinite(v) for v in p.values())
 assert r['mean_outer_seconds_excluding_first']>0
left,right=d['results']
for key in ['initial','initial_learner_digest','initial_replay_digest','initial_sample_rng_digest']:assert left[key]==right[key]
assert left['final_sample_rng_digest']!=right['final_sample_rng_digest']
assert not list(out.glob('*.pt'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,3,figsize=(14,7),layout='constrained')
keys=['terminal_mae','terminal_max','multistep_td_mae','q_mean','last100_critic_loss','last100_outer_seconds']
for ax,key in zip(axes.flat,keys):
 for r in d['results']:ax.plot([p['outer_updates'] for p in r['points']],[p[key] for p in r['points']],label=str(r['batch_size']))
 ax.set_title(key);ax.set_xlabel('Auxiliary outer updates');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Finite SERL batch comparison; shared GPU timing, no physics or weight promotion')
fig.savefig(out/'batch_comparison.png',dpi=150)
receipt=dict(passed=True,time=time.time(),report_sha256=hashlib.sha256((out/'REVIEW.json').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),plot_sha256=hashlib.sha256((out/'batch_comparison.png').read_bytes()).hexdigest(),budgets_and_parent_verified=True,all20_points_each_arm_finite=True,initial_full_state_replay_rng_and_diagnostics_identical=True,weights_saved=False,scope='Independent review of budgets, exact formal parent binding, immutable full-state receipts, paired initial diagnostics, different sample clocks, finite trajectories and output artifacts; not online or convergence validation')
(out/'INDEPENDENT_REVIEW.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
