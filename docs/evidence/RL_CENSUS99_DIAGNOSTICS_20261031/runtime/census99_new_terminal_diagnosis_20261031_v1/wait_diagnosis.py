"""Finite read-only full99/new-terminal consumer; no training dispatch."""
from pathlib import Path
import os, sys, json, hashlib, time, subprocess, traceback, ast

D = Path(__file__).resolve().parent
B = D.parents[1]
O = B / 'runs/census99_new_terminal_diagnosis_20261031_v1'
R = B / 'runs/parameter_census_cycle99_20261031_v1'
V = B / 'runs/parameter_census_cycle99_review_20261031_v1'
F = B / 'runs/census99_fixed98_terminal_20261031_v1'
C = B / 'runtime/census99_prefix_comparison_20261031_v1'
read = lambda p: json.loads(Path(p).read_text())

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def ref(p):
    return dict(path=str(p), sha256=sha(p))

def put(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')

def live(j):
    s = Path('/proc', str(j['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
    assert s[0] != 'Z' and s[19] == j.get('start', j.get('proc_start_ticks'))

def sources(p):
    for name, h in p['source_hashes'].items():
        assert sha(D / name) == h
        ast.parse((D / name).read_text())
    for path, h in p['fixed_inputs'].items():
        assert sha(path) == h
    for name, h in p['runtime_hashes'].items():
        assert sha(Path(p['restore_runtime']) / name) == h

def ready():
    assert read(V / 'FINISHED.json')['completed']
    full = read(V / 'REVIEW.json')
    assert full['passed'] and read(V / 'loss/REVIEW.json')['passed']
    assert read(V / 'health/DIAGNOSIS.json')['cycle'] == 99
    assert read(F / 'FINISHED.json')['passed'] and read(F / 'REVIEW.json')['passed']
    assert read(C / 'COMPARISON_FINISHED.json')['passed']
    assert read(C / 'CACHE_POPULATION_FULL_REVIEW.json')['passed']
    return full

def preflight(p):
    sources(p)
    for job in p['original_consumers']:
        live(job['identity'])
    assert time.time() < p['deadline_unix']
    try:
        ready()
    except FileNotFoundError:
        missing = True
    else:
        raise AssertionError('Unexpected complete99 already ready before waiting registration')
    import numpy as np
    sys.path.insert(0, str(D))
    from build_reference99 import stats
    previous = B / 'runs/census98_new_terminal_diagnosis_20261031_v1/reference98'
    details = {}
    for m in p['methods']:
        rv = read(previous / (m + '_REVIEW.json'))
        with np.load(previous / (m + '_values.npz')) as z:
            actual = stats(z['initial_prediction'], z['rewards'], z['masks'])
            assert len(z['indices']) == p['methods'][m]['old_terminal_rows']
            assert np.count_nonzero(z['cycles'] == 98) == 30
        assert actual == rv['stats']
        details[m] = dict(all_prior98_saved_stats_exact=True, old_terminal_rows=rv['terminal_rows'])
    put(O / 'PREFLIGHT_REVIEW.json', dict(passed=True, time=time.time(),
        actual_missing_complete99_rejected=missing, original_consumers_live=True,
        methods=details, neural_forwards=0, physics_steps=0, optimizer_updates=0))

def bind(p, full):
    methods, inputs = {}, []
    for m, e in p['methods'].items():
        train = R / m / 'train'
        cp = B / 'runs/parameter_census_cycle99_archive_20261031_v1' / m / 'cycle_00099.pt'
        assert sha(cp) == full['methods'][m]['checkpoint_sha256']
        old_review = F / (m + '_REVIEW.json')
        from fixed_report_contract import check_fixed_report
        check_fixed_report(read(F / 'REVIEW.json'), read(old_review), m, full['methods'][m]['checkpoint_sha256'], F / (m+'_values.npz'))
        item = dict(checkpoint=ref(cp), registration=ref(R / m / 'REGISTRATION.json'),
                    old_values=ref(F / (m+'_values.npz')), old_review=ref(old_review),
                    transitions=ref(train / 'transitions.jsonl'), episodes=ref(train / 'episodes.jsonl'),
                    terminal_rows=e['old_terminal_rows']+30,
                    prediction_block_boundaries=e['prediction_block_boundaries']+[e['old_terminal_rows']+30])
        methods[m] = item
        inputs.extend(v for v in item.values() if isinstance(v, dict) and 'path' in v)
    for path in [V / 'REVIEW.json', V / 'loss/REVIEW.json', V / 'health/DIAGNOSIS.json',
                 F / 'REVIEW.json', C / 'CACHE_POPULATION_FULL_REVIEW.json']:
        inputs.append(ref(path))
    put(O / 'REFERENCE_PLAN.json', dict(time=time.time(), deadline_unix=p['deadline_unix'],
        source_sha256=p['source_hashes']['build_reference99.py'], methods=methods, inputs=inputs,
        restore_runtime=p['restore_runtime'], runtime_hashes=p['runtime_hashes'],
        physics_steps=0, formal_updates=0,
        scope='Bound after actual full99 reviews. All8893 terminal reference, old8803 predictions exact;90new terminals retained including failures. No100 dispatch.'))

def main(p):
    sources(p)
    assert read(O / 'PREFLIGHT_REVIEW.json')['passed']
    os.sched_setaffinity(0, {12})
    while True:
        assert time.time() < p['deadline_unix']
        assert not (R / 'ARCHIVE_REVIEW_FAILURE.json').exists()
        assert not list(F.glob('*FAILURE*')) and not list(C.glob('COMPARISON_FAILURE*'))
        pending = [job for job in p['original_consumers'] if not Path(job['finished']).exists()]
        if not pending:
            break
        for job in pending:
            live(job['identity'])
        time.sleep(15)
    full = ready()
    sources(p)
    bind(p, full)
    for name in ['build_reference99.py', 'analyze.py', 'review_saved.py']:
        with (O / (name + '.log')).open('x') as log:
            subprocess.run([str(B / 'env/bin/python'), str(D / name)], check=True,
                stdout=log, stderr=subprocess.STDOUT,
                timeout=min(p['analysis_budget_seconds'], max(1, p['deadline_unix']-time.time())),
                env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    assert read(O / 'reference99/REVIEW.json')['passed'] and read(O / 'DIAGNOSIS.json')['passed']
    assert read(O / 'SAVED_ARITHMETIC_REVIEW.json')['passed']
    put(O / 'FINISHED.json', dict(passed=True, time=time.time(), actual_plot_inspection_pending=True,
        physics_steps=0, optimizer_updates=0, convergence_claim=False, automatic100=False))

if __name__ == '__main__':
    p = read(O / 'WAIT_PLAN.json')
    try:
        if '--preflight' in sys.argv:
            preflight(p)
        elif '--launch' in sys.argv:
            sources(p)
            assert read(O / 'PREFLIGHT_REVIEW.json')['passed'] and not (O / 'LAUNCH.json').exists()
            for job in p['original_consumers']:
                live(job['identity'])
            assert time.time() < p['deadline_unix']
            with (O / 'wait.log').open('xb') as log:
                process = subprocess.Popen([str(B / 'env/bin/python'), str(Path(__file__))],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            state = Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()
            assert state[0] != 'Z'
            put(O / 'LAUNCH.json', dict(pid=process.pid, proc_start_ticks=state[19], time=time.time(),
                deadline_unix=p['deadline_unix'], source_sha256=sha(__file__)))
            print('New-terminal read-only consumer launched', process.pid)
        else:
            main(p)
    except BaseException:
        put(O / ('WAIT_FAILURE_' + str(time.time_ns()) + '.json'), dict(time=time.time(), traceback=traceback.format_exc()))
        raise
