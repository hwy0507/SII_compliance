"""Execute a prospectively saved 30-identity collection, sequentially.

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
    'ball': {'VMC_BALL_SPEED_MPS', 'VMC_BALL_SHIFT_M', 'VMC_BALL_HEIGHT_OFFSET_M'},
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


def validate(plan_path):
    plan = read(plan_path)
    if plan.get('schema') != 'sii-three-real-scenes-collection-plan-v2':
        raise ValueError('Require prospective v2 plan')
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
        if set(e['scene_parameters']) - ALLOWED_PARAMETERS[e['scene']]:
            raise ValueError(f'Unsupported experimental override: {e["id"]}')
        f = Path(e['folder']).resolve()
        if f.parent.parent != plan_path.parent or f.parent.name != e['id'] or f.name != e['scene']:
            raise ValueError('Episode path must be plan-directory/id/scene')
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
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
        command = [sys.executable, str(ROOT/'tools/run_video_reference_vmc_20261028.py'),
                   '--output', str(output), '--scenes', e['scene']]
        rc = subprocess.run(command, cwd=ROOT, env=env).returncode
        folder = Path(e['folder'])
        row = dict(id=e['id'], scene=e['scene'], returncode=rc, status='failed_preserved')
        if rc == 0:
            validate(plan_path)
            scripts = ['audit_video_reference_vmc_20261028.py']
            if e['scene'] == 'rod':
                scripts.append('audit_rod_yield_rejoin_v3_20261028.py')
            scripts.append('qualify_special_scene_demo_20261028.py')
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
