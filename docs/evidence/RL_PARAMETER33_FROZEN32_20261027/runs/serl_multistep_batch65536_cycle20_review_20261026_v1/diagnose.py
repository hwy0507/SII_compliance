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
sys.path.insert(0, str(B/'runtime/serl_multistep_batch65536_cycle20_20261026_v1'))
from serl_multistep_state_adapter_20261026 import SerlMultistepLearner as SerlStateLearner
from validate_serl_state_20261026 import digest

deadline = time.monotonic()+7200
while not (OUT/'REVIEW.json').exists():
    if time.monotonic()>deadline:
        raise RuntimeError('Review not ready within observation budget')
    time.sleep(2)
review = json.loads((OUT/'REVIEW.json').read_text())
x = torch.load(B/'runs/serl_multistep_batch65536_cycle20_archive_20261026_v1/direct/cycle_00020.pt', map_location='cpu', weights_only=False)
a = SerlStateLearner(B/'runtime/source_train17_clock',
    upstream=B/'runtime/serl_upstream_1fa2af7',
    upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',
    dimension=7, direct=True, seed=20261026, device='cuda:0')
a.load_state_dict(x['learner'])
before = digest(a.state_dict())
assert before == digest(x['learner'])
arrays = x['replay']['arrays']
terminal = np.flatnonzero(arrays['dones'].reshape(-1))
assert len(terminal)==630
jax = a.jax
def stats(v):
    v = np.asarray(v)
    assert np.isfinite(v).all()
    return dict(count=v.size, mean=float(v.mean()), minimum=float(v.min()),
                maximum=float(v.max()), p50=float(np.median(v)), p95=float(np.percentile(v,95)))
batch = a.batch(dict({k:v[terminal] for k,v in arrays.items()}, _bootstrap=1-arrays['dones'][terminal,0]))
q = np.asarray(a.agent.forward_critic(batch['observations'], batch['actions'], rng=jax.random.PRNGKey(261)))
report = dict(captured_unix=time.time(), checkpoint_sha256=review['methods']['direct']['checkpoint_sha256'],
    optimizer_updates=0, new_physics=0, terminal_count=630,
    terminal_reward=stats(batch['rewards']), terminal_q=stats(q),
    terminal_q_absolute_error=stats(q-np.asarray(batch['rewards'])[None]) )
report['terminal_q_absolute_error'] = stats(np.abs(q-np.asarray(batch['rewards'])[None]))
ids = np.random.default_rng(20261026).integers(x['replay']['size'], size=4096)
batch = a.batch(dict({k:v[ids] for k,v in arrays.items()}, _bootstrap=1-arrays['dones'][ids,0]))
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
    limitation='Fixed diagnostic pair; sampled_td is one-step and sampled_multistep_td is the registered behavior-return target. Off-policy bias remains. Terminal state has no actor clock; terminal error is diagnostic, not required zero fitting error.',
    convergence_claim=False)
extra=x['replay']['multistep_target_extension']
values={k:v[ids] for k,v in arrays.items()}
values.update(rewards=extra['target_rewards'][ids,None],next_observations=arrays['next_observations'][extra['target_endpoints'][ids]],_bootstrap=extra['target_bootstrap'][ids])
nb=a.batch(values)
na,_=a.agent._compute_next_actions(nb,action_key)
ntq=a.agent.forward_target_critic(nb['next_observations'],na,rng=key)
nt=nb['rewards']+.9995*nb['masks']*ntq[pair].min(axis=0)
report['sampled_multistep_td_absolute_error']=stats(np.abs(np.asarray(pred-nt[None])))
report['multistep_marker']=x['learner']['multistep_target_extension']
report['network_optimizer_rng_unchanged']=digest(a.state_dict())==before
assert report['network_optimizer_rng_unchanged']
(OUT/'DIAGNOSIS.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps(report,indent=2),flush=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
run = B/'runs/serl_multistep_batch65536_cycle20_20261026_v1/direct'
rows = [json.loads(s) for s in (run/'optimizer.jsonl').read_text().splitlines() if s.strip()]
rows = [r for r in rows if r['step']<=x['steps']]
groups = [rows[i:i+500] for i in range(0,len(rows),500)]
fig, axes = plt.subplots(2,2,figsize=(13,7),constrained_layout=True)
for ax,key in zip(axes.flat,['serl/critic/critic_loss','serl/critic/predicted_qs','serl/actor/entropy','serl/actor/temperature']):
    ax.plot([np.mean([r['step'] for r in g]) for g in groups], [np.mean([r[key] for r in g]) for g in groups])
    ax.set_title(key+' (500 updates/mean)');ax.set_xlabel('Online transitions');ax.grid(alpha=.2)
axes[0,0].set_yscale('log');axes[1,1].set_yscale('log')
fig.suptitle('Adapted SERL 32-step cycle20: optimizer diagnostics; no convergence claim')
fig.savefig(OUT/'training_diagnostics.png',dpi=150)
