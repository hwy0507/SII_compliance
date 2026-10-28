"""Finite teacher/student/scene controls after the mixed-scale failure.

No fitting, no changed test gate, no replacement of old receipts. Office
controls are diagnosis on an already inspected test condition, not held-out
selection evidence. All new demonstrations remain in the three real scenes.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from collect_special_scene_actions_20261028 import read, sha, write

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT/'outputs/special_scene_vmc_collection_20261028_v5'
TRAINING = ROOT/'outputs/special_scene_retrain_readout05_20261028_v1'
OLD_TEST = ROOT/'outputs/special_scene_frozen108_readout05_20261028_v1'
RUNTIME = ROOT/'outputs/baseline_local_rl_20261009/runtime'


def now():
    return datetime.now(timezone.utc).isoformat()


def prepare(root):
    if root.exists():
        raise FileExistsError(root)
    old = read(OLD_TEST/'execution.json')
    assert old['status'] == 'stopped_at_episode_boundary'
    assert old['completed'] == len(old['results']) == len(old['rows'])
    plan = read(COLLECTION/'COLLECTION_PLAN.json')
    models = read(TRAINING/'MODEL_LOCK.json')['models']
    teacher = read(Path(plan['teacher_config']))
    historical = read(ROOT/'outputs/teacher_student_15h_20261012_v3/TEACHER_CHOICE.json')['selected']['config']
    root.mkdir(parents=True)
    write(root/'teacher_new.json', teacher)
    write(root/'teacher_historical.json', historical)
    # This exact condition was already evaluated in the stopped matrix.
    row = next(r for r in old['rows'] if r['condition'].endswith('_000'))
    office_command = row['command'][:]
    k = office_command.index('--checkpoint')
    del office_command[k:k+2]
    cases = [dict(id='office_teacher_new', kind='office', config=str(root/'teacher_new.json'), command=office_command),
             dict(id='office_teacher_historical', kind='office', config=str(root/'teacher_historical.json'), command=office_command)]
    for scene in ('corner', 'rod', 'ball'):
        entry = next(e for e in plan['episodes'] if e['id'] == scene+'_00')
        assert entry['split'] == 'train'
        for actor in ('teacher', 'esn_ridge'):
            model = next((m for m in models if m['family'] == actor and m['seed'] == 2026102801), None)
            base = Path(entry['folder'])
            cases.append(dict(id=scene+'_'+actor, kind='scene', scene=scene, identity=entry['id'],
                seed=entry['seed'], scene_parameters=entry['scene_parameters'],
                expected_model_sha256=read(base/'execution.json')['model_sha256'],
                baseline=str(base), baseline_execution_sha256=sha(base/'execution.json'),
                config=str(root/'teacher_new.json'), model=model))
    rod = next(c for c in cases if c['id'] == 'rod_esn_ridge')
    for family in ('rnn_scratch', 'mlp_scratch'):
        model = next(m for m in models if m['family'] == family and m['seed'] == 2026102801)
        cases.append(dict(rod, id='rod_'+family, model=model))
    names = ('run_video_reference_vmc_20261028.py', 'audit_video_reference_vmc_20261028.py',
             'qualify_special_scene_demo_20261028.py', 'audit_rod_yield_rejoin_v3_20261028.py',
             'optimize_tool_contact_20261002.py', 'collect_special_scene_actions_20261028.py',
             Path(__file__).name)
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (ROOT/'scripts').glob('*.py')}
    sources.update({str(Path('tools')/n): sha(ROOT/'tools'/n) for n in names})
    registration = dict(schema='sii-special-regression-controls-v1', registered_utc=now(),
        old_test=str(OLD_TEST), old_execution_sha256=sha(OLD_TEST/'execution.json'), old_completed=old['completed'],
        model_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'), collection_plan_sha256=sha(COLLECTION/'COLLECTION_PLAN.json'),
        config_sha256={str(p): sha(p) for p in (root/'teacher_new.json', root/'teacher_historical.json')},
        maximum_episodes=len(cases), cases=cases, source_sha256=sources,
        resources=dict(simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        action_contract=dict(linear_yield_mps=.32, angular_yield_radps=.6, actor_dt_s=.04),
        interpretation='Teacher old/new on the same already-inspected office condition; teacher/student on identical real-scene training identities. No fit, no test-based model selection, no causality claim from one control.',
        next_step='Review every result including failures before new collection or retraining; final fair comparison remains required.')
    write(root/'REGISTRATION.json', registration)
    print(json.dumps(dict(root=str(root), episodes=len(cases), registration_sha256=sha(root/'REGISTRATION.json'))))


def run(root, training=TRAINING):
    reg = read(root/'REGISTRATION.json')
    lock = (root/'.probe.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (root/'execution.json').exists():
        raise FileExistsError('No duplicate or automatic replay')
    assert sha(OLD_TEST/'execution.json') == reg['old_execution_sha256']
    assert read(OLD_TEST/'execution.json')['status'] == 'stopped_at_episode_boundary'
    assert subprocess.run(['systemctl', '--user', 'is-active', '--quiet',
        'sii-special-frozen108-handoff-v1-20261028.service']).returncode != 0
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    assert (cg/'memory.max').read_text().strip() != 'max'
    assert int((cg/'memory.max').read_text()) <= 3221225472 and int((cg/'memory.swap.max').read_text()) == 0
    state = dict(status='running', started_utc=now(), registration_sha256=sha(root/'REGISTRATION.json'), episodes=[])
    write(root/'execution.json', state)
    try:
        for case in reg['cases']:
            for name, digest in reg['source_sha256'].items():
                assert sha(ROOT/name) == digest, name
            for name, digest in reg['config_sha256'].items():
                assert sha(Path(name)) == digest, name
            assert sha(training/'MODEL_LOCK.json') == reg['model_lock_sha256']
            env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
            env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                       MUJOCO_MENAGERIE_PATH=str(RUNTIME/'menagerie'),
                       SII_MEMORY_LIMIT_MODE='cgroup', SII_MEMORY_MAX_BYTES='3221225472',
                       SII_SWAP_MAX_BYTES='0')
            output = root/case['id']
            state.update(current=case['id'], updated_utc=now())
            write(root/'execution.json', state)
            global_lock = None
            if case['kind'] == 'office':
                global_lock = (ROOT/'outputs/.local-rl-compute.lock').open('a')
                fcntl.flock(global_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                command = case['command'][:]
                command[command.index('--config')+1] = case['config']
                command[command.index('--output')+1] = str(output)
                source = OLD_TEST/'source'
                env['PYTHONPATH'] = str(source/'scripts')+':'+str(source/'tools')
            else:
                env.update(PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
                           VMC_TEACHER_CONFIG=case['config'], VMC_SCENE_SEED=str(case['seed']))
                env.update({k: str(v) for k, v in case['scene_parameters'].items()})
                if case['model']:
                    model = case['model']
                    assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
                    env['VMC_STUDENT_CHECKPOINT'] = model['checkpoint']
                command = [sys.executable, str(ROOT/'tools/run_video_reference_vmc_20261028.py'),
                           '--output', str(output), '--scenes', case['scene']]
            try:
                with (root/(case['id']+'.log')).open('x') as log:
                    result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            finally:
                if global_lock:
                    global_lock.close()
            receipt = dict(id=case['id'], returncode=result.returncode)
            state['episodes'].append(receipt)
            write(root/'execution.json', state)
            if result.returncode:
                raise RuntimeError('Worker infrastructure failure: '+case['id'])
            if case['kind'] == 'office':
                receipt['audit'] = read(output/'AUDIT.json')
                receipt['audit_sha256'] = sha(output/'AUDIT.json')
            else:
                folder = output/case['scene']
                execution = read(folder/'execution.json')
                assert execution['model_sha256'] == case['expected_model_sha256'], 'Geometry changed'
                assert execution['filter_config']['maximum_linear_yield_mps'] == .32
                audits = ['audit_video_reference_vmc_20261028.py']
                if case['scene'] == 'rod':
                    audits.append('audit_rod_yield_rejoin_v3_20261028.py')
                audits.append('qualify_special_scene_demo_20261028.py')
                for name in audits:
                    with (output/(name+'.log')).open('x') as log:
                        subprocess.run([sys.executable, str(ROOT/'tools'/name), str(folder)],
                                       cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
                receipt['qualification'] = read(folder/'DEMONSTRATION_QUALIFICATION.json')
                receipt['qualification_sha256'] = sha(folder/'DEMONSTRATION_QUALIFICATION.json')
            write(root/'execution.json', state)
        state.update(status='complete_pending_review', ended_utc=now())
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'execution.json', state)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    (run if a.run else prepare)(a.root.resolve())
