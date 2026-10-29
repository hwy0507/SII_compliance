"""Four fixed train-identity recovery probes after complete student diagnosis.

Not final evaluation or a model-selection step. No unseen conditions are read.
Only independently qualified executed teacher suffixes are data candidates.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, write, sha
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties
PARENT = ROOT/'outputs/contact_yield_student_development_20261030_v1'
FINAL = ROOT/'outputs/contact_yield_final108_handoff_20261030_v1'
WORKER = ROOT/'experiments/run_contact_yield_recovery_probe_20261030.py'
AUDITOR = ROOT/'experiments/audit_contact_yield_recovery_probe_20261030.py'
UNITS = ('sii-contact-yield-student-diagnosis-handoff-20261030.service',
         'sii-contact-yield-final108-handoff-20261030.service')
PLAN = (('rod_mlp01_7s','rod','mlp_scratch',175),
        ('ball_rnn01_10s','ball','rnn_scratch',250),
        ('ball_mlp01_10s','ball','mlp_scratch',250),
        ('ball_rnn01_20s','ball','rnn_scratch',500))


def prerequisites():
    assert all(properties(u)['ActiveState']=='inactive' and properties(u)['MainPID']=='0' for u in UNITS)
    state=read(PARENT/'execution.json'); report=read(PARENT/'REVIEW.json')
    assert state['status']=='complete_development_diagnosis_pending_review' and len(state['rows'])==27
    assert report['status']=='verified_fixed27_development_diagnosis'
    assert report['execution_sha256']==sha(PARENT/'execution.json') and report['registration_sha256']==sha(PARENT/'REGISTRATION.json')
    assert report['failed_ids'] and report['no_model_reselection'] and report['no_final_test_performed']
    final=read(FINAL/'execution.json')
    assert final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    return read(PARENT/'REGISTRATION.json')


def prepare(root):
    assert not root.exists(); reg=prerequisites(); cases=[]
    for identity,scene,family,prefix in PLAN:
        case=next(c for c in reg['cases'] if c['condition']['scene']==scene and c['model']['family']==family and c['model']['seed']==2026102801)
        cases.append(dict(id=identity,scene=scene,student_steps=prefix,model=case['model'],condition=case['condition'],teacher_reference=case['teacher_reference']))
    sources={str(p.relative_to(ROOT)):sha(p) for directory in ('tools','scripts') for p in (ROOT/directory).glob('*.py')}
    for p in (WORKER,AUDITOR,Path(__file__).resolve()): sources[str(p.relative_to(ROOT))]=sha(p)
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json',dict(schema='contact-yield-recovery-development-v1',registered_utc=now(),cases=cases,maximum_episodes=4,source_sha256=sources,
        parent_files={n:sha(PARENT/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')},final_execution_sha256=sha(FINAL/'execution.json'),
        teacher_config=reg['teacher_config'],teacher_config_sha256=reg['teacher_config_sha256'],python=os.path.abspath(sys.executable),
        resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),
        purpose='Test actual teacher recovery after fixed failed student prefixes. No model reselection, unseen test, fitting, gate/physics change, or automatic retry. All scientific failures remain. Prefix teacher outputs are counterfactual; only actual qualified teacher suffixes may be considered by a separate shared-data protocol.'))


def check(reg):
    prerequisites()
    assert reg['schema']=='contact-yield-recovery-development-v1' and reg['maximum_episodes']==4
    assert [(c['id'],c['scene'],c['model']['family'],c['student_steps']) for c in reg['cases']]==list(PLAN)
    for n,h in reg['source_sha256'].items(): assert sha(ROOT/n)==h,n
    for n,h in reg['parent_files'].items(): assert sha(PARENT/n)==h,n
    assert sha(FINAL/'execution.json')==reg['final_execution_sha256']
    assert sha(Path(reg['teacher_config']))==reg['teacher_config_sha256']
    assert reg['python']==os.path.abspath(sys.executable)
    for c in reg['cases']:
        for k in ('checkpoint','metadata'): assert sha(Path(c['model'][k]))==c['model'][k+'_sha256']


def run(root):
    check_resources();reg=read(root/'REGISTRATION.json');check(reg)
    assert not (root/'execution.json').exists()
    with (ROOT/'outputs/.contact-yield-recovery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (ROOT/'outputs/.local-rl-compute.lock').open('a') as physics: fcntl.flock(physics,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=dict(status='running_four_recovery_probes',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),rows=[])
        write(root/'execution.json',state)
        try:
            for case in reg['cases']:
                check(reg); state['current']=case['id'];write(root/'execution.json',state)
                output=root/case['id'];assert not output.exists()
                env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
                env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                    PYTHONPATH=str(ROOT/'tools')+':'+str(ROOT/'scripts'),MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
                    VMC_TEACHER_CONFIG=reg['teacher_config'],VMC_SCENE_SEED=str(case['condition']['seed']),VMC_STUDENT_CHECKPOINT=case['model']['checkpoint'])
                env.update({k:str(v) for k,v in case['condition']['parameters'].items()})
                with (root/(case['id']+'.log')).open('x') as log:
                    subprocess.run([sys.executable,str(WORKER),'--output',str(output),'--student-steps',str(case['student_steps']),'--scene',case['scene']],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                    subprocess.run([sys.executable,str(AUDITOR),str(output/case['scene'])],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                folder=output/case['scene'];review=read(folder/'HANDOFF_REVIEW.json')
                # Exact failing-student prefix pairing: same initial state, scene, actor and physics.
                import numpy as np
                original=PARENT/'episodes'/(case['condition']['id']+'__'+case['model']['name'])/case['scene']
                assert sha(folder/'scene.mjb')==sha(original/'scene.mjb')
                assert read(folder/'execution.json')['filter_config']==read(original/'execution.json')['filter_config']
                with np.load(folder/'trajectory.npz') as a,np.load(original/'trajectory.npz') as b:
                    for key in ('observation','action'): np.testing.assert_array_equal(a[key][:case['student_steps']],b[key][:case['student_steps']])
                state['rows'].append(dict(id=case['id'],folder=str(folder),qualified=review['qualified'],review_sha256=sha(folder/'HANDOFF_REVIEW.json'),prefix_pairing_max_abs=0.))
                write(root/'execution.json',state)
            state.update(status='complete_four_recovery_probes_pending_shared_data_decision',ended_utc=now())
        except BaseException as exc:
            state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());raise
        finally: write(root/'execution.json',state)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    (prepare if a.mode=='prepare' else run)(a.root.resolve())
