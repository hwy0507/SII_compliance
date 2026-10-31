"""Summarize the completed finite observation without hiding its wait timeout."""
from pathlib import Path
import json, time, hashlib

D = Path(__file__).resolve().parent
B = D.parents[1]
read = lambda p: json.loads(p.read_text())
plan = read(D / 'PLAN.json')
timeout = read(D / 'OBSERVATION_TIMEOUT.json')
assert timeout['scientific_failure'] is False
assert not (D / 'OBSERVATION_REVIEW.json').exists()
assert not list(D.glob('OBSERVATION_FAILURE*'))
assert hashlib.sha256((D / 'observe_boundary.py').read_bytes()).hexdigest() == plan['observer_sha256']
rows = [json.loads(line) for line in (D / 'OBSERVATIONS.jsonl').read_text().splitlines()]
assert len(rows) == timeout['samples'] and all(r['verified_identities'] == 102 for r in rows)
assert all(not r['boundary_complete'] for r in rows)
assert all(rows[i+1]['time'] > rows[i]['time'] for i in range(len(rows)-1))
for m in plan['methods']:
    assert all(rows[i+1]['progress'][m]['steps'] >= rows[i]['progress'][m]['steps'] for i in range(len(rows)-1))
    assert rows[-1]['progress'][m]['steps'] > rows[0]['progress'][m]['steps']
boundary = read(B / 'runs/census97_capacity_boundary_20261031_v1/REVIEW.json')
assert boundary['passed'] and boundary['time'] > plan['observation_deadline_unix']
final_ids = []
for j in plan['identities']:
    if j['pid'] == plan['boundary_pid']:
        continue
    s = Path('/proc', str(j['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
    assert s[0] != 'Z' and s[19] == j['start']
    final_ids.append(j)
assert len(final_ids) == 101
result = dict(passed=True, time=time.time(), samples=len(rows),
    elapsed_seconds=rows[-1]['time']-rows[0]['time'], identities=plan['identities'],
    first_steps={m:rows[0]['progress'][m]['steps'] for m in plan['methods']},
    last_steps={m:rows[-1]['progress'][m]['steps'] for m in plan['methods']},
    boundary_completed=False, bounded_wait_timed_out=True, convergence_claim=False,
    boundary_completion_time=boundary['time'], observation_deadline=plan['observation_deadline_unix'],
    boundary_completed_after_deadline_seconds=boundary['time']-plan['observation_deadline_unix'],
    final_identities_verified_after_boundary=final_ids,
    scope='The finite observer timed out and is retained. All original102 identities/progress passed its34 samples. Boundary completed just after its deadline; final101 continuing identities were checked separately. This summary does not claim the original wait completed successfully or extend its budget.')
with (D / 'OBSERVATION_REVIEW.json').open('x') as f:
    json.dump(result, f, indent=2)
    f.write('\n')
print(json.dumps({k:result[k] for k in ['samples','elapsed_seconds','first_steps','last_steps','boundary_completed_after_deadline_seconds']}))
