"""Replace only an idle RL coordinator; preserve all simulation processes.

Create an independent runtime and amendment. Refuse any prior RL dispatch,
unexpected service PID/command or existing output. Never rewrite old receipts.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

FILES = ('research72_rl_campaign_20261003.py', 'research72_rl_schedule_20261003.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False); stream.write('\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('root', 'old-runtime', 'new-runtime', 'overlay', 'output'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--expected-execution-sha256', required=True)
    a = p.parse_args(); root = a.root.resolve(); old = root/'rl_office_adaptation_v1'
    service = 'sii-r72-rl-office-adaptation-v1.service'
    for path in (a.new_runtime, a.output, root/'rl_office_adaptation_v2', root/'AMENDMENT_RL_ROUND_ROBIN.json'):
        assert not path.exists(), 'Existing output: '+str(path)
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    assert sha(old/'execution.json') == a.expected_execution_sha256
    assert read(old/'execution.json')['status'] == 'waiting_for_predecessor'
    assert not list(old.glob('queue_*'))
    # Check the exact registered coordinator, not a pattern-matched simulator.
    before = subprocess.check_output(['systemctl', '--user', 'show', service,
        '-p', 'MainPID', '-p', 'ActiveState', '-p', 'SubState'], text=True)
    properties = dict(line.split('=', 1) for line in before.splitlines())
    assert properties['ActiveState'] == 'active' and properties['SubState'] == 'running'
    pid = int(properties['MainPID']); assert pid > 1
    argv = (Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')
    assert str(a.old_runtime.resolve()/'tools'/FILES[0]).encode() in argv
    assert str(old).encode() in argv
    assert read(root/'followup_v1/execution.json')['status'] != 'complete'
    overlay = {name: sha(a.overlay/'tools'/name) for name in FILES}
    a.output.mkdir(parents=False)
    subprocess.run(['systemctl', '--user', 'stop', service], check=True)
    after = subprocess.check_output(['systemctl', '--user', 'show', service,
        '-p', 'MainPID', '-p', 'ActiveState', '-p', 'SubState'], text=True)
    assert 'MainPID=0' in after and 'ActiveState=inactive' in after
    assert sha(old/'execution.json') == a.expected_execution_sha256
    assert not list(old.glob('queue_*'))
    shutil.copytree(a.old_runtime, a.new_runtime,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs'))
    for name in FILES:
        shutil.copy2(a.overlay/'tools'/name, a.new_runtime/'tools'/name)
        assert sha(a.new_runtime/'tools'/name) == overlay[name]
    original_train = a.old_runtime/'tools/research72_train_rl_20261003.py'
    new_train = a.new_runtime/'tools/research72_train_rl_20261003.py'
    assert sha(original_train) == sha(new_train)
    # Every runnable file is preserved except the two explicitly listed tools.
    def hashes(path):
        return {str(f.relative_to(path)): sha(f) for folder in ('tools', 'scripts', 'assets')
                for f in (path/folder).rglob('*') if f.is_file()
                and '__pycache__' not in f.parts and 'outputs' not in f.relative_to(path).parts
                and f.suffix != '.pyc'}
    previous = hashes(a.old_runtime); updated = hashes(a.new_runtime)
    expected_changes = {'tools/'+name for name in FILES}
    assert set(previous)-set(updated) == set()
    changed = {name for name, digest in updated.items() if previous.get(name) != digest}
    assert changed <= expected_changes
    receipt = dict(status='complete', completed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), old_service=service, old_service_before=before, old_service_after=after,
        old_execution_sha256=sha(old/'execution.json'), old_specification_sha256=sha(old/'SPECIFICATION.json'),
        old_receipts_preserved=True, stopped_physics_processes=0, old_rl_physics_episodes=0,
        old_runtime=str(a.old_runtime), new_runtime=str(a.new_runtime), overlay_sha256=overlay,
        unchanged_trainer_sha256=sha(new_train), runtime_files_sha256=updated,
        changes=sorted(changed), source_base_commit='2da38895ce8a91eb9cc7b47d94a72e53ff615166',
        source_provenance='Independent copy of rl_runtime_v3 plus the two hashed scheduling files; not a clean-commit runtime.')
    write(a.output/'execution.json', receipt)
    amendment = dict(registered_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha(root/'PROTOCOL.json'), scope='outcome_independent_round_robin_rl_dispatch',
        cumulative_step_boundaries=[5500,27500,49500,71500,80000],
        active_campaign='rl_office_adaptation_v2', superseded_campaign=old.name,
        superseded_execution_sha256=sha(old/'execution.json'),
        supersession_receipt=str(a.output/'execution.json'), supersession_receipt_sha256=sha(a.output/'execution.json'),
        reason='Reduce risk that a late queued family/seed has no checkpoint at the fixed development cutoff. Registered before any office RL training outcome.',
        unchanged=['15 family/seed jobs', '80000 total-step optimizer schedule and per-model cap',
            'original deadline', 'reward', 'agent configuration', 'training identities',
            'replay/RNG/normalization/optimizer continuation', 'latest completed boundary selection',
            'geometry, task and strict gates, actor fields and actuator limits', 'three leased queues'],
        limitations=['More process launches may increase compilation overhead.',
            'Actual episode-boundary steps may differ below the common cap; report every value.',
            'A concluded finite queue is not evidence of optimizer convergence or success.',
            'The former waiting registration remains historical and is not a second training cohort.'],
        physical_continuation_verified=False, sealed_contents_read=False)
    write(root/'AMENDMENT_RL_ROUND_ROBIN.json', amendment)
    print(json.dumps(dict(amendment_sha256=sha(root/'AMENDMENT_RL_ROUND_ROBIN.json'),
        receipt_sha256=sha(a.output/'execution.json'), runtime=str(a.new_runtime), physics_processes_stopped=0)))


if __name__ == '__main__':
    main()
