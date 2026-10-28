"""Finite extra development after baseline learning-rate correction.

One leased simulator can coexist with three RL trainers after the old four-queue
pipeline completes. No duplicate original-rate evaluations or sealed tests.
"""
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT, sha, write, now


def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--predecessor',type=Path,required=True)
    p.add_argument('--learning-specification',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json')
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    assert read(a.learning_specification)['protocol_sha256']==pdigest
    out.mkdir(parents=True,exist_ok=False)
    nominal=dict(protocol_sha256=pdigest,conditions=[c['id'] for c in read(root/'CONDITIONS.json')['conditions']
        if c['role']=='development'],candidates=[dict(name='nominal_zero',category='nominal_zero',nominal=True,config={})],
        registered_utc=now(),purpose='Shared planner and feedback WBC with zero compliance action; untuned reference, same world/gates.')
    write(out/'NOMINAL_SPECIFICATION.json',nominal)
    state=dict(status='waiting_for_predecessor',started_utc=now(),source_sha256=sha(Path(__file__)),
        protocol_sha256=pdigest,learning_specification_sha256=sha(a.learning_specification),
        nominal_specification_sha256=sha(out/'NOMINAL_SPECIFICATION.json'),steps=[])
    write(out/'execution.json',state)
    try:
        while True:
            previous=read(a.predecessor/'execution.json')
            if previous['status']=='complete':break
            assert previous['status']=='waiting_for_controller_screen' or previous['status'].startswith('running_'),previous['status']
            assert datetime.now(timezone.utc)<deadline, 'Development cutoff; no dispatch'
            time.sleep(30)
        for label,spec in [('nominal',out/'NOMINAL_SPECIFICATION.json'),('neural_lr',a.learning_specification)]:
            if not read(spec)['candidates']:continue
            assert datetime.now(timezone.utc)<deadline, 'Development cutoff; no dispatch'
            command=[sys.executable,str(ROOT/'tools/research72_batch_20261003.py'),
                '--root',str(root),'--output',str(out/(label+'_development')),
                '--specification',str(spec),'--queue-count','1','--managed-slots']
            row=dict(label=label,command=command,started_utc=now());state['steps'].append(row)
            state['status']='running_'+label;write(out/'execution.json',state)
            with (out/(label+'.log')).open('x') as log:
                row['returncode']=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT).returncode
            row['ended_utc']=now();write(out/'execution.json',state)
            assert row['returncode']==0, 'Failed additional stage retained; no retry'
            assert read(out/(label+'_development')/'execution.json')['status']=='complete'
        state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
