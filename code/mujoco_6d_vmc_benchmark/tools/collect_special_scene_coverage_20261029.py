"""Execute a prospective coverage v3 collection of 30 identities, sequentially.

The caller supplies a real <=3GiB/swap-free systemd cgroup. The scene wrapper
owns the global simulator lock. Collection never launches student fitting or
changes a failed identity; failures block the later dataset builder.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_PARAMETERS = {
    'rod': {'VMC_ROD_EVENT_STAGE', 'VMC_ROD_EVENT_DELAY_S', 'VMC_ROD_HEIGHT_M',
            'VMC_ROD_TARGET_X_M', 'VMC_ROD_PUSH_FORCE_N', 'VMC_ROD_STROKE_M',
            'VMC_ROD_PRESS_S', 'VMC_ROD_HOLD_S', 'VMC_ROD_RETRACT_S', 'VMC_SCENE_DURATION_S'},
    'ball': {'VMC_BALL_SPEED_MPS', 'VMC_BALL_SHIFT_M', 'VMC_BALL_HEIGHT_OFFSET_M',
             'VMC_COVERAGE_INITIAL_X_M', 'VMC_COVERAGE_INITIAL_Y_M', 'VMC_COVERAGE_INITIAL_Z_M',
             'VMC_COVERAGE_CARRY_X_M', 'VMC_COVERAGE_CARRY_Y_M',
             'VMC_BALL_ANGLE_RAD', 'VMC_BALL_EVENT_STAGE'},
    'corner': {'PLACEMENT_SETTLE_GRIPPER_COMMAND', 'PLACE_APPROACH_DURATION_S',
               'INIT_JOINT_PERTURB_STD_RAD', 'LIFT_BOARD_Y_OFFSET_M', 'LIFT_BOARD_Z_OFFSET_M',
               'PLACE_X_OFFSET_M', 'PLACE_LOWER_M', 'PLACE_PITCH_DEG', 'PLACE_TOOL_ROLL_DEG',
               'UPRIGHT_PLACE', 'UPRIGHT_PLACE_X', 'UPRIGHT_PLACE_Z'},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


COVERAGE_PARAMETERS = {'VMC_COVERAGE_INITIAL_X_M', 'VMC_COVERAGE_INITIAL_Y_M',
    'VMC_COVERAGE_INITIAL_Z_M', 'VMC_COVERAGE_CARRY_X_M', 'VMC_COVERAGE_CARRY_Y_M',
    'VMC_BALL_ANGLE_RAD', 'VMC_BALL_EVENT_STAGE'}


def validate_override(entry):
    parameters = entry['scene_parameters']
    if set(parameters) - ALLOWED_PARAMETERS[entry['scene']]:
        raise ValueError('Unsupported experimental override: ' + entry['id'])
    if entry['scene'] == 'ball':
        if not COVERAGE_PARAMETERS <= set(parameters):
            raise ValueError('Every formal ball identity must explicitly register its coverage')
        if parameters['VMC_BALL_EVENT_STAGE'] != 'approach':
            raise ValueError('This coverage version only supports the reviewed approach event')
        # Reuse the exact bounds of the independently versioned physical adapter.
        import importlib.util
        spec = importlib.util.spec_from_file_location('formal_coverage_bounds',
            ROOT/'scripts/run_primitive_coverage_20261029.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.settings(parameters)


def require_complete_probe_review(plan):
    review_path = Path(plan['coverage_probe_review'])
    if not review_path.is_absolute():
        raise ValueError('Coverage review path must be absolute')
    review_path = review_path.resolve()
    if sha(review_path) != plan['coverage_probe_review_sha256']:
        raise ValueError('Coverage review changed after registration')
    review = read(review_path)
    root = review_path.parent
    registration = read(root/'REGISTRATION.json')
    state = read(root/'execution.json')
    if (review['status'] != 'complete_physical_coverage_review'
            or state['status'] != 'complete_pending_review'
            or registration['maximum_episodes'] != 8
            or len(registration['cases']) != 8
            or len(review['rows']) != len(state['episodes'])
            or len(review['rows']) != 8):
        raise ValueError('All eight physical development controls must be reviewed first')
    if (review['registration_sha256'] != sha(root/'REGISTRATION.json')
            or state['registration_sha256'] != review['registration_sha256']
            or review['execution_sha256'] != sha(root/'execution.json')):
        raise ValueError('Stale coverage review lineage')
    if ({r['id'] for r in review['rows']} != {r['id'] for r in registration['cases']}
            or len({r['id'] for r in review['rows']}) != 8):
        raise ValueError('Coverage review identities differ')
    if review['reviewer_sha256'] != sha(ROOT/'tools/review_ball_coverage_probe_20261029.py'):
        raise ValueError('Coverage reviewer changed')
    if datetime.fromisoformat(plan['registered_utc']) <= datetime.fromisoformat(review['created_utc']):
        raise ValueError('Formal plan must follow the actual complete coverage review')
    for row, receipt in zip(review['rows'], state['episodes']):
        qualification = root/row['id']/'ball/DEMONSTRATION_QUALIFICATION.json'
        if (row['id'] != receipt['id'] or sha(qualification) != row['qualification_sha256']
                or row['qualification_sha256'] != receipt['qualification_sha256']):
            raise ValueError('Coverage qualification changed')
    # Qualification failures remain visible; this does not silently promote
    # development controls to training/validation identities or labels.
    return review


def require_resources():
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    if (memory == 'max' or int(memory) > 3221225472
            or (cg/'memory.swap.max').read_text().strip() != '0'):
        raise ValueError('Actual MemoryMax<=3GiB and no swap required')
    cpu_max = (cg/'cpu.max').read_text().split() if (cg/'cpu.max').exists() else None
    quota_bounded = (cpu_max is not None and cpu_max[0] != 'max'
                     and 0 < int(cpu_max[0]) <= int(cpu_max[1]))
    affinity = sorted(os.sched_getaffinity(0))
    if not quota_bounded and len(affinity) != 1:
        raise ValueError('Actual CPU<=100% requires cgroup quota or inherited single-CPU affinity')
    if any(os.environ.get(k) != '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')):
        raise ValueError('Single numerical thread required')
    return dict(cgroup=str(cg), memory_max=int(memory), swap_max=0, cpu_max=cpu_max,
                affinity=affinity, cpu_bound='cgroup_quota' if quota_bounded else 'single_cpu_affinity')


def validate(plan_path):
    plan = read(plan_path)
    if plan.get('schema') != 'sii-three-real-scenes-collection-plan-v3':
        raise ValueError('Require prospective coverage v3 plan')
    require_complete_probe_review(plan)
    required_sources = {str(p.relative_to(ROOT)) for p in (ROOT/'scripts').glob('*.py')}
    required_sources.update('tools/' + name for name in (
        'collect_special_scene_coverage_20261029.py',
        'run_registered_special_coverage_20261029.py',
        'qualify_registered_special_coverage_20261029.py',
        'build_special_coverage_dataset_20261029.py',
        'audit_video_reference_vmc_20261028.py', 'audit_rod_yield_rejoin_v3_20261028.py',
        'optimize_tool_contact_20261002.py', 'intent_recovery_teacher_20261029.py',
        'intent_equilibrium_teacher_20261029.py'))
    if not required_sources <= set(plan.get('source_sha256', {})):
        raise ValueError('Formal collection requires its complete bound source set')
    for name, digest in plan.get('source_sha256', {}).items():
        if sha(ROOT/name) != digest:
            raise ValueError('Collection source changed after registration: '+name)
    entries = plan['episodes']
    if len(entries) != 30 or len({e['id'] for e in entries}) != 30:
        raise ValueError('Require 30 distinct identities')
    if Counter((e['scene'], e['split']) for e in entries) != Counter(
            {(s, p): n for s in ALLOWED_PARAMETERS for p, n in [('train', 8), ('validation', 2)]}):
        raise ValueError('Require 8 train + 2 validation in each scene')
    teacher = Path(plan['teacher_config']).resolve()
    if sha(teacher) != plan['teacher_file_sha256']:
        raise ValueError('Changed teacher configuration file')
    serialized = json.dumps(read(teacher), indent=2, allow_nan=False) + '\n'
    if hashlib.sha256(serialized.encode()).hexdigest() != plan['teacher_config_sha256']:
        raise ValueError('Teacher output serialization does not match plan')
    for scene in ALLOWED_PARAMETERS:
        conditions = [e['scene_parameters'] for e in entries if e['scene'] == scene]
        if len({json.dumps(v, sort_keys=True) for v in conditions}) != 10:
            raise ValueError(f'Duplicate physical conditions for {scene}')
    for e in entries:
        validate_override(e)
        f = Path(e['folder']).resolve()
        if f.parent.parent != plan_path.parent or f.parent.name != e['id'] or f.name != e['scene']:
            raise ValueError('Episode path must be plan-directory/id/scene')
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
    require_resources()
    plan_path = args.plan.resolve()
    plan = validate(plan_path)
    digest = sha(plan_path)
    lock = (plan_path.parent / '.collection.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = plan_path.parent / 'COLLECTION_PROGRESS.json'
    if state_path.exists():
        state = read(state_path)
        if state['plan_sha256'] != digest:
            raise ValueError('Plan changed after dispatch')
    else:
        state = dict(status='running', plan_sha256=digest, episodes=[],
                     started_utc=datetime.now(timezone.utc).isoformat())
    finished = {r['id'] for r in state['episodes']}
    for e in plan['episodes']:
        if e['id'] in finished:
            continue
        if (plan_path.parent / 'STOP_REQUESTED').exists():
            state['status'] = 'stopped_at_episode_boundary'
            write(state_path, state)
            return
        if sha(plan_path) != digest:
            raise ValueError('Plan changed during collection')
        validate(plan_path)
        output = Path(e['folder']).resolve().parent
        if output.exists():
            raise FileExistsError(f'Unreviewed partial identity, preserve and inspect: {output}')
        # Prevent unregistered experimental environment from leaking between
        # scene workers. Normal runtime paths/display selection are retained.
        env = {k: v for k, v in os.environ.items() if k in
               {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
        env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   PYTHONPATH=str(ROOT/'scripts') + ':' + str(ROOT/'tools'),
                   VMC_TEACHER_CONFIG=plan['teacher_config'], VMC_COLLECTION_PLAN=str(plan_path),
                   VMC_COLLECTION_ID=e['id'], VMC_SCENE_SEED=str(e['seed']))
        env.update({k: str(v) for k, v in e['scene_parameters'].items()})
        state.update(status='running', current=e['id'])
        write(state_path, state)
        command = [sys.executable, str(ROOT/'tools/run_registered_special_coverage_20261029.py'),
                   '--output', str(output), '--scenes', e['scene']]
        rc = subprocess.run(command, cwd=ROOT, env=env).returncode
        folder = Path(e['folder'])
        row = dict(id=e['id'], scene=e['scene'], returncode=rc, status='failed_preserved')
        if rc == 0:
            validate(plan_path)
            scripts = ['audit_video_reference_vmc_20261028.py']
            if e['scene'] == 'rod':
                scripts.append('audit_rod_yield_rejoin_v3_20261028.py')
            scripts.append('qualify_registered_special_coverage_20261029.py')
            for name in scripts:
                with (output/(name+'.log')).open('x') as log:
                    audit_rc = subprocess.run([sys.executable, str(ROOT/'tools'/name), str(folder)],
                                              cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
                if audit_rc:
                    row['audit_failure'] = name
                    break
            else:
                row['status'] = read(folder/'DEMONSTRATION_QUALIFICATION.json')['status']
        state['episodes'].append(row)
        write(state_path, state)
        if rc != 0 or row.get('audit_failure'):
            # Infrastructure failures require inspection, not blind dispatch.
            state['status'] = 'infrastructure_failure_preserved'
            write(state_path, state)
            raise SystemExit(1)
    state['status'] = ('qualified_complete' if all(r['status'] == 'qualified' for r in state['episodes'])
                       else 'finished_with_nonqualified_demonstrations')
    state['ended_utc'] = datetime.now(timezone.utc).isoformat()
    write(state_path, state)


if __name__ == '__main__':
    main()
