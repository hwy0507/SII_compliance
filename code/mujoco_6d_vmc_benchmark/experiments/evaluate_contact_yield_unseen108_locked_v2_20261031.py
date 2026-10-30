"""One-shot final108 evaluation for the already locked v7/MLP384 model set.

Development failures are retained as evidence but do not suppress the
pre-registered comparison. This adapter changes only dispatch eligibility;
the frozen evaluator, test conditions, gates, metrics and replay are unchanged.
"""
import argparse
import os
from pathlib import Path
import sys

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tools')]
import run_v9_unseen_matrix_20261030 as evaluator
import diagnose_contact_yield_mlp384_fixed27_20261031_v4 as wide_development
from current_student_policy_mlp384_20261031 import load_current as load_wide_model
from collect_special_scene_actions_20261028 import read, sha, write
from diagnose_special_scene_regression_20261028 import now

DEVELOPMENT = ROOT / 'outputs/contact_yield_mlp384_fixed27_20261031_v4'
CAPACITY = ROOT / 'outputs/contact_yield_mlp_capacity_20261031_v1'
V7 = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
OUTPUTS = ROOT / 'outputs'
SCHEMA = 'sii-contact-yield-locked-unseen108-v2'
LEGACY_HANDOFF_UNIT = 'sii-contact-yield-student-diagnosis-handoff-20261030.service'


def verify_development():
    reg_path = DEVELOPMENT / 'REGISTRATION.json'
    execution_path = DEVELOPMENT / 'execution.json'
    review_path = DEVELOPMENT / 'REVIEW_WIDE.json'
    reg, state, review = map(read, (reg_path, execution_path, review_path))
    assert state['status'] == 'complete_development_diagnosis_pending_review'
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['registration_sha256'] == sha(reg_path)
    assert review['execution_sha256'] == sha(execution_path)
    assert review['reviewer_sha256'] == sha(ROOT / 'experiments/diagnose_contact_yield_students_20261030.py')
    assert review['wide_review_wrapper_sha256'] == sha(ROOT / 'experiments/review_contact_yield_mlp384_fixed27_20261031.py')
    assert reg['schema'] == 'sii-contact-yield-mlp384-fixed27-diagnosis-v4'
    models = reg['models']
    assert len(models) == 9
    expected = {(m['name'], scene + '_00') for m in models for scene in ('rod', 'ball', 'corner')}
    assert {(r['method'], r['condition']) for r in review['rows']} == expected
    assert len(review['rows']) == len(review['independent_replays']) == 27
    assert all(x['actor_replay_max_abs'] == 0 and x['filter_replay_max_abs'] == 0
               for x in review['independent_replays'])
    assert review['task_successes'] == sum(bool(r['task_success']) for r in review['rows'])
    assert review['strict_successes'] == sum(bool(r['strict_success']) for r in review['rows'])
    assert review['failed_ids'] == [
        r['condition'] + '__' + r['method'] for r in review['rows']
        if not (r['task_success'] and r['strict_success'])]
    assert state['registration_sha256'] == sha(reg_path)

    capacity_lock = read(CAPACITY / 'MODEL_LOCK.json')
    v7_lock = read(V7 / 'MODEL_LOCK.json')
    assert reg['parent_hashes']['fit_lock_sha256'] == sha(V7 / 'MODEL_LOCK.json')
    assert reg['parent_hashes']['fit_audit_sha256'] == sha(V7 / 'FIT_AUDIT.json')
    assert reg['parent_hashes']['dataset_sha256'] == sha(V7 / 'data/training_data.npz')
    assert reg['parent_hashes']['capacity_lock_sha256'] == sha(CAPACITY / 'MODEL_LOCK.json')
    capacity_by_seed = {m['seed']: m for m in capacity_lock['models']}
    locked_by_checkpoint = {m['checkpoint_sha256']: m for m in v7_lock['models']}
    locked_by_checkpoint.update({m['checkpoint_sha256']: m for m in capacity_lock['models']})
    for model in models:
        assert model['checkpoint_sha256'] in locked_by_checkpoint
        source = locked_by_checkpoint[model['checkpoint_sha256']]
        assert model['checkpoint'] == source['checkpoint']
        assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
        assert sha(Path(model['metadata'])) == model['metadata_sha256']
        expected_metadata = source.get('metadata') or str(
            Path(source['checkpoint']).parent / 'TRAINING_COMPLETE.json')
        assert model['metadata'] == expected_metadata
        if model['family'] == 'mlp_scratch':
            selected = capacity_by_seed[model['seed']]
            assert model['hidden_width'] == selected['width'] == 384
            assert model['selected_trial'] == selected['selected_trial']
            assert model['capacity_model_lock_sha256'] == sha(CAPACITY / 'MODEL_LOCK.json')
        else:
            assert model['family'] in ('esn_ridge', 'rnn_scratch')
            assert source['family'] == model['family'] and source['seed'] == model['seed']
    return reg, state, review, capacity_lock, v7_lock


