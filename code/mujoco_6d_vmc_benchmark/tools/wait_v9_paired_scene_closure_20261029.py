"""Bounded serial handoff; no simulation while the original scope is active."""
import argparse
import fcntl
import json
import subprocess
import sys
import time
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    lock = (root/'.handoff.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (root/'HANDOFF.json').exists(), 'Never duplicate or silently retry'
    reg = read(root/'REGISTRATION.json')
    digest = sha(root/'REGISTRATION.json')
    state = dict(status='waiting_for_original108', started_utc=now(),
        registration_sha256=digest, source_sha256=sha(Path(__file__)), maximum_wait_s=43200)
    write(root/'HANDOFF.json', state)
    deadline = time.monotonic()+43200
    try:
        while time.monotonic() < deadline:
            assert sha(root/'REGISTRATION.json') == digest
            parent = read(Path(reg['prerequisite']))
            if parent['status'] in ('failed_preserved', 'stopped_at_episode_boundary'):
                raise RuntimeError('Parent did not complete; preserve and review, no automatic recovery')
            if parent['status'] == 'complete':
                assert parent['completed'] == 108 and len(parent['results']) == 108
                status = subprocess.run(['systemctl', '--user', 'show',
                    'run-raa08b13eb33f4583ab899210958345fa.scope', '-p', 'ActiveState', '-p', 'LoadState'],
                    text=True, capture_output=True, check=True)
                values = dict(line.split('=', 1) for line in status.stdout.splitlines())
                if values.get('ActiveState') == 'inactive' or values.get('LoadState') == 'not-found':
                    break
            time.sleep(30)
        else:
            raise TimeoutError('Finite 12h handoff wait exhausted; no dispatch')
        state.update(status='running_registered_development_closure', dispatched_utc=now())
        write(root/'HANDOFF.json', state)
        subprocess.run([sys.executable, str(ROOT/'tools/prepare_v9_paired_scene_closure_20261029.py'),
            '--root', str(root), '--run'], cwd=ROOT, check=True)
        state.update(status='complete_pending_review', ended_utc=now())
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'HANDOFF.json', state)


if __name__ == '__main__':
    main()
