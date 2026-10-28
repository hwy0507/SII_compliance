"""Independently audit only actual collection attempts in a locked terminal snapshot.

No simulation, parameter selection, dataset export, or unique-label counting.
Registered-but-unrun conditions are reported as unrun, never as audited cases.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

import numpy as np

import teacher_bank_validation_audit_20260930 as audit
from teacher_bank_spark_collection_20260930 import verify_locked_review


def terminal_contract(review):
    if (review.get('snapshot_kind')!='terminal_evidence'
            or review.get('snapshot_consistency',{}).get('stable') is not True
            or review.get('terminal_basis',{}).get('explicit_marker') is not True
            or review.get('terminal_basis',{}).get('active_attempts_present') is not False):
        raise ValueError('Stable explicit terminal snapshot without active attempts required')


def registered_collection(plan,fixtures):
    by_id={}
    for fixture in fixtures:
        if fixture['id'] in by_id:raise ValueError('Duplicate registered fixture ID')
        by_id[fixture['id']]=fixture
    result={}
    for category in plan['categories']:
        for index in range(plan['train_per_category']):
            identity=f'{category}_train_{index:04d}'
            fixture=by_id.get(identity)
            if fixture is None or fixture['split']!='train' or fixture['category']!=category:
                raise ValueError('Missing or wrong-split preregistered training fixture: '+identity)
            for method in plan['methods']:
                result[f'collection/{identity}/{method}']=(fixture,method)
    if len(result)!=plan['max_collection_attempts']:raise ValueError('Collection plan budget mismatch')
    return result


def attempted_collection(review,registered):
    selected={}
    for row in review['status']['attempts']:
        folder=row['folder'];phase=row.get('phase')
        if phase!='collection' and not folder.startswith('collection/'):continue
        if phase!='collection' or folder not in registered:
            raise ValueError('Unregistered collection path or mixed phase: '+folder)
        if folder in selected:raise ValueError('Duplicate actual collection attempt: '+folder)
        fixture,method=registered[folder]
        if (row.get('split')!='train' or row.get('fixture_id')!=fixture['id']
                or row.get('category')!=fixture['category'] or row.get('method')!=method):
            raise ValueError('Snapshot attempt differs from preregistered training fixture')
        if row.get('execution_status')=='running':raise ValueError('Running attempt in terminal snapshot')
        selected[folder]=row
    return selected


def counts(rows,planned):
    statuses=Counter(row['status'] for row in rows)
    if len(rows)>planned:raise ValueError('More attempts than registered collection plan')
    return dict(registered_plan_cases=planned,actual_attempts=len(rows),
        registered_not_attempted=planned-len(rows),dynamic_audited=statuses['audited'],
        invalid_initial_scene=statuses['invalid_initial_scene'],incomplete=statuses['incomplete'],
        audit_failed=statuses['audit_failed'],statuses=dict(statuses))


def duration_groups(rows):
    """Do not mix aborted/truncated records with the common full task horizon."""
    groups={}
    for row in rows:
        if row['status']!='audited':continue
        stratum='full_task_horizon' if row['full_task_horizon_completed'] else 'abort_or_truncated'
        key=(row['category'],row['method'],stratum)
        groups.setdefault(key,[]).append(row)
    result=[]
    for (category,method,stratum),group in sorted(groups.items()):
        result.append(dict(category=category,method=method,duration_stratum=stratum,
            count=len(group),eligible=sum(r['eligible'] for r in group),
            durations_s=[r['metrics']['actual_duration_s'] for r in group],
            mean_metrics={k:float(np.mean([r['metrics'][k] for r in group])) for k in
                ('rmse_m','peak_torque_nm','peak_speed_mps')},
            scope='Descriptive per-method means over all audited outcomes in this duration stratum, including physical/task/exposure failures and possibly incompletely paired fixtures. Not a fair cross-method ranking or unique-label count; formal comparisons use the fair_comparison common, completely paired 55 s cohort.'))
    return result


def run(root,review_path,review_sha,bank_sha,output):
    started=datetime.now(timezone.utc).isoformat();monotonic=time.monotonic()
    root,review_path,output=(Path(p).resolve() for p in (root,review_path,output))
    metadata=review_path.parent/'metadata_snapshot'
    if output.exists() or any(output==p or p in output.parents for p in (root,review_path.parent)):
        raise ValueError('Require new output outside raw run and terminal snapshot')
    if audit.sha(review_path)!=review_sha:raise ValueError('Caller terminal review hash mismatch')
    review=audit.read(review_path);terminal_contract(review)
    if Path(review['original_run']).resolve()!=root:raise ValueError('Raw root differs from terminal review')
    review,plan,bank=verify_locked_review(review_path,review_sha,metadata)
    if review['metadata_sha256']['teacher_bank.json']!=bank_sha:raise ValueError('Bank hash differs from snapshot')
    actual_plan,actual_bank=audit.verify_lock(root,bank_sha)
    if actual_plan!=plan or actual_bank!=bank:raise ValueError('Raw plan/bank differs from locked snapshot')
    hashes=review['metadata_sha256'];verified={}
    def pin_metadata(relative):
        part=Path(relative)
        if part.is_absolute() or '..' in part.parts:raise ValueError('Unsafe metadata path')
        if relative not in hashes:raise ValueError('Metadata absent from frozen snapshot: '+relative)
        source=metadata/part;raw=root/part
        if source.is_symlink() or raw.is_symlink() or audit.sha(source)!=hashes[relative] or audit.sha(raw)!=hashes[relative]:
            raise ValueError('Snapshot/raw metadata hash mismatch: '+relative)
        verified[relative]=hashes[relative]
        return audit.read(source)
    for name in ('plan.json','teacher_bank.json','fixtures.json'):pin_metadata(name)
    if audit.sha(root/'fixtures.json')!=plan['fixtures_sha256']:raise ValueError('Fixture manifest hash mismatch')
    for name,digest in plan['sources'].items():
        if audit.sha(root/'source'/name)!=digest:raise ValueError('Frozen source drift: '+name)
    for name,digest in plan['source_inputs'].items():
        if audit.sha(root/'source_inputs'/name)!=digest:raise ValueError('Frozen source input drift: '+name)
    registered=registered_collection(plan,audit.read(metadata/'fixtures.json'))
    attempted=attempted_collection(review,registered)
    raw_folders={str(p.parent.relative_to(root)) for p in (root/'collection').glob('*/*/request.json')}
    if raw_folders!=set(attempted):raise ValueError('Actual collection request inventory differs from terminal snapshot')
    for folder in attempted:
        pin_metadata(folder+'/request.json')
        for name in ('execution.json','audit.json','command.json','archive_manifest.json'):
            relative=folder+'/'+name
            if (root/relative).exists():pin_metadata(relative)
    sys.path.insert(0,str(root/'source/tools'));sys.path.insert(0,str(root/'source/scripts'))
    import mujoco
    if mujoco.__version__!=plan['mujoco_version']:raise ValueError('MuJoCo version differs')
    def forbidden(*args,**kwargs):raise RuntimeError('No MuJoCo integration permitted in collection audit')
    for name in ('mj_step','mj_step1','mj_step2'):setattr(mujoco,name,forbidden)
    spec=importlib.util.spec_from_file_location('frozen_collection_audit_runner',root/'source/tools/teacher_bank_rollout_20260930.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    rows=[];output.mkdir(parents=True)
    for folder in sorted(attempted):
        fixture,method=registered[folder]
        try:
            row=audit.audit_case(root,root/folder,fixture,method,bank[fixture['category']+'/'+method][0],
                                 plan,runner,expected_phase='collection')
            if row['status']=='skipped':row['status']='incomplete'
            if row['status']=='invalid_initial_scene':
                manifest=pin_metadata(folder+'/archive_manifest.json')
                if any(manifest.get(name)!=digest for name,digest in row['raw_sha256'].items()):
                    raise ValueError('Initial-rejection raw files differ from terminal-bound archive manifest')
        except Exception as error:
            row=dict(folder=str(root/folder),status='audit_failed',error_type=type(error).__name__,reason=str(error))
        row.update(relative_folder=folder,fixture_id=fixture['id'],category=fixture['category'],
                   method=method,phase='collection',split='train')
        rows.append(row);print(json.dumps(dict(folder=folder,status=row['status'])),flush=True);gc.collect()
    for name,digest in verified.items():
        if audit.sha(root/name)!=digest or audit.sha(metadata/name)!=digest:raise ValueError('Metadata changed during audit')
    if audit.sha(review_path)!=review_sha:raise ValueError('Terminal review changed during audit')
    pair_error=None
    try:paired=audit.paired_groups(rows,plan['methods'])
    except Exception as error:paired=[];pair_error=str(error)
    report=dict(scope='Independent collection audit of actual terminal attempts only; train split, locked bank, no simulation/tuning/unique-label claim.',
        root=str(root),terminal_review=str(review_path),terminal_review_sha256=review_sha,
        locked_bank_sha256=bank_sha,plan_sha256=hashes['plan.json'],fixtures_sha256=hashes['fixtures.json'],
        metadata_sha256_verified=verified,frozen_source_sha256=plan['sources'],source_inputs_sha256=plan['source_inputs'],
        audit_source_sha256={Path(p).name:audit.sha(Path(p)) for p in
            (__file__,audit.__file__,sys.modules[verify_locked_review.__module__].__file__,sys.modules[audit.sha.__module__].__file__)},
        audit_execution=dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),hostname=platform.node(),
            machine=platform.machine(),python_version=platform.python_version(),numpy_version=np.__version__,
            mujoco_version=mujoco.__version__,started_utc=started,audit_finished_utc=datetime.now(timezone.utc).isoformat(),
            elapsed_s=time.monotonic()-monotonic,thread_environment={k:os.environ.get(k) for k in
            ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},integration_guard=['mj_step','mj_step1','mj_step2']),
        accounting=counts(rows,len(registered)),duration_groups=duration_groups(rows),
        paired_fixtures=paired,pairing_error=pair_error,cases=rows,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        limitations=['Penetration verified against hashed metadata, not reconstructed from every substep contact.',
            'Repeated search/collection executions do not increase unique training labels; separate duplicate audit is required.',
            'No validation/heldout case is used as collection evidence. Aborted/truncated metrics are a separate duration stratum.'])
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:audit.sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--terminal-review',required=True,type=Path)
    parser.add_argument('--terminal-review-sha256',required=True)
    parser.add_argument('--locked-bank-sha256',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    run(args.root,args.terminal_review,args.terminal_review_sha256,args.locked_bank_sha256,args.output)


if __name__=='__main__':main()
