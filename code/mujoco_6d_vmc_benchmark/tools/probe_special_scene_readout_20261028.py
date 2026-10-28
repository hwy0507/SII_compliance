"""Register/run a finite four-case teacher readout probe after collection.

Changes velocity_weight only. Exact failed training conditions remain in scope;
no test data, extended hold, smaller perturbation, or automatic student fitting.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from collect_special_scene_actions_20261028 import ALLOWED_PARAMETERS, read, sha, write

ROOT=Path(__file__).resolve().parents[1]
COLLECTION=ROOT/'outputs/special_scene_vmc_collection_20261028_v3'


def prepare(root):
    if root.exists(): raise FileExistsError(root)
    plan=read(COLLECTION/'COLLECTION_PLAN.json')
    candidate=ROOT/'configs/special_scene_vmc_readout06_20261028.json'
    original=read(Path(plan['teacher_config']));changed=read(candidate)
    assert original['velocity_weight']==.3 and changed['velocity_weight']==.6
    comparison=dict(changed);comparison['velocity_weight']=.3
    assert comparison==original
    cases=[]
    for identity in ('rod_00','rod_04','ball_00'):
        entry=next(e for e in plan['episodes'] if e['id']==identity)
        assert entry['split']=='train'
        baseline=Path(entry['folder']);execution=read(baseline/'execution.json')
        assert execution['status']=='complete'
        cases.append(dict(id=identity,scene=entry['scene'],seed=entry['seed'],
                          scene_parameters=entry['scene_parameters'],baseline=str(baseline),
                          baseline_execution_sha256=sha(baseline/'execution.json'),
                          expected_model_sha256=execution['model_sha256']))
    baseline=ROOT/'outputs/special_scene_corner_dev05_20261028/corner'
    execution=read(baseline/'execution.json')
    assert read(baseline/'DEMONSTRATION_QUALIFICATION.json')['status']=='qualified'
    argv=execution['argv'];seed=int(argv[argv.index('--seed')+1])
    cases.append(dict(id='corner_reference',scene='corner',seed=seed,baseline=str(baseline),
                      baseline_execution_sha256=sha(baseline/'execution.json'),
                      expected_model_sha256=execution['model_sha256'],
                      scene_parameters={k:v for k,v in execution['experiment_environment'].items()
                                        if k in ALLOWED_PARAMETERS['corner']}))
    scripts=['run_video_reference_vmc_20261028.py','audit_video_reference_vmc_20261028.py',
             'audit_rod_yield_rejoin_v3_20261028.py','qualify_special_scene_demo_20261028.py',
             'collect_special_scene_actions_20261028.py','probe_special_scene_readout_20261028.py']
    sources={str(Path('tools')/name):sha(ROOT/'tools'/name) for name in scripts}
    sources.update({str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts').glob('*.py')})
    registration=dict(schema='sii-special-scene-readout-probe-v1',
                      registered_utc=datetime.now(timezone.utc).isoformat(),
                      collection=str(COLLECTION),collection_plan_sha256=sha(COLLECTION/'COLLECTION_PLAN.json'),
                      candidate=str(candidate),candidate_file_sha256=sha(candidate),
                      candidate_config_sha256=hashlib.sha256((json.dumps(changed,indent=2)+'\n').encode()).hexdigest(),
                      cases=cases,source_hashes=sources,maximum_episodes=4,
                      prerequisite='Existing original30 collection terminal with all30 receipts and no active original service; never interrupt it',
                      selection='Two failed TRAINING rod identities, one preselected first ball training identity, original qualified corner development. No validation/test selection.',
                      disposition='Development only. Never replace or overwrite original30 failures. Review all four before any new collection decision.')
    root.mkdir(parents=True);write(root/'REGISTRATION.json',registration)
    return registration


def run(root):
    registration=read(root/'REGISTRATION.json')
    for name,digest in registration['source_hashes'].items():
        if sha(ROOT/name)!=digest: raise ValueError(f'Probe source changed: {name}')
    collection=Path(registration['collection'])
    assert sha(collection/'COLLECTION_PLAN.json')==registration['collection_plan_sha256']
    progress=read(collection/'COLLECTION_PROGRESS.json')
    if progress['status'] not in ('qualified_complete','finished_with_nonqualified_demonstrations') or len(progress['episodes'])!=30:
        raise RuntimeError('Original30 collection still running or incomplete; do not interrupt/restart it')
    if subprocess.run(['systemctl','--user','is-active','--quiet',registration.get(
            'collection_service','sii-special-collection-v3-20261028.service')]).returncode==0:
        raise RuntimeError('Original collection service is still active')
    candidate=Path(registration['candidate'])
    assert sha(candidate)==registration['candidate_file_sha256']
    lock=(root/'.probe.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state_path=root/'execution.json'
    if state_path.exists(): raise FileExistsError('Inspect existing probe execution; no automatic replay')
    state=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),
               registration_sha256=sha(root/'REGISTRATION.json'),episodes=[])
    write(state_path,state)
    for entry in registration['cases']:
        baseline=Path(entry['baseline'])
        assert sha(baseline/'execution.json')==entry['baseline_execution_sha256']
        output=root/entry['id'];folder=output/entry['scene']
        env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
        env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                   PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
                   VMC_TEACHER_CONFIG=str(candidate),VMC_SCENE_SEED=str(entry['seed']))
        env.update({k:str(v) for k,v in entry['scene_parameters'].items()})
        state['current']=entry['id'];write(state_path,state)
        command=[sys.executable,str(ROOT/'tools/run_video_reference_vmc_20261028.py'),
                 '--output',str(output),'--scenes',entry['scene']]
        rc=subprocess.run(command,cwd=ROOT,env=env).returncode
        row=dict(id=entry['id'],returncode=rc,status='failed_preserved')
        if rc:
            state['episodes'].append(row);state['status']='infrastructure_failure_preserved';write(state_path,state)
            raise SystemExit(1)
        e=read(folder/'execution.json')
        assert e['teacher_config_sha256']==registration['candidate_config_sha256']
        if e['model_sha256']!=entry['expected_model_sha256']:
            state['episodes'].append(dict(**row,error='MJB changed'));state['status']='model_mismatch_preserved';write(state_path,state)
            raise RuntimeError('MJB changed despite identical scene condition')
        audits=['audit_video_reference_vmc_20261028.py']
        if entry['scene']=='rod': audits.append('audit_rod_yield_rejoin_v3_20261028.py')
        audits.append('qualify_special_scene_demo_20261028.py')
        for name in audits:
            with (output/(name+'.log')).open('x') as log:
                result=subprocess.run([sys.executable,str(ROOT/'tools'/name),str(folder)],
                                      cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode:
                state['episodes'].append(dict(**row,audit_error=name));state['status']='audit_failure_preserved';write(state_path,state)
                raise SystemExit(1)
        row['status']=read(folder/'DEMONSTRATION_QUALIFICATION.json')['status']
        state['episodes'].append(row);write(state_path,state)
    state.update(status='complete',ended_utc=datetime.now(timezone.utc).isoformat())
    write(state_path,state)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if args.run: run(args.root.resolve())
    else: print(json.dumps(prepare(args.root.resolve()),indent=2))
