"""Bounded, resumable, isolated diagnostic queue. Never schedules withheld cases."""
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'results'
    out.mkdir(exist_ok=True)
    with (out/'queue.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        plan=json.loads((root/'configs/esn_office_development_protocol_20260927.json').read_text())
        checkpoint=root/'models/r30.npz'
        jobs=[]
        # Original R30 paired with zero and exactly pulse-disabled R30.
        for events in plan['diagnostics']['events']:
            for actor in plan['diagnostics']['actors']:
                output=out/f'{actor}_{events}'/'rollout'
                command=[sys.executable,str(root/'scripts/validate_office_apparatus_v5_20260917.py'),
                    '--output',str(output),'--task','pick_place','--events',events,
                    '--seed',str(plan['diagnostics']['seed']),'--variant','0',
                    '--duration',str(plan['diagnostic_duration_s']),'--dt',str(plan['physics_dt_s'])]
                if actor!='zero':command+=['--esn-model',str(checkpoint),'--esn-mode','control']
                if actor=='r30_no_pulse':command+=['--disable-selector-pulse']
                jobs.append((output,command))
        def run(job):
            output,command=job
            output.parent.mkdir(exist_ok=True)
            status=output.parent/'execution.json'
            if status.exists() or output.with_suffix('.json').exists():
                return dict(case=output.parent.name,status='preserved_existing_attempt')
            start=time.time()
            manifest=dict(command=command,start_unix_s=start,pid=os.getpid(),
                checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MUJOCO_MENAGERIE_PATH')})
            status.write_text(json.dumps(manifest,indent=2))
            with (output.parent/'stdout.log').open('w') as log:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            manifest.update(exit_code=result.returncode,elapsed_s=time.time()-start)
            status.write_text(json.dumps(manifest,indent=2))
            return dict(case=output.parent.name,exit_code=result.returncode)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            for result in pool.map(run,jobs):print(json.dumps(result),flush=True)


if __name__=='__main__':main()
