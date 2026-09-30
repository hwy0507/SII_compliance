"""Prepare an independently audited Spark collection shard; never retune.

Preparation and inspection do not integrate physics. Dynamic launch requires
an explicitly pinned locked-bank review, static compatibility evidence and
``run-worker --start``. The parent run and its immutable sources stay intact.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time

CATEGORIES = ('passive_corner', 'active_short', 'active_long')
METHODS = ('vmc', 'admittance', 'impedance')
DEADLINE = 1790776096
WORKERS = 3


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def pin(path,expected):
    if sha(path)!=expected:raise RuntimeError('Pinned evidence changed: '+str(path))


def verify_locked_review(review_path,expected_sha,metadata):
    """Consume the existing terminal-review schema, never invented success."""
    pin(review_path,expected_sha);review=read(review_path);metadata=Path(metadata)
    close=review['closeout']
    if review['snapshot_consistency'].get('stable') is not True:
        raise RuntimeError('Review snapshot was not stable')
    for key in ('bank_certified_locked','all_candidate_summaries_and_rank_verified','source_manifest_verified'):
        if close.get(key) is not True:raise RuntimeError('Uncertified search: '+key)
    for name in ('teacher_bank.json','plan.json','fixtures.json'):
        pin(metadata/name,review['metadata_sha256'][name])
    plan=read(metadata/'plan.json');bank=read(metadata/'teacher_bank.json')
    if plan['search_candidates_per_category']!=6:raise RuntimeError('Expected exactly six search candidates')
    expected={f'{category}/{method}' for category in CATEGORIES for method in METHODS}
    groups=close['reconstructed_groups']
    if set(groups)!=expected or set(bank)!=expected:raise RuntimeError('Expected all nine method/category groups')
    for key,group in groups.items():
        if (group.get('all_budget_candidates_verified') is not True or
                group.get('recorded_selection_matches_independent_rank') is not True or
                len(group.get('candidates',[]))!=6):
            raise RuntimeError('Incomplete candidate certification: '+key)
        if bank[key]!=[group['recorded_selection']]:raise RuntimeError('Bank differs from reviewed selection')
        best=group['best_complete_candidate']
        if best['x']!=bank[key][0]['x'] or not group.get('selected_controller_config'):
            raise RuntimeError('Missing reviewed controller parameters')
    return review,plan,bank


def verify_assets(assets,manifest):
    """Require both actually used robot families; don't silently accept Panda-only."""
    assets=Path(assets);expected=read(manifest)
    families={Path(name).parts[0] for name in expected}
    if not {'franka_fr3','franka_emika_panda'}<=families:
        raise RuntimeError('Complete FR3 plus Panda-hand asset manifest required')
    for name,digest in expected.items():
        part=Path(name)
        if part.is_absolute() or '..' in part.parts:raise RuntimeError('Unsafe asset relative path')
        pin(assets/part,digest)
    return dict(files_verified=len(expected),manifest_sha256=sha(manifest),checked_epoch=time.time())


def verify_static_review(path,expected_sha,parent_plan_sha,asset_manifest_sha):
    """Byte mismatches remain blocked for the parent agent's separate review."""
    pin(path,expected_sha);evidence=read(path)
    if (evidence.get('compatible_for_collection') is not True or
            evidence.get('no_dynamic_steps') is not True or
            evidence.get('target_architecture')!=platform.machine() or
            evidence.get('parent_plan_sha256')!=parent_plan_sha or
            evidence.get('asset_manifest_sha256')!=asset_manifest_sha):
        raise RuntimeError('Static compatibility review is missing or not applicable')
    checks=evidence.get('model_checks',[])
    required={f'{category}_train_{index:04d}' for category in CATEGORIES for index in (0,337,671)}
    if {row.get('fixture_id') for row in checks}!=required or any(not row.get('reference_mjb_sha256') or
        row.get('reference_mjb_sha256')!=row.get('target_mjb_sha256') for row in checks):
        raise RuntimeError('Cross-host compiled model differs; remain in preparation state')
    return evidence


def shard_fixtures(fixtures,worker):
    if worker not in range(WORKERS):raise ValueError('Worker must be 0, 1 or 2')
    selected=[]
    for index in range(900,1000):
        for category in CATEGORIES:
            identity=f'{category}_train_{index:04d}'
            matches=[f for f in fixtures if f['id']==identity and f['split']=='train' and f['category']==category]
            if len(matches)!=1:raise RuntimeError('Missing/duplicate preregistered fixture: '+identity)
            if (index-900)%WORKERS==worker:selected.append(matches[0])
    return selected


