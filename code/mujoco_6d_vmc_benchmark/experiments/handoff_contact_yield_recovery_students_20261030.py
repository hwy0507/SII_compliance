"""Wait for the v3 fit audit, then run the fixed train-only 27-cell review."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties

FIT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
FIT_HANDOFF = ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v3'
FIT_UNIT = 'sii-contact-yield-recovery-fit-v3-20261030.service'
TARGET = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v1'
DIAGNOSIS = ROOT/'experiments/diagnose_contact_yield_recovery_students_20261030.py'
BASE_DIAGNOSIS = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'


def source_manifest():
    paths = [Path(__file__), DIAGNOSIS, BASE_DIAGNOSIS]
    paths += [p for folder in ('scripts', 'tools') for p in (ROOT/folder).glob('*.py')]
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))}


def fit_result():
    handoff = read(FIT_HANDOFF/'execution.json')
    fit = read(FIT/'execution.json')
    active = properties(FIT_UNIT)
    if active['ActiveState'] in ('active', 'activating', 'deactivating', 'reloading'):
        return 'wait'
    if handoff['status'] == 'complete_nine_refits_pending_fixed_development_review' and fit['status'] == 'complete':
        assert active['MainPID'] == '0'
        audit = read(FIT/'FIT_AUDIT.json')
        assert audit['status'] == 'passed' and len(audit['candidate_jobs']) == 75
        assert len(audit['frozen_actor_replays']) == 9
        return 'ready'
    if handoff['status'] == 'failed_preserved_no_retry' or fit['status'] != 'training':
        return 'parent_failed_preserved_no_dispatch'
    return 'wait'


def prepare(root):
    assert not root.exists() and not TARGET.exists()
    assert read(FIT/'execution.json')['status'] == 'training'
    root.mkdir()
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-recovery-fixed27-handoff-v1',
        registered_utc=now(), fit=str(FIT), fit_handoff=str(FIT_HANDOFF),
        fit_unit=FIT_UNIT, target=str(TARGET), diagnosis=str(DIAGNOSIS),
        source_sha256=source_manifest(), maximum_wait_seconds=86400,
        no_final_test=True, no_reselection=True, no_retry=True,
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0)))


def run(root):
    check_resources()
    reg = read(root/'REGISTRATION.json')
    assert not (root/'execution.json').exists()
    state = dict(status='waiting_for_audited_recovery_fits', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'), dispatch_attempted=False)
    write(root/'execution.json', state)

    def check():
        assert sha(root/'REGISTRATION.json') == state['registration_sha256']
        assert reg['source_sha256'] == source_manifest()
        assert reg['fit'] == str(FIT) and reg['fit_handoff'] == str(FIT_HANDOFF)

    deadline = time.monotonic() + reg['maximum_wait_seconds']
    try:
        while True:
            check()
            choice = fit_result()
            if (root/'STOP_REQUESTED').exists():
                choice = 'stopped_before_dispatch'
            if choice != 'wait':
                break
            if time.monotonic() > deadline:
                choice = 'finite_wait_timeout_no_dispatch'
                break
            time.sleep(20)
        if choice != 'ready':
            state.update(status=choice, ended_utc=now())
            write(root/'execution.json', state)
            return
        assert not TARGET.exists()
        with (root/'diagnosis.log').open('x') as log:
            for mode in ('prepare', 'run', 'review'):
                check()
                state.update(status='diagnosis_'+mode, dispatch_attempted=mode != 'prepare')
                write(root/'execution.json', state)
                command = [sys.executable, str(DIAGNOSIS), mode, '--root', str(TARGET)]
                if mode == 'review':
                    command += ['--output', str(TARGET/'REVIEW.json')]
                subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        report = read(TARGET/'REVIEW.json')
        assert report['status'] == 'verified_fixed27_development_diagnosis'
        state.update(
            status=('fixed27_verified_pending_new_final_registration' if not report['failed_ids']
                    else 'fixed27_scientific_failures_preserved_require_repair'),
            review_sha256=sha(TARGET/'REVIEW.json'), failed_ids=report['failed_ids'],
            ended_utc=now())
        write(root/'execution.json', state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry', error=repr(exc), ended_utc=now())
        write(root/'execution.json', state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args()
    prepare(args.root.resolve()) if args.prepare else run(args.root.resolve())
