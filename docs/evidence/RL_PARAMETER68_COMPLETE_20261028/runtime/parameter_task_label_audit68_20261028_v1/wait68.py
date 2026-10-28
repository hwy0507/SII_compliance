"""Wait for the registered original cycle68; run only saved-label audit."""
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
OUT = BASE / 'runs/parameter_task_label_audit68_20261028_v1'


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
    plan = read(OUT / 'PLAN68.json')
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
    subprocess.run([sys.executable, str(HERE / 'audit_labels.py'), '--before', '67', '--after', '68',
                    '--output', str(OUT / 'COMPLETE67_68.json')], check=True)
    (OUT / 'FINISHED68.json').write_text(json.dumps(dict(completed=True, time=time.time())) + '\n')
except BaseException as error:
    (OUT / 'WAIT68_FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error))) + '\n')
    raise
