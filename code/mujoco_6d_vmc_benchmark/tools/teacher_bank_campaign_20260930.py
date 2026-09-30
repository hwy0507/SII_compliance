"""Resumable, single-simulator teacher search and 3 x 1000 fixture collection."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

from teacher_bank_design_20260930 import CATEGORIES, SEED, DT, DURATION, decode, design, propose, sha, warm_points, write

REPO = Path(os.environ.get('SII_TEACHER_RESEARCH_ROOT',Path(__file__).resolve().parents[1])).resolve()
DEFAULT = REPO/'outputs/teacher_bank_three_domains_20260930_v6'
SERVER = 'arm1@192.168.31.70'
REMOTE_BASE = '/home/arm1/sii_shared/SII_compliance/runs/main'
ASSETS = REPO/'outputs/canonical_rl_assets_20260923/menagerie'
METHODS = ('vmc','admittance','impedance')
DEADLINE = 1790776096  # 2026-09-30 13:48:16 UTC, user-authorized 10-hour budget


def controller_config(x, method):
    if method=='vmc':return decode(x)
    from teacher_bank_classical_20260930 import decode as classical_decode
    return classical_decode(x,method)


def initial_points(seed,method,count=8):
    from teacher_bank_classical_20260930 import SEARCH_DIMENSIONS
    return warm_points(seed,count=count,dimensions=7 if method=='vmc' else SEARCH_DIMENSIONS[method],vmc_reference=method=='vmc')


def prepare(root):
    import mujoco
    if (root/'plan.json').exists():return
    if mujoco.__version__!='3.11.0':raise RuntimeError('MuJoCo 3.11.0 required')
    if root.exists() and any(root.iterdir()):raise RuntimeError('Nonempty unregistered directory')
    root.mkdir(parents=True,exist_ok=True)
    source=root/'source';source.mkdir()
    shutil.copytree(REPO/'scripts',source/'scripts',ignore=shutil.ignore_patterns('__pycache__','outputs','*.log'))
    (source/'tools').mkdir()
    for path in (REPO/'tools').glob('teacher_bank_*_20260930.py'):
        shutil.copy2(path,source/'tools'/path.name)
    reference=REPO/'outputs/teacher_repair_followup_20260930/corner/velocity025_stiff2/rollout.npz'
    fixtures=design(reference)
    write(root/'fixtures.json',fixtures)
    write(root/'plan.json',dict(schema=1,seed=SEED,train_per_category=1000,validation_per_category=100,
        categories=CATEGORIES,dt=DT,duration_s=DURATION,policy_dt_s=.04,formal=False,
        search_candidates_per_category=6,warm_candidates=3,anchor_indices=[0,333,666],
        methods=METHODS,deadline_utc='2026-09-30T13:48:16Z',deadline_epoch=DEADLINE,
        collection_candidates_per_fixture=1,validation_candidates_per_category=1,
        max_search_rollouts=162,max_collection_attempts=9000,max_validation_rollouts=27,
        validation_indices=[0,1,2],validation_before_collection=True,
        budget_revision='Before optimization: v4 full rollout measured 98.3s compute plus archive; 3 initial + 3 BO candidates per method/category, 3 validation fixtures/category then paired collection until deadline.',
        max_total_attempts=9198,wall_clock_budget_overrides_attempt_maxima=True,
        score='RMSE/.05 + .3*max_joint_torque_ratio + .1*retreat_start/55',
        promotion='All search anchors must pass task, unchanged evaluator strict, actual contact and replay/actuator audit.',
        selection='One locked feasibility-first controller per category/method, including explicitly infeasible best observed baselines; only audited feasible VMC trajectories enter labels.',
        raw_data_target='1000 accepted independent training trajectories per category; report any shortfall without replacing failed scenes.',
        validation='100 defined per category; first 3 per category budgeted this window, one locked teacher; no tuning on validation; old heldouts unopened',
        observation='canonical48D; VMC uses estimated wrench; admittance uses encoders/load/nominal twist/error and FK; impedance uses encoders/nominal twist/error and FK. Scene fields are simulator-only.',
        server=SERVER,remote=REMOTE_BASE+'/'+root.name,local_compute_host=socket.gethostname(),python=sys.executable,
        mujoco_version=mujoco.__version__,assets=str(ASSETS),nominal_reference=str(reference),nominal_reference_sha256=sha(reference),
        fixtures_sha256=sha(root/'fixtures.json'),
        sources={str(p.relative_to(source)):sha(p) for p in source.rglob('*.py')},
        base_git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
        source_is_uncommitted_snapshot=True,created=time.time(),memory_max_bytes=3*1024**3,threads=1))
    print(json.dumps({'prepared':str(root),'train':3000,'validation':300}),flush=True)


def verify(root):
    plan=json.loads((root/'plan.json').read_text())
    if sha(root/'fixtures.json')!=plan['fixtures_sha256']:raise RuntimeError('Fixture plan changed')
    for name,digest in plan['sources'].items():
        if sha(root/'source'/name)!=digest:raise RuntimeError('Frozen source changed: '+name)
    return plan


def archive(root, relative):
    """Verify a dedicated incoming directory before publishing it; no deletion."""
    local=root/relative
    manifest={str(p.relative_to(local)):sha(p) for p in local.rglob('*') if p.is_file() and p.name!='archive_manifest.json'}
    write(local/'archive_manifest.json',manifest)
    if not root.name.replace('_','').isalnum() or any(part in ('..','') for part in Path(relative).parts):raise ValueError('Invalid archive namespace')
    remote=REMOTE_BASE+'/'+root.name+'/'+relative
    incoming='/home/arm1/sii_shared/SII_compliance/incoming/'+root.name+'/'+relative
    subprocess.run(['ssh','-o','BatchMode=yes',SERVER,'mkdir -p '+incoming],check=True,timeout=30)
    subprocess.run(['rsync','-a','--checksum',str(local)+'/',SERVER+':'+incoming+'/'],check=True,timeout=900)
    code="""import hashlib,json,sys
