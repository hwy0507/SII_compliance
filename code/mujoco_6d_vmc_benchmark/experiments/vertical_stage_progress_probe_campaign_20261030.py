"""Register and run a one-worker, three-identity teacher repair probe."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import check_resources

PARENT = ROOT / 'outputs/special_scene_vertical_aware_collection_20261030_v2'
UNIT = 'sii-vertical-stage-progress-probe-20261030.service'
CASES = ('rod_09', 'rod_04', 'rod_01')
PYTHON = Path('/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python')


def prepare(root):
    assert not root.exists()
    old_cgroup = Path('/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/sii-vertical-aware-special-scene-collection-20261030.service')
    assert not old_cgroup.exists(), 'Previous collection cgroup is still present'
    parent_state = read(PARENT / 'execution.json')
    parent_reg = read(PARENT / 'REGISTRATION.json')
    assert parent_state['status'] == 'complete_with_scientific_failures_preserved_no_dataset'
    assert len(parent_state['rows']) == 30 and sum(x['qualified'] for x in parent_state['rows']) == 29
    assert [x['id'] for x in parent_state['rows'] if not x['qualified']] == ['rod_09']
    cases = []
    for identity in CASES:
        case = next(x for x in parent_reg['cases'] if x['id'] == identity)
        row = next(x for x in parent_state['rows'] if x['id'] == identity)
        ref = Path(row['folder'])
        cases.append(dict(id=identity, scene='rod', split=case['split'], seed=case['seed'],
            parameters=case['parameters'], reference=str(ref),
            reference_execution_sha256=sha(ref / 'execution.json'),
            reference_qualification_sha256=sha(ref / 'DEMONSTRATION_QUALIFICATION.json'),
            reference_behavior_sha256=sha(ref / 'ROD_YIELD_REJOIN_AUDIT_V3.json'),
            expected_previous_qualification=row['qualified']))
    teacher = read(PARENT / 'teacher.json')
    teacher['path_progress_recovery'] = dict(version='bounded_vertical_stage_progress_v1', gain=1.0,
        maximum_speed_mps=.02, opposition_threshold_n=.5, deficit_scale_mps=.02)
    root.mkdir(parents=True)
    write(root / 'teacher.json', teacher)
    sources = {str(p.relative_to(ROOT)): sha(p) for folder in ('scripts', 'tools')
               for p in sorted((ROOT / folder).glob('*.py'))}
    sources[str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    write(root / 'REGISTRATION.json', dict(schema='sii-vertical-stage-progress-probe-v1',
        registered_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        parent_directory=str(PARENT), parent_unit='sii-vertical-aware-special-scene-collection-20261030.service',
        parent_registration_sha256=sha(PARENT / 'REGISTRATION.json'),
        parent_execution_sha256=sha(PARENT / 'execution.json'), cases=cases,
        teacher_config_sha256=sha(root / 'teacher.json'), source_sha256=sources,
        resources=dict(cpu=6, simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        fixed=['MJB/physics', 'canonical48 actor input', 'public action filter', 'actuator limits', 'dt=5e-5', 'task/safety/rod gates'],
        stop_rule='Run each identity once; preserve every failure; no parameter sweep, retry, fitting or unseen test.'))


def run(root):
    check_resources()
    reg = read(root / 'REGISTRATION.json')
    assert sha(PARENT / 'execution.json') == reg['parent_execution_sha256']
    assert sha(PARENT / 'REGISTRATION.json') == reg['parent_registration_sha256']
    assert sha(root / 'teacher.json') == reg['teacher_config_sha256']
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    assert all(sha(Path(c['reference']) / 'execution.json') == c['reference_execution_sha256'] for c in reg['cases'])
    lock = (ROOT / 'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out = root / 'runs'
    out.mkdir()
    state = dict(status='running_registered_teacher_probes', registration_sha256=sha(root / 'REGISTRATION.json'), rows=[])
    write(root / 'execution.json', state)
    try:
        for case in reg['cases']:
            assert sha(root / 'REGISTRATION.json') == state['registration_sha256']
            for name, digest in reg['source_sha256'].items():
                assert sha(ROOT / name) == digest, name
            assert sha(root / 'teacher.json') == reg['teacher_config_sha256']
            run_root = out / case['id']
            env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
            env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                PYTHONPATH=str(ROOT / 'scripts') + ':' + str(ROOT / 'tools'),
                MUJOCO_MENAGERIE_PATH=str(ROOT / 'outputs/baseline_local_rl_20261009/runtime/menagerie'),
                VMC_TEACHER_CONFIG=str(root / 'teacher.json'),
                VMC_SCENE_SEED=str(case['seed']),
                VMC_STUDENT_CHECKPOINT=str(read(PARENT / 'REGISTRATION.json')['candidate']['checkpoint']))
            env.update({k: str(v) for k, v in case['parameters'].items()})
            log = (root / (case['id'] + '.log')).open('x')
            state['current'] = case['id']; write(root / 'execution.json', state)
            try:
                subprocess.run([str(PYTHON), str(ROOT / 'tools/run_vertical_stage_progress_probe_20261030.py'),
                    '--output', str(run_root), '--scene', 'rod', '--student-steps', '0'],
                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
                folder = run_root / 'rod'
                subprocess.run([str(PYTHON), str(ROOT / 'tools/audit_vertical_stage_progress_probe_20261030.py'), str(folder)],
                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
                review = read(folder / 'HANDOFF_REVIEW.json')
                row = dict(id=case['id'], folder=str(folder), qualified=review['qualified'],
                    review_sha256=sha(folder / 'HANDOFF_REVIEW.json'),
                    qualification_sha256=sha(folder / 'DEMONSTRATION_QUALIFICATION.json'),
                    behavior_sha256=sha(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json'))
                state['rows'].append(row); write(root / 'execution.json', state)
            finally:
                log.close()
        state.update(status='three_probes_qualified_pending_collection_review' if all(x['qualified'] for x in state['rows'])
                     else 'complete_with_failures_preserved_no_collection', ended_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
        write(root / 'execution.json', state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry', error=repr(exc))
        write(root / 'execution.json', state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prepare', action='store_true')
    args = parser.parse_args(); root = args.root.resolve()
    prepare(root) if args.prepare else run(root)
