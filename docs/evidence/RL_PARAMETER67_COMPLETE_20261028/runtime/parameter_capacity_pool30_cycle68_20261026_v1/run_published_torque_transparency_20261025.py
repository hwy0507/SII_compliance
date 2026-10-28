"""Run one registered transparency evaluation after finite CPU54 probes end.

Waits on original process identities and successful receipts. Never replaces
missing jobs, retries physics, or starts a second copy of this evaluation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def live(identity):
    try:
        fields = Path(f"/proc/{identity['pid']}/stat").read_text().rsplit(')', 1)[1].split()
    except FileNotFoundError:
        return False
    return fields[0] != 'Z' and fields[19] == identity['start_ticks']


def main(args):
    protocol = json.loads(args.registration.read_text())
    out = Path(protocol['output'])
    if (out/'STARTED.json').exists():
        raise FileExistsError('Already dispatched; inspect existing process/evidence')
    if sha(__file__) != protocol['coordinator_sha256']:
        raise ValueError('Frozen coordinator source drift')
    os.sched_setaffinity(0, {protocol['cpu']})
    write(out/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
        registration_sha256=sha(args.registration)))
    try:
        while any(live(identity) for identity in protocol['wait_processes']):
            write(out/'WAITING.json', dict(updated_unix=time.time(),
                active_original_pids=[x['pid'] for x in protocol['wait_processes'] if live(x)]))
            time.sleep(5)
        for path in protocol['required_finished_receipts']:
            if not Path(path).is_file():
                raise RuntimeError('Prerequisite ended without success receipt: '+path)
            json.loads(Path(path).read_text())
        for path, digest in protocol['source_and_input_hashes'].items():
            if sha(path) != digest:
                raise ValueError('Registered source/input changed: '+path)
        audit_root = Path(protocol['audit_runtime'])
        command = [sys.executable, '-B', str(audit_root/'evaluate_published_compliance_20261025.py'),
            '--runtime', protocol['runtime'], '--registration', protocol['training_registration'],
            '--checkpoint', protocol['checkpoint'], '--output', str(out/'evaluation'),
            '--device', protocol['device'], '--learner-cpu', str(protocol['cpu']),
            '--physics-cpu', str(protocol['cpu']), '--case-id', protocol['case_id'], '--audit-substeps']
        with (out/'evaluation.log').open('xb') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            write(out/'EVALUATION_LAUNCH.json', dict(pid=child.pid, command=command, started_unix=time.time()))
            if child.wait() != 0:
                raise RuntimeError('Registered physical evaluation failed; retain evidence')
        sys.path.insert(0, str(audit_root))
        from compare_published_audit_trajectories_20261025 import compare
        from replay_published_filter_audit_20261025 import audit as filter_audit
        from replay_published_torque_audit_20261025 import audit as torque_audit
        from summarize_published_episode_audit_20261025 import summarize
        folder = out/'evaluation'/protocol['case_id']
        original = Path(protocol['original_episode'])
        transparency = compare(original, folder)
        write(out/'TRANSPARENCY.json', transparency)
        if not transparency['passed']:
            raise RuntimeError('Observational extension changed trajectory')
        same_contact = sha(original/'audit_substeps.npy') == sha(folder/'audit_substeps.npy')
        write(out/'CONTACT_AUDIT_EQUIVALENCE.json', dict(identical=same_contact))
        if not same_contact:
            raise RuntimeError('Original physical contact audit changed')
        write(out/'FILTER_REPLAY_AUDIT.json', filter_audit(folder))
        write(out/'TORQUE_REPLAY_AUDIT.json', torque_audit(folder))
        write(out/'PHYSICAL_AUDIT.json', summarize(folder, 'interim_impedance', protocol['case_id']))
        write(out/'FINISHED.json', dict(ended_unix=time.time(), transparency_passed=True,
            public_filter_replay_passed=True, torque_projection_and_physical_linkage_passed=True,
            scope='One early checkpoint/case transparency and safety-path audit; not final policy evaluation'))
    except BaseException as error:
        write(out/'FAILURE.json', dict(error=repr(error), ended_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
