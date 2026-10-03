"""Read-only completed-phase audits, with new immutable analysis outputs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model-sha256',default='173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11')
    p.add_argument('--allow-partial',action='store_true',help='Audit completed episodes in a stopped failed phase; retain pending attempts explicitly')
    a=p.parse_args();phase=a.phase.resolve();out=a.output.resolve()
    state=json.loads((phase/'execution.json').read_text())
    assert state['status'] in (('complete','deadline_no_new_dispatch','failed_preserved') if a.allow_partial else ('complete','deadline_no_new_dispatch'))
    runs=[];pending=[]
    for row in state['rows']:
        run=phase/row['name'];execution=run/'execution.json'
        if execution.exists() and json.loads(execution.read_text())['status']=='complete' and (run/'AUDIT.json').exists():
            runs.append(run)
        else:pending.append(dict(name=row['name'],reason='No completed physical execution and audit'))
    assert a.allow_partial or not pending
    out.mkdir(parents=True,exist_ok=False)
    sources=[Path(__file__),Path(__file__).with_name('report_tool_campaign_20261002.py'),Path(__file__).with_name('paper_metrics_20261002.py')]
    for src in sources:shutil.copy2(src,out/src.name)
    record=dict(status='running',started_utc=now(),argv=sys.argv,phase=str(phase),
                phase_execution_sha256=sha(phase/'execution.json'),sources={s.name:sha(s) for s in sources},commands=[],
                allow_partial=a.allow_partial,pending_attempts=pending,attempted_episodes=len(state['rows']),
                completion_semantics='Audit finished; does not imply all planned physics episodes finished')
    write(out/'execution.json',record)
    commands=[[sys.executable,str(sources[1]),'--root',str(phase.parent),'--batch',phase.name,
               '--output',str(out/'INDEPENDENT_AUDIT.json'),'--expected-model-sha256',a.model_sha256]]
    commands.extend([sys.executable,str(sources[2]),'--run',str(run),'--output',str(out/(run.name+'.metrics.json'))] for run in runs)
    try:
        for i,command in enumerate(commands):
            record['commands'].append(command);write(out/'execution.json',record)
            with (out/f'{i:02d}.log').open('x') as log:
                subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
        assert sha(phase/'execution.json')==record['phase_execution_sha256']
        assert all(sha(s)==record['sources'][s.name] for s in sources)
        record.update(status='complete',episodes=len(runs),outputs={f.name:sha(f) for f in out.glob('*.json') if f.name!='execution.json'})
        print(json.dumps(dict(status='complete',episodes=len(runs),output=str(out))))
    except BaseException as exc:
        record.update(status='failed_preserved',error=repr(exc));raise
    finally:
        record['ended_utc']=now();write(out/'execution.json',record)


if __name__=='__main__':main()
