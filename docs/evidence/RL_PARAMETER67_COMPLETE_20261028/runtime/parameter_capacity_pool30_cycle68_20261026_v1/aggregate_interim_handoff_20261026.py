"""Finite read-only aggregation of a registered representative evaluation.

Uses completed rows from the original run and the three handed-off slots.
Never dispatches or restarts physics; failed/missing workers are surfaced.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def run(registration):
    p = read(registration)
    out = Path(p['output'])
    if (out/'AGGREGATION_STARTED.json').exists():
        raise FileExistsError('Already observing this handoff')
    for name, h in p['input_hashes'].items():
        if sha(name) != h:
            raise ValueError('Registered aggregation source/input drift: '+name)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    write(out/'AGGREGATION_STARTED.json', dict(pid=os.getpid(),
        registration_sha256=sha(registration), started_unix=time.time()))
    try:
        while True:
            rows = list(read(p['completed_direct_rows'])['rows'])
            completed = []
            for method, slot in p['slots'].items():
                folder = Path(slot['folder'])
                if (folder/'FAILURE.json').exists():
                    raise RuntimeError('Slot failed; preserve evidence: '+method)
                if (folder/'FINISHED.json').exists():
                    part = read(folder/'ROWS.json')['rows']
                    if len(part) != 3 or any(r['controller'] != method for r in part):
                        raise ValueError('Unexpected completed slot rows')
                    rows.extend(part)
                    completed.append(method)
                else:
                    proc = Path(f"/proc/{slot['pid']}")
                    try:
                        state = (proc/'stat').read_text().rsplit(')', 1)[1].split()[0]
                        command = (proc/'cmdline').read_bytes().replace(b'\0', b' ').decode()
                    except FileNotFoundError:
                        # Completion can be published between the first file
                        # check and process exit. Re-read it on the next pass.
                        if (folder/'FINISHED.json').exists():
                            continue
                        raise RuntimeError('Slot exited without completion: '+method)
                    if state == 'Z':
                        if (folder/'FINISHED.json').exists():
                            continue
                        raise RuntimeError('Slot is zombie without completion: '+method)
                    if slot['registration'] not in command:
                        raise ValueError('Slot PID identity changed: '+method)
            write(out/'AGGREGATION_PROGRESS.json', dict(completed_slots=completed,
                complete_case_count=len(rows), updated_unix=time.time()))
            if len(completed) == len(p['slots']):
                keys = [(r['controller'], r['case_id']) for r in rows]
                expected = {(m,c) for m in p['methods'] for c in p['case_ids']}
                if len(keys) != len(set(keys)) or set(keys) != expected:
                    raise ValueError('Incomplete or duplicated registered matrix')
                if not all(r['public_filter_verified'] and r['torque_projection_verified'] for r in rows):
                    raise ValueError('Execution-chain audit incomplete')
                write(out/'ROWS.json', dict(rows=rows, complete_registered_training_cohort=False,
                    final_spt_reference_selected=False, convergence_claim=False))
                write(out/'FINISHED.json', dict(cases=len(rows), finished_unix=time.time(),
                    complete_interim_matrix=True, complete_registered_training_cohort=False,
                    final_spt_reference_selected=False, convergence_claim=False,
                    rows_sha256=sha(out/'ROWS.json'), independent_scientific_review_completed=False))
                break
            time.sleep(5)
    except BaseException as error:
        write(out/'AGGREGATION_FAILURE.json', dict(error=repr(error), failed_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    run(parser.parse_args().registration)
