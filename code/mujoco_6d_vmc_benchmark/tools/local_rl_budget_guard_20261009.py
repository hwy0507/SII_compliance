"""Finite deadline guard for an ALREADY running immutable RL dispatcher.

No scheduler, new simulation, checkpoint selection or remote compute. At the
deadline freeze only the registered dispatcher, request trainers' existing
episode-boundary checkpoint handler, drain independent worker units, then remove
the frozen dispatcher. Original receipts remain untouched; interruption is
recorded separately, never presented as a completed interaction budget.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def systemd(unit):
    result = subprocess.run(['systemctl','--user','show',unit,
        '-p','MainPID','-p','ActiveState','-p','SubState','-p','ControlGroup'],
        check=True, capture_output=True, text=True)
    return dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)


def identity(pid):
    directory = Path('/proc')/str(pid)
    fields = (directory/'stat').read_text().rsplit(')',1)[1].split()
    return dict(pid=pid, start_ticks=fields[19],
        argv=(directory/'cmdline').read_bytes().decode().rstrip('\0').split('\0'))


def signal_exact(expected, sig):
    # Prefer pidfd when the interpreter exposes it. The research venv's Python
    # build omits the wrappers, so retain a checked os.kill fallback; the
    # fallback verifies identity immediately before delivery and is only used
    # for the guard's own explicitly owned processes.
    assert identity(expected['pid']) == expected, 'Process identity changed'
    if hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'):
        fd = os.pidfd_open(expected['pid'])
        try: signal.pidfd_send_signal(fd, sig)
        finally: os.close(fd)
    else:
        os.kill(expected['pid'], sig)


def owned_receipts(root, registration_hash):
    answer = []
    for path in root.glob('*.execution.json'):
        try: receipt = read(path)
        except (json.JSONDecodeError, FileNotFoundError): continue
        if (receipt.get('status') != 'running' or
                receipt.get('extension_sha256') != registration_hash): continue
        argv = receipt['command']
        unit = next(s.split('=',1)[1]+'.service' for s in receipt['managed_command']
                    if s.startswith('--unit='))
        assert unit.startswith('sii-local-rl-extend-')
        state = systemd(unit)
        pid = int(state['MainPID'])
        if not pid: continue
        proc = identity(pid)
        assert proc['argv'] == argv, (unit, 'command mismatch')
        answer.append(dict(unit=unit, receipt=str(path), identity=proc,
            trainer=Path(argv[1]).name == 'train_baseline_repair_rl_20261008.py'))
    return answer


def snapshot(root):
    records = []
    for job in read(root/'PROTOCOL.json')['jobs']:
        for path in sorted(root.glob(job['name']+'_extended*/execution.json')):
            state = read(path)
            if 'rows' not in state: continue  # excludes development worker receipts
            rows = [r for r in state['rows'] if 'result' in r]
            records.append(dict(name=path.parent.name, status=state['status'],
                steps=state['steps'], updates=state.get('updates'),
                completed_new_episodes=len(rows), task=sum(r['result']['task_success'] for r in rows),
                strict=sum(r['result']['strict_success'] for r in rows),
                stop_reason=state.get('stop_reason'), checkpoints=[r['step'] for r in state['checkpoint_rows']]))
    return records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registration',type=Path,required=True)
    a = p.parse_args(); regpath=a.registration.resolve(); out=regpath.parent; reg=read(regpath)
    assert platform.node() == reg['compute_host'] == 'airpig'
    root=Path(reg['root']); extension=Path(reg['extension'])
    assert digest(extension/'REGISTRATION.json') == reg['extension_registration_sha256']
    assert digest(root/'PROTOCOL.json') == reg['protocol_sha256']
    assert digest(__file__) == reg['guard_source_sha256']
    deadline=datetime.fromisoformat(reg['dispatch_deadline_utc'])
    assert datetime.fromisoformat(reg['authorization_start_utc']) < deadline
    lock=(out/'guard.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (out/'execution.json').exists(), 'Preserve previous attempt'
    original=reg['coordinator_identity']; unit=reg['coordinator_unit']
    assert int(systemd(unit)['MainPID']) == original['pid'] and identity(original['pid']) == original
    state=dict(status='watching',started_utc=now(),registration_sha256=digest(regpath),
        actions=[],new_simulations=0,server_compute=False)
    def save():
        state.update(updated_utc=now(),training=snapshot(root));write(out/'execution.json',state)
    save()
    while datetime.now(timezone.utc) < deadline:
        service=systemd(unit)
        if int(service['MainPID']) != original['pid']:
            state.update(status='coordinator_ended_before_deadline',coordinator=service,ended_utc=now())
            save();return
        save();time.sleep(min(30,max(0,(deadline-datetime.now(timezone.utc)).total_seconds())))
    # Freeze dispatch before discovering workers. No running simulation is paused.
    signal_exact(original,signal.SIGSTOP)
    state['actions'].append(dict(utc=now(),signal='SIGSTOP',target=original,scope='dispatcher only'))
    state['status']='draining_already_started_episodes';save()
    # Let a systemd-run client already issued just before SIGSTOP finish unit
    # creation. The dispatcher itself cannot issue any further commands.
    time.sleep(5)
    workers=owned_receipts(root,reg['extension_registration_sha256'])
    state['deadline_workers']=workers;save()
    for worker in workers:
        if worker['trainer']:
            try: signal_exact(worker['identity'],signal.SIGUSR1)
            except ProcessLookupError: continue
            state['actions'].append(dict(utc=now(),signal='SIGUSR1',target=worker['identity'],
                scope='trainer existing handler: finish current episode and checkpoint'))
            save()
    while True:
        alive=[w['unit'] for w in workers if int(systemd(w['unit'])['MainPID'])]
        if not alive: break
        state['draining_units']=alive;save();time.sleep(30)
    # Independent workers have exited and flushed results. A frozen dispatcher
    # cannot be resumed safely: it would dispatch again with the OLD deadline.
    signal_exact(original,signal.SIGKILL)
    state['actions'].append(dict(utc=now(),signal='SIGKILL',target=original,
        scope='frozen dispatcher only, after all registered workers exited'))
    state.update(status='budget_closed_review_required',ended_utc=now(),draining_units=[],
        original_receipts='Preserved; stale running dispatch receipts superseded by this budget receipt, not rewritten as success',
        converged=False,final_comparison_ready=False)
    save()


if __name__ == '__main__':main()
