"""Registered 108-cell isolated-scene test; no fitting or test-based selection.

Register only after the complete full-grid development review and inactive
selection services. Run once, serially. Infrastructure failures are preserved,
never retried or silently dropped. Review independently reconstructs each row.
"""
import argparse
import copy
import fcntl
import os
from pathlib import Path
import statistics
import subprocess
import sys

import mujoco
import numpy as np

from audit_special_scene_metrics_v2_20261030 import episode
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now
from review_v9_full_grid_eligibility_20261030 import review as review_selection
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties
from special_scene_metrics_20261030 import aggregate

REPO = ROOT.parents[1]
CONDITIONS = REPO/'docs/evidence/nonrl_v9_candidate_catalogue_20261029/UNSEEN_CONDITIONS_20261030.json'
CONDITIONS_SHA = 'c99f0f962ab44821693f9928c9f68dc4a3ff907617bcc9e55cce3ccdbfbcc24d'
SELECTION = ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1'
UNITS = ('sii-v9-common-eligibility-v3-20261029.service',
         'sii-v9-full-grid-eligibility-20261030.service')
FAMILIES = ('esn_ridge','rnn_scratch','mlp_scratch')
SEEDS = (2026102801,2026102802,2026102803)


def make_cases(models, conditions):
    assert len(models)==9 and {(m['family'],m['seed']) for m in models} == {
        (f,s) for f in FAMILIES for s in SEEDS}, 'Need nine distinct qualified family/seed models'
    assert len({m['name'] for m in models})==9
    assert len(conditions)==12 and len({c['id'] for c in conditions})==12
    assert all(sum(c['scene']==s for c in conditions)==4 for s in ('rod','ball','corner'))
    rows = []
    for condition in conditions:
        for model in models:
            rows.append(dict(id=condition['id']+'__'+model['name'],condition=copy.deepcopy(condition),
                             model=copy.deepcopy(model),expected_duration_s={
                                 'rod':20.,'ball':30.,'corner':13.}[condition['scene']]))
    assert len(rows)==len({r['id'] for r in rows})==108
    return rows


def inactive():
    assert all(properties(u)['ActiveState']=='inactive' for u in UNITS), 'Selection still active or failed'


def register(root):
    assert root.parent==ROOT/'outputs' and not root.exists(), 'Use a new output directory'
    inactive()
    assert sha(CONDITIONS)==CONDITIONS_SHA
    contract=read(CONDITIONS)
    for name,digest in contract['frozen_sources'].items():
        assert sha(REPO/name)==digest, name
    selected=read(SELECTION/'execution.json')
    assert selected['status']=='selection_complete_pending_independent_audit', 'Null selection requires development repair'
    output=SELECTION/'FINAL_REVIEW.json'
    if not output.exists():
        review_selection(SELECTION,output)
    report=read(output)
    assert report['status']=='verified_complete_development_selection' and report['selected_groups']==9
    assert report['execution_snapshot_sha256']==sha(SELECTION/'execution.json')
    assert report['registration_sha256']==sha(SELECTION/'REGISTRATION.json')
    assert report['reviewer_sha256']==sha(ROOT/'tools/review_v9_full_grid_eligibility_20261030.py')
    models=selected['selected_models']
    cases=make_cases(models,contract['conditions'])
    selection_registration=read(SELECTION/'REGISTRATION.json')
    teacher=Path(selection_registration['references'][0]['folder'])/'teacher.json'
    assert sha(teacher)==selection_registration['references'][0]['config_sha256']
    assert all(r['config_sha256']==sha(teacher) for r in selection_registration['references'])
    # Bind models/metadata before creating any output or dispatching physics.
    for model in models:
        assert sha(Path(model['checkpoint']))==model['checkpoint_sha256']
        assert sha(Path(model['metadata']))==model['metadata_sha256']
    sources={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools')
             for p in (ROOT/folder).glob('*.py')}
    reg=dict(schema='sii-v9-isolated-unseen-matrix-v1',registered_utc=now(),
        conditions_path=str(CONDITIONS),conditions_sha256=CONDITIONS_SHA,
        selection=str(SELECTION),selection_files={n:sha(SELECTION/n) for n in
            ('execution.json','REGISTRATION.json','FINAL_REVIEW.json','DEVELOPMENT_SELECTION.json')},
        models=models,cases=cases,maximum_episodes=108,teacher_config=str(teacher),
        teacher_config_sha256=sha(teacher),source_sha256=sources,
        recipe_config_sha256={n:sha(ROOT/n) for n in
            ('configs/ball_source_demo.json','configs/workstation_source_demo.json')},
        python=os.path.abspath(sys.executable),runtime_versions=dict(
            python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__),
        resources=dict(cpu=6,simulators=1,threads=1,
            memory_max_bytes=3221225472,swap_bytes=0),
        metric_contract=contract,metric_supplement='v2 full-horizon checks; unchanged frozen gates and conditions',
        failure_policy='Preserve every failed/incomplete cell. No automatic retries, no fallback models, no test-based tuning.')
    root.mkdir()
    write(root/'REGISTRATION.json',reg)


