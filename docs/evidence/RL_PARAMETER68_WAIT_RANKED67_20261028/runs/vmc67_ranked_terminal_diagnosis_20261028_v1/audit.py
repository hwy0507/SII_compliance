"""Posthoc rank all saved complete67 terminals, without a model forward."""
from pathlib import Path
import hashlib
import json
import math
import os
import time
os.sched_setaffinity(0, {53})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
def read(p):
    return json.loads(p.read_text())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
plan = read(OUT / 'PLAN.json')
for item in plan['inputs'].values():
    assert sha(Path(item['path'])) == item['sha256']
prior = read(Path(plan['inputs']['REVIEW.json']['path']))
assert prior['passed'] and read(Path(plan['inputs']['SAVED_VALUES_REVIEW.json']['path']))['passed']
with np.load(plan['inputs']['values.npz']['path'], allow_pickle=False) as v:
    idx = v['indices'].copy()
    reward = v['rewards'].astype(float)
    mask = v['masks'].astype(float)
    q = v['q_after'].astype(float)
    qb = v['q_before'].astype(float)
    den = v['denominator'].astype(float)
assert len(idx) == 2034 and len(set(map(int, idx))) == 2034
assert q.shape == mask.shape == (5, 2034) and qb.shape == (5, 2004)
assert all(np.isfinite(x).all() for x in [reward, mask, q, qb, den])
per = mask * (q - reward[None, :]) ** 2
before = (mask[:, :2004] * (qb - reward[None, :2004]) ** 2).sum(axis=0)
after = per.sum(axis=0)
contrib = (128 * per / den[:, None]).sum(axis=0)
order = sorted(range(2034), key=lambda i: (-float(after[i]), int(idx[i])))
rows = [dict(rank=rank + 1, replay_index=int(idx[i]), old_fixed_row=i < 2004,
             terminal_reward=float(reward[i]), sse67=float(after[i]),
             sse66=float(before[i]) if i < 2004 else None,
             contribution67=float(contrib[i]), per_head_sse=per[:, i].tolist())
        for rank, i in enumerate(order)]
total = math.fsum(map(float, after))
old_before = math.fsum(map(float, before))
old_after = math.fsum(map(float, after[:2004]))
assert math.isclose(old_before, prior['old2004_sse_before'], rel_tol=1e-12)
assert math.isclose(old_after, prior['old2004_sse_after'], rel_tol=1e-12)
assert math.isclose(math.fsum(map(float, contrib)), prior['all_terminal_contribution'], rel_tol=1e-12)
focus_ids = [x['replay_index'] for x in prior['focus']]
focus = [next(x for x in rows if x['replay_index'] == i) for i in focus_ids]
for old, new in zip(prior['focus'], focus):
    assert math.isclose(old['sse_before'], new['sse66'], rel_tol=1e-12)
    assert math.isclose(old['sse_after'], new['sse67'], rel_tol=1e-12)
delta = after[:2004] - before
report = dict(passed=True, time=time.time(), plan_sha256=sha(OUT/'PLAN.json'),
              source_sha256=sha(Path(__file__)), all2034_ranked=rows,
              all2034_sse=total, old2004_sse_before=old_before,
              old2004_sse_after=old_after, new30_sse=math.fsum(map(float, after[2004:])),
              all2034_contribution=math.fsum(map(float, contrib)),
              improved_old=int((delta < 0).sum()), worsened_old=int((delta > 0).sum()),
              unchanged_old=int((delta == 0).sum()), original_five_focus=focus,
              top_shares={str(n): math.fsum(x['sse67'] for x in rows[:n])/total for n in [1,2,5,10]},
              new_forward=0, new_physics=0, optimizer_updates=0, replay_writes=0,
              new_stopping_gate=False, causal_claim=False, convergence_claim=False,
              limitation='Posthoc complete67 ranking during68. All2034 rows retained; original five focus unchanged. Concentration and signed changes do not prove gradient causality, aliasing, convergence or generalization. No new terminal-error gate.')
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), constrained_layout=True)
ax[0].plot(range(1,2035), np.cumsum([x['sse67'] for x in rows])/total)
ax[0].set(xscale='log', xlabel='Rank among all 2034 terminals', ylabel='Cumulative masked SSE fraction', title='Complete67 error concentration (posthoc)')
ax[0].grid(alpha=.25)
ax[1].scatter(before, after[:2004], s=8, alpha=.35)
limit=max(float(before.max()),float(after[:2004].max()))
ax[1].plot([0,limit],[0,limit],color='black',lw=.8)
ax[1].set(xscale='symlog',yscale='symlog',xlabel='Complete66 masked SSE',ylabel='Complete67 masked SSE',title='All 2004 fixed old terminals')
for row in focus:
    ax[1].scatter(row['sse66'],row['sse67'],s=30,facecolors='none',edgecolors='red')
ax[1].grid(alpha=.25)
fig.savefig(OUT/'ranked_terminals.png',dpi=160)
report['plot_sha256']=sha(OUT/'ranked_terminals.png')
for item in plan['inputs'].values():
    assert sha(Path(item['path'])) == item['sha256']
with (OUT/'REVIEW.json').open('x') as f:
    json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k != 'all2034_ranked'},indent=2))
