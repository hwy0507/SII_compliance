"""Finite sequential continuation after the registered controller screen.

This is one running process, not a timer or recurring automation. It never
retries failed stages, unlocks heldout data, or launches overlapping batches.
"""
import argparse
from datetime import datetime, timezone, timedelta
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT, now, sha, write


def read(p):
    return json.loads(p.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--screen', type=Path, required=True)
    p.add_argument('--learning-specification', type=Path, required=True)
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    protocol = read(root/'PROTOCOL.json')
    deadline = datetime.fromisoformat(protocol['authorization_start_utc']) + timedelta(hours=48)
    assert read(a.learning_specification)['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert read(a.screen/'SPECIFICATION.json')['protocol_sha256'] == sha(root/'PROTOCOL.json')
    out.mkdir(parents=True, exist_ok=False)
    state = dict(status='waiting_for_controller_screen', started_utc=now(),
        protocol_sha256=sha(root/'PROTOCOL.json'), source_sha256=sha(Path(__file__)),
        learning_specification_sha256=sha(a.learning_specification), steps=[])
    write(out/'execution.json', state)
    def run(label, args):
        if datetime.now(timezone.utc) >= deadline:
            raise TimeoutError('Development deadline reached; no new stage dispatched')
        command = [sys.executable, *map(str, args)]
        row = dict(label=label, command=command, started_utc=now())
        state['steps'].append(row)
        state['status'] = 'running_'+label
        write(out/'execution.json', state)
        with (out/(label+'.log')).open('x') as log:
            row['returncode'] = subprocess.run(command, cwd=ROOT, env=os.environ.copy(),
                stdout=log, stderr=subprocess.STDOUT).returncode
        row['ended_utc'] = now()
        write(out/'execution.json', state)
        assert row['returncode'] == 0, label+' failed; no retry'
    with (out/'coordinator.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            while True:
                prior = read(a.screen/'execution.json')
                if prior['status'] == 'complete':
                    break
                assert prior['status'] == 'running', 'Predecessor did not complete: '+prior['status']
                assert datetime.now(timezone.utc) < deadline, 'Deadline; no dispatch'
                time.sleep(30)
            run('learning_development', [ROOT/'tools/research72_batch_20261003.py',
                '--root', root, '--output', root/'learning_development_v1',
                '--specification', a.learning_specification])
            run('controller_selection', [ROOT/'tools/research72_select_controllers_20261003.py',
                '--root', root, '--screen', a.screen,
                '--output', out/'CONTROLLER_CONFIRM_SPECIFICATION.json'])
            run('controller_confirmation', [ROOT/'tools/research72_batch_20261003.py',
                '--root', root, '--output', root/'controller_confirmation_v1',
                '--specification', out/'CONTROLLER_CONFIRM_SPECIFICATION.json'])
            run('controller_final_choice', [ROOT/'tools/research72_select_controllers_20261003.py',
                '--root', root, '--screen', root/'controller_confirmation_v1',
                '--output', out/'CONTROLLER_CHOICE.json', '--final-choice'])
            state['status'] = 'complete'
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc))
            raise
        finally:
            state['ended_utc'] = now()
            write(out/'execution.json', state)


if __name__ == '__main__':
    main()
