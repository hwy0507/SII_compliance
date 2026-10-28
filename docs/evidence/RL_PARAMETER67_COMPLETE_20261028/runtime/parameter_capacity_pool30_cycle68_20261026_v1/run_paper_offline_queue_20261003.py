"""Run registered offline fits sequentially from an immutable source copy.

Explicit argv arrays avoid systemd/shell variable expansion. Completed jobs are
never restarted and failures are preserved with their exact source and command.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT,sha,write,now

ALLOWED={'train_paper_context_esn_20261003.py','train_office_mlp_rnn_20261002.py',
         'train_paper_feature_matched_network_20261003.py',
         'refine_paper_esn_readout_20261003.py','train_paper_adaptive_leak_esn_20261003.py'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();manifest=json.loads(a.manifest.read_text())
    jobs=manifest['jobs'];assert jobs and len(jobs)<=24
    deadline=datetime.fromisoformat(manifest['dispatch_until'])
    assert deadline.tzinfo is not None and deadline<=datetime(2026,10,2,22,11,36,tzinfo=timezone.utc)
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for job in jobs:
        assert job['script'] in ALLOWED and all(isinstance(v,str) for v in job['arguments'])
        args=job['arguments'];assert '--output' in args
        for flag in ('--output','--data','--metadata','--checkpoint','--checkpoint-metadata','--data-metadata'):
            if flag in args:assert Path(args[args.index(flag)+1]).is_absolute()
        assert not Path(args[args.index('--output')+1]).exists()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,out/'source'/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    shutil.copy2(a.manifest,out/'manifest.json')
    record=dict(status='running',started_utc=now(),manifest_sha256=sha(a.manifest),
                source_sha256={str(f.relative_to(out/'source')):sha(f) for f in (out/'source').rglob('*') if f.is_file()},rows=[])
    write(out/'execution.json',record)
    try:
        for i,job in enumerate(jobs):
            if datetime.now(timezone.utc)>=deadline:
                record['status']='deadline_no_new_dispatch';break
            cmd=[sys.executable,str(out/'source/tools'/job['script']),*job['arguments']]
            row=dict(command=cmd,started_utc=now());record['rows'].append(row);write(out/'execution.json',record)
            with (out/f'{i:02d}.log').open('x') as log:
                result=subprocess.run(cmd,cwd=out/'source',stdout=log,stderr=subprocess.STDOUT)
            row.update(returncode=result.returncode,ended_utc=now());write(out/'execution.json',record)
            if result.returncode:raise RuntimeError(f'Offline job {i} failed; outputs preserved')
        else:record['status']='complete'
    except BaseException as exc:record.update(status='failed_preserved',error=repr(exc));raise
    finally:record['ended_utc']=now();write(out/'execution.json',record)

if __name__=='__main__':main()
