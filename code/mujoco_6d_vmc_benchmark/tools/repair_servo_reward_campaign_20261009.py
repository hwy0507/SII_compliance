"""One finite reward-repair transition, preserving physics and original deadline.

Prepare only after affected jobs drained. Rebuild the eight metric prefixes
with correct servo-time rewards, resume each exactly once, then hand the ten
jobs to the finite evaluation coordinator. The two task-reward jobs stay live.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import fcntl
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes
from run_baseline_repair_screen_20261008 import managed
from baseline_repair_reward_clock_20261009 import slew_cost_rows, SERVO_DT, TIME_BASE


def active(unit):
    p = subprocess.run(['systemctl','--user','is-active',unit],capture_output=True,text=True)
    assert p.returncode in (0,3,4)
    return p.returncode == 0


def prepare(root, patch_directory):
    assert not active('sii-r15-continuation-v2.service')
    assert not (root/'FINAL_MODEL_LOCK.json').exists()
    protocol = read(root/'PROTOCOL.json'); old = read(root/'RL_JOBS.json')
    affected = [j for j in old['jobs'] if j['reward']=='metric']; assert len(affected)==8
    plans = []
    for job in affected:
        output = Path(job['output']); s = read(output/'execution.json')
        assert s['status']=='complete' and not active(job['unit'])
        latest = max(s['checkpoint_rows'],key=lambda x:x['step']); cp = Path(latest['path'])
        assert latest['step']==s['steps'] and checkpoint_hashes(cp)==latest['hashes']
        base = output.parent; rebuild = base/'servo_clock_rebuild_v1'; continued = base/'continued_v9'
        assert not rebuild.exists() and not continued.exists()
        plans.append(dict(job=job,checkpoint=str(cp),checkpoint_hashes=latest['hashes'],
            old_execution_sha256=sha(output/'execution.json'),rebuild=str(rebuild),continued=str(continued),
            discarded_gradient_updates=s['updates'],
            unit='sii-r15-rl-'+job['family'].replace('_','-')+'-'+str(job['seed'])+'-servo.service'))
    # Independent empirical proof: physical timestamps vs native 250Hz output.
    native = next(p for p in plans if p['job']['family']=='parameter_impedance' and p['job']['seed']==2026100811)
    row = read(Path(native['job']['output'])/'execution.json')['rows'][0]; run = Path(row['run'])
    rates = np.asarray(read(run/'execution.json')['action_filter_config']['maximum_torque_rate_nmps'])
    with np.load(run/'rollout_metrics/substep_metrics.npz') as f:
        tau=f['qfrc_actuator'].astype(float);dt=f['dt'].astype(float)
    with np.load(run/'impedance_servo.npz') as f: servo=f['values']
    delta=np.diff(tau,axis=0)
    physical=float(np.sum(np.sum((delta/(dt[1:,None]*rates))**2,axis=1)*dt[1:])/55.)
    corrected=float(slew_cost_rows(tau,rates).sum())
    sdt=np.diff(servo[:,0]);sd=np.diff(servo[:,20:27],axis=0)
    independent=float(np.sum(np.sum((sd/(sdt[:,None]*rates))**2,axis=1)*sdt)/55.)
    np.testing.assert_allclose(corrected,independent,rtol=1e-6)
    np.testing.assert_allclose(physical/corrected,SERVO_DT/protocol['physics_dt_s'],rtol=1e-6)
    evidence=dict(created_utc=now(),run=str(run),physics_dt_s=protocol['physics_dt_s'],
        servo_dt_s=SERVO_DT,old_smooth_cost=physical,corrected_smooth_cost=corrected,
        independently_reconstructed_servo_cost=independent,old_inflation_factor=physical/corrected,
        max_old_normalized_physical_rate=float(np.max(abs(delta)/(dt[1:,None]*rates))),
        max_actual_servo_rate=float(np.max(abs(sd)/(sdt[:,None]*rates))),
        hashes={str(p):sha(p) for p in [run/'rollout_metrics/substep_metrics.npz',run/'impedance_servo.npz',run/'RL_INTERVALS.json']},
        finding='Physics-step derivative of zero-order-held motor torque inflates cost by80 and invalidates old7*remaining/horizon bound. Use4ms executed update changes and ceil remaining updates.',
        unchanged=['physics','actor inputs','executed actions','gate','torque/speed limits','classical selection','heldout seal'])
    write(root/'SERVO_CLOCK_DIAGNOSTIC.json',evidence)
    source=root/'source_v9'
    shutil.copytree(root/'source_v8',source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    patches=list(patch_directory.glob('*.py'));assert patches
    for p in patches:shutil.copy2(p,source/'tools'/p.name)
    hashes={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and p.suffix in ('.py','.json')}
    write(root/'SOURCE_V9_HASHES.json',hashes)
    write(root/'SERVO_CLOCK_REPAIR_PLAN.json',dict(registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),
        diagnostic_sha256=sha(root/'SERVO_CLOCK_DIAGNOSTIC.json'),source=str(source),source_hashes=hashes,
        training_cutoff_unchanged_utc='2026-10-08T22:00:00+00:00',overall_deadline_utc=protocol['dispatch_deadline_utc'],
        old_jobs_sha256=sha(root/'RL_JOBS.json'),plans=plans,unaffected=[j for j in old['jobs'] if j['reward']=='office_task'],
        policy='Fresh learner reconstruction on exactly retained off-policy data, no teacher labels/BC or repeated physics. Discarded optimizer work is reported separately.'))
    write(root/'continuation_v2/SUPERSEDED.json',dict(time_utc=now(),reason='Confirmed servo/physics reward-clock mismatch',
        next_source=str(source),old_execution_preserved=True,no_final_access=True))
    print('Prepared',source,'affected',len(plans),flush=True)


def rebuild_and_resume(root, source, plan, log_directory):
    job=plan['job']; label=job['family']+'_'+str(job['seed'])
    assert not active(job['unit']) and checkpoint_hashes(Path(plan['checkpoint']))==plan['checkpoint_hashes']
    assert sha(Path(job['output'])/'execution.json')==plan['old_execution_sha256']
    command=[sys.executable,str(source/'tools/audit_rebuild_repair_reward_20261008.py'),
        '--checkpoint',plan['checkpoint'],'--output',plan['rebuild'],'--rebuild']
    receipt=log_directory/(label+'.json')
    write(receipt,dict(status='rebuilding',started_utc=now(),command=command,plan=plan))
    with (log_directory/(label+'.log')).open('x') as log:
        rc=subprocess.run(managed(source,command,'sii-r15-servo-rebuild-'+label.replace('_','-')),
                          stdout=log,stderr=subprocess.STDOUT).returncode
    if rc:
        write(receipt,dict(status='failed_preserved',returncode=rc,ended_utc=now(),plan=plan))
        raise RuntimeError(label+' rebuild failed; original evidence preserved')
    rebuilt=Path(plan['rebuild']);state=read(rebuilt/'execution.json');assert state['status']=='complete'
    checkpoint=state['checkpoint_rows'][0];assert checkpoint_hashes(Path(checkpoint['path']))==checkpoint['hashes']
    assert read(rebuilt/'PROTOCOL.json')['torque_slew_time_base']==TIME_BASE
    command=[sys.executable,str(source/'tools/train_baseline_repair_rl_20261008.py'),
        '--root',str(root),'--output',plan['continued'],'--parameter-source',job['parameter_source'],
        '--reward','metric','--seed',str(job['seed']),'--steps','200000','--resume-checkpoint',checkpoint['path']]
    if job['controller']:command+=['--controller',job['controller']]
    assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-10-08T22:00:00+00:00')
    assert not Path(plan['continued']).exists() and not active(plan['unit'])
    launch=[x for x in managed(source,command,plan['unit'].removesuffix('.service')) if x not in ('--wait','--pipe','--collect')]
    subprocess.run(launch,check=True)
    started=time.monotonic()
    while not (Path(plan['continued'])/'execution.json').exists():
        assert time.monotonic()-started<120., 'Replacement did not initialize'
        time.sleep(2)
    s=read(Path(plan['continued'])/'execution.json');assert s['status']=='running'
    new=dict(job,output=plan['continued'],unit=plan['unit'],already_running=True,
        reward_rebuild_receipt=str(receipt),discarded_gradient_updates=plan['discarded_gradient_updates'])
    write(receipt,dict(status='rebuilt_and_resumed',ended_utc=now(),checkpoint=checkpoint,
        reward_audit_sha256=sha(rebuilt/'REWARD_AUDIT.json'),new_job=new,physics_rerun=False))
    return new


def run(root):
    lock=(root/'.servo_reward_repair.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=read(root/'SERVO_CLOCK_REPAIR_PLAN.json');source=Path(plan['source'])
    assert plan['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert datetime.now(timezone.utc)<datetime.fromisoformat(plan['training_cutoff_unchanged_utc'])
    assert not active('sii-r15-continuation-v2.service')
    for name,digest in plan['source_hashes'].items():assert sha(source/name)==digest
    directory=root/'servo_reward_repair_v1';directory.mkdir(exist_ok=False)
    write(directory/'execution.json',dict(status='running',started_utc=now(),plan_sha256=sha(root/'SERVO_CLOCK_REPAIR_PLAN.json')))
    results=[];failures=[]
    # Start the larger historical direct prefix first; other fresh prefixes
    # have zero optimizer updates and resume promptly on the second worker.
    ordered=sorted(plan['plans'],key=lambda p:p['discarded_gradient_updates'],reverse=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(rebuild_and_resume,root,source,p,directory) for p in ordered]
        for f in as_completed(futures):
            try:results.append(f.result())
            except Exception as exc:failures.append(repr(exc))
    if failures:
        write(directory/'execution.json',dict(status='failed_preserved',failures=failures,resumed=results))
        raise RuntimeError(failures)
    jobs=results+plan['unaffected'];assert len(jobs)==10
    registration=root/'RL_JOBS_CORRECTED.json'
    write(registration,dict(registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),jobs=jobs,
        correction_plan_sha256=sha(root/'SERVO_CLOCK_REPAIR_PLAN.json'),no_physics_rerun=True))
    command=[sys.executable,str(source/'tools/continue_baseline_repair_campaign_20261008.py'),
        '--root',str(root),'--source',str(source),'--attempt','continuation_v3','--resume-jobs',str(registration)]
    assert not active('sii-r15-continuation-v3.service') and not (root/'continuation_v3').exists()
    subprocess.run([x for x in managed(source,command,'sii-r15-continuation-v3') if x not in ('--wait','--pipe','--collect')],check=True)
    write(directory/'execution.json',dict(status='complete',ended_utc=now(),resumed=results,unaffected=plan['unaffected'],
        continuation='sii-r15-continuation-v3.service',final_comparison_still_pending=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--prepare-from',type=Path);a=p.parse_args()
    if a.prepare_from:prepare(a.root.resolve(),a.prepare_from.resolve())
    else:run(a.root.resolve())
