"""Two bounded local lanes for an already registered and smoke-tested RL queue.

Infrastructure-only continuation: same immutable source, rewards, seeds, steps,
conditions and checkpoint lineage. No server commands and no periodic wakeups.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import queue
import shutil
import subprocess
import sys
import threading

import local_rl_campaign_20261009 as campaign
from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    protocol = read(root/'PROTOCOL.json')
    assert platform.node() == protocol['compute_host'] == 'airpig'
    assert read(root/'PREFLIGHT.json')['status'] == 'passed'
    smoke = read(root/'direct_office_task_smoke/execution.json')
    assert smoke['status'] == 'complete' and smoke['episodes'] >= 1
    assert campaign.hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert campaign.hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    runtime = Path(protocol['runtime'])
    assert {name: campaign.hashes(runtime/name) for name in read(root/'RUNTIME_HASHES.json')} == read(root/'RUNTIME_HASHES.json')
    lock = (root.parent/'.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    live = subprocess.check_output(['systemctl', '--user', 'list-units', '--type=service',
        '--state=running', '--no-legend', '--plain', '--no-pager'], text=True)
    assert not any('sii-local-rl-' in line and ('-lane' in line or '-smoke-' in line)
                   for line in live.splitlines()), 'A prior physics unit is still running; do not duplicate it'
    available_kib = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                             if line.startswith('MemAvailable:')))
    assert available_kib >= 7*1024**2, 'Need >=7GiB available before admitting two 3GiB lanes'
    amendment_path = root/'LOCAL_RESOURCE_AMENDMENT.json'
    amendment = dict(protocol_sha256=sha(root/'PROTOCOL.json'), host='airpig', server_compute=False,
        authorization='User requests full local compute; adapt the conservative one-simulator initial setup after successful smoke',
        local_max_simulators=2, memory_max_per_lane=3221225472, maximum_lane_memory_total=6442450944,
        memory_swap_max=0, numerical_threads_per_lane=1, cpu_affinity_per_lane=['1,6','2,7'],
        schedule='Two independent configurations; each lane serializes training and its eight development episodes',
        unchanged='All scientific protocol, physics, inputs, seeds, rewards, optimizer schedule and per-job limits unchanged',
        launcher_sha256=sha(Path(__file__)), helper_sha256=sha(Path(campaign.__file__)))
    if amendment_path.exists():
        assert read(amendment_path) == amendment
    else:
        write(amendment_path, amendment)
    state = dict(status='running', started_utc=now(), host=platform.node(),
        source_sha256=amendment['launcher_sha256'], helper_sha256=amendment['helper_sha256'],
        resource_amendment_sha256=sha(amendment_path), initial_available_kib=available_kib,
        jobs=protocol['jobs'], completed=[], failures=[])
    state_lock = threading.Lock()
    stop = threading.Event()
    current_lane = threading.local()
    env = dict(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='egl',
        JAX_PLATFORMS='cuda', XLA_PYTHON_CLIENT_PREALLOCATE='false', XLA_PYTHON_CLIENT_MEM_FRACTION='0.12',
        SII_LOCAL_RUNTIME=str(runtime))

    def save():
        state['updated_utc'] = now()
        write(root/'parallel.execution.json', state)

    def managed(directory, label, argv):
        receipt = directory/(label+'.execution.json')
        if receipt.exists():
            old = read(receipt)
            assert old['status'] == 'complete' and old['command'] == argv
            for path, digest in old.get('artifacts', {}).items():
                assert sha(path) == digest
            return
        assert not stop.is_set(), 'Other lane failed; do not start a new job'
        assert datetime.now(timezone.utc) < datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])
        assert shutil.disk_usage(root).free >= 30*1024**3
        unit = ('sii-local-rl-'+sha(root/'PROTOCOL.json')[:8]+'-lane'+str(current_lane.number)
                +'-'+hashlib.sha256(label.encode()).hexdigest()[:10])
        command = ['systemd-run', '--user', '--wait', '--pipe', '--collect', '--unit='+unit,
            '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=TasksMax=256',
            '--property=CPUAffinity='+amendment['cpu_affinity_per_lane'][current_lane.number],
            '--working-directory='+str(root/'source')]
        command += ['--setenv='+k+'='+v for k,v in env.items()]
        command += argv
        record = dict(status='running', started_utc=now(), command=argv, managed_command=command,
            resource_amendment_sha256=sha(amendment_path), host=platform.node(), lane=current_lane.number)
        write(receipt, record)
        with (root/(label+'.log')).open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, pass_fds=(lock.fileno(),))
        record.update(returncode=result.returncode, ended_utc=now(),
                      status='complete' if result.returncode == 0 else 'failed_preserved')
        outputs = [root/label/'execution.json', root/label/'AUDIT.json']
        if '--output' in argv:
            candidate = Path(argv[argv.index('--output')+1])
            if candidate.is_file():
                outputs.append(candidate)
        record['artifacts'] = {str(p):sha(p) for p in outputs if p.is_file()}
        write(receipt, record)
        if result.returncode:
            raise RuntimeError(label+' failed; preserved '+str(receipt))

    campaign.command = managed
    pending = queue.Queue()
    for job in protocol['jobs']:
        pending.put(job)

    def lane(index):
        current_lane.number = index
        while not stop.is_set():
            try:
                job = pending.get_nowait()
            except queue.Empty:
                return
            try:
                label = job['name']+'_segment011k'
                cp = smoke['checkpoint_rows'][-1]['path'] if job['name']=='direct_office_task' else None
                managed(root, label, campaign.training_command(root, job, label, 11000, cp))
                if job['controller']:
                    for row in read(root/label/'execution.json')['rows']:
                        campaign.parameter_audit(root, str(Path(row['run']).relative_to(root)))
                campaign.development(root, job, label)
                with state_lock:
                    state['completed'].append(job['name']); save()
            except BaseException as exc:
                stop.set()
                with state_lock:
                    state['failures'].append(dict(job=job, error=repr(exc))); save()
                return

    save()
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lane, range(2)))
    state.update(status='failed_preserved' if state['failures'] else 'diagnostics_complete_review_required', ended_utc=now())
    save()
    if state['failures']:
        raise RuntimeError(state['failures'])


if __name__ == '__main__':
    main()
