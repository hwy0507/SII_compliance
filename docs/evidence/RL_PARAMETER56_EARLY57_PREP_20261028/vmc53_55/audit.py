"""Retrospective descriptive loss distribution; no training or acceptance gate."""
from pathlib import Path
import hashlib
import json
import os
import time

os.sched_setaffinity(0, {54})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = Path(__file__).resolve().parent
plan = json.loads((OUT / 'PLAN.json').read_text())
assert plan['cycles'] == [53, 54, 55]
assert plan['source_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def summarize(a):
    count = len(a)
    ordered = np.sort(a)
    top_count = int(np.ceil(count * .01))
    return dict(count=count, mean=float(a.mean()), median=float(np.median(a)),
                p95=float(np.quantile(a, .95)), p99=float(np.quantile(a, .99)),
                maximum=float(a.max()), minimum=float(a.min()),
                top_one_percent_count=top_count,
                top_one_percent_sum_fraction=float(ordered[-top_count:].sum()/a.sum()),
                bottom_99percent_mean=float(ordered[:-top_count].mean()),
                greater_than_5_count=int((a > 5).sum()),
                greater_than_10_count=int((a > 10).sum()))

fig, axes = plt.subplots(3, 2, figsize=(12, 10), constrained_layout=True)
results = {}
for row, cycle in enumerate(plan['cycles']):
    source = plan['inputs'][str(cycle)]
    raw = Path(source['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    episode_bytes = Path(source['episodes_path']).read_bytes()
    assert hashlib.sha256(episode_bytes).hexdigest() == source['episodes_sha256']
    eps = [json.loads(line) for line in episode_bytes.splitlines()]
    assert len(eps) == 30 and sum(e['steps'] for e in eps) == len(rows) == 41250
    assert [r['step'] for r in rows] == list(range(rows[0]['step'], rows[-1]['step']+1))
    values = np.array([r['agent_train/q_loss'] for r in rows], dtype=np.float64)
    assert np.isfinite(values).all() and (values >= 0).all()
    bins = []
    for start in range(0, len(values), 1000):
        bins.append(dict(first_update_offset=start, last_update_offset=min(start+1000,len(values))-1,
                         **summarize(values[start:start+1000])))
    result = dict(all=summarize(values), first5000=summarize(values[:5000]),
                  last5000=summarize(values[-5000:]), bins=bins,
                  source=source, first_step=rows[0]['step'], last_step=rows[-1]['step'])
    results[str(cycle)] = result
    np.save(OUT / f'cycle{cycle}_critic.npy', values)
    ax = axes[row, 0]
    ax.plot(values, alpha=.2, linewidth=.4)
    for key in ['mean', 'median', 'p95']:
        ax.plot([x['last_update_offset'] for x in bins], [x[key] for x in bins], label=key)
    ax.set_title(f'VMC cycle {cycle}: complete critic loss; 1000-update bins')
    ax.set_xlabel('Update offset (final bin has 250 updates)')
    ax.legend()
    ax = axes[row, 1]
    for name, data in [('first5000',values[:5000]), ('last5000',values[-5000:])]:
        ax.plot(np.sort(data), np.arange(1,len(data)+1)/len(data), label=name)
    ax.set_xscale('log')
    ax.set_title(f'VMC cycle {cycle}: empirical CDF')
    ax.set_xlabel('Critic loss (log scale)')
    ax.set_ylabel('Fraction of updates')
    ax.legend()
fig.savefig(OUT / 'loss_distribution.png', dpi=130)
report = dict(passed=True, time=time.time(), methods={'vmc':results},
              descriptive_only=True, convergence_claim=False,
              new_physics=0, optimizer_updates=0, replay_writes=0,
              plot_sha256=hashlib.sha256((OUT/'loss_distribution.png').read_bytes()).hexdigest(),
              limitations=plan['limitations'])
(OUT / 'REVIEW.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({c:{k:v for k,v in result.items() if k in ['all','first5000','last5000']} for c,result in results.items()}, indent=2))
