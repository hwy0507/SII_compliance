"""Preserve exact complete-cycle checkpoints without altering live learners.

The trainer atomically replaces checkpoint_latest.pt. An opened inode is copied
and checked against CYCLES.json; missed boundaries are recorded, never relabelled.
The monitor ends when its original learner processes exit or MONITOR_STOP exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

import torch


def process_identity(pid):
    try:
        stat = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        return None if stat[0] == 'Z' else stat[19]
    except FileNotFoundError:
        return None


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main(args):
    torch.set_num_threads(1)
    args.output.mkdir(parents=True, exist_ok=False)
    jobs = json.loads((args.run/'LAUNCH.json').read_text())['jobs']
    identities = {job['controller']: process_identity(job['pid']) for job in jobs}
    if any(identity is None for identity in identities.values()):
        raise ValueError('All original learner handles must be live at monitor start')
    source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write(args.output/'MONITOR.json', dict(pid=os.getpid(), run=str(args.run.resolve()),
        started_unix=time.time(), source_sha256=source_hash, process_start_ticks=identities,
        role='read-only learner observation and exact checkpoint archival'))
    archived, missed = {}, set()
    with (args.output/'EVENTS.jsonl').open('x', buffering=1) as events:
        while not (args.output/'MONITOR_STOP').exists():
            active = {job['controller']: process_identity(job['pid']) == identities[job['controller']]
                for job in jobs}
            for job in jobs:
                method = job['controller']
                cycles_path = args.run/method/'CYCLES.json'
                if not cycles_path.exists():
                    continue
                cycles = json.loads(cycles_path.read_text())['cycles']
                if not cycles:
                    continue
                latest = cycles[-1]
                key = method+':'+str(latest['cycle'])
                if key in archived or key in missed:
                    continue
                if shutil.disk_usage(args.output).free < 20*1024**3:
                    raise OSError('20GiB archive free-space reserve reached')
                target = args.output/method
                target.mkdir(exist_ok=True)
                snapshot = target/('cycle_'+str(latest['cycle']).zfill(5)+'.tmp')
                with (args.run/method/'checkpoint_latest.pt').open('rb') as source, snapshot.open('xb') as output:
                    shutil.copyfileobj(source, output)
                checkpoint = torch.load(snapshot, map_location='cpu', weights_only=False)
                valid = (checkpoint.get('boundary') == 'complete_condition_cycle'
                    and checkpoint['cycle'] == latest['cycle'] and checkpoint['steps'] == latest['steps']
                    and checkpoint['controller'] == method)
                if valid:
                    final = snapshot.with_suffix('.pt')
                    snapshot.replace(final)
                    record = dict(method=method, cycle=latest['cycle'], steps=latest['steps'],
                        path=str(final), sha256=hashlib.sha256(final.read_bytes()).hexdigest(),
                        protocol_sha256=checkpoint['protocol_sha256'], cycle_metrics=latest,
                        archived_unix=time.time(), convergence_claim=False)
                    write(final.with_suffix('.json'), record)
                    archived[key] = record
                    events.write(json.dumps(dict(event='archived_complete_cycle', **record))+'\n')
                else:
                    snapshot.unlink()
                    missed.add(key)
                    events.write(json.dumps(dict(event='boundary_already_replaced', method=method,
                        requested_cycle=latest['cycle'], observed_boundary=checkpoint.get('boundary'),
                        observed_cycle=checkpoint['cycle'], observed_steps=checkpoint['steps']))+'\n')
                del checkpoint
            write(args.output/'PROGRESS.json', dict(updated_unix=time.time(), active_original_processes=active,
                archived=list(archived), missed=list(sorted(missed))))
            if not any(active.values()):
                break
            time.sleep(5)
    write(args.output/'FINISHED.json', dict(ended_unix=time.time(), archived=list(archived), missed=list(sorted(missed))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
