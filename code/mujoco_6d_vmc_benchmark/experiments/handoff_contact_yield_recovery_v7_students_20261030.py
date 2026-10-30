"""Bind the audited v7 models to one finite fixed27 train-only diagnosis."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_contact_yield_scrape_scenes_20261030 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

FIT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
FIT_HANDOFF = ROOT/'outputs/contact_yield_v6_mlp_rod_refit_handoff_20261030_v3'
FIT_UNIT = 'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope'
DIAGNOSIS = ROOT/'experiments/diagnose_contact_yield_recovery_v7_students_20261030.py'
BASE_DIAGNOSIS = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
TARGET = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v6'
HANDOFF = ROOT/'outputs/contact_yield_recovery_student_handoff_20261030_v5'
SOURCES = (Path(__file__).resolve(), DIAGNOSIS, BASE_DIAGNOSIS,
           ROOT/'tools/audit_special_scene_metrics_v2_20261030.py',
           ROOT/'tools/run_v9_unseen_matrix_20261030.py')


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_fit():
    fit_unit = properties(FIT_UNIT)
    assert fit_unit['ActiveState'] == 'inactive' and fit_unit.get('MainPID', '0') in ('0', '')
    handoff = read(FIT_HANDOFF/'execution.json')
    state = read(FIT/'execution.json')
    lock = read(FIT/'MODEL_LOCK.json')
    audit = read(FIT/'FIT_AUDIT.json')
    data = read(FIT/'data/DATA_COMPLETE.json')
    assert handoff['status'] == 'complete_nine_refits_pending_fixed27_review'
    assert state['status'] == 'complete' and len(state['fits']) == 75
    assert all(item['status'] == 'complete' for item in state['fits'])
    assert lock['status'] == 'frozen' and len(lock['models']) == 9
    assert state['model_lock_sha256'] == sha(FIT/'MODEL_LOCK.json')
    assert audit['status'] == 'passed'
    assert audit['model_lock_sha256'] == state['model_lock_sha256']
    assert audit['dataset_sha256'] == state['dataset_sha256'] == lock['training_data_sha256']
    assert data['training_data_sha256'] == state['dataset_sha256']
    assert data['episodes'] == 40 and data['frames'] == 21500
    assert len(audit['candidate_jobs']) == 75 and len(audit['frozen_actor_replays']) == 9
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False
    return lock, audit


def source_manifest():
    paths = list(SOURCES)
    paths += [p for folder in ('scripts', 'tools') for p in (ROOT/folder).glob('*.py')]
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))}


def prepare(root):
    root = Path(root).resolve()
    assert root == HANDOFF.resolve() and not root.exists()
    lock, audit = verify_fit()
    assert not TARGET.exists(), 'Preserve previous development receipts'
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-recovery-v7-fixed27-handoff-v1',
        registered_utc=now(), fit=str(FIT), fit_handoff=str(FIT_HANDOFF),
        fit_unit=FIT_UNIT, target=str(TARGET), diagnosis=str(DIAGNOSIS),
        fit_execution_sha256=sha(FIT/'execution.json'),
        model_lock_sha256=sha(FIT/'MODEL_LOCK.json'),
        audit_sha256=sha(FIT/'FIT_AUDIT.json'),
        dataset_sha256=lock['training_data_sha256'],
        source_sha256=source_manifest(), maximum_wait_seconds=0,
        no_final_test=True, no_reselection=True, no_retry=True,
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        scope='Fixed rod_00, ball_00, and corner_00 train identities; 9 locked models; preserve all 27 rows.'))


def check(reg):
    lock, audit = verify_fit()
    assert reg['schema'] == 'sii-contact-yield-recovery-v7-fixed27-handoff-v1'
    assert reg['fit_execution_sha256'] == sha(FIT/'execution.json')
    assert reg['model_lock_sha256'] == sha(FIT/'MODEL_LOCK.json')
    assert reg['audit_sha256'] == sha(FIT/'FIT_AUDIT.json')
    assert reg['dataset_sha256'] == lock['training_data_sha256']
    assert reg['source_sha256'] == source_manifest()
    assert reg['target'] == str(TARGET)
    if TARGET.exists():
        target_reg = read(TARGET/'REGISTRATION.json')
        assert target_reg['schema'] == 'sii-contact-yield-recovery-v7-fixed27-diagnosis-v1'
        assert target_reg['training_files'] == {
            name: sha(FIT/name) for name in (
                'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
                'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    assert audit['status'] == 'passed'


def run(root):
    root = Path(root).resolve()
    reg = read(root/'REGISTRATION.json')
    check(reg)
    state_path = root/'execution.json'
    assert not state_path.exists(), 'Preserve any previous attempt'
    state = dict(status='registered_fixed27_not_dispatched', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'), dispatch_attempted=False)
    write(state_path, state)

    def command(args):
        check(reg)
        assert sha(root/'REGISTRATION.json') == state['registration_sha256']
        with (root/'diagnosis.log').open('a') as log:
            subprocess.run([sys.executable, str(DIAGNOSIS), *map(str, args)],
                           cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)

    try:
        state.update(status='prepare_fixed27', dispatch_attempted=False)
        write(state_path, state)
        command(['prepare', '--root', TARGET])
        state.update(status='running_fixed27', dispatch_attempted=True, dispatch_utc=now())
        write(state_path, state)
        command(['run', '--root', TARGET])
        state.update(status='independent_fixed27_review', dispatch_attempted=True)
        write(state_path, state)
        command(['review', '--root', TARGET, '--output', TARGET/'REVIEW.json'])
        report = read(TARGET/'REVIEW.json')
        assert report['status'] == 'verified_fixed27_development_diagnosis'
        state.update(status=('fixed27_verified_pending_failure_analysis'
                             if report['failed_ids'] else 'fixed27_verified_all_pass'),
                     review_sha256=sha(TARGET/'REVIEW.json'),
                     failed_ids=report['failed_ids'], ended_utc=now())
        write(state_path, state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry', error=repr(exc), ended_utc=now())
        write(state_path, state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, default=HANDOFF)
    args = parser.parse_args()
    (prepare if args.mode == 'prepare' else run)(args.root.resolve())
