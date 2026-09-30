"""Freeze and run 12 fixed-teacher contact-history diagnostics; never retrain.

Preparation audits historical fixture metadata, copies a source snapshot and
model files, and writes the exact commands before any simulation starts.
Execution is a separate invocation and accepts only that frozen protocol.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def dump(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def fixtures():
    specs=[('train',9600,-.12,.576,.090,.496),('train',9601,-.02,.579,.100,.498),
           ('train',9602,.08,.584,.110,.5005),('validation',9610,-.08,.578,.095,.497),
           ('validation',9611,.02,.582,.105,.499),('validation',9612,.12,.586,.115,.5015)]
    return [dict(split=s,seed=n,push_angle=a,push_height=h,payload_mass=m,
                 back_inner_x=b,front_inner_x=round(b+.095,6)) for s,n,a,h,m,b in specs]


def guard_boxes(panel):
    b,f,t=panel['back_inner_x'],panel['front_inner_x'],panel['pad_thickness']
    y=(panel['pad_lower_y']+panel['pad_upper_y'])/2;z=(panel['pad_bottom_z']+panel['pad_top_z'])/2
    half=[t/2,(panel['pad_upper_y']-panel['pad_lower_y'])/2,(panel['pad_top_z']-panel['pad_bottom_z'])/2]
    return [dict(name='push_back_guard',position_m=[b-t/2,y,z],half_size_m=half),
            dict(name='push_front_guard',position_m=[f+t/2,y,z],half_size_m=half)]


def descriptor(scene, boxes):
    return dict(push_angle=scene['push_angle'],push_height=scene['push_height'],
                payload_mass=scene['payload_mass'],guard_boxes=sorted([
                    {k:b[k] for k in ('name','position_m','half_size_m')} for b in boxes],key=lambda b:b['name']))


def same_geometry(a,b):
    if any(abs(a[k]-b[k])>1e-9 for k in ('push_angle','push_height','payload_mass')):return False
    if [x['name'] for x in a['guard_boxes']] != [x['name'] for x in b['guard_boxes']]:return False
    return all(np.allclose(x[k],y[k],atol=1e-9,rtol=0) for x,y in zip(a['guard_boxes'],b['guard_boxes'])
               for k in ('position_m','half_size_m'))


def prepare(args):
    if args.output.exists():raise FileExistsError('Fresh output required')
    base=json.loads(args.base_protocol.read_text());manifest=json.loads((args.bank/'manifest.json').read_text())
    teacher_row=min((r for r in manifest['train'] if r['scene']=='push'),key=lambda r:r['id'])
    teacher_source=Path(teacher_row['source_search_result'])
    teacher=json.loads(teacher_source.read_text())['config']
    old=[];missing=[]
    # Read metadata JSON only, including test geometry; never open test NPZ.
    for split in ('train','validation','test'):
        for row in manifest[split]:
            if row['scene']!='push':continue
            source=Path(row['source_result'])
            if not source.exists():missing.append(str(source));continue
            result=json.loads(source.read_text())
            old.append(dict(id=row['id'],split=split,source=str(source),source_sha256=sha(source),
                            descriptor=descriptor(result['scene'],result['panel_audit']['physical_panels'])))
    for row in base['fixtures']:
        old.append(dict(id=str(row['seed']),split='previous_development',
                        descriptor=descriptor(row,guard_boxes(base['panel']))))
    # Six previously declared classical validation conditions; geometry unchanged.
    triples=[(-.125,.5775,.0925),(-.125,.5825,.1075),(0.,.5775,.1075),
             (0.,.5825,.0925),(.075,.5775,.0925),(.075,.5825,.1075)]
    for i,(a,h,m) in enumerate(triples):
        old.append(dict(id=str(9400+i),split='previous_validation',descriptor=descriptor(
            dict(push_angle=a,push_height=h,payload_mass=m),guard_boxes(base['panel']))))
    if missing:raise ValueError('Cannot complete historical geometry metadata audit: '+str(missing[:3]))
    planned=[]
    for f in fixtures():
        panel=dict(base['panel'],back_inner_x=f['back_inner_x'],front_inner_x=f['front_inner_x'],rod_height_m=f['push_height'])
        desc=descriptor(f,guard_boxes(panel));overlap=[x['id'] for x in old if same_geometry(desc,x['descriptor'])]
        if overlap:raise ValueError('Exact physical descriptor overlap: '+str(overlap))
        planned.append(dict(**f,panel=panel,physical_descriptor=desc,descriptor_sha256=json_sha(desc)))
    if any(same_geometry(a['physical_descriptor'],b['physical_descriptor']) for i,a in enumerate(planned) for b in planned[i+1:]):
        raise ValueError('New train/validation physical descriptor overlap')
    args.output.mkdir(parents=True)
    snapshot=args.output/'source_snapshot';snapshot.mkdir()
    for name in ('scripts','assets','configs'):
        shutil.copytree(args.source/name,snapshot/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copy2(Path(__file__),snapshot/'scripts'/Path(__file__).name)
    frozen_models={}
    for name,record in base['models'].items():
        if sha(record['path'])!=record['sha256']:raise ValueError('Checkpoint SHA mismatch '+name)
        dst=args.output/'frozen_models'/f'{name}.npz';dst.parent.mkdir(exist_ok=True)
        shutil.copy2(record['path'],dst);frozen_models[name]=dict(path=str(dst),sha256=sha(dst))
    source_hashes={str(p.relative_to(snapshot)):sha(p) for p in sorted(snapshot.rglob('*')) if p.is_file()}
    jobs=[]
    for f in planned:
        for event_stage in ('approach','loaded_lift'):
            job_id=f"{f['split']}_{f['seed']}_{event_stage}";job=args.output/'jobs'/job_id
            params={k:v for k,v in base['reference'].items() if v is not None and k not in ('output','render','settle_only','model')}
            params.update({k:f[k] for k in ('seed','push_angle','push_height','payload_mass')})
            params.update(scene='push',event_stage=event_stage,event_delay=0.,duration=24.,
                          menagerie=str(args.menagerie),mixture=0.,teacher_profile='memory',
                          teacher_force_source='estimated',push_target_x=.57,push_target_y=0.,
                          ball_target_x=.54,ball_target_y=0.,ball_target_z=.62,output=str(job/'rollout/rollout'))
            command=[sys.executable,str(snapshot/'scripts/run_with_substep_metrics_20260923.py'),
                     '--runner',str(snapshot/'scripts/run_panel_push_20260920.py'),
                     '--metrics-output',str(job/'metrics'),'--']
            for key,value in params.items():command.extend(['--'+key.replace('_','-'),str(value)])
            env=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',
                     MUJOCO_GL='egl',PANELS_ENABLED='1',UNIFIED_6D_TEACHER='1',
                     PRIMITIVE_RUNNER_PATH=str(snapshot/'scripts/run_primitive_teacher_v7_20260917.py'),
                     CORE_VMC_CONFIG=json.dumps(teacher),PANEL_CONFIG=json.dumps(f['panel']))
            jobs.append(dict(id=job_id,fixture=f,requested_event_stage=event_stage,arguments=params,
                             command=command,environment=env,directory=str(job)))
    protocol=dict(version=1,scope='fixed-teacher causal history diagnostic; no training or new model selection',
        created_unix=time.time(),duration_s=24.,max_workers=4,jobs=jobs,fixtures=planned,source_snapshot=str(snapshot),
        source_sha256=source_hashes,models=frozen_models,teacher=teacher,
        teacher_selection_rule='lexicographically smallest id among existing train push rows; no performance selection',
        teacher_source_id=teacher_row['id'],teacher_source=str(teacher_source),teacher_source_sha256=sha(teacher_source),
        teacher_config_sha256=json_sha(teacher),bank_manifest_sha256=sha(args.bank/'manifest.json'),
        base_protocol_sha256=sha(args.base_protocol),menagerie=str(args.menagerie),
        isolation=dict(historical_metadata_checked=len(old),exact_descriptor_overlaps=0,
                       new_train_validation_overlaps=0,metadata_missing=missing,
                       historical=old,comparison_fields=['push_angle','push_height','payload_mass','actual guard box positions/sizes'],
                       excluded_ids='930x and 940x never enter new data',
                       limits='Numerically distinct local physical configurations, not unseen layouts or a generalization proof. Historical MJB equivalence not exhaustively checked. Teacher config deliberately shared across new train/validation.'),
        retain_all_runs=True,no_replacement_seeds=True,no_test_trajectory_read=True,
        analysis='Offline frozen MLP/ESN on teacher-visited observations; raw action and safety-filter requests by phase, no student closed-loop score')
    dump(args.output/'protocol.json',protocol)
    dump(args.output/'READY.json',dict(protocol_sha256=sha(args.output/'protocol.json'),jobs=12,status='prepared_not_started'))
    for p in snapshot.rglob('*'):
        if p.is_file():p.chmod(0o444)
    print(json.dumps(dict(output=str(args.output),teacher=teacher_row['id'],jobs=len(jobs),
                         historical_metadata_checked=len(old),protocol_sha256=sha(args.output/'protocol.json'))))


def offline_metrics(protocol, job, result):
    from current_student_policy_20260921 import load_current
    from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig
    path=Path(job['directory'])/'rollout/rollout.npz'
    with np.load(path,allow_pickle=False) as z:
        obs=z['observation'];labels=z['teacher_action'];actions=z['action'];times=z['time']-.04
        post_force=z['force']
    if obs.shape!=(600,48):raise ValueError('Incomplete 24s proprio48 episode')
    teacher=SixDVirtualDynamics(protocol['teacher']);replay=np.stack([teacher.act(o[39:45],.04) for o in obs])
    parity=float(np.max(abs(replay-labels)))
    if parity>1e-6 or np.max(abs(actions-labels))>1e-6:raise ValueError('Teacher label replay mismatch')
    stage=np.zeros(len(obs),dtype=int)
    for event in result['events']:stage[times>=event['t']-1e-8]=event['stage']
    contact=np.r_[False,np.linalg.norm(post_force[:-1],axis=1)>.05]
    masks=dict(all=np.ones(len(obs),dtype=bool),loaded=stage==3,
               loaded_contact=(stage==3)&contact,loaded_no_contact=(stage==3)&~contact)
    def filt(seq):
        f=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
        rows=[f.filter(a,.04) for a in seq]
        return np.stack([r.cartesian_yield_twist for r in rows])
    teacher_yield=filt(labels);students={}
    for name,model in protocol['models'].items():
        policy=load_current(model['path']);pred=np.stack([policy.act(o) for o in obs]);applied=filt(pred)
        stats={}
        for phase,mask in masks.items():
            strong=mask&(abs(labels[:,1])>.01)
            stats[phase]=dict(samples=int(mask.sum()),action_mae=np.mean(abs(pred[mask]-labels[mask]),axis=0).tolist() if mask.any() else None,
                action_rmse=float(np.sqrt(np.mean((pred[mask]-labels[mask])**2))) if mask.any() else None,
                slew_yield_mae=np.mean(abs(applied[mask]-teacher_yield[mask]),axis=0).tolist() if mask.any() else None,
                x_sign_conflict_rate=float(np.mean(pred[strong,1]*labels[strong,1]<0)) if strong.any() else None,
                x_sign_reference_samples=int(strong.sum()))
        students[name]=stats
    return dict(scope='offline teacher-visited-state imitation, not alternate student trajectories',teacher_replay_max_error=parity,
                sparse_contact_samples_by_phase={k:int(v.sum()) for k,v in masks.items()},students=students)


def execute(args):
    directory=args.protocol.parent;protocol=json.loads(args.protocol.read_text());ready=json.loads((directory/'READY.json').read_text())
    if sha(args.protocol)!=ready['protocol_sha256']:raise ValueError('Frozen protocol changed')
    if (directory/'status.json').exists():raise FileExistsError('No silent repeat/resume')
    snapshot=Path(protocol['source_snapshot'])
    for name,expected in protocol['source_sha256'].items():
        if sha(snapshot/name)!=expected:raise ValueError('Snapshot changed: '+name)
    for model in protocol['models'].values():
        if sha(model['path'])!=model['sha256']:raise ValueError('Frozen model changed')
    sys.path.insert(0,str(snapshot/'scripts'))
    def run(job):
        target=Path(job['directory']);target.mkdir(parents=True);dump(target/'command.json',job)
        row=dict(id=job['id'],fixture=job['fixture'],requested_event_stage=job['requested_event_stage'])
        try:
            with (target/'run.log').open('w') as log:
                done=subprocess.run(job['command'],cwd=snapshot,env=dict(os.environ,**job['environment']),
                                    stdout=log,stderr=subprocess.STDOUT,timeout=1800)
            if done.returncode:raise RuntimeError('runner exit '+str(done.returncode))
            stem=target/'rollout/rollout';result=json.loads(stem.with_suffix('.json').read_text())
            audit=json.loads((target/'metrics/audit_manifest.json').read_text())
            if audit['error'] or len(audit['episodes'])!=1:raise ValueError('Invalid physical audit')
            physical=audit['episodes'][0]
            if physical['samples']<int(23.99/physical['timestep_s']):raise ValueError('Incomplete substeps')
            desc=descriptor(result['scene'],result['panel_audit']['physical_panels'])
            if not same_geometry(desc,job['fixture']['physical_descriptor']):raise ValueError('Realized geometry differs from plan')
            contacts=result['panel_audit']['contacts'];external=[v for k,v in contacts.items() if k!='target_object_geom']
            upstream=any(set(v['bodies'])&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external)
            row.update(status='complete',task_success=bool(result['success']),strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                       actual_first_contact=result['contact'],actual_events=result['events'],physical=physical,
                       offline=offline_metrics(protocol,job,result),model_mjb_sha256=sha(stem.with_suffix('.mjb')),
                       trace_sha256=sha(stem.with_suffix('.npz')),result_sha256=sha(stem.with_suffix('.json')))
        except Exception as exc:row.update(status='execution_error',error=f'{type(exc).__name__}: {exc}')
        dump(target/'result.json',row);return row
    started=time.time();rows=[]
    dump(directory/'status.json',dict(status='running',pid=os.getpid(),started_unix=started,completed=0,total=12))
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(run,j) for j in protocol['jobs']]):
            row=future.result();rows.append(row);dump(directory/'results.json',rows)
            dump(directory/'status.json',dict(status='running',pid=os.getpid(),started_unix=started,completed=len(rows),total=12))
            print(json.dumps(dict(completed=len(rows),id=row['id'],status=row['status'],error=row.get('error'))),flush=True)
    pairs={}
    for fixture in protocol['fixtures']:
        part=[r for r in rows if r['fixture']['seed']==fixture['seed']]
        pairs[str(fixture['seed'])]=dict(complete=all(r['status']=='complete' for r in part),
                same_compiled_model=len({r.get('model_mjb_sha256') for r in part})==1)
    complete=all(r['status']=='complete' for r in rows) and all(p['same_compiled_model'] for p in pairs.values())
    dump(directory/'FINAL_RESULT.json',dict(rows=rows,paired_geometry=pairs,complete=complete))
    dump(directory/'status.json',dict(status='complete' if complete else 'finished_with_errors',pid=os.getpid(),completed=len(rows),total=12))
    if complete:dump(directory/'COMPLETE.json',dict(jobs=12,protocol_sha256=sha(args.protocol)))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path)
    p.add_argument('--base-protocol',type=Path);p.add_argument('--bank',type=Path)
    p.add_argument('--source',type=Path);p.add_argument('--menagerie',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.protocol:execute(args)
    else:
        if any(getattr(args,x) is None for x in ('base_protocol','bank','source','menagerie','output')):p.error('prepare requires all paths')
        prepare(args)


if __name__=='__main__':main()
