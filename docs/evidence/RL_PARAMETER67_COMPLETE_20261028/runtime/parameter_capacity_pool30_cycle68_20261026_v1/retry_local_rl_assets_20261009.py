"""Retry only the verified pre-physics missing-Menagerie failure, in a new path.

The other registered local lane may finish its existing training. This launcher
occupies the vacant lane only; it never stops or restarts the healthy learner.
"""
import argparse
import fcntl
import os
from pathlib import Path
import platform
import subprocess
import sys

import local_rl_campaign_20261009 as campaign
from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert platform.node() == 'airpig'
    lock = (root/'.assets-retry.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    parent = read(root/'parallel.execution.json')
    assert parent['failures'] and parent['failures'][0]['job']['name'] == 'direct_office_task'
    assert campaign.hashes(root/'source') == read(root/'SOURCE_HASHES.json')
    assert campaign.hashes(root/'parameter_fullrange') == read(root/'PARAMETER_HASHES.json')
    protocol = read(root/'PROTOCOL.json')
    runtime = Path(protocol['runtime'])
    assert {name:campaign.hashes(runtime/name) for name in read(root/'RUNTIME_HASHES.json')} == read(root/'RUNTIME_HASHES.json')
    live = subprocess.check_output(['systemctl', '--user', 'list-units', '--type=service',
        '--state=running', '--no-legend', '--plain', '--no-pager'], text=True)
    own_unit = Path(Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1]).name
    lanes = [line for line in live.splitlines() if 'sii-local-rl-' in line and '-lane' in line
             and line.split()[0] != own_unit]
    assert len(lanes) <= 1 and all('-lane1-' in line for line in lanes), 'Vacant lane0 required'
    label = 'direct_office_task_segment011k__repair_development_000'
    receipt = root/(label+'.execution.json')
    old = read(receipt)
    assert old['status'] == 'failed_preserved' and old['returncode'] == 1
    log = root/(label+'.log')
    assert 'FileNotFoundError: MuJoCo Menagerie not found:' in log.read_text()
    assert not (root/label/'rollout.npz').exists()
    assert not (root/label/'rollout_metrics').exists()
    argv = list(old['command'])
    assert argv[0] == sys.executable
    assert argv[argv.index('--worker-kind')+1] == 'adapted_rl'
    assert Path(argv[argv.index('--output')+1]) == root/label
    label += '_assets_retry_v2'
    argv[argv.index('--output')+1] = str(root/label)
    new_receipt = root/(label+'.execution.json')
    assert not new_receipt.exists() and not (root/label).exists()
    env = dict(os.environ, MUJOCO_MENAGERIE_PATH=str(runtime/'menagerie'),
               SII_LOCAL_RUNTIME=str(runtime), SII_SOURCE_BASE_COMMIT=protocol['source_base_commit'])
    state = dict(status='running', started_utc=now(), host=platform.node(), command=argv,
        launch_source_sha256=sha(__file__), protocol_sha256=sha(root/'PROTOCOL.json'),
        environment_correction={k:env[k] for k in ('MUJOCO_MENAGERIE_PATH','SII_SOURCE_BASE_COMMIT')},
        preserved_failed_attempt=dict(receipt=str(receipt), receipt_sha256=sha(receipt),
            log=str(log), log_sha256=sha(log), physics_steps=0),
        explanation='One vacant local lane; unchanged checkpoint/model/condition, no new training')
    write(new_receipt, state)
    with (root/(label+'.log')).open('x') as stream:
        result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, env=env,
                                pass_fds=(lock.fileno(),))
    state.update(ended_utc=now(), returncode=result.returncode,
                 status='complete' if result.returncode == 0 else 'failed_preserved')
    state['artifacts'] = {str(root/label/name):sha(root/label/name)
                          for name in ('execution.json','AUDIT.json') if (root/label/name).exists()}
    write(new_receipt, state)
    if result.returncode:
        raise RuntimeError('Retry failed; both attempts preserved')


if __name__ == '__main__':
    main()
