"""Sequential full-length three-view gallery from completed saved trajectories."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT,sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,nargs='+',required=True)
    p.add_argument('--labels',nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--allow-aborted',action='store_true',help='Include aborted short histories without padding or changing their failure')
    a=p.parse_args();assert len(a.runs)==len(a.labels)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    files=['render_office_threeview_20260929.py','audit_tool_media_20261002.py','archive_tool_campaign_20261002.py']
    for name in files:shutil.copy2(ROOT/'tools'/name,out/name)
    state=dict(status='running',started_utc=now(),source_sha256={n:sha(out/n) for n in files},rows=[],argv=sys.argv)
    write(out/'execution.json',state)
    try:
        for index,(run,label) in enumerate(zip(a.runs,a.labels)):
            assert datetime.now(timezone.utc)<datetime(2026,10,3,2,11,36,tzinfo=timezone.utc)
            record=json.loads((run/'execution.json').read_text());assert record['status']=='complete'
            summary=json.loads((run/'rollout.json').read_text())
            if not summary['full_task_horizon_completed']:
                assert a.allow_aborted and summary['abort_reason'] and not summary['task_success'] and not summary['strict_success']
                label+=' [ABORT: '+summary['abort_reason']+']'
            target=out/(f'{index:02d}_'+run.name)
            row=dict(run=str(run.resolve()),label=label,output=str(target),trace_sha256=sha(run/'rollout.npz'),
                     task_success=summary['task_success'],strict_success=summary['strict_success'],commands=[])
            state['rows'].append(row);write(out/'execution.json',state)
            commands=[[sys.executable,str(out/files[0]),'--rollout',str(run/'rollout.npz'),
                       '--output',str(target),'--label',label,'--scene-label','office-validation-v6',
                       '--stride','1','--fps','25','--gif-stride','5'],
                      [sys.executable,str(out/files[1]),str(target),*(['--allow-aborted'] if a.allow_aborted else [])]]
            for j,cmd in enumerate(commands):
                row['commands'].append(cmd);write(out/'execution.json',state)
                with (out/f'{index:02d}_{j}.log').open('x') as log:
                    subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
            row['media_audit_sha256']=sha(target/'MEDIA_AUDIT.json');write(out/'execution.json',state)
        state['status']='complete'
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
