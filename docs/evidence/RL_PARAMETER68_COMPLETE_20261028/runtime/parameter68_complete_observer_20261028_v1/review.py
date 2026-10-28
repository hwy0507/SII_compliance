from pathlib import Path
import hashlib
import json
import math
import time

ROOT = Path(__file__).parent
finished = json.loads((ROOT / 'FINISHED.json').read_text())
samples = [json.loads(line) for line in (ROOT / 'SAMPLES.jsonl').read_text().splitlines()]
assert finished['completed'] and not finished['science_restarted']
assert len(samples) == finished['samples']
assert [s['index'] for s in samples] == list(range(len(samples)))
assert all(a['time'] < b['time'] for a, b in zip(samples, samples[1:]))
for i in range(3):
    rows = [s['learners'][i] for s in samples]
    assert rows[0]['live']
    assert all(not r['failure'] and (r['live'] or r['finished']) for r in rows)
    assert len({(r['pid'], r['expected_start']) for r in rows}) == 1
    assert all(a['progress']['steps'] <= b['progress']['steps'] for a, b in zip(rows, rows[1:]))
    if not rows[-1]['live']:
        assert rows[-1]['finished']['status'] == 'stopped_at_complete_cycle'
        assert rows[-1]['finished']['steps'] == rows[-1]['progress']['steps']
assert all(v['live'] for s in samples for k, v in s['watchers'].items() if k.startswith('guard'))
guard = []
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as stream:
    for line in stream:
        row = json.loads(line)
        if samples[0]['time'] <= row['time'] <= samples[-1]['time']:
            guard.append(row)
assert len(guard) > 1
(ROOT / 'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in guard))
gpus = {}
for i in range(4):
    values = [next(g['utilization'] for g in r['gpus'] if g['gpu'] == i) for r in guard]
    assert all(math.isfinite(v) for v in values)
    gpus[str(i)] = dict(minimum=min(values), mean=math.fsum(values) / len(values),
                       below50=sum(v < 50 for v in values))
result = dict(time=time.time(), passed=True, samples=len(samples),
              first_time=samples[0]['time'], last_time=samples[-1]['time'],
              first_steps=[v['progress']['steps'] for v in samples[0]['learners']],
              last_steps=[v['progress']['steps'] for v in samples[-1]['learners']],
              all_original_learners_naturally_completed=all(not v['live'] and v['finished'] for v in samples[-1]['learners']),
              all_original_guard_identities_live=True, no_failure=True,
              no_science_restart=True, goal_completion=False,
              samples_sha256=hashlib.sha256((ROOT / 'SAMPLES.jsonl').read_bytes()).hexdigest(),
              reviewer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
gr = dict(samples=len(guard), first_time=guard[0]['time'], last_time=guard[-1]['time'],
          max_gap_seconds=max(b['time'] - a['time'] for a, b in zip(guard, guard[1:])),
          gpus=gpus, synthetic_guard_included=True, per_instant_guarantee=False)
(ROOT / 'REVIEW.json').write_text(json.dumps(result, indent=2) + '\n')
(ROOT / 'GUARD_REVIEW.json').write_text(json.dumps(gr, indent=2) + '\n')
print(json.dumps(dict(observer=result, guard=gr), indent=2))
