"""Continuous one-shot observation of real RL progress; never restarts jobs."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from overnight_baseline_coordinator_20261010 import read, write


def unit_state(unit):
    result = subprocess.run(['systemctl','--user','show',unit,'-p','ActiveState','-p','Result',
                             '-p','ExecMainStatus'],capture_output=True,text=True,check=True)
    return dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)


def snapshot(outer_root, run_root, unit):
    outer_path=outer_root/'execution.json'
    outer=read(outer_path) if outer_path.exists() else {}
    path=run_root/'execution.json'
    state=read(path) if path.exists() else {}
    service=unit_state(unit)
    failures=[]
    if outer.get('status')=='failed_preserved' or state.get('failures'):
        failures.append('Coordinator recorded failure, regardless of systemd exit status')
    terminal=outer.get('status') in ('complete_review_required','stopped_at_deadline','failed_preserved')
    if not terminal and service.get('ActiveState') in ('inactive','failed'):
        failures.append('Coordinator is not active and has no terminal receipt')
    active=[]
    for lane,row in state.get('active',{}).items():
        target=Path(row['target']); train=target/'execution.json'
        worker=unit_state(row['unit'])
        item=dict(lane=lane,target=str(target),service=worker,training=row.get('training',False))
        if train.exists():
            value=read(train)
            item.update({k:value.get(k) for k in ('status','steps','episodes','updates')})
            item['checkpoints']=[dict(step=c['step'],path=c['path']) for c in value.get('checkpoint_rows',[])]
            if value.get('status')=='failed_preserved':failures.append('Trainer failed: '+str(target))
            item['progress_age_s']=max(0,time.time()-train.stat().st_mtime)
        else:
            progress=target/'rollout.progress.json'
            if progress.exists():
                try:
                    value=read(progress)
                    item.update(simulated_s=value.get('time_s'),stage=value.get('stage'))
                    item['progress_age_s']=max(0,time.time()-progress.stat().st_mtime)
                except (json.JSONDecodeError,FileNotFoundError):
                    item['progress_read']='writer_in_progress'
            elif row.get('started_utc'):
                item['progress_age_s']=time.time()-datetime.fromisoformat(row['started_utc']).timestamp()
        if item.get('progress_age_s',0)>1200:
            failures.append('No recorded worker progress for 20 minutes: '+str(target))
        active.append(item)
    return dict(time_utc=datetime.now(timezone.utc).isoformat(),outer_status=outer.get('status'),
                service=service,run_status=state.get('status'),active=active,
                histories=state.get('histories',{}),failures=failures,terminal=terminal,
                new_physics_steps=0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('outer-root','run-root','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--unit',required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    try:
        with (args.output/'events.jsonl').open('x') as log:
            while True:
                value=snapshot(args.outer_root,args.run_root,args.unit)
                write(args.output/'LATEST.json',value)
                log.write(json.dumps(value)+'\n');log.flush()
                print(json.dumps(value),flush=True)
                if value['failures']:
                    write(args.output/'ALERT.json',value)
                    raise RuntimeError('; '.join(value['failures']))
                if value['terminal']:
                    write(args.output/'CLOSE.json',value);return
                time.sleep(30)
    except BaseException as exc:
        if not (args.output/'ALERT.json').exists():
            write(args.output/'ALERT.json',dict(error=repr(exc)))
        raise


if __name__=='__main__':main()
