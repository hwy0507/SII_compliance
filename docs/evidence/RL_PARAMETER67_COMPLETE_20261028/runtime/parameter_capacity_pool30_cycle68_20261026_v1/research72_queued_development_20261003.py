"""Wait for the old unleased stage, then run one finite managed development batch.

No timers, retries, new fits, model selection or heldout access. Each physics
episode releases its lease so other registered development work can progress.
"""
import argparse
from datetime import datetime,timezone,timedelta
import os
from pathlib import Path
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from research72_batch_20261003 import read,validate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('root','output','predecessor','specification'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    protocol=validate(root,read(a.specification))
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    out.mkdir(parents=True,exist_ok=False)
    state=dict(status='waiting_for_predecessor',started_utc=now(),source_sha256=sha(Path(__file__)),
        specification_sha256=sha(a.specification),predecessor=str(a.predecessor.resolve()),protocol_sha256=sha(root/'PROTOCOL.json'))
    write(out/'execution.json',state)
    try:
        while True:
            previous=read(a.predecessor/'execution.json')
            if previous['status']=='complete':break
            assert previous['status']=='waiting_for_controller_screen' or previous['status'].startswith('running_')
            assert datetime.now(timezone.utc)<deadline,'No new development after cutoff'
            time.sleep(30)
        assert sha(a.specification)==state['specification_sha256']
        command=[sys.executable,str(ROOT/'tools/research72_batch_20261003.py'),'--root',str(root),
            '--output',str(out/'development'),'--specification',str(a.specification),'--queue-count','1','--managed-slots']
        state.update(status='running',command=command);write(out/'execution.json',state)
        with (out/'development.log').open('x') as log:
            state['returncode']=subprocess.run(command,cwd=ROOT,env=os.environ.copy(),stdout=log,stderr=subprocess.STDOUT).returncode
        assert state['returncode']==0,'Failed stage retained, no automatic retry'
        state['status']=read(out/'development/execution.json')['status']
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
