"""Review observed progress, allowing verified natural completion of original jobs."""
from pathlib import Path
import hashlib
import json
import math
import time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


finished = read(OUT / 'FINISHED.json')
assert finished['completed'] and not finished['science_restarted']
rows = [json.loads(line) for line in (OUT / 'SAMPLES.jsonl').read_text().splitlines()]
assert len(rows) == finished['samples']
assert [row['index'] for row in rows] == list(range(len(rows)))
assert all(a['time'] < b['time'] for a, b in zip(rows, rows[1:]))
for row in rows:
    for learner in row['learners']:
        assert not learner['failure']
        assert learner['live'] or learner['finished']
        if learner['finished']:
            assert learner['finished']['status'] == 'stopped_at_complete_cycle'
    assert all(v['live'] for k, v in row['watchers'].items() if k.startswith('guard'))
for i in range(3):
    assert all(a['learners'][i]['progress']['steps'] <= b['learners'][i]['progress']['steps'] for a, b in zip(rows, rows[1:]))
    assert rows[-1]['learners'][i]['progress']['steps'] > rows[0]['learners'][i]['progress']['steps']
    expected = rows[0]['learners'][i]
    assert all(x['learners'][i]['pid'] == expected['pid'] and x['learners'][i]['expected_start'] == expected['expected_start'] for x in rows)

markers = {
    'archive': B / 'runs/parameter_capacity_pool30_cycle66_20261026_v1/ARCHIVE_REVIEW_FINISHED.json',
    'loss66': B / 'runs/parameter66_loss_20261028_v1/FINISHED.json',
    'terminal66': B / 'runs/vmc66_terminal_anchor_followup_20261028_v1/FINISHED.json',
    'labels66': B / 'runs/parameter_task_label_audit66_20261028_v1/FINISHED66.json',
    'restore67': B / 'runtime/prepare_parameter67_20261028_v1/parameter_FINISHED.json',
    'ranked66': B / 'runs/vmc66_ranked65_terminal_followup_20261028_v1/FINISHED.json',
}
ended = {}
for name in rows[0]['watchers']:
    absent = [row for row in rows if not row['watchers'][name]['live']]
    if absent:
        assert name in markers, ('Unexpected missing waiter/guard', name)
        marker = markers[name]
        value = read(marker)
        assert value.get('completed', value.get('prepared', False))
        ended[name] = dict(first_observed_not_live=absent[0]['time'], completion_verified_now=True,
                           marker=str(marker), marker_sha256=sha(marker))

guard = []
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as source:
    for line in source:
        row = json.loads(line)
        if rows[0]['time'] <= row['time'] <= rows[-1]['time']:
            guard.append(row)
assert len(guard) > 1
with (OUT / 'GUARD_SAMPLES.jsonl').open('x') as target:
    target.write(''.join(json.dumps(row) + '\n' for row in guard))
stats = {}
for i in range(4):
    values = [next(g['utilization'] for g in row['gpus'] if g['gpu'] == i) for row in guard]
    assert all(math.isfinite(value) for value in values)
    stats[str(i)] = dict(minimum=min(values), mean=math.fsum(values) / len(values), below50=sum(value < 50 for value in values))
guard_report = dict(samples=len(guard), first_time=guard[0]['time'], last_time=guard[-1]['time'],
                    max_gap_seconds=max(b['time'] - a['time'] for a, b in zip(guard, guard[1:])),
                    gpus=stats, synthetic_guard_included=True, per_instant_guarantee=False)
with (OUT / 'GUARD_REVIEW.json').open('x') as target:
    target.write(json.dumps(guard_report, indent=2) + '\n')
report = dict(passed=True, time=time.time(), samples=len(rows), first_time=rows[0]['time'], last_time=rows[-1]['time'],
              first_steps=[x['progress']['steps'] for x in rows[0]['learners']],
              last_steps=[x['progress']['steps'] for x in rows[-1]['learners']],
              all_steps_nondecreasing=True, original_identities_or_complete_cycle=True,
              naturally_ended_watchers=ended, observer_finished=True, science_restarted=False,
              convergence_claim=False, source_sha256=sha(Path(__file__)), samples_sha256=sha(OUT / 'SAMPLES.jsonl'))
with (OUT / 'REVIEW.json').open('x') as target:
    target.write(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(observer=report, guard=guard_report), indent=2))