def check_registration(reg):
    inactive()
    assert sha(CONDITIONS)==reg['conditions_sha256']==CONDITIONS_SHA
    assert read(CONDITIONS)==reg['metric_contract']
    assert reg['cases']==make_cases(reg['models'],reg['metric_contract']['conditions'])
    assert reg['maximum_episodes']==108
    assert reg['resources']==dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0)
    assert os.path.abspath(sys.executable)==reg['python']
    assert reg['runtime_versions']==dict(python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__)
    assert set(reg['recipe_config_sha256'])=={'configs/ball_source_demo.json','configs/workstation_source_demo.json'}
    for name,digest in reg['recipe_config_sha256'].items():
        assert sha(ROOT/name)==digest,name
    assert reg['selection']==str(SELECTION)
    for name,digest in reg['selection_files'].items():
        assert sha(SELECTION/name)==digest,name
    selected=read(SELECTION/'execution.json')
    report=read(SELECTION/'FINAL_REVIEW.json')
    assert selected['status']=='selection_complete_pending_independent_audit'
    assert reg['models']==selected['selected_models']
    assert report['status']=='verified_complete_development_selection' and report['selected_groups']==9
    assert report['execution_snapshot_sha256']==reg['selection_files']['execution.json']
    assert report['registration_sha256']==reg['selection_files']['REGISTRATION.json']
    assert report['reviewer_sha256']==sha(ROOT/'tools/review_v9_full_grid_eligibility_20261030.py')
    for name,digest in reg['source_sha256'].items():
        assert sha(ROOT/name)==digest,name
    assert sha(Path(reg['teacher_config']))==reg['teacher_config_sha256']
    for model in reg['models']:
        assert sha(Path(model['checkpoint']))==model['checkpoint_sha256']
        assert sha(Path(model['metadata']))==model['metadata_sha256']


def case_folder(root,case):
    return root/'episodes'/case['id']/case['condition']['scene']


def check_episode(folder,case,reg):
    e=read(folder/'execution.json')
    c=case['condition'];m=case['model']
    assert e['scene']==c['scene'] and e['physics_dt_s']==.00005
    assert os.path.abspath(e['python'])==reg['python']
    assert e['mujoco']==reg['runtime_versions']['mujoco']
    assert sha(folder/'scene.mjb')==e['model_sha256']
    assert sha(folder/'student_checkpoint.npz')==e['student_checkpoint_sha256']==m['checkpoint_sha256']
    assert sha(folder/'teacher.json')==e['teacher_config_sha256']==reg['teacher_config_sha256']
    assert e['experiment_environment']['VMC_SCENE_SEED']==str(c['seed'])
    for name,value in c['parameters'].items():
        assert e['experiment_environment'][name]==str(value)
    # Bind every source captured by the worker to the pre-dispatch registration.
    for name,digest in read(folder/'SOURCE_HASHES.json').items():
        assert reg['source_sha256'][name]==digest,name
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
        initial=z['observation'][0].copy()
    assert initial.shape==(48,) and np.isfinite(initial).all()
    return dict(model_sha256=e['model_sha256'],initial_observation=initial.tolist(),filter_config=e['filter_config'])


