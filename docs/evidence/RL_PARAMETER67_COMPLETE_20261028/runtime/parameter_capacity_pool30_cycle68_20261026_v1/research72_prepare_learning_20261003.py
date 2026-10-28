"""Continuous dependency wait: collect -> audit -> real-data export -> RL parity.

No recurring automation. Does not restart collection or overwrite a failed stage.
Independent dataset export finishes before the separate RL diagnostic.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT,sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    protocol=json.loads((root/'PROTOCOL.json').read_text());out.mkdir(parents=True,exist_ok=False)
    state=dict(status='waiting_for_existing_collection',started_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),steps=[])
    write(out/'execution.json',state)
    try:
        while True:
            current=json.loads((root/'teacher_bank/execution.json').read_text())
            if current['status']!='running':break
            if datetime.now(timezone.utc)>=datetime.fromisoformat(protocol['dispatch_deadline_utc']):
                raise RuntimeError('Collection unfinished at new dispatch deadline')
            time.sleep(15)
        assert current['status']=='complete','Collection incomplete; preserve and diagnose before continuation'
        commands=[('data',[sys.executable,str(ROOT/'tools/research72_build_demonstrations_20261003.py'),
                   '--root',str(root),'--output',str(out/'demonstrations')]),
                  ('rl_parity',[sys.executable,str(ROOT/'tools/research72_probe_online_20261003.py'),
                   '--root',str(root),'--teacher-run',str(root/'teacher_bank/queue_0/train_000'),'--output',str(out/'rl_parity')])]
        for label,command in commands:
            row=dict(label=label,command=command,started_utc=now());state['steps'].append(row);state['status']='running_'+label
            write(out/'execution.json',state)
            with (out/(label+'.log')).open('x') as log:
                rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy()).returncode
            row.update(returncode=rc,ended_utc=now());write(out/'execution.json',state)
            if rc:raise RuntimeError(label+' failed; no automatic retry or qualification relaxation')
        state['status']='complete'
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