from pathlib import Path
src,dst=map(Path,sys.argv[1:]);entries=json.loads((src/'archive_manifest.json').read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
for name,expected in entries.items():
 if digest(src/name)!=expected:raise RuntimeError('Incoming hash mismatch: '+name)
if dst.exists():
 for name,expected in entries.items():
  if not (dst/name).is_file() or digest(dst/name)!=expected:raise RuntimeError('Existing archive differs: '+name)
else:
 dst.parent.mkdir(parents=True,exist_ok=True);src.rename(dst)
print('VERIFIED',len(entries),str(dst))
"""
    # Paths are fixed program-generated strings, not user-supplied shell fragments.
    subprocess.run(['ssh','-o','BatchMode=yes',SERVER,'python3 - '+incoming+' '+remote],input=code,text=True,check=True,timeout=300)
    return SERVER+':'+remote


def process_identity(pid, proc_root=Path('/proc')):
    """Read Linux process identity without signaling or trusting PID alone."""
    if isinstance(pid,bool) or not isinstance(pid,int) or pid<=0:
        raise RuntimeError('Invalid saved PID; cannot establish process identity')
    path=Path(proc_root)/str(pid)
    try:
        fields=(path/'stat').read_text().rsplit(')',1)[1].split()
        command=[v.decode(errors='surrogateescape') for v in (path/'cmdline').read_bytes().split(b'\0') if v]
        boot=(Path(proc_root)/'sys/kernel/random/boot_id').read_text().strip()
    except FileNotFoundError:
        if not path.exists():return None
        raise RuntimeError('Incomplete process identity; refusing recovery')
    except (OSError,IndexError,ValueError) as error:
        raise RuntimeError('Cannot inspect saved process safely') from error
    return dict(pid=pid,start_ticks=int(fields[19]),boot_id=boot,command=command,
                alive=fields[0] not in ('Z','X'))


def stale_execution_evidence(execution, expected_command, proc_root=Path('/proc')):
    """Return evidence only when the previous child is conclusively absent.

    The exact request command is also scanned for the Popen-before-PID-write
    crash window. A live matching request blocks even when a PID was reused.
    """
    if execution.get('host',socket.gethostname())!=socket.gethostname():
        raise RuntimeError('Execution belongs to another host; cannot prove it stopped')
    pid=execution.get('pid')
    current=process_identity(pid,proc_root) if pid is not None else None
    stored=execution.get('process_identity')
    if current and current['alive']:
        if current['command']==expected_command:
            raise RuntimeError('Prior rollout is alive; do not restart')
        if stored and all(current[k]==stored.get(k) for k in ('pid','start_ticks','boot_id')):
            raise RuntimeError('Prior process identity is alive with changed argv; do not restart')
    # Restrict scans to our uid. Unreadable own-process metadata is uncertainty,
    # not proof that a simulator is absent.
    for path in Path(proc_root).iterdir():
        if not path.name.isdecimal():continue
        try:
            if path.stat().st_uid!=os.getuid():continue
            identity=process_identity(int(path.name),proc_root)
        except FileNotFoundError:
            continue
        if identity and identity['alive'] and identity['command']==expected_command:
            raise RuntimeError('Matching rollout request is alive; do not restart')
    return dict(saved_pid=pid,saved_identity=stored,observed_identity=current,
                reason='prior_process_absent_or_reaped_or_pid_reused',checked_at=time.time(),
                host=socket.gethostname())


def resolve_attempt_recovery(root, relative):
    """Preserve stale folders byte-for-byte; retry in a distinct linked path.

    Infrastructure failures never become optimizer observations. Only stale
    running/interrupted executions get a fresh attempt on explicit resumption.
    """
    root=Path(root)
    mapping_path=root/'recovery_records'/(relative+'.json')
    mapping=json.loads(mapping_path.read_text()) if mapping_path.exists() else dict(
        origin_relative=relative,active_relative=relative,history=[])
    if mapping['origin_relative']!=relative:raise RuntimeError('Recovery mapping mismatch')
    active=mapping['active_relative'];folder=root/active
    if not folder.exists() or not any(folder.iterdir()):return active
    execution_path=folder/'execution.json'
    execution=json.loads(execution_path.read_text()) if execution_path.exists() else dict(
        status='interrupted',host=socket.gethostname())
    expected=[sys.executable,str(root/'source/tools/teacher_bank_rollout_20260930.py'),
              '--root',str(root),'--request',str(folder/'request.json')]
    recorded=execution.get('command',expected)
    if recorded[1:]!=expected[1:]:raise RuntimeError('Execution command/request identity mismatch')
    # Also inspect completed records: audit.json can appear before child exit.
    evidence=stale_execution_evidence(execution,recorded)
    status=execution.get('status')
    if status=='completed' and execution.get('returncode')==0:
        if not (folder/'audit.json').is_file():raise RuntimeError('Completed execution has no audit; infrastructure failure')
        return active
    if status not in ('running','interrupted'):
        raise RuntimeError('Infrastructure failure requires diagnosis; not an optimization sample: '+active)
    retry_index=len(mapping['history'])+1
    retry=f'recovery_attempts/{relative}/retry{retry_index:04d}'
    if (root/retry).exists():raise RuntimeError('Recovery target already exists; refusing overwrite')
    mapping['history'].append(dict(source_relative=active,retry_relative=retry,
        prior_status=status,execution_sha256=sha(execution_path) if execution_path.exists() else None,
        evidence=evidence,preserved_without_modification=True))
    mapping['active_relative']=retry
    write(mapping_path,mapping)
    return retry


def attempt(root, relative, fixture, x, phase, archive_enabled, method='vmc'):
    relative=resolve_attempt_recovery(root,relative)
    folder=root/relative
    if (folder/'audit.json').exists():
        result=json.loads((folder/'audit.json').read_text())
    else:
        if time.time()>=DEADLINE:
            write(root/'deadline_reached.json',dict(stopped_dispatch=True,time=time.time(),next_attempt=relative))
            raise SystemExit('10-hour deadline reached; no new simulation dispatched')
        if (folder/'execution.json').exists():
            raise RuntimeError('Prior execution was not safely resolved: '+relative)
        if shutil.disk_usage(root).free<40*1024**3:raise RuntimeError('Less than 40 GiB local free space')
        request=dict(fixture=fixture,method=method,teacher=controller_config(x,method),x=x,phase=phase,plan_sha256=sha(root/'plan.json'))
        write(folder/'request.json',request)
        cmd=[sys.executable,str(root/'source/tools/teacher_bank_rollout_20260930.py'),'--root',str(root),'--request',str(folder/'request.json')]
        env=os.environ.copy();env.update({k:'1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
        env['MUJOCO_MENAGERIE_PATH']=str(ASSETS)
        execution=dict(command=cmd,status='running',started=time.time(),host=socket.gethostname(),plan_sha256=sha(root/'plan.json'))
        write(folder/'execution.json',execution)
        with (folder/'run.log').open('w') as log:
            child=subprocess.Popen(cmd,cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT)
            execution['pid']=child.pid
            execution['process_identity']=process_identity(child.pid)
            write(folder/'execution.json',execution)
            try:rc=child.wait(timeout=7200)
            except subprocess.TimeoutExpired:
                child.terminate()
                try:child.wait(timeout=20)
                except subprocess.TimeoutExpired:child.kill();child.wait()
                rc=124
        execution.update(status='completed' if rc==0 else 'failed',returncode=rc,finished=time.time())
        write(folder/'execution.json',execution)
        if rc:
            if archive_enabled:
                write(root/'archive_receipts'/relative/'receipt.json',dict(
                    verified_path=archive(root,relative),verified_at=time.time(),execution_failed=True))
            raise RuntimeError('Execution failed; stop instead of launching repeated broken jobs: '+relative)
        result=json.loads((folder/'audit.json').read_text())
    result['folder']=relative
    if archive_enabled:
        marker=root/'archive_receipts'/relative/'receipt.json'
        if not marker.exists():write(marker,dict(verified_path=archive(root,relative),verified_at=time.time()))
    print(json.dumps({k:result.get(k) for k in ('folder','eligible','failure_reasons','rmse_m','peak_torque_nm','peak_speed_mps')}),flush=True)
    return result


def check_paired_models(root,phase,rows):
    """A shared scene seed is insufficient: verify compiled world identity."""
    groups={}
    for row in rows:
        groups.setdefault(row['fixture_id'],[]).append(row)
    checks=[]
    for fixture_id,group in groups.items():
        methods=[row['method'] for row in group]
        if len(methods)!=len(set(methods)):raise RuntimeError('Duplicate method in paired group')
        hashes={row['model_sha256'] for row in group}
        if len(hashes)!=1:raise RuntimeError('Paired methods compiled different worlds: '+fixture_id)
        checks.append(dict(fixture_id=fixture_id,methods=methods,model_sha256=next(iter(hashes)),
                           complete=set(methods)==set(METHODS)))
    write(root/'paired_model_checks'/(phase+'.json'),checks)
    return checks


def run(root, mode, archive_enabled):
    plan=verify(root);fixtures=json.loads((root/'fixtures.json').read_text())
    lock=(root/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    # Inspect other known simulator commands as well as our per-campaign lock.
    process_lines=subprocess.check_output(['ps','-eo','pid,args'],text=True).splitlines()
    tokens=('validate_office_apparatus_v5_20260917.py','teacher_repair_campaign_20260930.py --child','teacher_bank_rollout_20260930.py --root')
    if any(any(t in line for t in tokens) for line in process_lines):raise RuntimeError('Another local simulator is active')
    train={c:[f for f in fixtures if f['category']==c and f['split']=='train'] for c in CATEGORIES}
    if archive_enabled:
        if not (root/'source_archived.json').exists():
            path=archive(root,'source');metadata=root/'metadata';metadata.mkdir(exist_ok=True)
            for name in ('plan.json','fixtures.json'):shutil.copy2(root/name,metadata/name)
            archive(root,'metadata');write(root/'source_archived.json',dict(path=path))
    if mode in ('pilot','pilot-active'):
        categories=CATEGORIES if mode=='pilot' else CATEGORIES[1:]
        rows=[attempt(root,f'pilot/{c}/{method}',train[c][0],initial_points(SEED,method)[0],'pilot',archive_enabled,method) for c in categories for method in METHODS]
        check_paired_models(root,mode,rows)
        write(root/(mode+'_summary.json'),dict(rows=rows,eligible=sum(r['eligible'] for r in rows),not_full_dataset=True))
        return
    bank={};histories={f'{c}/{m}':[] for c in CATEGORIES for m in METHODS}
    # Round robin: the deadline cannot give one method the entire budget first.
    for index in range(plan['search_candidates_per_category']):
        for ci,category in enumerate(CATEGORIES):
            paired=[]
            for method in METHODS:
                key=f'{category}/{method}';history=histories[key];warm=initial_points(SEED+ci,method,plan['warm_candidates'])
                decision=root/f'search/{key}/c{index:02d}/decision.json'
                if decision.exists():x=json.loads(decision.read_text())['x']
                else:
                    x=warm[index] if index<len(warm) else propose(history,SEED+ci*100+index)
                    write(decision,dict(x=x,algorithm='latin_hypercube' if index<len(warm) else 'constrained_gp_bo',history_count=len(history)))
                rows=[attempt(root,f'search/{key}/c{index:02d}/{i}',train[category][i],x,'search',archive_enabled,method) for i in plan['anchor_indices']]
                paired.extend(rows)
                history.append(dict(x=x,constraint=max(r['constraint'] for r in rows),score=sum(r['score'] for r in rows)/len(rows),index=index))
                write(root/f'search/{key}/history.json',history)
                ranked=sorted(history,key=lambda r:(max(0.,r['constraint']),r['score']))
                bank[key]=[dict(ranked[0],anchor_feasible=ranked[0]['constraint']<=0)]
                write(root/'teacher_bank.json',bank)
            check_paired_models(root,f'search/{category}/c{index:02d}',paired)
    missing=[key for key in bank if not bank[key][0]['anchor_feasible']]
    write(root/'anchor_feasibility.json',dict(infeasible_method_categories=missing,
        note='All baselines still evaluated with their locked best observed candidate; no infeasible trajectory promoted to ESN labels.'))
    validation=[]
    # Complete a predeclared validation subset before the large data collection.
    # Its results never enter selection or change the locked teacher bank.
    for ci,category in enumerate(CATEGORIES):
        subset=[f for f in fixtures if f['split']=='validation' and f['category']==category]
        for index in plan['validation_indices']:
            fixture=subset[index];paired=[]
            for method in METHODS:
                row=attempt(root,f'validation/{fixture["id"]}/{method}',fixture,bank[f'{category}/{method}'][0]['x'],'validation',archive_enabled,method)
                paired.append(row);validation.append(row)
                write(root/'validation_results.json',validation)
            check_paired_models(root,f'validation/{fixture["id"]}',paired)
    selected=[]
    for i in range(1000):
        for category in CATEGORIES:
            fixture=train[category][i]
            rows=[attempt(root,f'collection/{fixture["id"]}/{method}',fixture,bank[f'{category}/{method}'][0]['x'],'collection',archive_enabled,method) for method in METHODS]
            check_paired_models(root,f'collection/{fixture["id"]}',rows)
            winner=rows[0] if rows[0]['eligible'] else None
            selected.append(dict(fixture_id=fixture['id'],category=category,selected=winner,baseline_results=rows,
                                 attempted=[r['folder'] for r in rows],failures=[r['failure_reasons'] for r in rows]))
            write(root/'dataset_index.json',selected)
            write(root/'status.json',dict(attempted_environments=len(selected),accepted={c:sum(r['category']==c and r['selected'] is not None for r in selected) for c in CATEGORIES},target_per_class=1000))
    accepted={c:sum(r['category']==c and r['selected'] is not None for r in selected) for c in CATEGORIES}
    write(root/'complete.json',dict(accepted=accepted,target_met=all(n>=1000 for n in accepted.values()),
        validation_eligible=sum(r['eligible'] for r in validation),validation_total=len(validation),
        esn_started=False,failures_retained=True,finished=time.time()))
    if archive_enabled:
        reports=root/'final_reports';reports.mkdir(exist_ok=True)
        for name in ('teacher_bank.json','dataset_index.json','status.json','validation_results.json','complete.json'):
            shutil.copy2(root/name,reports/name)
        archive(root,'final_reports')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','pilot','pilot-active','run'));p.add_argument('--root',type=Path,default=DEFAULT)
    p.add_argument('--archive',action='store_true');a=p.parse_args();root=a.root.resolve()
    if a.mode=='prepare':prepare(root)
    else:run(root,a.mode,a.archive)
