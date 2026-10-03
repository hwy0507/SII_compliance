"""Four shared simulation leases for new research queues on the same host.

Queues hold one OS lock throughout their child simulations. Old unleased
workers prevent acquisition; they are never stopped. A queued process does not
consume a simulation slot until it owns a lock. Existing frozen jobs are intact.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import time

WORKERS = {'research72_worker_20261003.py', 'paper_office_worker_20261002.py',
    'paper_classical_worker_20261002.py', 'paper_rl_worker_20261002.py',
    'validate_office_apparatus_v5_20260917.py', 'validate_office_v5_20260918.py'}


def unleased_workers():
    result = []
    for proc in Path('/proc').glob('[0-9]*'):
        names = set()
        try:
            status = (proc/'status').read_text()
            if any(line.startswith('State:') and ('T (stopped)' in line or 't (tracing stop)' in line)
                   for line in status.splitlines()):
                continue
            names = {Path(x.decode(errors='replace')).name
                     for x in (proc/'cmdline').read_bytes().split(b'\0')[1:]}
            if names & WORKERS:
                env = (proc/'environ').read_bytes().split(b'\0')
                owner = next((x.split(b'=',1)[1] for x in env if x.startswith(b'SII_R72_LEASE_OWNER_PID=')), b'')
                if b'SII_R72_SIMULATION_LEASE=1' not in env or not owner.isdigit() or not Path('/proc',owner.decode()).exists():
                    result.append(int(proc.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            # An unreadable candidate is not evidence of an available slot.
            if names & WORKERS:
                result.append(int(proc.name))
    return result


@contextmanager
def simulation_slot(root, deadline):
    directory = Path(root)/'simulation_slots'
    directory.mkdir(exist_ok=True)
    handle = None
    while datetime.now(timezone.utc) < deadline:
        if unleased_workers():
            time.sleep(1)
            continue
        for index in range(4):
            candidate = (directory/f'slot_{index}.lock').open('a+')
            try:
                fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                candidate.close()
                continue
            handle = candidate
            break
        if handle is not None:
            break
        time.sleep(1)
    if handle is None:
        raise TimeoutError('No simulation lease before development cutoff')
    old = os.environ.get('SII_R72_SIMULATION_LEASE')
    old_owner = os.environ.get('SII_R72_LEASE_OWNER_PID')
    os.environ['SII_R72_SIMULATION_LEASE'] = '1'
    os.environ['SII_R72_LEASE_OWNER_PID'] = str(os.getpid())
    try:
        yield dict(slot=index, owner_pid=os.getpid(), locking='flock held by supervising queue')
    finally:
        if old is None:
            os.environ.pop('SII_R72_SIMULATION_LEASE', None)
        else:
            os.environ['SII_R72_SIMULATION_LEASE'] = old
        if old_owner is None:
            os.environ.pop('SII_R72_LEASE_OWNER_PID',None)
        else:
            os.environ['SII_R72_LEASE_OWNER_PID'] = old_owner
        handle.close()
