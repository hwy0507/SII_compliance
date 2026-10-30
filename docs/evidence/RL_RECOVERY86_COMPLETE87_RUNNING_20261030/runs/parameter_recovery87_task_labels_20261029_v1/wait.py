"""Wait for the registered recovery cycle87; run only saved-label audit."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

os.sched_setaffinity(0, {53})
HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
OUT = HERE


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live(job):
    path = Path(f'/proc/{job["pid"]}/stat')
    if not path.exists():
        return False
    stat = path.read_text().rsplit(')', 1)[1].split()
    return stat[19] == job['proc_start_ticks'] and stat[0] != 'Z'


try:
    plan = read(OUT / 'PLAN.json')
    for name, digest in plan['sources'].items():
        assert sha(HERE / name) == digest
    run = Path(plan['parent_run'])
    assert sha(run / 'LAUNCH.json') == plan['parent_launch_sha256']
    deadline = time.monotonic() + plan['wait_seconds']
    while True:
        assert not (run / 'ARCHIVE_REVIEW_FAILURE.json').exists()
        for job in plan['jobs']:
            assert not (run / job['controller'] / 'train/FAILURE.json').exists()
        finished = run / 'ARCHIVE_REVIEW_FINISHED.json'
        if finished.exists():
            assert read(finished)['completed']
            if not any(live(job) for job in plan['jobs']):
                break
        else:
            assert live(plan['monitor']), 'Original monitor absent without completion'
        assert time.monotonic() < deadline, 'Observation expired; do not restart training'
        time.sleep(5)
    for name, digest in plan['sources'].items():
        assert sha(HERE / name) == digest
    subprocess.run([sys.executable, str(HERE / 'audit_labels.py'), '--before', '86', '--after', '87',
                    '--output', str(OUT / 'COMPLETE86_87.json')], check=True)
    (OUT / 'LABELS_FINISHED.json').write_text(json.dumps(dict(completed=True, time=time.time())) + '\n')
    loss = BASE / 'runs/parameter_recovery87_loss_20261029_v1'
    while not (loss / 'SAVED_REVIEW.json').exists():
        assert not (loss / 'FAILURE.json').exists()
        assert time.monotonic() < deadline, 'Saved loss review wait expired'
        time.sleep(5)
    subprocess.run([sys.executable, str(HERE / 'review_labels87.py')], check=True)
    (OUT / 'FINISHED.json').write_text(json.dumps(dict(completed=True, time=time.time())) + '\n')
except BaseException as error:
    (OUT / 'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error))) + '\n')
    raise
