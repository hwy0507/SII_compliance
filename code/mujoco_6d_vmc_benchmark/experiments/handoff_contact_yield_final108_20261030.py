"""Finite sequential final108 handoff; no fitting, fallback or test tuning."""
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

PARENT = ROOT/'outputs/contact_yield_student_diagnosis_handoff_20261030_v1'
TARGET = ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1'
UNIT = 'sii-contact-yield-student-diagnosis-handoff-20261030.service'
ADAPTER = ROOT/'experiments/evaluate_contact_yield_unseen108_20261030.py'


def decision(state, active):
    if active in ('active', 'activating', 'deactivating', 'reloading'):
        return 'wait'
    if active == 'inactive' and state['status'] == 'fixed27_verified_pending_final_registration':
        return 'ready'
    return 'development_not_qualified_no_final_dispatch'


def prepare(root):
    assert root.parent == ROOT/'outputs' and not root.exists() and not TARGET.exists()
    assert read(PARENT/'execution.json')['status'] == 'waiting_for_audited_fits'
    parent = read(PARENT/'REGISTRATION.json')
    assert parent['schema'] == 'sii-contact-yield-fixed27-handoff-v1'
    sources = dict(parent['source_sha256'])
    for path in (Path(__file__), ADAPTER):
        sources[str(path.relative_to(ROOT))] = sha(path)
    for name, digest in sources.items():
        assert sha(ROOT/name) == digest, name
    root.mkdir()
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-final108-handoff-v1', registered_utc=now(),
        parent=str(PARENT), parent_unit=UNIT, target=str(TARGET),
        parent_registration_sha256=sha(PARENT/'REGISTRATION.json'),
        source_sha256=sources, maximum_wait_seconds=86400,
        no_retry=True, no_reselection=True, preserve_all_failures=True,
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0)))


def run(root):
    check_resources()
    reg = read(root/'REGISTRATION.json')
    assert not (root/'execution.json').exists()
    state = dict(status='waiting_for_fixed27_review', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'),
                 dispatch_attempted=False)
    write(root/'execution.json', state)

    def check():
        assert sha(root/'REGISTRATION.json') == state['registration_sha256']
        assert sha(PARENT/'REGISTRATION.json') == reg['parent_registration_sha256']
        assert reg['parent'] == str(PARENT) and reg['parent_unit'] == UNIT
        assert reg['target'] == str(TARGET)
        for name, digest in reg['source_sha256'].items():
            assert sha(ROOT/name) == digest, name

    deadline = time.monotonic()+reg['maximum_wait_seconds']
    try:
        while True:
            check()
            choice = decision(read(PARENT/'execution.json'), properties(UNIT)['ActiveState'])
            if (root/'STOP_REQUESTED').exists():
                choice = 'stopped_before_final_dispatch'
            if choice != 'wait':
                break
            if time.monotonic() > deadline:
                choice = 'finite_wait_timeout_no_final_dispatch'
                break
            time.sleep(20)
        if choice != 'ready':
            state.update(status=choice, ended_utc=now())
            write(root/'execution.json', state)
            return
        assert not TARGET.exists()
        # The adapter independently revalidates all fits and all27 replays
        # before it opens the frozen final condition file.
        with (root/'final108.log').open('x') as log:
            for mode in ('register', 'run', 'review'):
                check()
                state.update(status='final108_'+mode, dispatch_attempted=True)
                write(root/'execution.json', state)
                args = [sys.executable, str(ADAPTER), mode, '--root', str(TARGET)]
                if mode == 'review':
                    args.extend(['--output', str(TARGET/'FINAL_REVIEW.json')])
                subprocess.run(args, cwd=ROOT, stdout=log,
                               stderr=subprocess.STDOUT, check=True)
        report = read(TARGET/'FINAL_REVIEW.json')
        assert report['status'] == 'verified_complete_isolated_unseen_matrix'
        assert len(report['rows']) == len(report['independent_replays']) == 108
        state.update(status='final108_verified_pending_delivery',
                     review_sha256=sha(TARGET/'FINAL_REVIEW.json'), ended_utc=now())
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
