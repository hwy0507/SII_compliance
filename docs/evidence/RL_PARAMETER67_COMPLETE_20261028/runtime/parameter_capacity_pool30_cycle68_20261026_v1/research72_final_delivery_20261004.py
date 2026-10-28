"""One-shot postprocessing after the existing final transition terminates.

Never dispatch physics, fit/select a model, or read sealed condition contents.
Use the original frozen runtime for replay, statistics, figures and saved-state
media. Partial final evidence stays partial; command failures are never retried.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

TERMINAL = {'complete', 'failed_preserved', 'deadline_no_new_dispatch'}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def ready(transition, phase, alive):
    """A terminal final batch is required even if its parent failed afterward."""
    state = read(transition/'execution.json')
    if state['status'] not in TERMINAL:
        assert alive(state), 'Final transition process disappeared; preserve for review'
        return False
    assert (phase/'execution.json').is_file(), 'Transition ended without final evaluations'
    final = read(phase/'execution.json')
    assert final['status'] in TERMINAL, 'Parent ended but final queue shutdown is unverified'
    return True


def owner_alive(state):
    try:
        proc = Path('/proc')/str(state['owner_pid'])
        args = (proc/'cmdline').read_bytes().split(b'\0')
        status = (proc/'status').read_text()
        return (str(Path(state['argv'][0])).encode() in args and
                not any(x.startswith('State:') and 'Z (zombie)' in x for x in status.splitlines()))
    except (FileNotFoundError, ProcessLookupError):
        return False


def replay_plan(candidates, rows):
    assert len(candidates) == 38 and len({c['name'] for c in candidates}) == 38
    models = {c['name']: c for c in candidates}
    reinforcement = [c for c in candidates if c.get('adapted_rl')]
    assert len(reinforcement) == 15
    seen = set()
    for row in rows:
        key = row['candidate'], row['condition_id']
        assert key not in seen and key[0] in models
        seen.add(key)
    return [dict(candidate=c['name'], adapted_rl=c['adapted_rl'],
                 runs=[r['run'] for r in sorted(rows, key=lambda r: r['condition_id'])
                       if r['candidate'] == c['name']])
            for c in sorted(reinforcement, key=lambda c: c['name'])]


def run_delivery(runtime, root, transition, phase, out, execute, guard):
    # Import the already-frozen reporting code, without changing it or reading
    # heldout environmental values. Its loader verifies lock and phase audits.
    sys.path.insert(0, str(runtime/'tools'))
    from research72_comparison_report_20261003 import load_evidence
    guard()
    lock_path = transition/'MODEL_LOCK.json'; digest = sha(lock_path)
    candidates, conditions, rows, evidence, engineering = load_evidence(root, phase, lock_path, digest)
    assert len(conditions) == 24
    plan = replay_plan(candidates, rows)
    write(out/'REPLAY_PLAN.json', dict(model_lock_sha256=digest, models=plan,
        audited_episodes=len(rows), planned_episodes=912, evidence=evidence, engineering=engineering,
        rule='All physically audited RL episodes, including failures and short episodes; no success filter.'))
    receipts = []; incomplete = []
    for item in plan:
        name = item['candidate']; target = out/(name+'.replay.json')
        if not item['runs']:
            incomplete.append(dict(candidate=name, reason='No physically audited episodes'))
            continue
        rl = item['adapted_rl']
        command = [sys.executable, str(runtime/'tools/research72_rl_actor_replay_20261004.py'),
            '--checkpoint-manifest', rl['manifest'], '--parameter-source', rl['parameter_source'],
            '--runs', *item['runs'], '--output', str(target)]
        guard()
        rc = execute('replay_'+name, command)
        if target.exists():
            status = read(target)['status']
            if status in ('complete', 'failed_preserved'):
                receipts.append(target)
            else:
                incomplete.append(dict(candidate=name, reason='Nonterminal replay receipt', returncode=rc))
        if rc or not target.exists():
            incomplete.append(dict(candidate=name, reason='Replay command failed or receipt missing', returncode=rc))
        # Continue peers after a failed replay; the report keeps missing coverage.
    report = out/'comparison'
    guard()
    command = [sys.executable, str(runtime/'tools/research72_comparison_report_20261003.py'),
        '--root', str(root), '--phase', str(phase), '--model-lock', str(lock_path),
        '--lock-sha256', digest, '--output', str(report), '--rl-actor-replay', *map(str, receipts)]
    assert execute('comparison', command) == 0, 'Report verification failed; preserve all evidence'
    summary = read(report/'REPORT.json')
    outputs = dict(report_sha256=sha(report/'REPORT.json'), matrix_sha256=sha(report/'MATRIX.md'))
    for label, script, extra in (
        ('figures', 'plot_research72_comparison_20261003.py', []),
        ('media', 'research72_media_20261003.py', ['--model-lock', str(lock_path)])):
        guard()
        rc = execute(label, [sys.executable, str(runtime/'tools'/script),
            '--report', str(report/'REPORT.json'), '--output', str(out/label), *extra])
        if rc:
            incomplete.append(dict(step=label, reason='Command failed; no retry', returncode=rc))
    media_path = out/'media/execution.json'
    media = read(media_path) if media_path.exists() else {}
    if media.get('status') != 'complete':
        incomplete.append(dict(step='media', reason='Media coverage incomplete', status=media.get('status')))
    if summary['audited'] != 912 or summary['independent_rl_actor_replay']['status'] != 'complete':
        incomplete.append(dict(step='evidence', reason='Physical or independent actor coverage incomplete'))
    guard()
    assert sha(lock_path) == digest and sha(report/'REPORT.json') == outputs['report_sha256']
    return dict(status='complete_with_gaps' if incomplete else 'complete', incomplete=incomplete,
        audited_episodes=summary['audited'], planned_episodes=912,
        rl_actor_replay=summary['independent_rl_actor_replay']['status'], **outputs,
        scope='Postprocessing only. Manuscript interpretation and visual inspection still require researcher review; no automatic winner or submission-ready claim.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'runtime', 'transition', 'phase', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    root, runtime, transition, phase, out = (getattr(args, x).resolve() for x in
        ('root', 'runtime', 'transition', 'phase', 'output'))
    assert out.parent == transition.parent == phase.parent == root
    assert len({out, transition, phase}) == 3
    assert not out.exists()
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 3*1024**3
    sys.path.insert(0, str(runtime/'tools'))
    from research72_final_lock_20261003 import runtime_hashes
    from run_paper_final_validation_20261003 import ENV
    spec = read(transition/'SPECIFICATION.json')
    assert Path(spec['runtime']).resolve() == runtime
    assert runtime_hashes(runtime) == spec['runtime_source_sha256']
    protocol_digest = sha(root/'PROTOCOL.json')
    assert protocol_digest == spec['protocol_sha256']
    out.mkdir(); handle = (out/'coordinator.lock').open('x')
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    registration = dict(created_utc=now(), source_sha256=sha(__file__), runtime=str(runtime),
        runtime_source_commit=spec['runtime_source_commit'], protocol_sha256=protocol_digest,
        transition_specification_sha256=sha(transition/'SPECIFICATION.json'),
        expected_models=38, expected_episodes=912, physics_steps=0, training_updates=0,
        sealed_contents_read=False, scheduled_automation=False, automatic_retries=False,
        commands_use_original_frozen_runtime=True)
    write(out/'SPECIFICATION.json', registration)
    state = dict(status='waiting_for_final', started_utc=now(), owner_pid=os.getpid(), argv=sys.argv,
                 specification_sha256=sha(out/'SPECIFICATION.json'), steps=[])
    def save():
        write(out/'execution.json', state)
    def guard():
        assert sha(__file__) == registration['source_sha256']
        assert sha(root/'PROTOCOL.json') == protocol_digest
        assert sha(transition/'SPECIFICATION.json') == registration['transition_specification_sha256']
        assert runtime_hashes(runtime) == spec['runtime_source_sha256']
    def execute(label, command):
        # Sequential postprocessing, no simulation slot or extra physical budget.
        env = {**os.environ, **ENV, 'PYTHONDONTWRITEBYTECODE':'1',
               'SII_SOURCE_BASE_COMMIT':spec['runtime_source_commit']}
        state['status'] = 'running_'+label
        row = dict(label=label, command=command, started_utc=now()); state['steps'].append(row); save()
        with (out/(label+'.log')).open('x') as log:
            rc = subprocess.run(command, cwd=runtime, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        row.update(returncode=rc, ended_utc=now()); save()
        return rc
    save()
    try:
        while not ready(transition, phase, owner_alive):
            state['last_checked_utc'] = now(); save(); time.sleep(30)
        guard()
        state.update(run_delivery(runtime, root, transition, phase, out, execute, guard))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = now(); save(); handle.close()


if __name__ == '__main__':
    main()
