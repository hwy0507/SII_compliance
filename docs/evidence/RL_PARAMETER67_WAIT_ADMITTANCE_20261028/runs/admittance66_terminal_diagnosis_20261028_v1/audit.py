"""Posthoc complete66 admittance terminal and optimizer timeline diagnosis."""
from pathlib import Path
import hashlib
import json
import math
import os
import sys
import time

os.sched_setaffinity(0, {53})
import numpy as np
import torch
torch.set_num_threads(1)
OUT = Path(__file__).parent


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def near(a, b):
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (a, b)


plan = read(OUT / 'PLAN.json')
assert sha(Path(__file__)) == plan['source_sha256']
for ref in plan['inputs'].values():
    assert sha(ref['path']) == ref['sha256']
inputs = {key: Path(value['path']) for key, value in plan['inputs'].items()}
reg = read(inputs['registration'])
runtime = Path(reg['runtime'])
helper = Path(plan['helper_runtime'])
assert sha(runtime / 'RUNTIME.json') == reg['runtime_sha256']
for name, digest in read(runtime / 'SOURCE_HASHES.json').items():
    assert sha(runtime / 'source' / name) == digest
for name, digest in reg['batch_size_stage']['dependency_hashes'].items():
    assert sha(helper / name) == digest
sys.path[:0] = [str(helper), str(runtime / 'source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest

checkpoint = torch.load(inputs['checkpoint'], map_location='cpu', weights_only=False)
assert checkpoint['cycle'] == 66 and checkpoint['boundary'] == 'complete_condition_cycle'
assert checkpoint['controller'] == 'admittance'
arrays = checkpoint['replay']['arrays']
state = checkpoint['learner']
indices = np.flatnonzero(arrays['dones'][:, 0] == 1)
assert len(indices) == 2004 and checkpoint['replay']['size'] == 2759750
assert checkpoint['replay']['capacity'] == 4_000_000
assert state['terminal_loss_weight'] == 128 and state['target_pair_reduction']['target'] == 'mean'
parent_rows = read(inputs['full_review'])['methods']['admittance']['retained_replay_rows']
assert parent_rows == 2718500
new = indices >= parent_rows
assert int(new.sum()) == 30
learner = PublishedLearner(runtime, dimension=7, direct=False, seed=42, device='cpu',
                           algorithm=state['algorithm'],
                           **{k: state[k] for k in ['critic_layer_norm', 'numerical_amendments', 'critic_clock']})
agent = learner.learner.agent
agent.load_state_dict(state['agent'])
original = digest(agent.state_dict())
assert original == digest(state['agent'])
rng = torch.get_rng_state().clone()
with torch.no_grad():
    observations = torch.as_tensor(arrays['observations'][indices])
    actions = torch.as_tensor(arrays['actions'][indices])
    q = torch.stack([agent.get_q_value(observations, actions, i, target=False).reshape(-1) for i in range(5)]).numpy()
assert np.isfinite(q).all() and original == digest(agent.state_dict()) and torch.equal(rng, torch.get_rng_state())
rewards = arrays['rewards'][indices, 0]
masks = arrays['masks'][indices].T.astype(float)
denominator = arrays['masks'].sum(axis=0, dtype=float) + 127 * masks.sum(axis=1)
sse = masks * (q.astype(float) - rewards.astype(float)[None]) ** 2
contributions = (128 * sse / denominator[:, None]).sum(axis=0)
health = read(inputs['health'])['methods']['admittance']
assert health['checkpoint_sha256'] == plan['inputs']['checkpoint']['sha256'] and health['terminal_count'] == 2004
error = np.abs(q - rewards[None]).astype(float)
assert np.isclose(error.mean(), health['terminal_q_absolute_error']['mean'], rtol=0, atol=1e-9)
assert np.isclose(error[masks.astype(bool)].mean(), health['terminal_q_in_bag_absolute_error']['mean'], rtol=0, atol=1e-9)
positions = {int(index): i for i, index in enumerate(indices)}
episodes = list(map(json.loads, inputs['episodes'].read_text().splitlines()))
terminals = [x for x in map(json.loads, inputs['transitions'].read_text().splitlines()) if x['done']]
assert len(episodes) == len(terminals) == 30
terminal_by_condition = {x['condition']: x for x in terminals}
assert len(terminal_by_condition) == 30
new_rows = []
for episode in episodes:
    transition = terminal_by_condition[episode['condition']]
    index = transition['step'] - 1
    assert index >= parent_rows and index in positions and transition['step'] == episode['total_steps']
    i = positions[index]
    assert rewards[i] == np.float32(transition['reward']) and arrays['dones'][index, 0] == 1
    folder = Path(episode['episode_path'])
    rollout = read(folder / 'rollout.json')
    assert rollout['task_success'] == episode['task_success'] and rollout['strict_success'] == episode['strict_success']
    evaluator = (folder / 'executed_evaluator.py.txt').read_text()
    assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in evaluator
    physical = rollout['abort_reason'] is None and rollout['stats']['max_external_penetration_m'] <= .0002
    assert physical == episode['physical_valid'] and bool(rollout['task_success'] and physical) == episode['strict_success']
    assert sha(folder / 'rollout.mjb') == episode['model_sha256']
    new_rows.append(dict(condition=episode['condition'], replay_index=index, global_step=transition['step'],
                         within_cycle_step=transition['step'] - parent_rows, task=episode['task_success'],
                         strict=episode['strict_success'], physical_valid=physical,
                         penetration_mm=rollout['stats']['max_external_penetration_m'] * 1000,
                         terminal_reward=float(rewards[i]), original_terminal_reward=transition['reward'],
                         episode_reward=episode['reward'], masked_sse=float(sse[:, i].sum()),
                         per_head_sse=sse[:, i].tolist(), contribution=float(contributions[i]),
                         rollout=dict(path=str(folder / 'rollout.json'), sha256=sha(folder / 'rollout.json')),
                         model_sha256=episode['model_sha256'], evaluator_sha256=sha(folder / 'executed_evaluator.py.txt')))
assert {row['replay_index'] for row in new_rows} == set(map(int, indices[new]))
focus = next(row for row in new_rows if row['condition'] == 'active_short_train_0600')
logs = list(map(json.loads, inputs['optimizer'].read_text().splitlines()))
assert len(logs) == 41250 and [x['step'] for x in logs] == list(range(parent_rows + 1, checkpoint['steps'] + 1))
assert all(math.isfinite(value) for row in logs for value in row.values() if isinstance(value, (int, float)))
before = [row['agent_train/q_loss'] for row in logs if row['step'] < focus['global_step']]
after = [row['agent_train/q_loss'] for row in logs if row['step'] >= focus['global_step']]
timeline = dict(event_step=focus['global_step'], event_within_cycle_step=focus['within_cycle_step'],
                before_count=len(before), at_or_after_count=len(after),
                before_mean=math.fsum(before) / len(before), at_or_after_mean=math.fsum(after) / len(after),
                before_max=max(before), at_or_after_max=max(after), posthoc_boundary=True)
full_loss = read(inputs['loss_review'])['methods']['admittance']['loss']['agent_train/q_loss']
near(math.fsum(before + after) / len(logs), full_loss['mean'])
assert max(before + after) == full_loss['maximum']
ranked = sorted([dict(replay_index=int(index), masked_sse=float(sse[:, i].sum()),
                      contribution=float(contributions[i]), new66=bool(new[i])) for i, index in enumerate(indices)],
                key=lambda row: (-row['masked_sse'], row['replay_index']))
features = np.concatenate([arrays['observations'][indices], arrays['actions'][indices]], axis=1)
np.savez_compressed(OUT / 'values.npz', indices=indices, features=features, rewards=rewards,
                    masks=masks, q=q, denominator=denominator, new66=new)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
loss = np.array([row['agent_train/q_loss'] for row in logs])
axes[0].plot(np.arange(1, len(logs) + 1), loss, alpha=.25, lw=.4)
axes[0].plot(np.arange(1000, len(logs) + 1), np.convolve(loss, np.ones(1000) / 1000, mode='valid'))
axes[0].axvline(focus['within_cycle_step'], color='red', ls='--', label='short0600 terminal recorded')
axes[0].set(xlabel='Within-cycle update', ylabel='Logged critic loss', title='Complete66 admittance; posthoc timing')
axes[0].legend(fontsize=8)
axes[1].scatter(indices[~new], sse[:, ~new].sum(axis=0), s=8, alpha=.4, label='Old1974')
axes[1].scatter(indices[new], sse[:, new].sum(axis=0), s=16, label='New30')
axes[1].scatter([focus['replay_index']], [focus['masked_sse']], color='red', s=35, label='short0600')
axes[1].set(xlabel='Replay index', ylabel='Complete66 masked terminal SSE', title='All2004 terminal rows')
axes[1].legend(fontsize=8)
for axis in axes:
    axis.grid(alpha=.2)
fig.savefig(OUT / 'diagnosis.png', dpi=140)
plt.close(fig)
report = dict(passed=True, time=time.time(), all2004_ranked=ranked, new30=new_rows, focus=focus,
              all2004_sse=float(sse.sum()), old1974_sse=float(sse[:, ~new].sum()), new30_sse=float(sse[:, new].sum()),
              all2004_contribution=float(contributions.sum()), old1974_contribution=float(contributions[~new].sum()),
              new30_contribution=float(contributions[new].sum()), focus_share_of_all2004_sse=focus['masked_sse'] / float(sse.sum()),
              timeline=timeline, network_and_forward_rng_unchanged=True, health_reproduced=True,
              values_sha256=sha(OUT / 'values.npz'), plot_sha256=sha(OUT / 'diagnosis.png'),
              plan_sha256=sha(OUT / 'PLAN.json'), new_physics=0, optimizer_updates=0, replay_writes=0,
              causal_claim=False, convergence_claim=False,
              limitation='Posthoc complete66 CPU forward on all2004 terminals and saved optimizer timeline. Boundary selected from observed short0600 label flip. End-checkpoint errors do not reconstruct earlier minibatches or prove the online spike cause. Full-replay terminal component is not the logged stochastic full critic loss. No new stop gate.')
for ref in plan['inputs'].values():
    assert sha(ref['path']) == ref['sha256']
with (OUT / 'REVIEW.json').open('x') as target:
    target.write(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['all2004_sse', 'new30_sse', 'all2004_contribution', 'new30_contribution', 'focus', 'timeline']}, indent=2))