def development_bundle():
    return {
        'registration_sha256': sha(DEVELOPMENT / 'REGISTRATION.json'),
        'execution_sha256': sha(DEVELOPMENT / 'execution.json'),
        'review_sha256': sha(DEVELOPMENT / 'REVIEW_WIDE.json'),
        'models_sha256': sha(CAPACITY / 'MODEL_LOCK.json'),
        'fit_audit_sha256': sha(CAPACITY / 'FIT_AUDIT.json'),
        'training_data_sha256': sha(V7 / 'data/training_data.npz'),
        'v7_model_lock_sha256': sha(V7 / 'MODEL_LOCK.json'),
        'v7_fit_audit_sha256': sha(V7 / 'FIT_AUDIT.json'),
    }


def register(root):
    assert root.parent == OUTPUTS and not root.exists()
    dev_reg, dev_state, dev_review, capacity_lock, v7_lock = verify_development()
    assert read(CAPACITY / 'execution.json')['status'] == 'complete'
    assert read(CAPACITY / 'FIT_AUDIT.json')['status'] == 'passed'
    assert read(V7 / 'execution.json')['status'] == 'complete'
    assert read(V7 / 'FIT_AUDIT.json')['status'] == 'passed'
    assert sha(evaluator.CONDITIONS) == evaluator.CONDITIONS_SHA
    contract = read(evaluator.CONDITIONS)
    for name, digest in contract['frozen_sources'].items():
        assert sha(evaluator.REPO / name) == digest, name
    for model in dev_reg['models']:
        for key in ('checkpoint', 'metadata'):
            assert sha(Path(model[key])) == model[key + '_sha256']
    cases = evaluator.make_cases(dev_reg['models'], contract['conditions'])
    sources = {str(p.relative_to(ROOT)): sha(p)
               for folder in ('scripts', 'tools') for p in (ROOT / folder).glob('*.py')}
    sources[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    sources['experiments/review_contact_yield_mlp384_fixed27_20261031.py'] = sha(
        ROOT / 'experiments/review_contact_yield_mlp384_fixed27_20261031.py')
    sources['experiments/diagnose_contact_yield_mlp384_fixed27_20261031_v4.py'] = sha(
        ROOT / 'experiments/diagnose_contact_yield_mlp384_fixed27_20261031_v4.py')
    sources['experiments/diagnose_contact_yield_students_20261030.py'] = sha(
        ROOT / 'experiments/diagnose_contact_yield_students_20261030.py')
    reg = dict(
        schema=SCHEMA,
        registered_utc=now(),
        conditions_path=str(evaluator.CONDITIONS),
        conditions_sha256=evaluator.CONDITIONS_SHA,
        metric_contract=contract,
        models=dev_reg['models'],
        cases=cases,
        maximum_episodes=108,
        teacher_config=str(ROOT / 'outputs/contact_yield_scrape_collection_20261030_v1/teacher.json'),
        teacher_config_sha256=sha(ROOT / 'outputs/contact_yield_scrape_collection_20261030_v1/teacher.json'),
        source_sha256=sources,
        recipe_config_sha256={n: sha(ROOT / n) for n in
                              ('configs/ball_source_demo.json', 'configs/workstation_source_demo.json')},
        python=os.path.abspath(sys.executable),
        runtime_versions=dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__),
        resources=dict(cpu=6, simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        development_files={n: sha(DEVELOPMENT / n) for n in
                           ('REGISTRATION.json', 'execution.json', 'REVIEW_WIDE.json')},
        model_lock_files={
            'capacity/MODEL_LOCK.json': sha(CAPACITY / 'MODEL_LOCK.json'),
            'capacity/FIT_AUDIT.json': sha(CAPACITY / 'FIT_AUDIT.json'),
            'capacity/execution.json': sha(CAPACITY / 'execution.json'),
            'v7/MODEL_LOCK.json': sha(V7 / 'MODEL_LOCK.json'),
            'v7/FIT_AUDIT.json': sha(V7 / 'FIT_AUDIT.json'),
            'v7/execution.json': sha(V7 / 'execution.json'),
            'v7/data/training_data.npz': sha(V7 / 'data/training_data.npz'),
        },
        development_outcomes=dict(task_successes=dev_review['task_successes'],
                                  strict_successes=dev_review['strict_successes'],
                                  failed_ids=dev_review['failed_ids']),
        selection='The exact nine checkpoints in the completed v4 fixed27 registration; no reselection.',
        dispatch_policy='Development outcomes, including failures, are recorded and do not gate this one-shot comparison. No model substitution or test-based tuning.',
        failure_policy='Run once; preserve every failed/incomplete cell. No automatic retries, fallback models, or test-based tuning. Original Task/Strict, sampled hold, dual-pass SPT, torque, comfort NA/proxy and machine compliance remain unchanged.',
        scope='Only dispatch eligibility changes from v1. Frozen 12 isolated conditions, 9 locked models, physical workers, gates, metrics, and independent replay remain the original evaluator.',
    )
    root.mkdir()
    write(root / 'REGISTRATION.json', reg)


def check(reg):
    dev_reg, _, dev_review, _, _ = verify_development()
    assert reg['schema'] == SCHEMA and reg['models'] == dev_reg['models']
    assert reg['development_outcomes']['task_successes'] == dev_review['task_successes']
    assert reg['development_outcomes']['strict_successes'] == dev_review['strict_successes']
    assert reg['development_outcomes']['failed_ids'] == dev_review['failed_ids']
    assert reg['development_files'] == {n: sha(DEVELOPMENT / n) for n in
                                        ('REGISTRATION.json', 'execution.json', 'REVIEW_WIDE.json')}
    assert reg['model_lock_files'] == {
        'capacity/MODEL_LOCK.json': sha(CAPACITY / 'MODEL_LOCK.json'),
        'capacity/FIT_AUDIT.json': sha(CAPACITY / 'FIT_AUDIT.json'),
        'capacity/execution.json': sha(CAPACITY / 'execution.json'),
        'v7/MODEL_LOCK.json': sha(V7 / 'MODEL_LOCK.json'),
        'v7/FIT_AUDIT.json': sha(V7 / 'FIT_AUDIT.json'),
        'v7/execution.json': sha(V7 / 'execution.json'),
        'v7/data/training_data.npz': sha(V7 / 'data/training_data.npz'),
    }
    assert reg['cases'] == evaluator.make_cases(reg['models'], reg['metric_contract']['conditions'])
    assert reg['maximum_episodes'] == 108
    assert sha(evaluator.CONDITIONS) == reg['conditions_sha256'] == evaluator.CONDITIONS_SHA
    assert read(evaluator.CONDITIONS) == reg['metric_contract']
    for name, digest in reg['metric_contract']['frozen_sources'].items():
        assert sha(evaluator.REPO / name) == digest, name
    assert reg['resources'] == dict(cpu=6, simulators=1, threads=1,
                                    memory_max_bytes=3221225472, swap_bytes=0)
    assert reg['python'] == os.path.abspath(sys.executable)
    assert reg['runtime_versions'] == dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__)
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in reg['recipe_config_sha256'].items():
        assert sha(ROOT / name) == digest, name
    assert sha(Path(reg['teacher_config'])) == reg['teacher_config_sha256']
    for model in reg['models']:
        for key in ('checkpoint', 'metadata'):
            assert sha(Path(model[key])) == model[key + '_sha256']


def run(root):
    evaluator.inactive()
    assert evaluator.properties(LEGACY_HANDOFF_UNIT)['ActiveState'] == 'inactive'
    original = evaluator.check_registration
    original_case = evaluator.run_case
    evaluator.check_registration = check
    evaluator.run_case = wide_development.run_case
    try:
        evaluator.run(root)
    finally:
        evaluator.check_registration = original
        evaluator.run_case = original_case


def review(root, output):
    original = evaluator.check_registration
    import current_student_policy_20260921 as legacy_policy
    original_loader = legacy_policy.load_current
    evaluator.check_registration = check
    legacy_policy.load_current = load_wide_model
    try:
        evaluator.review(root, output)
    finally:
        evaluator.check_registration = original
        legacy_policy.load_current = original_loader


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('register', 'run', 'review'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.mode == 'register':
        register(args.root.resolve())
    elif args.mode == 'run':
        run(args.root.resolve())
    else:
        assert args.output is not None
        review(args.root.resolve(), args.output.resolve())
