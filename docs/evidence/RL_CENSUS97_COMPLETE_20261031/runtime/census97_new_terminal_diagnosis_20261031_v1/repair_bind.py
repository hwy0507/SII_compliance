"""Repair the per-method report schema binding; preserve original failure/source."""
from pathlib import Path
import os, time, json, subprocess, traceback
import wait_diagnosis as w

def main():
    os.sched_setaffinity(0, {12})
    p = w.read(w.O / 'WAIT_PLAN.json')
    repair = w.read(w.O / 'BIND_REPAIR_PLAN.json')
    assert w.sha(Path(__file__)) == repair['repair_source_sha256']
    assert w.sha(Path(repair['original_failure']['path'])) == repair['original_failure']['sha256']
    assert not Path('/proc', str(repair['original_wait_pid'])).exists()
    w.sources(p)
    full = w.ready()
    aggregate = w.read(w.F / 'REVIEW.json')
    assert aggregate['passed'] and time.time() < p['deadline_unix']
    assert not (w.O / 'REFERENCE_PLAN.json').exists() and not (w.O / 'reference97').exists()
    methods, inputs = {}, []
    for m, e in p['methods'].items():
        train = w.R / m / 'train'
        cp = w.B / 'runs/parameter_census_cycle97_archive_20261031_v1' / m / 'cycle_00097.pt'
        assert w.sha(cp) == full['methods'][m]['checkpoint_sha256']
        old_review = w.F / (m + '_REVIEW.json')
        old = w.read(old_review)
        assert old == aggregate['methods'][m]
        assert old['checkpoint_sha256'] == full['methods'][m]['checkpoint_sha256']
        assert old['full_learner_optimizer_replay_rng_unchanged'] and old['saved_scalar_arithmetic_verified']
        assert w.sha(w.F / (m + '_values.npz')) == old['values_sha256']
        item = dict(checkpoint=w.ref(cp), registration=w.ref(w.R / m / 'REGISTRATION.json'),
                    old_values=w.ref(w.F / (m+'_values.npz')), old_review=w.ref(old_review),
                    transitions=w.ref(train / 'transitions.jsonl'), episodes=w.ref(train / 'episodes.jsonl'),
                    terminal_rows=e['old_terminal_rows']+30,
                    prediction_block_boundaries=e['prediction_block_boundaries']+[e['old_terminal_rows']+30])
        methods[m] = item
        inputs.extend(v for v in item.values() if isinstance(v, dict) and 'path' in v)
    for path in [w.V / 'REVIEW.json', w.V / 'loss/REVIEW.json', w.V / 'health/DIAGNOSIS.json',
                 w.F / 'REVIEW.json', w.C / 'CACHE_POPULATION_FULL_REVIEW.json']:
        inputs.append(w.ref(path))
    w.put(w.O / 'REFERENCE_PLAN.json', dict(time=time.time(), deadline_unix=p['deadline_unix'],
        source_sha256=p['source_hashes']['build_reference97.py'], methods=methods, inputs=inputs,
        restore_runtime=p['restore_runtime'], runtime_hashes=p['runtime_hashes'],
        physics_steps=0, formal_updates=0,
        scope='Bound actual complete97 after fixing report schema. Root passed plus exact per-method report equality/state/masks/values hashes required. All8713 terminals, no98 dispatch.'))
    w.put(w.O / 'BIND_REPAIR_REVIEW.json', dict(passed=True, time=time.time(),
        root_passed_and_all_per_method_records_exact=True, original_failure_preserved=True,
        original_sources_unchanged=True, analysis_sources_unchanged=True,
        original_inference_not_started=True, physics_steps=0, optimizer_updates=0))
    for name in ['build_reference97.py', 'analyze.py', 'review_saved.py']:
        with (w.O / (name + '.log')).open('x') as log:
            subprocess.run([str(w.B / 'env/bin/python'), str(w.D / name)], check=True,
                stdout=log, stderr=subprocess.STDOUT,
                timeout=min(p['analysis_budget_seconds'], max(1,p['deadline_unix']-time.time())),
                env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1'))
    for path in [w.O / 'reference97/REVIEW.json', w.O / 'DIAGNOSIS.json', w.O / 'SAVED_ARITHMETIC_REVIEW.json']:
        assert w.read(path)['passed']
    w.put(w.O / 'FINISHED.json', dict(passed=True, time=time.time(), actual_plot_inspection_pending=True,
        original_binding_failure_retained=True, binding_repair=w.ref(w.O / 'BIND_REPAIR_REVIEW.json'),
        physics_steps=0, optimizer_updates=0, convergence_claim=False, automatic98=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        w.put(w.O / ('REPAIR_FAILURE_'+str(time.time_ns())+'.json'),dict(time=time.time(),traceback=traceback.format_exc()))
        raise
