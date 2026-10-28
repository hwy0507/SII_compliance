"""Independent saved scalar checks; no learner imports or network forward."""
from pathlib import Path
import hashlib
import json
import math
import os
import time

os.sched_setaffinity(0, {53})
import numpy as np
OUT = Path(__file__).parent


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def near(a, b):
    assert math.isfinite(a) and math.isfinite(b)
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (a, b)


report = read(OUT / 'REVIEW.json')
plan = read(OUT / 'PLAN.json')
assert report['passed'] and report['plan_sha256'] == sha(OUT / 'PLAN.json')
assert report['values_sha256'] == sha(OUT / 'values.npz')
assert report['plot_sha256'] == sha(OUT / 'diagnosis.png')
for ref in plan['inputs'].values():
    assert sha(ref['path']) == ref['sha256']
assert sha(OUT / 'audit.py') == plan['source_sha256']
with np.load(OUT / 'values.npz', allow_pickle=False) as values:
    assert len(values['indices']) == 2004 and values['features'].shape == (2004, 57)
    assert values['q'].shape == values['masks'].shape == (5, 2004)
    assert all(np.isfinite(values[key]).all() for key in values.files)
    positions = {int(index): i for i, index in enumerate(values['indices'])}
    assert len(positions) == 2004
    np.testing.assert_array_equal(values['new66'], values['indices'] >= 2718500)
    assert int(values['new66'].sum()) == 30
    scalars = {}
    for index, i in positions.items():
        parts = [float(values['masks'][h, i]) * (float(values['q'][h, i]) - float(values['rewards'][i])) ** 2 for h in range(5)]
        scalars[index] = dict(masked_sse=math.fsum(parts), contribution=math.fsum(128 * parts[h] / float(values['denominator'][h]) for h in range(5)), parts=parts)
    rows = report['all2004_ranked']
    assert len(rows) == 2004 and {row['replay_index'] for row in rows} == set(positions)
    assert rows == sorted(rows, key=lambda row: (-row['masked_sse'], row['replay_index']))
    for row in rows:
        index = row['replay_index']
        assert row['new66'] == (index >= 2718500)
        for key in ['masked_sse', 'contribution']:
            near(row[key], scalars[index][key])
    for label, group in [('all2004', list(scalars)), ('old1974', [i for i in scalars if i < 2718500]), ('new30', [i for i in scalars if i >= 2718500])]:
        near(report[label + '_sse'], math.fsum(scalars[i]['masked_sse'] for i in group))
        near(report[label + '_contribution'], math.fsum(scalars[i]['contribution'] for i in group))
    episodes = {row['condition']: row for row in map(json.loads, Path(plan['inputs']['episodes']['path']).read_text().splitlines())}
    transitions = {row['condition']: row for row in map(json.loads, Path(plan['inputs']['transitions']['path']).read_text().splitlines()) if row['done']}
    assert len(report['new30']) == 30 and {row['condition'] for row in report['new30']} == set(episodes) == set(transitions)
    for row in report['new30']:
        index = row['replay_index']
        i = positions[index]
        episode = episodes[row['condition']]
        transition = transitions[row['condition']]
        assert row['global_step'] == index + 1 == episode['total_steps'] == transition['step']
        assert row['within_cycle_step'] == row['global_step'] - 2718500
        assert row['terminal_reward'] == float(values['rewards'][i]) == float(np.float32(transition['reward']))
        assert row['original_terminal_reward'] == transition['reward'] and row['episode_reward'] == episode['reward']
        assert row['per_head_sse'] == scalars[index]['parts']
        near(row['masked_sse'], scalars[index]['masked_sse'])
        near(row['contribution'], scalars[index]['contribution'])
        rollout = read(row['rollout']['path'])
        assert sha(row['rollout']['path']) == row['rollout']['sha256']
        assert row['task'] == rollout['task_success'] and row['strict'] == rollout['strict_success']
        physical = rollout['abort_reason'] is None and rollout['stats']['max_external_penetration_m'] <= .0002
        assert physical == row['physical_valid'] and bool(row['task'] and physical) == row['strict']
        near(row['penetration_mm'], 1000 * rollout['stats']['max_external_penetration_m'])
    focus = next(row for row in report['new30'] if row['condition'] == 'active_short_train_0600')
    assert focus == report['focus']
    near(report['focus_share_of_all2004_sse'], focus['masked_sse'] / report['all2004_sse'])
logs = list(map(json.loads, Path(plan['inputs']['optimizer']['path']).read_text().splitlines()))
assert len(logs) == 41250 and [row['step'] for row in logs] == list(range(2718501, 2759751))
before = [row['agent_train/q_loss'] for row in logs if row['step'] < focus['global_step']]
after = [row['agent_train/q_loss'] for row in logs if row['step'] >= focus['global_step']]
timeline = report['timeline']
assert timeline['event_step'] == focus['global_step'] and timeline['event_within_cycle_step'] == focus['within_cycle_step']
assert len(before) == timeline['before_count'] and len(after) == timeline['at_or_after_count']
for label, group in [('before', before), ('at_or_after', after)]:
    near(timeline[label + '_mean'], math.fsum(group) / len(group))
    near(timeline[label + '_max'], max(group))
result = dict(passed=True, time=time.time(), all2004_scalar_sse_and_contributions_verified=True,
              all30_actual_terminal_and_rollout_labels_verified=True, optimizer_timeline_reproduced=True,
              report_sha256=sha(OUT / 'REVIEW.json'), reviewer_sha256=sha(Path(__file__)),
              new_forward=0, new_physics=0, optimizer_updates=0, convergence_claim=False, causal_claim=False)
with (OUT / 'SAVED_REVIEW.json').open('x') as target:
    target.write(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
