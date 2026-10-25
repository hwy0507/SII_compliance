"""Finite read-only audit of the parent and two registered critic-restart cycles.

Waits for immutable complete-cycle archives, never starts training or physics.
Missing archives are not replaced with live partial checkpoints. The stage
budget/deadline bounds this observer, not the persistent training objective.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(registration):
    p = json.loads(registration.read_text())
    for name, expected in p['source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Frozen audit source drift: '+name)
    out = Path(p['output'])
    out.mkdir(exist_ok=False)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    write(out/'EXECUTION.json', dict(pid=os.getpid(), registration_sha256=sha(registration),
        started_unix=time.time(), optimizer_updates=0, physical_transitions=0))
    completed = []
    try:
        for stage in p['stages']:
            run, root = Path(stage['run']), Path(stage['runtime'])
            if sha(root/'RUNTIME.json') != stage['runtime_sha256']:
                raise ValueError('Runtime manifest drift')
            if sha(stage['training_registration']) != stage['training_registration_sha256']:
                raise ValueError('Training registration drift')
            target = out/stage['name']
            target.mkdir()
            snapshots = target/'snapshots'
            snapshots.mkdir()
            while True:
                paths = {}
                for method in p['methods']:
                    candidates = [run/a/method/f"cycle_{stage['cycle']:05d}.pt" for a in stage['archives']]
                    found = next((path for path in candidates if path.exists()), None)
                    if found:
                        paths[method] = found
                if len(paths) == len(p['methods']):
                    break
                for failure in [run/'MIGRATION_FAILURE.json', *[run/m/'FAILURE.json' for m in p['methods']]]:
                    if failure.exists():
                        raise RuntimeError('Training failure while waiting for archives: '+str(failure))
                write(out/'PROGRESS.json', dict(stage=stage['name'], state='waiting_for_complete_cycle_archives',
                    cycle=stage['cycle'], available=list(paths), completed=completed, updated_unix=time.time()))
                if time.time() >= p['deadline_unix']:
                    raise TimeoutError('Read-only audit dispatch deadline; training remains independently managed')
                time.sleep(10)
            records = {}
            # Archive files are immutable; copy one complete state per method
            # into this audit before reading live append-only diagnostics.
            for method, source in paths.items():
                execution = json.loads((run/method/'EXECUTION.json').read_text())
                if execution['protocol_sha256'] != stage['training_registration_sha256']:
                    raise ValueError('Unexpected training protocol: '+method)
                dest = snapshots/method/source.name
                dest.parent.mkdir()
                shutil.copy2(source, dest)
                digest = sha(source)
                if sha(dest) != digest:
                    raise ValueError('Archive copy mismatch')
                records[method] = dict(source=str(source), sha256=digest)
            write(target/'SNAPSHOTS.json', records)
            command = [sys.executable, '-B', str(Path(__file__).with_name('diagnose_published_training_20261025.py')),
                '--runtime', str(root), '--run', str(run), '--output', str(target/'results'),
                '--cycle-archive', str(snapshots), '--cycle', str(stage['cycle'])]
            with (target/'diagnose.log').open('x') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                write(out/'PROGRESS.json', dict(stage=stage['name'], state='read_only_diagnosis_running',
                    child_pid=child.pid, command=command, completed=completed, updated_unix=time.time()))
                code = child.wait()
            if code:
                raise RuntimeError('Read-only diagnosis failed: '+stage['name'])
            result = json.loads((target/'results/DIAGNOSIS.json').read_text())
            for method in p['methods']:
                data = result['methods'][method]
                if data['checkpoint_sha256'] != records[method]['sha256'] or not data['network_state_unchanged']:
                    raise ValueError('Unexpected diagnostic state: '+method)
            completed.append(stage['name'])
            write(target/'FINISHED.json', dict(finished_unix=time.time(), snapshots=records,
                report_sha256=sha(target/'results/DIAGNOSIS.json'), convergence_claim=False))
        write(out/'FINISHED.json', dict(completed=completed, finished_unix=time.time(),
            optimizer_updates=0, new_physical_transitions=0, convergence_claim=False,
            note='Reports need scientific review; no training/algorithm decision is automated'))
    except BaseException as error:
        write(out/'FAILURE.json', dict(error=repr(error), completed=completed,
            training_unchanged=True, note='Inspect observer and training before retrying; never duplicate learners'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args().registration)
