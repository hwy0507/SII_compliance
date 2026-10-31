"""Verify actual final gates after the retained read-only binder/observer failures."""
from pathlib import Path
import json, hashlib, time
D = Path(__file__).resolve().parent
B = D.parents[1]
N = B / 'runs/census97_new_terminal_diagnosis_20261031_v1'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = read(D / 'COMPLETION_PLAN.json')
rows = [json.loads(line) for line in (D / 'COMPLETION_OBSERVATIONS.jsonl').read_text().splitlines()]
assert rows and all(not x['all_complete'] for x in rows)
original_failure = N / 'WAIT_FAILURE_1793449231883653909.json'
assert set(N.glob('WAIT_FAILURE*')) == {original_failure}
assert not list(N.glob('REPAIR_FAILURE*'))
observer_failures = list(D.glob('COMPLETION_FAILURE*'))
assert len(observer_failures) == 1 and 'new97' in read(observer_failures[0])['traceback']
assert "KeyError: 'passed'" in read(original_failure)['traceback']
assert read(N / 'BIND_REPAIR_REVIEW.json')['passed']
final = {}
for name, job in p['jobs'].items():
    path = Path(job['finished'])
    value = read(path)
    assert value[job['finish_key']] == job['finish_value']
    final[name] = dict(path=str(path), sha256=sha(path))
assert read(N / 'FINISHED.json')['original_binding_failure_retained']
assert read(N / 'reference97/REVIEW.json')['passed']
assert read(N / 'DIAGNOSIS.json')['passed'] and read(N / 'SAVED_ARITHMETIC_REVIEW.json')['passed']
for j in p['guards']:
    s = Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split()
    assert s[0] != 'Z' and s[19] == j.get('start',j.get('proc_start_ticks'))
assert not (Path(p['guard_root'])/'STOP').exists()
result = dict(passed=True,time=time.time(),all_complete=True,samples=len(rows),
    elapsed_seconds=rows[-1]['time']-rows[0]['time'],
    first_steps={m:rows[0]['progress'][m]['steps'] for m in p['methods']},
    last_steps={m:read(Path(p['run'])/m/'train/PROGRESS.json')['steps'] for m in p['methods']},
    actual_plots_pending=True,convergence_claim=False,original_observer_failed=True,
    original_observer_failure=dict(path=str(observer_failures[0]),sha256=sha(observer_failures[0])),
    original_binding_failure=dict(path=str(original_failure),sha256=sha(original_failure)),
    original_raw_observations_sha256=sha(D/'COMPLETION_OBSERVATIONS.jsonl'),
    final_gates=final,physics_restarted=False,training_restarted=False,
    scope='Original finite observation failed on a read-only binder schema error; failures retained. Repair ran the originally registered analysis after root/per-method schema validation. All original scientific completion gates and repaired diagnostic completion are now individually verified. No claim that the original observer completed successfully.')
with (D/'COMPLETION_REVIEW.json').open('x') as f:
    json.dump(result,f,indent=2)
    f.write('\n')
print('Actual completion gates reconciled, original failures retained')