def replay(folder):
    """Recompute action/filter output, rather than trusting a prior passed flag."""
    from current_student_policy_20260921 import load_current
    from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig
    e=read(folder/'execution.json')
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
        obs,action=z['observation'],z['action']
    with np.load(folder/'filter.npz',allow_pickle=False) as z:
        chain={k:z[k] for k in z.files}
    model=load_current(folder/'student_checkpoint.npz');model.reset()
    np.testing.assert_array_equal(np.asarray([model.act(o) for o in obs]),action)
    assert len(chain['request'])==len(action)==e['steps']
    np.testing.assert_array_equal(chain['request'],action)
    cfg=copy.deepcopy(e['filter_config'])
    for k,v in cfg.items():
        if isinstance(v,list):cfg[k]=np.asarray(v)
    filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(**cfg))
    for i,act in enumerate(action):
        out=filt.filter(act,float(chain['dt'][i]))
        np.testing.assert_array_equal(out.cartesian_yield_twist,chain['twist'][i])
        np.testing.assert_array_equal(out.raw_action_clipped,chain['clipped'][i])
        assert out.wbc_scale==chain['scale'][i]
    return dict(actor_replay_max_abs=0.,filter_replay_max_abs=0.,rows=len(action))


def run_case(root,case,reg):
    output=case_folder(root,case).parent
    assert not output.exists(), 'Existing complete or incomplete evidence must not be overwritten'
    output.parent.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in
        {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
        MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
        VMC_TEACHER_CONFIG=reg['teacher_config'],VMC_SCENE_SEED=str(case['condition']['seed']),
        VMC_STUDENT_CHECKPOINT=case['model']['checkpoint'])
    env.update({k:str(v) for k,v in case['condition']['parameters'].items()})
    with (output.parent/(case['id']+'.log')).open('x') as log:
        subprocess.run([sys.executable,str(ROOT/'tools/run_video_reference_coverage_20261029.py'),
            '--output',str(output),'--scenes',case['condition']['scene']],cwd=ROOT,env=env,
            stdout=log,stderr=subprocess.STDOUT,check=True)
    folder=case_folder(root,case)
    audits=['audit_video_reference_vmc_20261028.py']
    if case['condition']['scene']=='rod':
        audits.append('audit_rod_yield_rejoin_v3_20261028.py')
    audits.append('qualify_ball_coverage_demo_20261029.py')
    for tool in audits:
        with (output/(tool+'.log')).open('x') as log:
            subprocess.run([sys.executable,str(ROOT/'tools'/tool),str(folder)],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,check=True)
    pairing=check_episode(folder,case,reg)
    row=episode(folder,case['model']['name'],case['condition']['id'],case['expected_duration_s'])
    write(output/'METRICS.json',row)
    return dict(id=case['id'],folder=str(folder),pairing=pairing,metrics_sha256=sha(output/'METRICS.json'))


