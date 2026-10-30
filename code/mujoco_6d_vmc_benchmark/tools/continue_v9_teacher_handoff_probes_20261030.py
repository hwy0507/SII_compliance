"""One finite repair probe campaign after full-grid null and zero-test handoff.

Waits without a simulator. At a verified safe boundary registers exactly two
rod00 TRAIN-identity probes (7s and 11s student prefixes). Preserves both
scientific failures; infrastructure errors stop without retries. No fitting.
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
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties
from review_v9_full_grid_eligibility_20261030 import review

SELECTION=ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1'
HANDOFF=ROOT/'outputs/nonrl_v9_unseen_handoff_20261030_v1'
UNITS=['sii-v9-full-grid-eligibility-20261030.service','sii-v9-unseen-handoff-20261030.service']


def ready(selection,handoff,states):
    if any(state in ('active','activating','deactivating','reloading') for state in states):return False
    assert states==['inactive','inactive'], 'Unexpected service failure; preserve for review'
    assert selection['status']=='eligibility_exhausted_preserved'
    assert len(selection['groups'])==9 and len(selection['selected_models'])<9
    assert any(g.get('selected') is None and g.get('status')=='candidate_budget_exhausted_preserved' for g in selection['groups'])
    assert handoff['status']=='null_selection_requires_development_repair'
    assert handoff['dispatch_attempted'] is False
    return True


def prepare(root):
    assert not root.exists(),'No duplicate/recovery by overwriting'
    reg=read(SELECTION/'REGISTRATION.json')
    group=next(g for g in reg['catalogue']['groups'] if g['family']=='mlp_scratch' and g['seed']==2026102802)
    candidate=group['ordered_candidates'][0]
    ref=next(r for r in reg['references'] if r['identity']=='rod_00')
    assert ref['split']=='train'
    sources={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')}
    root.mkdir(parents=True)
    write(root/'PENDING.json',dict(status='prepared_waiting_no_physics',created_utc=now(),
        selection_registration_sha256=sha(SELECTION/'REGISTRATION.json'),candidate=candidate,reference=ref,
        source_sha256=sources,student_prefix_steps=[175,275],maximum_episodes=2,maximum_wait_s=21600,
        interpretation='Train rod00 only, no final/test or tuning search. Probe teacher recovery at 7s and 11s, including later post-crossing student deviation. Not a deployed correction. Failed trajectories preserved; passing executed suffixes only candidates for later shared augmentation; no fitting in this campaign.'))


def check(pending):
    assert sha(SELECTION/'REGISTRATION.json')==pending['selection_registration_sha256']
    for name,digest in pending['source_sha256'].items():assert sha(ROOT/name)==digest,name
    c=pending['candidate'];r=pending['reference'];f=Path(r['folder'])
    assert sha(Path(c['checkpoint']))==c['checkpoint_sha256']
    assert sha(Path(c['metadata']))==c['metadata_sha256']
    assert sha(f/'execution.json')==r['execution_sha256']
    assert sha(f/'teacher.json')==r['config_sha256']
    assert sha(f/'DEMONSTRATION_QUALIFICATION.json')==r['qualification_sha256']
    assert not (ROOT/'outputs/nonrl_v9_isolated_unseen_108_20261030_v1').exists()


def run(root):
    check_resources();pending=read(root/'PENDING.json');check(pending)
    assert not (root/'HANDOFF.json').exists()
    lock=(root/'campaign.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=dict(status='waiting_for_full_grid_null_boundary',started_utc=now(),
        pending_sha256=sha(root/'PENDING.json'),rows=[],dispatch_attempted=False)
    write(root/'HANDOFF.json',state);start=time.monotonic()
    try:
        while True:
            check(pending)
            selection=read(SELECTION/'execution.json');handoff=read(HANDOFF/'HANDOFF.json')
            states=[properties(unit)['ActiveState'] for unit in UNITS]
            if ready(selection,handoff,states):break
            assert time.monotonic()-start<pending['maximum_wait_s'],'Finite wait expired, no dispatch'
            time.sleep(20)
        check(pending)
        review_path=root/'FULL_GRID_TERMINAL_REVIEW.json'
        review(SELECTION,review_path)
        report=read(review_path)
        assert report['status']=='verified_complete_development_selection' and report['selected_groups']<9
        registration={**pending, 'registered_utc':now(), 'status':'registered_two_development_probes',
            'full_grid_execution_sha256':sha(SELECTION/'execution.json'),
            'full_grid_review_sha256':sha(review_path), 'final_waiter_sha256':sha(HANDOFF/'HANDOFF.json')}
        write(root/'REGISTRATION.json',registration)
        compute=(ROOT/'outputs/.local-rl-compute.lock').open('a')
        fcntl.flock(compute,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state.update(status='running_registered_two_probes',dispatch_attempted=True,
            registration_sha256=sha(root/'REGISTRATION.json'));write(root/'HANDOFF.json',state)
        ref=pending['reference'];candidate=pending['candidate']
        for prefix in pending['student_prefix_steps']:
            check(pending)
            assert sha(root/'REGISTRATION.json')==state['registration_sha256']
            output=root/('rod00_prefix'+str(prefix))
            env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
            env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
                MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
                VMC_TEACHER_CONFIG=str(Path(ref['folder'])/'teacher.json'),VMC_SCENE_SEED=str(ref['seed']),
                VMC_STUDENT_CHECKPOINT=candidate['checkpoint'])
            env.update({k:str(v) for k,v in ref['parameters'].items()})
            with (root/('prefix'+str(prefix)+'.log')).open('x') as log:
                subprocess.run([sys.executable,str(ROOT/'tools/run_v9_teacher_handoff_probe_20261030.py'),
                    '--output',str(output),'--student-steps',str(prefix)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                subprocess.run([sys.executable,str(ROOT/'tools/audit_v9_teacher_handoff_probe_20261030.py'),
                    str(output/'rod')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            result=read(output/'rod/HANDOFF_REVIEW.json')
            execution=read(output/'rod/execution.json')
            assert execution['model_sha256']==ref['model_sha256']
            assert execution['filter_config']==read(Path(ref['folder'])/'execution.json')['filter_config']
            with __import__('numpy').load(output/'rod/trajectory.npz') as new, __import__('numpy').load(Path(ref['folder'])/'trajectory.npz') as old:
                __import__('numpy').testing.assert_array_equal(new['observation'][0],old['observation'][0])
            state['rows'].append(dict(student_steps=prefix,folder=str(output/'rod'),
                review_sha256=sha(output/'rod/HANDOFF_REVIEW.json'),qualified=result['qualified']))
            write(root/'HANDOFF.json',state)
        state.update(status='two_probes_complete_pending_data_repair_decision',ended_utc=now())
        write(root/'HANDOFF.json',state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now())
        write(root/'HANDOFF.json',state);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--prepare',action='store_true');a=p.parse_args()
    if a.prepare:prepare(a.root.resolve())
    else:run(a.root.resolve())
