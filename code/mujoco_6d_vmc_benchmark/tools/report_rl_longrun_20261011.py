"""One-shot continuous development reporting and verified storage export.

No training, simulation, automatic restarts, final-test access, or Git writes.
Keep missing methods pending and early task failures in the denominator.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

from overnight_baseline_coordinator_20261010 import read, write
from archive_tool_campaign_20261002 import make


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verified_node(entry, identities, cache):
    path=Path(entry['audit']);digest=sha(path)
    if digest != entry['audit_sha256']:raise ValueError('Audit digest changed: '+str(path))
    if digest in cache:return cache[digest]
    audit=read(path);rows=audit['rows']
    if audit['status']!='passed' or audit['completed']!=8 or len(rows)!=8:
        raise ValueError('Incomplete development audit')
    if {r['condition'] for r in rows}!=identities:raise ValueError('Development identity mismatch')
    if audit['steps']!=entry['steps'] or any(audit[k]!=sum(bool(r[k]) for r in rows) for k in ('task','strict')):
        raise ValueError('Summary inconsistent with audit rows')
    cp=audit['checkpoint']
    for relative,digest_cp in cp['hashes'].items():
        if sha(Path(cp['path'])/relative)!=digest_cp:raise ValueError('Checkpoint changed: '+relative)
    result=dict(scheduled_limit=entry['scheduled_limit'],steps=audit['steps'],evaluated=8,
        task=audit['task'],strict=audit['strict'],
        full_horizon=sum(r['full_horizon'] for r in rows),
        stages={stage:sum(r['stage']==stage for r in rows) for stage in sorted({r['stage'] for r in rows})},
        means={k:statistics.mean(r[k] for r in rows) for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')},
        checkpoint=cp['path'],checkpoint_files_verified=len(cp['hashes']),audit=str(path),audit_sha256=digest)
    cache[digest]=result
    return result


def census(root, cache):
    reg=read(root/'REGISTRATION.json');state=read(root/'execution.json')
    if sha(root/'REGISTRATION.json')!=state['registration_sha256']:raise ValueError('Registration changed')
    parent=Path(reg['parent_root'])
    if sha(parent/'CONDITIONS.json')!=reg['condition_sha256']:raise ValueError('Condition file changed')
    ids={c['id'] for c in read(parent/'CONDITIONS.json')['conditions'] if c['role']=='development'}
    methods=[]
    for job in reg['jobs']:
        name=job['name'];history=[verified_node(e,ids,cache) for e in state.get('histories',{}).get(name,[])]
        training=[]
        for limit in reg['training_limits']:
            path=root/(name+f'_step{limit:06d}')/'execution.json'
            if path.exists():
                value=read(path);done=[r for r in value.get('rows',[]) if 'result' in r]
                training.append(dict(limit=limit,steps=value['steps'],status=value['status'],
                    completed_training_episodes=len(done),training_task=sum(r['result']['task_success'] for r in done),
                    training_strict=sum(r['result']['strict_success'] for r in done),
                    checkpoint_steps=[c['step'] for c in value.get('checkpoint_rows',[])]))
        methods.append(dict(method=name,development=history,training=training,
            status='development_available' if history else 'pending_development'))
    return dict(time_utc=datetime.now(timezone.utc).isoformat(),coordinator_status=state['status'],
        registration_sha256=state['registration_sha256'],dispatch_deadline_utc=reg['dispatch_deadline_utc'],
        methods=methods,failures=state.get('failures',[]),final_test_reads=0,new_physics_steps=0,
        interpretation='Latest audited development nodes; differing budgets are explicit. Training outcomes are not policy evaluation. Missing evaluation is pending, never 0/0 or a failure.')


def markdown(report):
    lines=['# RL development progress', '', 'Snapshot UTC: '+report['time_utc'], '',
           '| Method | Training steps | Audited steps | Task | Strict | RMSE mm | Mean episode peak torque Nm | Mean episode peak speed m/s |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in report['methods']:
        train=str(m['training'][-1]['steps']) if m['training'] else 'not resumed'
        if m['development']:
            d=m['development'][-1];v=d['means']
            cells=[m['method'],train,str(d['steps']),f"{d['task']}/8",f"{d['strict']}/8",
                   f"{v['rmse_mm']:.3f}",f"{v['peak_torque_nm']:.3f}",f"{v['peak_speed_mps']:.4f}"]
        else:cells=[m['method'],train]+['pending']*6
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['',report['interpretation'],'','Remaining work: complete registered nodes, independent seeds and final uniform comparison. No convergence claim.','']
    return '\n'.join(lines)


def export(root, output, report, number):
    """Small immutable report/audit package only; never claims raw traces uploaded."""
    evidence=output/f'export_{number:03d}'/'evidence';evidence.mkdir(parents=True)
    write(evidence/'REPORT.json',report)
    (evidence/'REPORT.md').write_text(markdown(report))
    shutil.copy2(root/'REGISTRATION.json',evidence/'REGISTRATION.json')
    shutil.copy2(__file__,evidence/Path(__file__).name)
    for method in report['methods']:
        for node in method['development']:
            shutil.copy2(node['audit'],evidence/(method['method']+f"_{node['scheduled_limit']}.audit.json"))
    make(evidence)
    name=output.name+f'_{number:03d}'
    incoming='/home/arm1/sii_shared/SII_compliance/incoming/'+name
    published='/home/arm1/sii_shared/SII_compliance/runs/main/'+name+'/evidence'
    remote_tool='/home/arm1/sii_shared/SII_compliance/runs/main/rl_convergence_v2_setup_20261010/evidence/source/tools/archive_tool_campaign_20261002.py'
    subprocess.run(['rsync','-a','--timeout=30','-e','ssh -o BatchMode=yes -o ConnectTimeout=10',str(evidence)+'/',
                    'arm1@192.168.31.70:'+incoming+'/'],check=True,timeout=120,capture_output=True,text=True)
    done=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','arm1@192.168.31.70',
        'python3',remote_tool,'--root',incoming,'--publish',published],check=True,timeout=120,capture_output=True,text=True)
    receipt=json.loads(done.stdout);write(evidence.parent/'REMOTE_VERIFICATION.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run-root','monitor-root','outer-root','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--archive-server',action='store_true')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    write(a.output/'REGISTRATION.json',dict(started_utc=datetime.now(timezone.utc).isoformat(),
        authority='2026-10-11 user requests continuous overnight baseline work; preserve live jobs',
        run_root=str(a.run_root.resolve()),source_sha256=sha(__file__),server_compute=False,
        scope='Read-only census, node-triggered storage export, cooperative stop on monitoring failure; no restart/extra simulation'))
    with (a.output/'reporter.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cache={};previous=None;number=0
        try:
            while True:
                report=census(a.run_root,cache)
                write(a.output/'LATEST.json',report)
                (a.output/'LATEST.md').write_text(markdown(report))
                outer=read(a.outer_root/'execution.json')
                terminal=outer['status'] in ('failed_preserved','complete_review_required','stopped_at_deadline','stopped_requested')
                monitor_path=a.monitor_root/'LATEST.json'
                monitor_failed=(a.monitor_root/'ALERT.json').exists() or time.time()-monitor_path.stat().st_mtime>300
                if monitor_failed and not terminal:
                    marker=a.run_root/'STOP_REQUESTED'
                    if not marker.exists():write(marker,dict(reason='Monitoring failed or stale over5min; preserve current episode then checkpoint, no blind unattended continuation'))
                    write(a.output/'ALERT.json',dict(reason='monitor_failed',cooperative_stop=str(marker)))
                    raise RuntimeError('Monitoring failed; cooperative stop requested')
                key=(tuple(n['audit_sha256'] for m in report['methods'] for n in m['development']),terminal)
                if key!=previous:
                    number+=1
                    if a.archive_server:
                        try:export(a.run_root,a.output,report,number)
                        except (subprocess.SubprocessError,OSError,ValueError) as exc:
                            write(a.output/f'EXPORT_FAILURE_{number:03d}.json',dict(error=repr(exc),training_untouched=True))
                    print(json.dumps(dict(time=report['time_utc'],node_count=len(key[0]),terminal=terminal)),flush=True)
                    previous=key
                if terminal:
                    write(a.output/'CLOSE.json',report)
                    if outer['status']=='failed_preserved':raise RuntimeError('Experiment failure preserved; see CLOSE and original execution')
                    return
                time.sleep(60)
        except BaseException as exc:
            if not (a.output/'ALERT.json').exists():write(a.output/'ALERT.json',dict(error=repr(exc)))
            raise


if __name__=='__main__':main()
