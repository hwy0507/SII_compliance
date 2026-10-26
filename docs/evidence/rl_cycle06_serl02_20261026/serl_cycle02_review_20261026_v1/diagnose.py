import os
os.sched_setaffinity(0, {52})
from pathlib import Path
import json
import sys
import time
import numpy as np
import torch
torch.set_num_threads(1)
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = Path(__file__).parent
sys.path.insert(0, str(B/'runtime/serl_state_adapter_20261026_v1'))
from serl_state_adapter_20261026 import SerlStateLearner
from validate_serl_state_20261026 import digest

deadline = time.monotonic()+3600
while not (OUT/'REVIEW.json').exists():
    if time.monotonic()>deadline:
        raise RuntimeError('Review not ready within observation budget')
    time.sleep(2)
review = json.loads((OUT/'REVIEW.json').read_text())
x = torch.load(B/'runs/reviewed_continuation_cycle_archive_20261026_v1/direct/cycle_00002.pt', map_location='cpu', weights_only=False)
a = SerlStateLearner(B/'runtime/source_train17_clock',
    upstream=B/'runtime/serl_upstream_1fa2af7',
    upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',
    dimension=7, direct=True, seed=20261026, device='cuda:0')
a.load_state_dict(x['learner'])
before = digest(a.state_dict())
arrays = x['replay']['arrays']
terminal = np.flatnonzero(arrays['dones'].reshape(-1))
assert len(terminal)==90
jax = a.jax
def stats(v):
    v = np.asarray(v)
    assert np.isfinite(v).all()
    return dict(count=v.size, mean=float(v.mean()), minimum=float(v.min()),
                maximum=float(v.max()), p50=float(np.median(v)), p95=float(np.percentile(v,95)))
batch = a.batch({k:v[terminal] for k,v in arrays.items()})
q = np.asarray(a.agent.forward_critic(batch['observations'], batch['actions'], rng=jax.random.PRNGKey(261)))
report = dict(captured_unix=time.time(), checkpoint_sha256=review['methods']['direct']['checkpoint_sha256'],
    optimizer_updates=0, new_physics=0, terminal_count=90,
    terminal_reward=stats(batch['rewards']), terminal_q=stats(q),
    terminal_q_absolute_error=stats(q-np.asarray(batch['rewards'])[None]) )
report['terminal_q_absolute_error'] = stats(np.abs(q-np.asarray(batch['rewards'])[None]))
ids = np.random.default_rng(20261026).integers(x['replay']['size'], size=4096)
batch = a.batch({k:v[ids] for k,v in arrays.items()})
key, action_key = jax.random.split(jax.random.PRNGKey(262))
actions, logp = a.agent._compute_next_actions(batch, action_key)
targetq = a.agent.forward_target_critic(batch['next_observations'],actions,rng=key)
_, pair_key = jax.random.split(key)
pair = jax.random.randint(pair_key, (2,), 0, 10)
target = batch['rewards'] + .9995*batch['masks']*targetq[pair].min(axis=0)
pred = a.agent.forward_critic(batch['observations'],batch['actions'],rng=key)
report.update(sampled_q=stats(pred), sampled_td_absolute_error=stats(np.abs(np.asarray(pred-target[None]))),
    diagnostic_target_pair=np.asarray(pair).tolist(), entropy=stats(-logp),
    temperature=float(a.agent.forward_temperature()), network_optimizer_rng_unchanged=(digest(a.state_dict())==before),
    limitation='Fixed diagnostic random target pair, not every training target. Terminal state has no actor clock; terminal error is diagnostic, not required zero fitting error.',
    convergence_claim=False)
assert report['network_optimizer_rng_unchanged']
(OUT/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps(report,indent=2),flush=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
run = B/'runs/serl_batch32768_cycle02_20261026_v1/direct'
rows = [json.loads(s) for s in (run/'optimizer.jsonl').read_text().splitlines() if s.strip()]
rows = [r for r in rows if r['step']<=x['steps']]
groups = [rows[i:i+500] for i in range(0,len(rows),500)]
fig, axes = plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
for ax,key in zip(axes.flat,['serl/critic/critic_loss','serl/critic/predicted_qs','serl/actor/entropy','serl/actor/temperature']):
    ax.plot([np.mean([r['step'] for r in g]) for g in groups], [np.mean([r[key] for r in g]) for g in groups])
    ax.set_title(key+' (500 updates/mean)');ax.set_xlabel('Online transitions');ax.grid(alpha=.2)
axes[0,0].set_yscale('log');axes[1,1].set_yscale('log')
fig.suptitle('Official SERL cycle2: optimizer diagnostics; no convergence claim')
fig.savefig(OUT/'training_diagnostics.png',dpi=150)