def runtime():
    return dict(host=socket.gethostname(),architecture=platform.machine(),python=sys.version,
        executable=sys.executable,packages={name:importlib.metadata.version(name) for name in ('mujoco','numpy','scipy')})


def prepare(root,parent,review_path,review_sha,metadata,assets,asset_manifest,static_review,static_sha):
    root,parent,metadata=Path(root).resolve(),Path(parent).resolve(),Path(metadata).resolve()
    review,plan,bank=verify_locked_review(review_path,review_sha,metadata)
    for name,digest in plan['sources'].items():pin(parent/'source'/name,digest)
    for name,digest in plan['source_inputs'].items():pin(parent/'source_inputs'/name,digest)
    asset_evidence=verify_assets(assets,asset_manifest)
    static=verify_static_review(static_review,static_sha,sha(metadata/'plan.json'),sha(asset_manifest))
    versions=runtime()
    if versions['architecture']!='aarch64' or versions['packages']['mujoco']!='3.11.0':
        raise RuntimeError('Spark ARM MuJoCo 3.11.0 runtime required')
    if time.time()>=DEADLINE:raise RuntimeError('Original ten-hour budget has expired')
    if root.exists() and any(root.iterdir()):raise FileExistsError('New empty supplemental run required')
    fixtures=read(metadata/'fixtures.json')
    for worker in range(WORKERS):shard_fixtures(fixtures,worker)
    root.mkdir(parents=True,exist_ok=True)
    (root/'source').symlink_to(parent/'source',target_is_directory=True)
    (root/'source_inputs').symlink_to(parent/'source_inputs',target_is_directory=True)
    evidence=root/'evidence';evidence.mkdir()
    for source,name in ((review_path,'review.json'),(metadata/'teacher_bank.json','teacher_bank.json'),
        (metadata/'plan.json','parent_plan.json'),(metadata/'fixtures.json','fixtures.json'),
        (asset_manifest,'complete_asset_manifest.json'),(static_review,'static_review.json'),(__file__,'driver.py')):
        shutil.copy2(source,evidence/name)
    new=dict(schema=1,role='supplemental_collection_only_no_search_no_validation',parent_run=str(parent),
        parent_plan_sha256=sha(metadata/'plan.json'),parent_git_commit=plan['base_git_commit'],
        reviewed_bank_sha256=sha(metadata/'teacher_bank.json'),review_sha256=review_sha,
        static_review_sha256=static_sha,fixtures_sha256=sha(metadata/'fixtures.json'),
        asset_manifest_sha256=sha(asset_manifest),driver_sha256=sha(__file__),source_manifest=plan['sources'],
        paths=dict(parent_source=str(parent/'source'),parent_source_inputs=str(parent/'source_inputs'),
                   parent_local_assets=plan['assets'],runtime_assets=str(Path(assets).resolve()),
                   parent_local_python=plan['python'],runtime_python=sys.executable),
        runtime=versions,asset_verification=asset_evidence,deadline_epoch=DEADLINE,
        workers=WORKERS,threads_per_worker=1,memory_max_bytes=3*1024**3,
        fixture_indices=[900,999],paired_methods=METHODS,created_epoch=time.time(),
        duplicate_policy='Check parent archived requests before dispatch; races remain possible. Final merge de-duplicates fixture/method and reports cross-host sensitivity.',
        cross_host_numerics='Same MuJoCo/model bytes do not guarantee identical floating-point closed-loop trajectories across architectures or NumPy versions.',
        status='prepared_only_not_started')
    write(root/'plan.json',new)
    return new


def verify_prepared(root):
    root=Path(root);plan=read(root/'plan.json');e=root/'evidence'
    for name,key in (('review.json','review_sha256'),('teacher_bank.json','reviewed_bank_sha256'),
        ('parent_plan.json','parent_plan_sha256'),('fixtures.json','fixtures_sha256'),
        ('complete_asset_manifest.json','asset_manifest_sha256'),('static_review.json','static_review_sha256'),
        ('driver.py','driver_sha256')):pin(e/name,plan[key])
    pin(__file__,plan['driver_sha256'])
    for name,digest in plan['source_manifest'].items():pin(root/'source'/name,digest)
    if runtime()!=plan['runtime']:raise RuntimeError('Supplemental runtime changed')
    verify_assets(plan['paths']['runtime_assets'],e/'complete_asset_manifest.json')
    return plan


