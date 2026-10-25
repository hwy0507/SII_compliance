"""Run a finite prepared job list, one serial lane per GPU, at most five lanes.

Run on the server itself. No SSH, automatic retries, test-set access or nested
distributed learning. A failed launch stops new jobs; in-flight jobs finish.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shlex
import subprocess
import threading

from prepare_rl_spt_campaign_20261025 import command, now, read, require, sha, verify, write


def jobs_by_gpu(jobs):
    require(isinstance(jobs, list) and 1 <= len(jobs) <= 64, 'Need a finite list of 1..64 jobs')
    lanes = {}; seen = set(); cpu_owners = {}
    for job in jobs:
        require(set(job) <= {'root','family','stop_at_step','resume_checkpoint'}, 'Unknown job field')
        root = Path(job['root']).resolve(); p = verify(root); r = p['resources']
        require(r['server_compute'], 'Parallel queue accepts server registrations only')
        key = (str(root), job['family'])
        require(key not in seen, 'Only one segment per family/root in a queue; resume in the next stage')
        seen.add(key)
        resume = Path(job['resume_checkpoint']) if job.get('resume_checkpoint') else None
        limit = job['stop_at_step']
        command(root, p, job['family'], limit, resume)
        gpu = r['gpu_uuid']
        for cpu in r['cpus']:
            require(cpu not in cpu_owners or cpu_owners[cpu] == gpu, 'CPU sets overlap across GPU lanes')
            cpu_owners[cpu] = gpu
        argv = [p['python'], str(Path(p['source'])/'tools/prepare_rl_spt_campaign_20261025.py'),
                'run','--root',str(root),'--family',job['family'],'--stop-at-step',str(limit)]
        if resume: argv += ['--resume-checkpoint',str(resume.resolve())]
        lanes.setdefault(gpu, []).append(dict(job=job, argv=argv, root=str(root),
            protocol_sha256=sha(root/'PROTOCOL.json'), status='queued'))
    require(len(lanes) <= 5, 'Register at most five GPU lanes')
    return lanes


def run_lanes(lanes, execute):
    """Stop new dispatch after a failure, preserving all in-flight work."""
    failed = threading.Event()
    def lane(rows):
        for row in rows:
            if failed.is_set():
                break
            if not execute(row):
                failed.set(); break
    with ThreadPoolExecutor(max_workers=len(lanes)) as pool:
        futures = [pool.submit(lane, rows) for rows in lanes.values()]
        for future in futures:
            future.result()
    return not failed.is_set()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    a = parser.parse_args(); lanes = jobs_by_gpu(read(a.jobs))
    for gpu, rows in lanes.items():
        for row in rows: print(gpu+': '+shlex.join(row['argv']), flush=True)
    if a.dry_run: return
    require(not a.receipt.exists(), 'Use a new batch receipt; failed receipts are never overwritten')
    state = dict(status='running', started_utc=now().isoformat(), jobs_sha256=sha(a.jobs), lanes=lanes)
    # Exclusive creation also excludes two coordinators claiming the same receipt.
    with a.receipt.open('x') as stream: json.dump(state, stream, indent=2)
    mutex = threading.Lock()
    def execute(row):
        with mutex:
            row.update(status='running', started_utc=now().isoformat()); write(a.receipt,state)
        try:
            result = subprocess.run(row['argv'], check=False)
            require(result.returncode == 0, f'Launcher exited {result.returncode}')
            job = row['job']; limit = job['stop_at_step']
            result_state = read(Path(row['root'])/job['family']/f'segment_{limit:07d}'/'execution.json')
            require(result_state.get('status') == 'complete', 'Trainer did not close cleanly')
            require(result_state.get('steps',0) > limit-1375, 'Segment stopped before its requested budget')
            row.update(status='segment_closed', steps=result_state['steps'])
        except Exception as exc:
            row.update(status='failed_or_incomplete_preserved', error=f'{type(exc).__name__}: {exc}')
        with mutex:
            row['ended_utc']=now().isoformat(); write(a.receipt,state)
        return row['status']=='segment_closed'
    success = run_lanes(lanes, execute)
    state.update(status='segments_closed' if success else 'failed_or_incomplete_preserved',
                 ended_utc=now().isoformat())
    write(a.receipt,state)
    raise SystemExit(0 if success else 1)


if __name__ == '__main__': main()