def run(root):
    check_resources()
    reg=read(root/'REGISTRATION.json');check_registration(reg)
    assert not (root/'execution.json').exists(), 'No implicit restart'
    with (ROOT/'outputs/.v9-unseen-matrix-coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # Check global simulator ownership without holding its lock while the
        # existing worker acquires it. Worker independently rejects any race.
        with (ROOT/'outputs/.local-rl-compute.lock').open('a') as physics:
            fcntl.flock(physics,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=dict(status='running_unseen_test',started_utc=now(),rows=[],
            registration_sha256=sha(root/'REGISTRATION.json'))
        write(root/'execution.json',state)
        paired={}
        try:
            for case in reg['cases']:
                assert sha(root/'REGISTRATION.json')==state['registration_sha256']
                check_registration(reg)
                state['current']=case['id'];write(root/'execution.json',state)
                result=run_case(root,case,reg)
                key=case['condition']['id']
                if key in paired:
                    assert result['pairing']==paired[key], 'Model/initial canonical48/filter pairing mismatch'
                else:
                    paired[key]=result['pairing']
                state['rows'].append(result);write(root/'execution.json',state)
            check_registration(reg)
            state.update(status='complete_pending_independent_review',ended_utc=now())
        except BaseException as exc:
            state.update(status='failed_preserved',error=repr(exc),ended_utc=now())
            raise
        finally:
            write(root/'execution.json',state)


def grouped(rows,models,tref,fields):
    lookup={m['name']:m for m in models}
    buckets={}
    for row in rows:
        metadata=dict(lookup[row['method']],scene=row['scene'])
        key=tuple(metadata[n] for n in fields)
        buckets.setdefault(key,[]).append(row)
    results=[]
    for key,original in sorted(buckets.items()):
        copied=[dict(r,method='group',condition=r['condition']+'__'+r['method']) for r in original]
        summary=aggregate(copied,[(r['method'],r['condition']) for r in copied])['methods'][0]
        summary.pop('method')
        good=[r for r in original if r['task_success'] and r['strict_success']]
        summary['spt_both_conditional']=statistics.mean(tref/max(tref,r['completion_time_s']) for r in good) if good else None
        results.append(dict(zip(fields,key),**summary))
    return results


def review(root,output):
    assert not output.exists()
    state_bytes=(root/'execution.json').read_bytes()
    state=read(root/'execution.json');reg=read(root/'REGISTRATION.json')
    check_registration(reg)
    assert state['status']=='complete_pending_independent_review'
    assert state['registration_sha256']==sha(root/'REGISTRATION.json')
    assert [r['id'] for r in state['rows']]==[c['id'] for c in reg['cases']]
    assert len(state['rows'])==108
    rows=[];paired={};replays=[]
    for case,receipt in zip(reg['cases'],state['rows']):
        folder=case_folder(root,case)
        assert receipt['folder']==str(folder)
        pairing=check_episode(folder,case,reg)
        assert pairing==receipt['pairing']
        key=case['condition']['id']
        if key in paired:
            assert pairing==paired[key]
        else:
            paired[key]=pairing
        replays.append(dict(id=case['id'],**replay(folder)))
        row=episode(folder,case['model']['name'],key,case['expected_duration_s'])
        assert sha(folder.parent/'METRICS.json')==receipt['metrics_sha256']
        assert row==read(folder.parent/'METRICS.json'), 'Independent metrics differ'
        rows.append(row)
    expected=[(c['model']['name'],c['condition']['id']) for c in reg['cases']]
    summary=aggregate(rows,expected)
    assert (root/'execution.json').read_bytes()==state_bytes
    check_registration(reg)
    write(output,dict(status='verified_complete_isolated_unseen_matrix',
        registration_sha256=sha(root/'REGISTRATION.json'),execution_sha256=sha(root/'execution.json'),
        reviewer_sha256=sha(Path(__file__)),rows=rows,summary=summary,
        independent_replays=replays,
        family=grouped(rows,reg['models'],summary['t_ref_s'],('family',)),
        family_scene=grouped(rows,reg['models'],summary['t_ref_s'],('family','scene')),
        limitations=['Only the registered interpolation conditions, not broad OOD.',
            'No human-force channel: human comfort NA; disturbance proxy separately labelled.',
            'Completion hold is 13 sampled states spanning .48s, not substep terminal proof.',
            'Distinct from historical office108 transfer pressure; no original result overwritten.']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('register','run','review'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args();root=a.root.resolve()
    if a.mode=='register':register(root)
    elif a.mode=='run':run(root)
    else:
        assert a.output is not None
        review(root,a.output.resolve())