def active_simulators(proc_root=Path('/proc')):
    """Count active sim processes; paused PIDs are reported but never resumed."""
    active,paused=[],[]
    tokens=('teacher_bank_rollout_','train_official_simba','simba_reward','validate_office_apparatus',
            'teacher_repair','progress_diagnostic')
    for path in Path(proc_root).iterdir():
        if not path.name.isdecimal():continue
        try:
            if path.stat().st_uid!=os.getuid():continue
            args=(path/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            state=(path/'stat').read_text().rsplit(')',1)[1].split()[0]
        except FileNotFoundError:continue
        if any(token in args for token in tokens) and 'python' in args:
            if state in ('T','t'):paused.append(int(path.name))
            elif state not in ('Z','X'):active.append(int(path.name))
    return dict(active=active,paused=paused)


def parent_attempts(parent,fixture_id):
    """Archive visibility is incomplete for running local jobs; never promise exclusion."""
    results=[]
    for request in (Path(parent)/'collection'/fixture_id).glob('*/request.json'):
        if read(request).get('fixture',{}).get('id')==fixture_id:results.append(str(request))
    return results


def worker_resource_limits(proc_cgroup=Path('/proc/self/cgroup'),sys_cgroup=Path('/sys/fs/cgroup')):
    """Require the coordinating systemd worker to enforce the declared budget."""
    entries=[line.split(':',2)[2] for line in Path(proc_cgroup).read_text().splitlines() if line.startswith('0::')]
    if len(entries)!=1:raise RuntimeError('A unified cgroup with explicit worker resource limits is required')
    path=Path(sys_cgroup)/entries[0].lstrip('/')
    memory=(path/'memory.max').read_text().strip()
    quota,period=(path/'cpu.max').read_text().split()
    if memory=='max' or int(memory)>3*1024**3 or quota=='max' or int(quota)>int(period):
        raise RuntimeError('Worker requires MemoryMax<=3GiB and CPUQuota<=100%')
    return dict(cgroup=str(path),memory_max_bytes=int(memory),cpu_quota=int(quota),cpu_period=int(period))


def run_worker(root,worker,start=False):
    if not start:raise RuntimeError('Dynamic execution requires explicit --start from coordinating agent')
    root=Path(root).resolve();plan=verify_prepared(root)
    limits=worker_resource_limits()
    if worker not in range(WORKERS):raise ValueError('Worker must be 0..2')
    worker_dir=root/f'workers/{worker}';worker_dir.mkdir(parents=True,exist_ok=True)
    lock=(worker_dir/'worker.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fixtures=shard_fixtures(read(root/'evidence/fixtures.json'),worker)
    review=read(root/'evidence/review.json');parent=Path(plan['parent_run'])
    dispatch_lock=(root/'dispatch.lock').open('w')
    for fixture in fixtures:
        group=worker_dir/fixture['id'];rows=[]
        seen=parent_attempts(parent,fixture['id'])
        if seen:
            write(group/'skipped_parent_overlap.json',dict(requests=seen,checked_epoch=time.time()))
            continue
        for method in METHODS:
            folder=group/method
            if folder.exists():raise RuntimeError('Prior attempt exists; inspect before resuming, never auto retry')
            if time.time()>=DEADLINE:
                write(group/'partial_deadline.json',dict(completed_methods=[r['method'] for r in rows],
                    stopped_dispatch=True,next_method=method,time=time.time()))
                return
            verify_assets(plan['paths']['runtime_assets'],root/'evidence/complete_asset_manifest.json')
            chosen=review['closeout']['reconstructed_groups'][fixture['category']+'/'+method]
            request=dict(fixture=fixture,method=method,teacher=chosen['selected_controller_config'],
                x=chosen['best_complete_candidate']['x'],phase='supplemental_collection',
                plan_sha256=sha(root/'plan.json'),parent_plan_sha256=plan['parent_plan_sha256'],
                review_sha256=plan['review_sha256'],no_new_optimization=True)
            write(folder/'request.json',request)
            command=[sys.executable,str(root/'source/tools/teacher_bank_rollout_20260930.py'),
                     '--root',str(root),'--request',str(folder/'request.json')]
            env=dict(os.environ,MUJOCO_MENAGERIE_PATH=plan['paths']['runtime_assets'],
                OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                PYTHONDONTWRITEBYTECODE='1')
            execution=dict(status='running',command=command,host=socket.gethostname(),started=time.time(),
                method=method,worker=worker,plan_sha256=sha(root/'plan.json'),worker_resource_limits=limits)
            with (folder/'run.log').open('w') as log:
                # Serialize our dispatches only; never signal unrelated PIDs.
                fcntl.flock(dispatch_lock,fcntl.LOCK_EX)
                try:
                    processes=active_simulators()
                    if len(processes['active'])>=4:raise RuntimeError('No free Spark simulation slot')
                    if time.time()>=DEADLINE:
                        write(group/'partial_deadline.json',dict(completed_methods=[r['method'] for r in rows],
                            stopped_dispatch=True,next_method=method,time=time.time()))
                        return
                    execution['resource_check']=processes
                    write(folder/'execution.json',execution)
                    child=subprocess.Popen(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
                    execution['pid']=child.pid;write(folder/'execution.json',execution)
                finally:fcntl.flock(dispatch_lock,fcntl.LOCK_UN)
                # Existing rollout RLIMIT_AS is 3 GiB. Coordinator must also
                # launch each worker under MemoryMax=3G and CPUQuota=100%.
                code=child.wait()
            execution.update(status='completed' if code==0 else 'failed',returncode=code,finished=time.time())
            write(folder/'execution.json',execution)
            if code:raise RuntimeError('Rollout failed; this shard stops, all evidence retained')
            result=read(folder/'audit.json');rows.append(result)
        if len({r['model_sha256'] for r in rows})!=1:
            write(group/'model_mismatch.json',rows);raise RuntimeError('Paired methods compiled different models')
        write(group/'paired_result.json',dict(fixture_id=fixture['id'],methods=METHODS,rows=rows,
            parent_overlap_after=parent_attempts(parent,fixture['id']),paired_complete=True))


def reconcile(root,parent):
    """Count each completed fixture/method once; retain duplicate-host evidence."""
    root,parent=Path(root),Path(parent);entries={};duplicates=[];host_methods={}
    for host,paths in (('parent',parent.glob('collection/*/*/audit.json')),
                       ('supplemental',root.glob('workers/*/*/*/audit.json'))):
        for path in paths:
            execution=read(path.parent/'execution.json')
            if execution.get('status')!='completed' or execution.get('returncode')!=0:continue
            row=read(path);key=(row['fixture_id'],row['method'])
            host_methods.setdefault((key[0],host),set()).add(key[1])
            value=dict(host=host,path=str(path),eligible=row['eligible'],model_sha256=row['model_sha256'],
                       rmse_m=row['rmse_m'],peak_torque_nm=row['peak_torque_nm'],peak_speed_mps=row['peak_speed_mps'])
            if key in entries:duplicates.append(dict(fixture_id=key[0],method=key[1],first=entries[key],additional=value))
            else:entries[key]=value
    method_sets={}
    for fixture_id,method in entries:method_sets.setdefault(fixture_id,set()).add(method)
    result=dict(unique_fixture_method_count=len(entries),unique_fixture_count=len(method_sets),
        complete_paired_fixture_count=len({fixture for (fixture,host),v in host_methods.items() if v==set(METHODS)}),
        cross_host_duplicates=duplicates,partial_fixture_ids=[k for k,v in method_sets.items() if v!=set(METHODS)],
        incomplete_same_host_pairing=[fixture for fixture in method_sets
            if not any(host_methods.get((fixture,host),set())==set(METHODS) for host in ('parent','supplemental'))],
        precedence='Parent host result retained for duplicate fixture/method regardless of success; no cherry-picking',
        limitation='Only currently archived parent collection is visible; rerun after final parent archive before final claims')
    write(root/'reconciliation.json',result);return result


def main():
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for key in ('root','parent','review','metadata','assets','asset-manifest','static-review'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--review-sha',required=True);p.add_argument('--static-sha',required=True)
    p=sub.add_parser('run-worker');p.add_argument('--root',type=Path,required=True)
    p.add_argument('--worker',type=int,required=True);p.add_argument('--start',action='store_true')
    p=sub.add_parser('reconcile');p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path,required=True)
    a=parser.parse_args()
    if a.mode=='prepare':prepare(a.root,a.parent,a.review,a.review_sha,a.metadata,a.assets,a.asset_manifest,a.static_review,a.static_sha)
    elif a.mode=='run-worker':run_worker(a.root,a.worker,a.start)
    else:reconcile(a.root,a.parent)


if __name__=='__main__':main()
