"""Register/run 18 development closures, only after the existing 108 ends.

Uses fixed models on existing train00/validation08 identities. These are NOT
unseen tests and cannot supply a final ranking or test-based model selection.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now

COLLECTION = ROOT/'outputs/special_scene_direction_collection_20261029_v9'
TRAINING = ROOT/'outputs/special_scene_direction_retrain_20261029_v9'
REGRESSION = ROOT/'outputs/special_scene_frozen108_20261029_v9'


def prepare(root):
    assert not root.exists()
    plan = read(COLLECTION/'COLLECTION_PLAN.json')
    lock = read(TRAINING/'MODEL_LOCK.json')
    assert lock['training_data_sha256'] == '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407'
    cases = []
    for scene in ('rod', 'ball', 'corner'):
        for identity in (scene+'_00', scene+'_08'):
            entry = next(e for e in plan['episodes'] if e['id'] == identity)
            folder = Path(entry['folder'])
            assert read(folder/'DEMONSTRATION_QUALIFICATION.json')['status'] == 'qualified'
            for family in ('esn_ridge', 'rnn_scratch', 'mlp_scratch'):
                model = next(m for m in lock['models'] if m['family'] == family and m['seed'] == 2026102801)
                assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
                cases.append(dict(id=identity+'_'+family, scene=scene, identity=identity,
                    split=entry['split'], seed=entry['seed'], parameters=entry['scene_parameters'],
                    teacher_reference=str(folder), teacher_execution_sha256=sha(folder/'execution.json'),
                    qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
                    physics_model_sha256=read(folder/'execution.json')['model_sha256'],
                    config=str(folder/'teacher.json'), config_sha256=sha(folder/'teacher.json'), model=model))
    sources = list((ROOT/'scripts').glob('*.py'))+list((ROOT/'tools').glob('*.py'))
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(schema='sii-v9-paired-scene-development-closure-v1',
        registered_utc=now(), status='registered_not_executed', cases=cases, maximum_episodes=18,
        prerequisite=str(REGRESSION/'execution.json'), prerequisite_completed=108,
        model_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),
        collection_plan_sha256=sha(COLLECTION/'COLLECTION_PLAN.json'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
        resources=dict(cpu=6, simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        interpretation='Development diagnosis on train00 and already-selected validation08, not unseen final testing. Paired teacher is the existing audited identical-identity rollout. No fitting or selection in this runner.',
        decision='Review all 18 including failures. If same-scene students fail, diagnose coverage/readout using train/validation only before new fit. If they reproduce teacher, register separate unseen isolated test plus preserve office transfer stress result. No gate relaxation or success promise.'))
    print(root)


def run(root):
    reg = read(root/'REGISTRATION.json')
    parent = read(Path(reg['prerequisite']))
    assert parent['status'] == 'complete' and parent['completed'] == 108
    assert len(parent['results']) == 108 and all('returncode' in r for r in parent['rows'])
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
                rc = subprocess.run([sys.executable, str(ROOT/'tools/run_video_reference_vmc_20261028.py'),
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
            audits.append('qualify_special_scene_demo_20261028.py')
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


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    (run if a.run else prepare)(a.root.resolve())
