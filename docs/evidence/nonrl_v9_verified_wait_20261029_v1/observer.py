"""Read-only finite host observation, seven samples thirty seconds apart."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]/'code/mujoco_6d_vmc_benchmark'
UNITS = ('run-raa08b13eb33f4583ab899210958345fa.scope',
         'sii-v9-paired-closure-handoff-v3-20261029.service')


def read(path):
    return json.loads(path.read_text())


def props(unit):
    names = ('ActiveState', 'SubState', 'InvocationID', 'MainPID', 'ControlGroup',
             'MemoryCurrent', 'MemoryMax', 'MemorySwapMax', 'Result')
    command = ['systemctl', '--user', 'show', unit]
    for name in names:
        command += ['-p', name]
    output = subprocess.check_output(command, text=True)
    return dict(line.split('=', 1) for line in output.splitlines())


def process(pid):
    p = Path('/proc')/str(pid)
    try:
        stat = (p/'stat').read_text().rsplit(')', 1)[1].split()
        return dict(pid=pid, start_ticks=stat[19], cpu_ticks=int(stat[11])+int(stat[12]),
                    command=(p/'cmdline').read_bytes().replace(b'\0', b' ').decode())
    except FileNotFoundError:
        return None


def sample():
    units = {u: props(u) for u in UNITS}
    group = Path('/sys/fs/cgroup')/units[UNITS[0]]['ControlGroup'].lstrip('/')
    cg = {name: (group/name).read_text().strip() if (group/name).exists() else None
          for name in ('memory.current', 'memory.peak', 'memory.events', 'memory.swap.current', 'cpu.stat')}
    procs = [process(int(p)) for p in (group/'cgroup.procs').read_text().split()] if group.exists() else []
    state = read(ROOT/'outputs/special_scene_frozen108_20261029_v9/execution.json')
    last = state['rows'][-1]
    folder = ROOT/'outputs/special_scene_frozen108_20261029_v9/evaluation'/(last['method']+'__'+last['condition'])
    progress = read(folder/'rollout.progress.json') if (folder/'rollout.progress.json').exists() else None
    return dict(utc=datetime.now(timezone.utc).isoformat(), units=units, cgroup=cg, processes=procs,
        original_status=state['status'], completed=state['completed'],
        task=sum(r['task_success'] for r in state['results']),
        strict=sum(r['strict_success'] for r in state['results']),
        current=dict(method=last['method'], condition=last['condition'], progress=progress),
        paired_handoff=read(ROOT/'outputs/nonrl_v9_paired_scene_closure_20261029_v3/HANDOFF.json'),
        paired_execution_exists=(ROOT/'outputs/nonrl_v9_paired_scene_closure_20261029_v3/execution.json').exists())


destination = HERE/'WAIT.json'
assert not destination.exists()
receipt = dict(status='observing', source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               samples=[], scope='Verified wait only; no dispatch, restart or physical integration')
try:
    for i in range(7):
        row = sample()
        receipt['samples'].append(row)
        for unit in UNITS:
            assert row['units'][unit]['InvocationID'] == receipt['samples'][0]['units'][unit]['InvocationID']
        coordinator = next((p for p in row['processes'] if p and p['pid'] == 1541733), None)
        if row['original_status'] == 'running':
            assert row['units'][UNITS[0]]['ActiveState'] == 'active' and coordinator is not None
            assert row['units'][UNITS[1]]['MainPID'] == '1636845'
        print(json.dumps(dict(sample=i, completed=row['completed'], current=row['current'])), flush=True)
        (HERE/'WAIT.tmp').write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
        (HERE/'WAIT.tmp').replace(destination)
        if row['original_status'] != 'running':
            break
        if i < 6:
            time.sleep(30)
    receipt['status'] = 'finite_verified_wait_complete'
except BaseException as exc:
    receipt.update(status='observation_failed_preserved', error=repr(exc))
    raise
finally:
    destination.write_text(json.dumps(receipt, indent=2, allow_nan=False)+'\n')
