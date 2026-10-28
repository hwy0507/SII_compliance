"""Run an explicit development-only manifest; archive attempts and enforce a lock."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    if not 1<=a.workers<=4:raise ValueError('At most four simulation workers')
    root=Path(__file__).resolve().parents[1];out=root/'results';out.mkdir(exist_ok=True)
    plan=json.loads(a.plan.read_text())
    with (out/'queue.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        def run(row):
            if row.get('split')!='development':raise ValueError('Only development here')
            case=out/row['id'];case.mkdir(exist_ok=True)
            status=case/'execution.json'
            if status.exists():return {'case':row['id'],'preserved':True}
            args=row['arguments']
            # Allow a plan-wide wrapper entrypoint while preserving the
            # per-job override used by older manifests.  The former is needed
            # for teacher/ESN wrappers because their wrapper-only arguments
            # must be consumed before invoking the frozen evaluator.
            entrypoint=(root/row.get('entrypoint', plan.get('entrypoint','scripts/validate_office_apparatus_v5_20260917.py'))).resolve()
            if not entrypoint.is_relative_to(root):raise ValueError('Entrypoint must be within isolated snapshot')
            command=[sys.executable,str(entrypoint),
                     '--output',str(case/'rollout')]+args
            record=dict(command=command,start_unix_s=time.time(),plan_sha256=hashlib.sha256(a.plan.read_bytes()).hexdigest())
            status.write_text(json.dumps(record,indent=2))
            with (case/'stdout.log').open('w') as log:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,cwd=root)
            record.update(exit_code=result.returncode,elapsed_s=time.time()-record['start_unix_s'])
            status.write_text(json.dumps(record,indent=2))
            return dict(case=row['id'],exit_code=result.returncode)
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            for future in as_completed([pool.submit(run,row) for row in plan['jobs']]):
                print(json.dumps(future.result()),flush=True)


if __name__=='__main__':main()
