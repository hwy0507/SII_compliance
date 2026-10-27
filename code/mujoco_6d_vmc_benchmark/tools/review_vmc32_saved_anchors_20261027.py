"""Check saved fixed terminal predictions, without rerunning inference."""
from pathlib import Path
import hashlib
import json
import os
import time

os.sched_setaffinity(0, {52})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root = B/'runs/vmc32_terminal_anchor_followup_20261027_v1'
oldroot = B/'runs/vmc30_31_terminal_concentration_20261027_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = json.loads((root/'REVIEW.json').read_text())
oldreport = json.loads((oldroot/'REVIEW.json').read_text())
assert report['passed'] and report['agent_weights_and_forward_rng_unchanged']
assert not (root/'SAVED_VALUE_REVIEW.json').exists()
oldpath = oldroot/'cycle31_terminal_values.npz'
newpath = root/'terminal32_values.npz'
assert sha(oldpath) == oldreport['cycles'][1]['values_sha256']
assert sha(newpath) == report['values_sha256']
with np.load(oldpath, allow_pickle=False) as data:
    old = {k: data[k].copy() for k in data.files}
with np.load(newpath, allow_pickle=False) as data:
    new = {k: data[k].copy() for k in data.files}
count = 954
np.testing.assert_array_equal(old['replay_indices'], new['indices'][:count])
np.testing.assert_array_equal(old['rewards'], new['rewards'][:count])
np.testing.assert_array_equal(old['masks'], new['masks'][:, :count])
sq0 = old['masks']*(old['q']-old['rewards'][None])**2
sq1 = new['masks']*(new['q'].astype(np.float64)-new['rewards'].astype(np.float64)[None])**2
contributions = (128*sq1/new['denominators'][:, None]).sum(axis=0)
np.testing.assert_allclose(contributions, new['contributions'], rtol=1e-14, atol=1e-14)
actual = dict(fixed954_masked_sse_before=sq0.sum(),
    fixed954_masked_sse_after=sq1[:, :count].sum(),
    fixed954_masked_sse_ratio=sq1[:, :count].sum()/sq0.sum(),
    terminal_population_contribution=contributions.sum(),
    retained954_population_contribution=contributions[:count].sum(),
    new30_population_contribution=contributions[count:].sum(),
    fixed954_contribution_using_old31_denominator=(128*sq1[:, :count]/old['denominators'][:, None]).sum())
for key, value in actual.items():
    np.testing.assert_allclose(value, report[key], rtol=1e-14, atol=1e-14)
focus = int(np.flatnonzero(new['indices'] == report['focus']['replay_index'])[0])
for key, value in [('masked_sse_before', sq0[:, focus].sum()),
                   ('masked_sse_after', sq1[:, focus].sum()),
                   ('population_contribution_after', contributions[focus])]:
    np.testing.assert_allclose(value, report['focus'][key], rtol=1e-14, atol=1e-14)
fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
axes[0].bar(['31', '32'], [sq0.sum(), sq1[:, :count].sum()])
axes[0].set(title='Same 954 terminal rows', ylabel='Masked squared error sum')
axes[1].bar(['31', '32'], [sq0[:, focus].sum(), sq1[:, focus].sum()])
axes[1].set(title='Fixed short0600 row 1304222', ylabel='Masked squared error sum')
axes[2].bar(['31', '32'], [old['contributions'].sum(), contributions[:count].sum()], label='Retained 954')
axes[2].bar(['32'], [contributions[count:].sum()], bottom=[contributions[:count].sum()], label='New 30')
axes[2].set(title='Terminal population contribution')
axes[2].legend()
fig.suptitle('VMC frozen critic endpoints; excludes nonterminal TD and historical minibatches')
plot = root/'fixed954_follow32.png'
fig.savefig(plot, dpi=140)
plt.close(fig)
result = dict(passed=True, time=time.time(), source_sha256=sha(Path(__file__)),
    input_hashes={str(p): sha(p) for p in [oldpath, newpath, root/'REVIEW.json']},
    arithmetic={k: float(v) for k, v in actual.items()}, plot_sha256=sha(plot),
    new_physics=0, optimizer_updates=0, neural_inference=0, convergence_claim=False,
    limitation='Saved endpoint terminal arithmetic only; no attribution of historical minibatch losses or policy convergence.')
(root/'SAVED_VALUE_REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
