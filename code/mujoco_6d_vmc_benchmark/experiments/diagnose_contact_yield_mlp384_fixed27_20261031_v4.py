"""Complete fixed27 closure review with wide-MLP-aware execution and replay."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import runpy
import sys
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v4'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
CAPACITY = ROOT/'outputs/contact_yield_mlp_capacity_20261031_v1'
COLLECTION = ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
PRIOR = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v3'
BASE = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
FIT_UNIT = 'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope'
RUNNER = ROOT/'tools/run_video_reference_coverage_mlp384_20261031_v4.py'
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]

from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('contact_yield_mlp384_fixed27_base', BASE)
diagnosis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diagnosis
spec.loader.exec_module(diagnosis)
diagnosis.COLLECTION = COLLECTION
diagnosis.TRAINING = TRAINING
diagnosis.UNITS = (FIT_UNIT,)
diagnosis.TARGET = TARGET


def selected_models():
    old_lock = read(TRAINING/'MODEL_LOCK.json')
    capacity_lock = read(CAPACITY/'MODEL_LOCK.json')
    capacity = {row['seed']: row for row in capacity_lock['models']}
    models = []
    for old in old_lock['models']:
        model = dict(old)
        if old['family'] == 'mlp_scratch':
            selected = capacity[old['seed']]
            metadata = CAPACITY/'learning'/selected['selected_trial']/'TRAINING_COMPLETE.json'
            model.update(name='special_mlp_scratch_s%d_w384' % old['seed'],
                         selected_trial=selected['selected_trial'],
                         checkpoint=selected['checkpoint'],
                         checkpoint_sha256=selected['checkpoint_sha256'],
                         metadata=str(metadata), metadata_sha256=sha(metadata),
                         validation_mse=selected['validation_mse'], trainable_parameters=16512,
                         hidden_width=384, capacity_model_lock_sha256=sha(CAPACITY/'MODEL_LOCK.json'))
        models.append(model)
    assert len(models) == 9 and len({m['name'] for m in models}) == 9
    assert sum(m.get('hidden_width') == 384 for m in models) == 3
    return models


def references():
    collection = read(COLLECTION/'REGISTRATION.json')
    state = read(COLLECTION/'execution.json')
    result = []
    for scene in ('rod', 'ball', 'corner'):
        case = next(c for c in collection['cases'] if c['id'] == scene+'_00')
        receipt = next(r for r in state['rows'] if r['id'] == case['id'])
        assert receipt['qualified']
        folder = Path(receipt['folder'])
        result.append(dict(id=case['id'], scene=scene, split='train', seed=case['seed'],
                           parameters=case['parameters'], folder=str(folder),
                           hashes={n: sha(folder/n) for n in
                                   ('execution.json', 'trajectory.npz', 'DEMONSTRATION_QUALIFICATION.json')},
                           model_sha256=read(folder/'execution.json')['model_sha256']))
    return collection, result


def input_hashes():
    fit_state = read(TRAINING/'execution.json')
    fit_audit = read(TRAINING/'FIT_AUDIT.json')
    fit_lock = read(TRAINING/'MODEL_LOCK.json')
    data = read(TRAINING/'data/DATA_COMPLETE.json')
    capacity_state = read(CAPACITY/'execution.json')
    capacity_audit = read(CAPACITY/'FIT_AUDIT.json')
    capacity_lock = read(CAPACITY/'MODEL_LOCK.json')
    assert properties(FIT_UNIT)['ActiveState'] == 'inactive'
    assert fit_state['status'] == 'complete' and len(fit_state['fits']) == 75
    assert all(row['status'] == 'complete' for row in fit_state['fits'])
    assert fit_lock['status'] == 'frozen' and fit_audit['status'] == 'passed'
    assert fit_audit['dataset_sha256'] == data['training_data_sha256']
    assert len(fit_audit['candidate_jobs']) == 75 and len(fit_audit['frozen_actor_replays']) == 9
    assert capacity_state['status'] == 'complete' and len(capacity_state['fits']) == 36
    assert all(row['status'] == 'complete' and row['updates'] == 32000 for row in capacity_state['fits'])
    assert capacity_audit['status'] == 'passed' and capacity_audit['candidates'] == 36
    assert capacity_audit['dataset_sha256'] == data['training_data_sha256']
    assert capacity_lock['status'] == 'frozen' and all(m['width'] == 384 for m in capacity_lock['models'])
    assert read(COLLECTION/'COLLECTION_REVIEW.json')['status'] == 'verified_all30_qualified'
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False
    return dict(fit_execution_sha256=sha(TRAINING/'execution.json'),
                fit_audit_sha256=sha(TRAINING/'FIT_AUDIT.json'),
                fit_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),
                capacity_execution_sha256=sha(CAPACITY/'execution.json'),
                capacity_audit_sha256=sha(CAPACITY/'FIT_AUDIT.json'),
                capacity_lock_sha256=sha(CAPACITY/'MODEL_LOCK.json'),
                dataset_sha256=data['training_data_sha256'])


def source_manifest():
    paths = [p for folder in ('scripts', 'tools') for p in (ROOT/folder).glob('*.py')]
    paths += [Path(__file__), RUNNER, ROOT/'scripts/current_student_policy_mlp384_20261031.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def check(reg):
    parent_hashes = input_hashes()
    assert reg['schema'] == 'sii-contact-yield-mlp384-fixed27-diagnosis-v4'
    assert reg['parent_hashes'] == parent_hashes
    assert reg['models'] == selected_models()
    assert reg['source_sha256'] == source_manifest()
    assert reg['cases'] == diagnosis.make_cases(reg['models'], reg['references'])
    assert len(reg['cases']) == reg['maximum_episodes'] == 27
    assert {c['condition']['id'] for c in reg['cases']} == {'rod_00', 'ball_00', 'corner_00'}
    assert reg['python'] == os.path.abspath(sys.executable)
    assert reg['runtime_versions'] == dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__)
    for ref in reg['references']:
        for name, digest in ref['hashes'].items():
            assert sha(Path(ref['folder'])/name) == digest
    for model in reg['models']:
        for key in ('checkpoint', 'metadata'):
            assert sha(Path(model[key])) == model[key+'_sha256']


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    root.mkdir(parents=True)
    collection, refs = references()
    models = selected_models()
    cases = diagnosis.make_cases(models, refs)
    source = source_manifest()
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-mlp384-fixed27-diagnosis-v4', registered_utc=diagnosis.now(),
        parent_hashes=input_hashes(), parent_attempt=dict(
            path=str(PRIOR), registration_sha256=sha(PRIOR/'REGISTRATION.json'),
            execution_sha256=sha(PRIOR/'execution.json'), status=read(PRIOR/'execution.json')['status'],
            completed_rows=len(read(PRIOR/'execution.json').get('rows', [])),
            failure='Independent audit subprocess used legacy loader and rejected v2 contract before qualification.',
            preparation_failure='Initial v4 prepare omitted run-root mkdir; failed before registration or simulator dispatch; fixed in versioned source.'),
        models=models, references=refs, cases=cases, maximum_episodes=27,
        teacher_config=str(COLLECTION/'teacher.json'),
        teacher_config_sha256=collection['teacher_config_sha256'],
        training_files={n: sha(TRAINING/n) for n in
                        ('execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
                         'data/training_data.npz', 'data/DATA_COMPLETE.json')},
        collection_files={n: sha(COLLECTION/n) for n in
                          ('REGISTRATION.json', 'execution.json', 'COLLECTION_REVIEW.json')},
        source_sha256=source, python=os.path.abspath(sys.executable),
        runtime_versions=dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__),
        resources=dict(cpu=6, simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        selection='Fixed original ESN/RNN lock plus the three capacity-selected width-384 MLPs. No closure-based reselection.',
        failure_policy='Run all 27 train00 identities. Preserve scientific gate failures as rows; infrastructure failure stops without retry.',
        no_unseen_or_final108=True, no_gate_or_physics_change=True))
    check(read(root/'REGISTRATION.json'))


def _run_python_script(script, argv, log_path, wide_loader=False):
    import current_student_policy_20260921 as legacy_loader
    original = legacy_loader.load_current
    if wide_loader:
        from current_student_policy_mlp384_20261031 import load_current
        legacy_loader.load_current = load_current
    old_argv = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        sys.argv = [str(script), *map(str, argv)]
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            runpy.run_path(str(script), run_name='__main__')
    except BaseException:
        log_path.write_text(stdout.getvalue()+stderr.getvalue())
        raise
    finally:
        sys.argv = old_argv
        legacy_loader.load_current = original
    log_path.write_text(stdout.getvalue()+stderr.getvalue())


def run_case(root, case, reg):
    output = diagnosis.case_folder(root, case).parent
    assert not output.exists(), 'Preserve existing complete or incomplete identity evidence'
    output.parent.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k in
           {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
               MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
               VMC_TEACHER_CONFIG=reg['teacher_config'],
               VMC_SCENE_SEED=str(case['condition']['seed']),
               VMC_STUDENT_CHECKPOINT=case['model']['checkpoint'])
    env.update({k: str(v) for k, v in case['condition']['parameters'].items()})
    with (output.parent/(case['id']+'.log')).open('x') as log:
        result = __import__('subprocess').run([sys.executable, str(RUNNER), '--output', str(output),
                                               '--scenes', case['condition']['scene']],
                                              cwd=ROOT, env=env, stdout=log,
                                              stderr=__import__('subprocess').STDOUT)
    if result.returncode != 0:
        raise RuntimeError('physical worker failed for %s (exit %d)' % (case['id'], result.returncode))
    folder = diagnosis.case_folder(root, case)
    audits = ['audit_video_reference_vmc_20261028.py']
    if case['condition']['scene'] == 'rod':
        audits.append('audit_rod_yield_rejoin_v3_20261028.py')
    audits.append('qualify_ball_coverage_demo_20261029.py')
    for tool in audits:
        _run_python_script(ROOT/'tools'/tool, [folder], output/(tool+'.log'), wide_loader=True)
    pairing = diagnosis.check_episode(folder, case, reg)
    row = diagnosis.episode(folder, case['model']['name'], case['condition']['id'],
                            case['expected_duration_s'])
    write(output/'METRICS.json', row)
    return dict(id=case['id'], folder=str(folder), pairing=pairing,
                metrics_sha256=sha(output/'METRICS.json'))


diagnosis.check = check
diagnosis.run_case = run_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'review'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == 'prepare':
        prepare(root)
    elif args.mode == 'run':
        check(read(root/'REGISTRATION.json'))
        diagnosis.run(root)
    else:
        assert args.output is not None
        diagnosis.review(root, args.output.resolve())


if __name__ == '__main__':
    main()
