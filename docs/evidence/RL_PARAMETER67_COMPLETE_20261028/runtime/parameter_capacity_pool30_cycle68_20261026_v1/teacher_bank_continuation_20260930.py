"""Continue a locked campaign without retrying invalid initial geometry.

Frozen search, source, plan and failure evidence remain unchanged. Only a precise
audit_initial rc=1 failure with no rollout/audit products may be classified and
skipped. Every other exception stops. All simulation still uses frozen attempt().
"""
import argparse
from datetime import datetime, timezone
import fcntl
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import time

from teacher_bank_spark_collection_20260930 import verify_locked_review, sha

DEADLINE = 1790776096
GEOMETRY_PREFIX = 'ValueError: Initial rigid body intersections: '


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path);path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n');temporary.replace(path)


def runtime():
    return dict(host=socket.gethostname(), python=sys.executable, python_version=sys.version,
        packages={name:importlib.metadata.version(name) for name in ('mujoco','numpy','scipy')})


def verify_search(review):
    count = 0
    for group in review['closeout']['reconstructed_groups'].values():
        for candidate in group['candidates']:
            anchors = candidate.get('anchors', [])
            if candidate.get('complete') is not True or len(anchors) != 3 or any(a.get('complete') is not True for a in anchors):
                raise RuntimeError('All 162 search executions must be certified complete')
            count += len(anchors)
    if count != 162:
        raise RuntimeError('Expected exactly 162 completed search executions')


def classify_geometry(folder, expected_source=None):
    """Return evidence only for the exact pre-integration audit_initial failure."""
    folder = Path(folder)
    execution = read(folder/'execution.json')
    if execution.get('status') != 'failed' or execution.get('returncode') != 1:
        raise RuntimeError('Not an audited rc1 initial-geometry failure')
    if any(folder.glob('rollout*')) or any((folder/name).exists() for name in ('audit.json','teacher_internal.npz','execution_chain.npz')):
        raise RuntimeError('Geometry skip prohibited when rollout or audit artifacts exist')
    lines = (folder/'run.log').read_text().strip().splitlines()
    frames=[match.groups() for line in lines if (match:=re.match(r'\s*File "([^"]+)", line \d+, in (\S+)$',line))]
    expected=Path(expected_source).resolve() if expected_source else None
    if (not lines or not lines[-1].startswith(GEOMETRY_PREFIX) or not frames
            or frames[-1][1]!='audit_initial'
            or Path(frames[-1][0]).name!='office_task_v4_20260917.py'
            or (expected is not None and Path(frames[-1][0]).resolve()!=expected)):
        raise RuntimeError('Failure is not the exact audit_initial geometry exception')
    intersections = json.loads(lines[-1][len(GEOMETRY_PREFIX):])
    if not isinstance(intersections,list) or not intersections or any(
        not isinstance(row.get('pair'),list) or len(row['pair']) != 2
        or any(not isinstance(name,str) for name in row['pair'])
        or type(row.get('depth_mm')) not in (int,float) or not 0 < row['depth_mm'] < float('inf')
        for row in intersections):
        raise RuntimeError('Malformed initial-geometry evidence')
    return dict(classification='invalid_initial_scene', intersections=intersections,
        execution_sha256=sha(folder/'execution.json'), log_sha256=sha(folder/'run.log'),
        no_rollout_or_audit=True, original_returncode=1, retried=False,
        metrics=None, success=None, reason='Initial rigid-body intersections before simulation; not a controller failure or optimizer observation')


def schedule(plan, fixtures, phase):
    by_id = {row['id']:row for row in fixtures}
    if phase == 'validation':
        for category in plan['categories']:
            subset = [row for row in fixtures if row['category']==category and row['split']=='validation']
            for index in plan['validation_indices']:
                fixture = subset[index]
                for method in plan['methods']:
                    yield f'validation/{fixture["id"]}/{method}', fixture, method
    else:
        for index in range(plan['train_per_category']):
            for category in plan['categories']:
                fixture = by_id[f'{category}_train_{index:04d}']
                for method in plan['methods']:
                    yield f'collection/{fixture["id"]}/{method}', fixture, method


