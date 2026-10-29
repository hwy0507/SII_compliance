"""Five finite train-identity development probes of one fixed new teacher.

Three nominal scenes plus two safe-student-prefix rod recoveries. No fitting,
unseen inputs, threshold changes, automatic retries or parameter search.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
from review_v9_paired_scene_closure_20261029 import verify_qualification

PARENT=ROOT/'outputs/nonrl_v9_teacher_handoff_probes_20261030_v1'
SELECTION=ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1'
UNITS=['sii-cross-track-teacher-development-20261030.service','sii-v9-full-grid-eligibility-20261030.service','sii-v9-unseen-handoff-20261030.service','sii-v9-teacher-handoff-probes-20261030.service']


def prerequisite():
    assert all(properties(u)['ActiveState']=='inactive' for u in UNITS)
    assert read(ROOT/'outputs/cross_track_teacher_development_20261030_v1/execution.json')['status']=='complete_five_probes_pending_independent_campaign_review'
    assert read(PARENT/'HANDOFF.json')['status']=='two_probes_complete_pending_data_repair_decision'
    assert len(read(PARENT/'HANDOFF.json')['rows'])==2
    assert read(SELECTION/'execution.json')['status']=='eligibility_exhausted_preserved'
    final=read(ROOT/'outputs/nonrl_v9_unseen_handoff_20261030_v1/HANDOFF.json')
    assert final['status']=='null_selection_requires_development_repair' and final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/nonrl_v9_isolated_unseen_108_20261030_v1').exists()


def prepare(root):
    assert not root.exists();prerequisite()
    reg=read(SELECTION/'REGISTRATION.json');state=read(SELECTION/'execution.json')
    group=next(g for g in state['groups'] if g['family']=='mlp_scratch' and g['seed']==2026102802)
    trial=group['trials'][1];candidate=trial['candidate'];assert candidate['validation_rank']==2
    fail=trial['cases'][0];q=verify_qualification(Path(fail['folder']),fail['qualification_sha256'])
    assert q['safety_valid'] is True and q['scene_contact_valid'] is False
    config=read(Path(reg['references'][0]['folder'])/'teacher.json')
    config['cross_track_recovery']=dict(version='bounded_cross_track_recovery_v2',gain_per_s=1.5,maximum_speed_mps=.02,load_scale_n=1.)
    cases=[]
    for scene,prefix in [('rod',0),('ball',0),('corner',0),('rod',175),('rod',275)]:
        ref=next(r for r in reg['references'] if r['identity']==scene+'_00');assert ref['split']=='train'
        cases.append(dict(id=scene+'_prefix'+str(prefix),scene=scene,student_steps=prefix,reference=ref,candidate=candidate))
    root.mkdir(parents=True);write(root/'teacher.json',config)
    sources={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')}
    write(root/'REGISTRATION.json',dict(status='registered_not_executed',registered_utc=now(),cases=cases,
        maximum_episodes=5,teacher_config_sha256=sha(root/'teacher.json'),source_sha256=sources,
        parent_execution_sha256=sha(PARENT/'HANDOFF.json'),selection_execution_sha256=sha(SELECTION/'execution.json'),
        safety_valid_student_reference=dict(folder=fail['folder'],qualification_sha256=fail['qualification_sha256']),
        resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),
        interpretation='One fixed prospective teacher config, three nominal train scenes and two actual recovery probes. All failures preserved; no final-test/fitting/automatic dataset assembly. Prefix0 is teacher-only, prefix>0 is mixed history and only qualified executed teacher suffix can become candidate labels.'))


def check(root,reg):
    assert sha(root/'teacher.json')==reg['teacher_config_sha256']
    for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
    assert sha(PARENT/'HANDOFF.json')==reg['parent_execution_sha256']
    assert sha(SELECTION/'execution.json')==reg['selection_execution_sha256']
    for case in reg['cases']:
        ref=case['reference'];c=case['candidate'];folder=Path(ref['folder'])
        for name,key in [('execution.json','execution_sha256'),('teacher.json','config_sha256'),('DEMONSTRATION_QUALIFICATION.json','qualification_sha256')]:assert sha(folder/name)==ref[key]
        assert sha(Path(c['checkpoint']))==c['checkpoint_sha256'] and sha(Path(c['metadata']))==c['metadata_sha256']


def run(root):
    check_resources();prerequisite();reg=read(root/'REGISTRATION.json');check(root,reg)
    assert not (root/'execution.json').exists(),'Preserve prior/incomplete campaign'
    lock=(ROOT/'outputs/.local-rl-compute.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=dict(status='running_registered_development_probes',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),rows=[])
    write(root/'execution.json',state)
    try:
        for case in reg['cases']:
            check(root,reg);assert sha(root/'REGISTRATION.json')==state['registration_sha256']
            out=root/case['id'];ref=case['reference'];candidate=case['candidate']
            state['current']=case['id'];write(root/'execution.json',state)
            env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
            env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
                MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
                VMC_TEACHER_CONFIG=str(root/'teacher.json'),VMC_SCENE_SEED=str(ref['seed']),VMC_STUDENT_CHECKPOINT=candidate['checkpoint'])
            env.update({k:str(v) for k,v in ref['parameters'].items()})
            with (root/(case['id']+'.log')).open('x') as log:
                subprocess.run([sys.executable,str(ROOT/'tools/run_persistent_cross_track_probe_20261030.py'),
                    '--output',str(out),'--scene',case['scene'],'--student-steps',str(case['student_steps'])],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                subprocess.run([sys.executable,str(ROOT/'tools/audit_persistent_cross_track_probe_20261030.py'),str(out/case['scene'])],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            folder=out/case['scene'];result=read(folder/'HANDOFF_REVIEW.json');execution=read(folder/'execution.json')
            assert execution['model_sha256']==ref['model_sha256']
            assert execution['filter_config']==read(Path(ref['folder'])/'execution.json')['filter_config']
            import numpy as np
            with np.load(folder/'trajectory.npz') as new,np.load(Path(ref['folder'])/'trajectory.npz') as old:
                np.testing.assert_array_equal(new['observation'][0],old['observation'][0])
            state['rows'].append(dict(id=case['id'],folder=str(folder),qualified=result['qualified'],
                review_sha256=sha(folder/'HANDOFF_REVIEW.json'),qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json')))
            write(root/'execution.json',state)
        state.update(status='complete_five_probes_pending_independent_campaign_review',ended_utc=now())
        write(root/'execution.json',state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(root/'execution.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if a.prepare:prepare(a.root.resolve())
    else:run(a.root.resolve())
