"""Prioritize same-scene diagnosis after an explicit, verified safe boundary.

Original results and unfinished office cells are preserved. No old receipt is
rewritten, no original run is declared complete, no frozen physical code changes.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now
from prepare_v9_paired_scene_closure_20261029 import (
    prepare, equivalent_physical_worker, TRAINING, COLLECTION, REGRESSION, WRAPPER, QUALIFIER)

ORIGINAL_UNIT = 'run-raa08b13eb33f4583ab899210958345fa.scope'
OLD_WAITER = 'sii-v9-paired-closure-handoff-v3-20261029.service'
EXPECTED_INVOCATION = '8beca05f1b344ec6985028452eed70d4'


def unit_state(unit):
    result = subprocess.run(['systemctl', '--user', 'show', unit, '-p', 'ActiveState',
                             '-p', 'InvocationID', '-p', 'MainPID'],
                            check=True, text=True, capture_output=True)
    return dict(line.split('=', 1) for line in result.stdout.splitlines())


def check_parent(parent, original_unit, old_waiter):
    assert parent['status'] == 'stopped_at_episode_boundary', 'Need explicit safe boundary, not timeout/failure'
    assert original_unit['ActiveState'] == 'inactive', 'Original scope still active'
    assert original_unit['InvocationID'] in ('', EXPECTED_INVOCATION), 'Original scope identity changed'
    assert old_waiter['ActiveState'] in ('failed', 'inactive'), 'Old waiter could still dispatch'
    rows, results = parent['rows'], parent['results']
    assert 0 < parent['completed'] == len(rows) == len(results) < 108
    assert all(r['returncode'] == 0 for r in rows), 'Incomplete worker at supposed boundary'
    names = lambda values: [(r['method'], r['condition']) for r in values]
    assert names(rows) == names(results) and len(set(names(rows))) == len(rows)
    return names(results)


def capture_boundary(root, reg):
    original = Path(reg['prerequisite'])
    parent = read(original)
    units = {name: unit_state(name) for name in (ORIGINAL_UNIT, OLD_WAITER)}
    completed = check_parent(parent, units[ORIGINAL_UNIT], units[OLD_WAITER])
    assert not (ROOT/'outputs/nonrl_v9_paired_scene_closure_20261029_v3/execution.json').exists()
    original_reg = read(REGRESSION/'REGISTRATION.json')
    expected = [(m, c) for c in original_reg['conditions'] for m in original_reg['methods']]
    assert completed == expected[:len(completed)], 'Original grid is not a complete ordered prefix'
    # Preserve exact bytes and hashes; do not turn a partial run into complete.
    destination = root/'PARENT_EXECUTION_AT_BOUNDARY.json'
    assert not destination.exists()
    content = original.read_bytes()
    destination.write_bytes(content)
    assert sha(destination) == sha(original)
    write(root/'BOUNDARY_HANDOFF.json', dict(status='verified_safe_boundary_priority_switch',
        created_utc=now(), original_execution=str(original), original_sha256=sha(original),
        original_registration_sha256=sha(REGRESSION/'REGISTRATION.json'),
        original_status=parent['status'], original_completed=len(completed), units=units,
        original_expected=108, unfinished_cells=[dict(method=m,condition=c) for m,c in expected[len(completed):]],
        old_waiter_handoff_sha256=sha(ROOT/'outputs/nonrl_v9_paired_scene_closure_20261029_v3/HANDOFF.json'),
        interpretation='Scheduling change only. Original incomplete transfer matrix and all failures remain. Complete remaining disjoint cells later; do not use it for parameter selection.'))


def verify_boundary(root, reg):
    receipt = read(root/'BOUNDARY_HANDOFF.json')
    original = Path(reg['prerequisite'])
    assert receipt['status'] == 'verified_safe_boundary_priority_switch'
    assert sha(original) == sha(root/'PARENT_EXECUTION_AT_BOUNDARY.json') == receipt['original_sha256']
    assert sha(REGRESSION/'REGISTRATION.json') == receipt['original_registration_sha256']
    parent = read(original)
    check_parent(parent, unit_state(ORIGINAL_UNIT), unit_state(OLD_WAITER))
    assert not (ROOT/'outputs/nonrl_v9_paired_scene_closure_20261029_v3/execution.json').exists()


def run(root):
    reg = read(root/'REGISTRATION.json')
    verify_boundary(root, reg)
    assert not (root/'execution.json').exists(), 'No duplicate or automatic retry'
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    assert (cg/'memory.max').read_text().strip() != 'max'
    assert int((cg/'memory.max').read_text()) <= 3221225472
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    assert sha(TRAINING/'MODEL_LOCK.json') == reg['model_lock_sha256']
    assert sha(COLLECTION/'COLLECTION_PLAN.json') == reg['collection_plan_sha256']
    assert equivalent_physical_worker() == reg['physical_worker_equivalence']
    assert reg['wrapper'] == WRAPPER and reg['qualifier'] == QUALIFIER
    state = dict(status='running', started_utc=now(), registration_sha256=sha(root/'REGISTRATION.json'), rows=[])
    write(root/'execution.json', state)
    try:
        for case in reg['cases']:
            model = case['model']
            baseline = Path(case['teacher_reference'])
            assert sha(baseline/'execution.json') == case['teacher_execution_sha256']
            assert sha(baseline/'DEMONSTRATION_QUALIFICATION.json') == case['qualification_sha256']
            assert sha(Path(case['config'])) == case['config_sha256']
            assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
            output = root/case['id']
            env = {k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
            env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
                VMC_TEACHER_CONFIG=case['config'], VMC_SCENE_SEED=str(case['seed']),
                VMC_STUDENT_CHECKPOINT=model['checkpoint'])
            env.update({k:str(v) for k,v in case['parameters'].items()})
            row = dict(id=case['id'], started_utc=now())
            state['rows'].append(row)
            write(root/'execution.json', state)
            with (root/(case['id']+'.log')).open('x') as log:
                rc = subprocess.run([sys.executable, str(ROOT/'tools'/reg['wrapper']),
                    '--output', str(output), '--scenes', case['scene']], cwd=ROOT, env=env,
                    stdout=log, stderr=subprocess.STDOUT).returncode
            row.update(returncode=rc, ended_utc=now())
            write(root/'execution.json', state)
            assert rc == 0, 'Infrastructure failure preserved; no automatic retry'
            folder = output/case['scene']
            assert read(folder/'execution.json')['model_sha256'] == case['physics_model_sha256']
            audits = ['audit_video_reference_vmc_20261028.py']
            if case['scene'] == 'rod':
                audits.append('audit_rod_yield_rejoin_v3_20261028.py')
            audits.append(reg['qualifier'])
            for audit in audits:
                with (output/(audit+'.log')).open('x') as log:
                    subprocess.run([sys.executable, str(ROOT/'tools'/audit), str(folder)], cwd=ROOT,
                        env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            row['qualification'] = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            row['qualification_sha256'] = sha(folder/'DEMONSTRATION_QUALIFICATION.json')
            write(root/'execution.json', state)
        state.update(status='complete_pending_review', ended_utc=now())
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'execution.json', state)

def register(root):
    prepare(root)
    reg = read(root/'REGISTRATION.json')
    reg.pop('prerequisite_completed')
    reg.update(schema='sii-v9-paired-scene-priority-boundary-v1',
        prerequisite_terminal_status='stopped_at_episode_boundary',
        scheduling_amendment_utc=now(), runner_sha256=sha(Path(__file__)),
        supersedes_waiter_only=OLD_WAITER,
        reason='User asks to repair teacher/learning/scenario now; old combined transfer test does not diagnose same-scene imitation. Preserve full safe episodes and incomplete cells, execute the unchanged 18-case development diagnosis first, finish disjoint original cells later.')
    write(root/'REGISTRATION.json', reg)


def wait_and_run(root):
    reg = read(root/'REGISTRATION.json')
    digest = sha(root/'REGISTRATION.json')
    assert not (root/'HANDOFF.json').exists()
    state = dict(status='waiting_for_requested_safe_boundary', started_utc=now(),
                 registration_sha256=digest, maximum_wait_s=10800)
    write(root/'HANDOFF.json', state)
    deadline = time.monotonic()+10800
    try:
        while time.monotonic() < deadline:
            assert sha(root/'REGISTRATION.json') == digest
            parent = read(Path(reg['prerequisite']))
            if parent['status'] in ('failed_preserved', 'complete'):
                raise RuntimeError('Unexpected parent terminal status; preserve and review')
            if (parent['status'] == 'stopped_at_episode_boundary'
                    and unit_state(ORIGINAL_UNIT)['ActiveState'] == 'inactive'
                    and unit_state(OLD_WAITER)['ActiveState'] in ('failed', 'inactive')):
                break
            time.sleep(15)
        else:
            raise TimeoutError('Priority boundary wait expired; no dispatch')
        capture_boundary(root, reg)
        state.update(status='running_registered_development_closure', dispatched_utc=now())
        write(root/'HANDOFF.json', state)
        with (ROOT/'outputs/.local-rl-compute.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
            run(root)
        state.update(status='complete_pending_review', ended_utc=now())
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'HANDOFF.json', state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--wait-and-run', action='store_true')
    args = parser.parse_args()
    (wait_and_run if args.wait_and_run else register)(args.root.resolve())