def prepare(root, review_path, review_sha, metadata, output):
    root, output, metadata = Path(root).resolve(), Path(output).resolve(), Path(metadata).resolve()
    review_path = Path(review_path).resolve()
    if output.exists() or any(output.is_relative_to(p) for p in (root,metadata,review_path.parent)):
        raise RuntimeError('New independent continuation output directory required')
    review, plan, bank = verify_locked_review(review_path,review_sha,metadata)
    verify_search(review)
    if Path(review['original_run']).resolve()!=root:
        raise RuntimeError('Reviewed run mismatch')
    for name in ('plan.json','fixtures.json','teacher_bank.json'):
        if sha(root/name)!=review['metadata_sha256'][name]:raise RuntimeError('Live immutable input differs: '+name)
    for prefix, mapping in (('source',plan['sources']),('source_inputs',plan['source_inputs'])):
        for name,digest in mapping.items():
            if sha(root/prefix/name)!=digest:raise RuntimeError('Frozen source mismatch: '+name)
    environment=runtime()
    if environment['python']!=plan['python'] or environment['packages']['mujoco']!=plan['mujoco_version']:
        raise RuntimeError('Must prepare under the original frozen interpreter')
    if plan['deadline_epoch']!=DEADLINE:raise RuntimeError('Original deadline mismatch')
    evaluator_source=(root/'source/scripts/validate_office_apparatus_v5_20260917.py').read_text()
    if not (evaluator_source.index('    audit_initial(m,d)') < evaluator_source.index('            teacher=SixDVirtualDynamics({})')
            < evaluator_source.index('    for step_index in range(planned_steps):')):
        raise RuntimeError('Cannot establish pre-actor, pre-loop initial audit ordering')
    output.mkdir(parents=True)
    source=output/'source';source.mkdir()
    for name in ('teacher_bank_continuation_20260930.py','teacher_bank_spark_collection_20260930.py'):
        shutil.copy2(Path(__file__).with_name(name),source/name)
    shutil.copy2(review_path,output/'locked_review.json')
    # The referenced review snapshot is immutable and SHA-pinned; no large data copy.
    protocol=dict(schema=1,purpose=__doc__,root=str(root),metadata=str(metadata),review_sha256=review_sha,
        bank_sha256=review['metadata_sha256']['teacher_bank.json'],plan_sha256=review['metadata_sha256']['plan.json'],
        deadline_epoch=DEADLINE, runtime=environment, prepared_epoch=time.time(),
        prepared_utc=datetime.now(timezone.utc).isoformat(), prepare_argv=sys.argv,
        source_sha256={p.name:sha(p) for p in source.iterdir()},
        allow_geometry_skip_only=True, search_replayed=False, original_validation_summary_untouched=True,
        initial_audit_order=dict(source='scripts/validate_office_apparatus_v5_20260917.py',
            verified_before_actor_factory_and_physics_loop=True, factory_binding_source='tools/teacher_bank_rollout_20260930.py'),
        classification_policy='rc1 + exact final audit_initial geometry exception + no rollout/audit artifacts + verified archived failure; no other exception continuation',
        resource_limits=dict(threads=1,memory_max_bytes=3*1024**3))
    write(output/'protocol.json',protocol)
    return protocol


