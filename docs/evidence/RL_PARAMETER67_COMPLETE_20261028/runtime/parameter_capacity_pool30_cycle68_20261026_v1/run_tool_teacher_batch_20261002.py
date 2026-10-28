"""Sequential frozen-source batches inside the explicit four-hour budget."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT,sha,write,now

DEADLINE=datetime(2026,10,2,13,1,55,tzinfo=timezone.utc)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--batch',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--reuse-audited',type=Path,help='Reuse completed physical rows with independently verified recovery receipts')
    args=p.parse_args();run=args.output.resolve()
    run.mkdir(parents=True,exist_ok=False)
    with (ROOT/'outputs/tool_teacher_four_hour_20261002.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        batch=json.loads(args.batch.read_text())
        runtime=run/'source';runtime.mkdir()
        for name in ['scripts','assets']:
            shutil.copytree(ROOT/name,runtime/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
        (runtime/'tools').mkdir()
        shutil.copy2(ROOT/'tools/optimize_tool_contact_20261002.py',runtime/'tools/optimize_tool_contact_20261002.py')
        shutil.copy2(__file__,runtime/'tools'/Path(__file__).name)
        shutil.copy2(args.batch,run/'batch.json')
        source={str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()}
        state=dict(started_utc=now(),deadline_utc=DEADLINE.isoformat(),status='running',
                   batch_sha256=sha(args.batch),reference_sha256=sha(args.reference),source=source,rows=[])
        write(run/'execution.json',state)
        for name,config in batch['candidates'].items():
            if args.reuse_audited:
                previous=args.reuse_audited/name
                receipt=previous/'RECOVERY_AUDIT.json'
                if receipt.is_file():
                    recovered=json.loads(receipt.read_text())
                    assert recovered['physical_complete_and_audited']
                    assert json.loads((previous/'config.json').read_text())==config
                    assert sha(previous/'rollout.npz')==recovered['trace_sha256']
                    state['rows'].append(dict(candidate=name,reused_audited=str(previous.resolve()),
                        recovery_sha256=sha(receipt),audit=json.loads((previous/'AUDIT.json').read_text())))
                    write(run/'execution.json',state);continue
            if (DEADLINE-datetime.now(timezone.utc)).total_seconds()<240:
                state['status']='deadline_no_new_dispatch';break
            config_path=run/(name+'.json');write(config_path,config)
            out=run/name
            command=[sys.executable,str(runtime/'tools/optimize_tool_contact_20261002.py'),
                     '--reference',str(args.reference.resolve()),'--output',str(out),'--config',str(config_path)]
            if name in batch.get('checkpoint_by_candidate',{}):
                command+=['--checkpoint',str(Path(batch['checkpoint_by_candidate'][name]).resolve())]
            if name in batch.get('memory_ablation_by_candidate',{}):
                command+=['--memory-ablation',batch['memory_ablation_by_candidate'][name]]
            if batch.get('contact_audit',False):command+=['--contact-audit']
            row=dict(candidate=name,started_utc=now(),command=command);state['rows'].append(row);write(run/'execution.json',state)
            with (run/(name+'.log')).open('x') as log:
                process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,cwd=runtime)
            row.update(returncode=process.returncode,ended_utc=now())
            if (out/'AUDIT.json').exists():row['audit']=json.loads((out/'AUDIT.json').read_text())
            if process.returncode:
                state['status']='worker_failure_preserved';break
            write(run/'execution.json',state)
        else:state['status']='complete'
        state['ended_utc']=now();write(run/'execution.json',state)
        print(json.dumps({k:v for k,v in state.items() if k!='source'},indent=2))

if __name__=='__main__':main()
