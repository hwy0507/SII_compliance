"""Publish one completed paper phase into a fresh SHA-verified server run.

No deletion, overwrite, live-job restart, or modification of earlier archives.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
from archive_tool_campaign_20261002 import make,sha

HOST='arm1@192.168.31.70'
BASE='/home/arm1/sii_shared/SII_compliance'
VERIFIER=BASE+'/runs/main/paper_esn_12h_initial_20261002_141136/evidence/source/tools/archive_tool_campaign_20261002.py'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phase',type=Path,required=True)
    p.add_argument('--run-id',required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    if not re.fullmatch(r'paper_esn_12h_[a-zA-Z0-9_]+',a.run_id):raise ValueError('Expected task-specific run id')
    if a.receipt.exists():raise FileExistsError(a.receipt)
    root=a.phase.resolve()
    if not (root/'archive_manifest.json').exists():make(root)
    expected=sha(root/'archive_manifest.json')
    incoming=BASE+'/incoming/'+a.run_id
    published=BASE+'/runs/main/'+a.run_id+'/evidence'
    command='test ! -e '+shlex.quote(str(Path(published).parent))+' && test ! -e '+shlex.quote(incoming)+' && mkdir '+shlex.quote(incoming)
    subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,command],check=True)
    subprocess.run(['rsync','-a','--exclude=__pycache__','--exclude=*.pyc','--exclude=source/scripts/outputs/',str(root)+'/',HOST+':'+incoming+'/'],check=True)
    command=' '.join(map(shlex.quote,['python3',VERIFIER,'--root',incoming,'--publish',published]))
    receipt=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,command],text=True))
    assert receipt['manifest_sha256']==expected
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    with a.receipt.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
