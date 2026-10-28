"""One foreground observer for the existing finite local RL queue, not a timer.

Never launches/restarts training, simulation, or a remote command. Records real
receipt changes and audits completed configurations. Exits on queue completion
or failure; stale physics progress is reported without terminating a learner.
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from office_v7_uniform24_20261008 import read, write, sha, now


def snapshot(root, jobs):
    state = read(root/'parallel_v2.execution.json')
    training, evaluations, active = [], [], []
    for job in jobs:
        label = job['name']+'_segment011k'
        path = root/label/'execution.json'
        if path.exists():
            train = read(path)
            training.append(dict(method=job['name'], **{key: train.get(key) for key in
                ('status', 'steps', 'episodes', 'updates')}))
        for path in sorted(root.glob(label+'__repair_development_*.execution.json')):
            if path.name.endswith('_parameter_audit.execution.json'):
                continue
            receipt = read(path)
            evaluations.append(dict(receipt=path.name, status=receipt['status']))
            if receipt['status'] == 'running':
                progress_path = path.with_name(path.name.removesuffix('.execution.json'))/'rollout.progress.json'
                if progress_path.exists():
                    # Historical frozen evaluator writes this tiny sidecar
                    # in place. A concurrent read can see an empty/partial JSON;
                    # that is not evidence that physics or its receipt failed.
                    try:
                        progress = read(progress_path)
                    except (json.JSONDecodeError, FileNotFoundError):
                        active.append(dict(receipt=path.name, progress_read='writer_in_progress'))
                        continue
                    age = max(0., time.time()-progress_path.stat().st_mtime)
                    active.append(dict(receipt=path.name, simulated_s=progress.get('time_s'),
                        stage=progress.get('stage'), stale_over_15min=age > 900))
    return dict(coordinator_status=state['status'], completed_configurations=state['completed'],
        failures=state['failures'], training=training, evaluations=evaluations, active=active)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--supersedes-observer', type=Path)
    a = p.parse_args(); root = a.root.resolve(); out = a.output.resolve()
    assert platform.node() == 'airpig'
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    protocol = read(root/'PROTOCOL.json'); jobs = protocol['jobs']
    deadline = datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])+timedelta(hours=1)
    out.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    names = ('watch_local_rl_campaign_20261009.py', 'audit_local_rl_development_20261009.py',
             'inspect_local_rl_progress_20261009.py')
    sources = {str(tools/name):sha(tools/name) for name in names}
    execution = dict(status='observing', started_utc=now(), host=platform.node(),
        protocol_sha256=sha(root/'PROTOCOL.json'), source_sha256=sources, audits=[],
        policy='Read-only finite foreground observer. No simulation/training/restarts/remote work; no scheduled task.',
        command=sys.argv)
    if a.supersedes_observer:
        parent = a.supersedes_observer.resolve()
        assert read(parent)['status'] == 'failed_preserved'
        execution['superseded_observer'] = dict(path=str(parent), sha256=sha(parent),
            reason='Read-only observer upgrade: tolerate in-place progress writes and exclude audit receipts from episode list. Training/evaluation coordinator untouched.')

    def save():
        execution['updated_utc'] = now(); write(out/'execution.json', execution)

    def run_audit(name, output):
        assert {path:sha(path) for path in sources} == sources
        command = [sys.executable, str(tools/name), '--root', str(root), '--output', str(output)]
        record = dict(command=command, started_utc=now()); execution['audits'].append(record); save()
        with output.with_suffix('.log').open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        record.update(returncode=result.returncode, ended_utc=now())
        if output.exists(): record['output_sha256'] = sha(output)
        save()
        if result.returncode: raise RuntimeError('Audit failed, artifacts preserved: '+str(output))

    previous = None; audited = set(); training_audited = set(); sequence = 0
    save()
    try:
        with (out/'events.jsonl').open('x') as events:
            while True:
                state = snapshot(root, jobs)
                if state != previous:
                    events.write(json.dumps(dict(time_utc=now(), **state))+'\n'); events.flush()
                    execution['latest'] = state; save()
                    print(json.dumps(dict(time_utc=now(), **state)), flush=True)
                    previous = state
                complete_training = {r['method'] for r in state['training'] if r['status'] == 'complete'}
                if complete_training-training_audited:
                    sequence += 1
                    run_audit('inspect_local_rl_progress_20261009.py', out/f'training_{sequence:03d}.json')
                    training_audited = complete_training
                completed = set(state['completed_configurations'])
                if completed-audited:
                    sequence += 1
                    run_audit('audit_local_rl_development_20261009.py', out/f'development_{sequence:03d}.json')
                    audited = completed
                if state['coordinator_status'] == 'diagnostics_complete_review_required':
                    assert len(completed) == len(jobs)
                    run_audit('audit_local_rl_development_20261009.py', out/'FINAL_DEVELOPMENT_AUDIT.json')
                    result = read(out/'FINAL_DEVELOPMENT_AUDIT.json')
                    assert len(result['methods']) == len(jobs)
                    assert all(m['all_development_complete'] for m in result['methods'])
                    assert all(r['parameter_audit_present'] is not False for m in result['methods'] for r in m['episodes'])
                    execution.update(status='complete_review_required', ended_utc=now()); save(); return
                if state['coordinator_status'] == 'failed_preserved':
                    raise RuntimeError('Coordinator failed; no automatic restart authorized by this observer')
                if datetime.now(timezone.utc) > deadline:
                    raise RuntimeError('Observer safety deadline reached; learners not touched')
                time.sleep(30)
    except BaseException as error:
        execution.update(status='failed_preserved', ended_utc=now(), error=repr(error)); save(); raise


if __name__ == '__main__':
    main()