def check_resources(group=None):
    threads={}
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        if os.environ.get(key)!='1':raise RuntimeError('Require one thread: '+key)
        threads[key]=os.environ[key]
    if group is None:
        relative=next(line.split(':',2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        group=Path('/sys/fs/cgroup')/relative.lstrip('/')
    group=Path(group)
    limit=(group/'memory.max').read_text().strip()
    if limit=='max' or int(limit)>3*1024**3:raise RuntimeError('Require cgroup MemoryMax <= 3 GiB')
    swap=(group/'memory.swap.max').read_text().strip()
    if swap!='0':raise RuntimeError('Require original MemorySwapMax=0')
    cpu=group/'cpu.max'
    if cpu.exists():
        quota,period=cpu.read_text().split()
        if quota=='max' or int(quota)>int(period):raise RuntimeError('Require CPUQuota <= 100% when cpu controller is available')
        cpu_evidence=dict(cpu_controller_available=True,quota_enforced=True,quota_us=int(quota),period_us=int(period))
    else:
        cpu_evidence=dict(cpu_controller_available=False,quota_enforced=False,
            reason='cpu.max absent; CPU controller unavailable in this delegated cgroup. Load is bounded by single simulator and one-thread settings, not an enforced CPU quota.')
    return dict(cgroup=str(group),memory_max_bytes=int(limit),memory_swap_max_bytes=int(swap),
        thread_environment=threads,**cpu_evidence)


def reject_other_simulators(campaign):
    tokens=('teacher_bank_rollout_20260930.py','validate_office_apparatus_v5_20260917.py',
            'teacher_repair_campaign_20260930.py','teacher_bank_campaign_20260930.py')
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal() or int(path.name)==os.getpid():continue
        try:
            if path.stat().st_uid!=os.getuid():continue
            identity=campaign.process_identity(int(path.name))
        except FileNotFoundError:continue
        if identity and identity['alive'] and any(any(token in arg for token in tokens) for arg in identity['command']):
            raise RuntimeError('Another campaign/simulator process exists: '+str(path.name))


def dispatch(campaign, root, relative, fixture, method, x, phase):
    folder=root/relative
    expected=dict(fixture=fixture, method=method, teacher=campaign.controller_config(x,method),
                  x=x,phase=phase,plan_sha256=sha(root/'plan.json'))
    if (folder/'request.json').exists() and read(folder/'request.json')!=expected:
        raise RuntimeError('Existing request/config identity differs: '+relative)
    execution=read(folder/'execution.json') if (folder/'execution.json').exists() else None
    if execution and not (execution.get('status')=='completed' and execution.get('returncode')==0):
        expected_command=[sys.executable,str(root/'source/tools/teacher_bank_rollout_20260930.py'),
            '--root',str(root),'--request',str(folder/'request.json')]
        if execution.get('command')!=expected_command:raise RuntimeError('Failed execution command identity mismatch')
        campaign.stale_execution_evidence(execution,expected_command)
        evidence=classify_geometry(folder,root/'source/scripts/office_task_v4_20260917.py')
    else:
        try:
            row=campaign.attempt(root,relative,fixture,x,phase,True,method)
            return dict(folder=relative,classification='completed',audit=row,reused=execution is not None)
        except RuntimeError:
            if not (folder/'execution.json').exists():raise
            evidence=classify_geometry(folder,root/'source/scripts/office_task_v4_20260917.py')
    # Geometry exceptions are permitted only after the frozen driver archived them.
    receipt=root/'archive_receipts'/relative/'receipt.json'
    if not receipt.is_file() or read(receipt).get('verified_path')!=f'{campaign.SERVER}:{campaign.REMOTE_BASE}/{root.name}/{relative}':
        raise RuntimeError('Invalid-scene failure lacks a verified archive receipt')
    manifest=read(folder/'archive_manifest.json')
    for name,digest in manifest.items():
        if sha(folder/name)!=digest:raise RuntimeError('Archived failure evidence changed')
    for name in ('request.json','execution.json','run.log'):
        if name not in manifest:raise RuntimeError('Missing failure provenance hash')
    if read(folder/'request.json')!=expected:raise RuntimeError('Failed request identity mismatch')
    evidence.update(folder=relative,fixture_id=fixture['id'],method=method,phase=phase,
        archive_receipt_sha256=sha(receipt),files_sha256=manifest,server_raw_directory=read(receipt)['verified_path'])
    return evidence


def check_finished_pair(campaign, root, phase, fixture_id, rows):
    """Only reconcile after all registered methods have a completed/invalid record."""
    audits=[row['audit'] for row in rows if row['classification']=='completed']
    if not audits:
        return dict(fixture_id=fixture_id,methods=[],complete=False,all_invalid_initial_scene=True)
    hashes={row['model_sha256'] for row in audits}
    if len(hashes)!=1:raise RuntimeError('Completed pair model disagreement')
    model=next(iter(hashes));methods=[row['method'] for row in audits]
    expected=[dict(fixture_id=fixture_id,methods=methods,model_sha256=model,complete=set(methods)==set(campaign.METHODS))]
    identities=read(root/'fixture_model_identity.json')
    if fixture_id in identities and identities[fixture_id]['model_sha256']!=model:
        raise RuntimeError('Previously recorded fixture model differs')
    marker=root/'paired_model_checks'/f'{phase}/{fixture_id}.json'
    if marker.exists():
        previous=read(marker)
        if previous==expected:return expected[0]
        if len(previous)!=1 or previous[0]['fixture_id']!=fixture_id or previous[0]['model_sha256']!=model or not set(previous[0]['methods'])<=set(methods):
            raise RuntimeError('Existing pair metadata differs from completed method evidence')
    campaign.check_paired_models(root,f'{phase}/{fixture_id}',audits)
    return expected[0]


def original_deadline_exit(error, root, relative, now):
    marker=Path(root)/'deadline_reached.json'
    if str(error)!='10-hour deadline reached; no new simulation dispatched' or now<DEADLINE or not marker.is_file():
        return False
    value=read(marker)
    return value.get('stopped_dispatch') is True and value.get('next_attempt')==relative and value.get('time',0)>=DEADLINE


def run(output, start=False):
    if not start:raise RuntimeError('Explicit --start required; preparation never launches dynamics')
    output=Path(output).resolve();protocol=read(output/'protocol.json');root=Path(protocol['root'])
    if Path(__file__).resolve()!=output/'source/teacher_bank_continuation_20260930.py':
        raise RuntimeError('Run the frozen continuation source snapshot')
    for name,digest in protocol['source_sha256'].items():
        if sha(output/'source'/name)!=digest:raise RuntimeError('Continuation source changed')
    if runtime()!=protocol['runtime']:raise RuntimeError('Runtime differs from pinned preparation')
    review,plan,bank=verify_locked_review(output/'locked_review.json',protocol['review_sha256'],protocol['metadata'])
    verify_search(review)
    if sha(root/'teacher_bank.json')!=protocol['bank_sha256'] or sha(root/'plan.json')!=protocol['plan_sha256']:
        raise RuntimeError('Locked controller bank or plan changed')
    actual_resources=check_resources();sys.dont_write_bytecode=True
    os.environ['SII_TEACHER_RESEARCH_ROOT']=str(root.parent.parent)
    sys.path.insert(0,str(root/'source/tools'))
    spec=importlib.util.spec_from_file_location('frozen_continuation_campaign',root/'source/tools/teacher_bank_campaign_20260930.py')
    campaign=importlib.util.module_from_spec(spec);spec.loader.exec_module(campaign)
    campaign.verify(root)
    if campaign.DEADLINE!=DEADLINE:raise RuntimeError('Frozen deadline changed')
    lock=(root/'campaign.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    reject_other_simulators(campaign)
    state_path=output/'state.json'
    state=read(state_path) if state_path.exists() else dict(attempts={},status='running',started=time.time(),
        protocol_sha256=sha(output/'protocol.json'),command=sys.argv,invalid_scene_count=0)
    if state['protocol_sha256']!=sha(output/'protocol.json'):raise RuntimeError('Continuation protocol changed')
    state['actual_resources']=actual_resources
    write(state_path,state)
    fixtures=read(root/'fixtures.json')
    try:
        for phase in ('validation','collection'):
            for relative,fixture,method in schedule(plan,fixtures,phase):
                reject_other_simulators(campaign)
                row=dispatch(campaign,root,relative,fixture,method,bank[f'{fixture["category"]}/{method}'][0]['x'],phase)
                state['attempts'][relative]=row
                state.update(status='running',last_finished=time.time(),current_phase=phase,
                    invalid_scene_count=sum(r['classification']=='invalid_initial_scene' for r in state['attempts'].values()))
                write(state_path,state)
                if row['classification']=='invalid_initial_scene':
                    write(output/'invalid_scenes'/(relative+'.json'),row)
                if method==plan['methods'][-1]:
                    group=[state['attempts'][f'{phase}/{fixture["id"]}/{m}'] for m in plan['methods']]
                    pair=check_finished_pair(campaign,root,phase,fixture['id'],group)
                    write(output/'pair_accounting'/f'{phase}/{fixture["id"]}.json',dict(pair=pair,
                        method_statuses={m:r['classification'] for m,r in zip(plan['methods'],group)},
                        invalid_scenes_are_not_successes=True))
            write(output/(phase+'_summary.json'),dict(
                attempts=[r for name,r in state['attempts'].items() if name.startswith(phase+'/')],
                original_summary_not_modified=True,unique_training_labels_not_counted_here=True,
                note='Invalid scenes retain null metrics/success; completed audit outcomes preserved; repeated fixture identities require the separate label exporter.'))
            if phase=='validation':
                completed=[r for name,r in state['attempts'].items() if name.startswith('validation/') and r['classification']=='completed']
                invalid=[r for name,r in state['attempts'].items() if name.startswith('validation/') and r['classification']=='invalid_initial_scene']
                marker=dict(finished_epoch=time.time(),registered_attempts_accounted_for=len(completed)+len(invalid),
                    registered_total=len(list(schedule(plan,fixtures,'validation'))),completed_rollouts=len(completed),
                    invalid_initial_scene_attempts=len(invalid),all_registered_rollouts_completed=not invalid,
                    original_validation_results_unchanged=True,invalid_scenes_are_not_completed_rollouts=True)
                write(output/'validation_finished.json',marker)
                print(json.dumps(dict(event='validation_finished',**marker)),flush=True)
        state.update(status='complete',finished=time.time());write(state_path,state)
    except SystemExit as error:
        if not original_deadline_exit(error,root,relative,time.time()):
            state.update(status='stopped_on_unclassified_error',finished=time.time(),error=repr(error));write(state_path,state)
            raise
        state.update(status='deadline_reached',finished=time.time(),message=str(error));write(state_path,state)
    except BaseException as error:
        state.update(status='stopped_on_unclassified_error',finished=time.time(),error=repr(error));write(state_path,state)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('prepare')
    for name in ('root','review','metadata','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--review-sha',required=True)
    p=sub.add_parser('run');p.add_argument('--output',type=Path,required=True);p.add_argument('--start',action='store_true')
    args=parser.parse_args()
    if args.mode=='prepare':
        prepare(args.root,args.review,args.review_sha,args.metadata,args.output)
        print(json.dumps(dict(prepared=str(args.output),simulation_started=False,source_frozen=True)))
    else:run(args.output,args.start)


if __name__=='__main__':main()
