"""Replay immutable actions through a candidate and compare full physical evidence.

Finite validation only: no learner, optimizer, replay write or training dispatch.
Observation timeouts poll the same child; a timeout never creates a replacement.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def compare_npz(expected, actual):
    with np.load(expected, allow_pickle=False) as left, np.load(actual, allow_pickle=False) as right:
        if set(left.files) != set(right.files):
            raise AssertionError('Array keys differ: '+str(actual))
        for key in left.files:
            a, b = left[key], right[key]
            if a.shape != b.shape or a.dtype != b.dtype or a.tobytes() != b.tobytes():
                raise AssertionError('Array differs: '+str(actual)+' / '+key)
        return dict(arrays=list(left.files), exact=True)


def compare_episode(expected, actual, candidate):
    checks = {}
    for name in ('rollout.mjb', 'actor_intervals.jsonl', 'TERMINAL.json', 'audit_substeps.npy'):
        if sha(expected/name) != sha(actual/name):
            raise AssertionError('File differs: '+name)
        checks[name] = dict(sha256=sha(actual/name), exact=True)
    for name in ('rollout.npz', 'audit_filter.npz', 'audit_torque.npz'):
        checks[name] = compare_npz(expected/name, actual/name)
    before = json.loads((expected/'rollout.json').read_text())
    after = json.loads((actual/'rollout.json').read_text())
    hashes = json.loads((candidate/'SOURCE_HASHES.json').read_text())
    changed = {'audited_velocity_env.py', 'validate_office_apparatus_v5_20260917.py'}
    if set(before['source_sha256']) != set(after['source_sha256']):
        raise AssertionError('Reported source set changed')
    for name, digest in before['source_sha256'].items():
        target = hashes['scripts/'+name] if name in changed else digest
        if after['source_sha256'][name] != target:
            raise AssertionError('Unexpected reported source: '+name)
    before.pop('source_sha256')
    after.pop('source_sha256')
    # Only normalize the exact episode-output prefix; numeric/result fields
    # and other source/asset hashes retain exact comparison.
    def normalized(value, folder):
        return json.dumps(value, sort_keys=True, allow_nan=False).replace(str(folder), '<episode>')
    if normalized(before, expected) != normalized(after, actual):
        raise AssertionError('Full rollout result differs beyond registered provenance')
    checks['rollout.json'] = dict(exact_except_registered_source_hashes_and_output_prefix=True)
    before_audit = json.loads((expected/'AUDIT_EXTENSION.json').read_text())
    after_audit = json.loads((actual/'AUDIT_EXTENSION.json').read_text())
    if not after_audit['completed'] or after_audit['samples'] != before_audit['samples']:
        raise AssertionError('Incomplete or different physical sample count')
    return dict(checks=checks, physical_substeps=after_audit['samples'],
                task=after['task_success'], strict=after['strict_success'])


def main(args):
    protocol = json.loads(args.registration.read_text())
    for path, digest in protocol['input_hashes'].items():
        if sha(path) != digest:
            raise ValueError('Registered input drift: '+path)
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Validator source drift')
    output, candidate = Path(protocol['output']), Path(protocol['candidate_runtime'])
    output.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {protocol['cpu']})
    os.nice(protocol['nice'])
    results = []
    start = time.time()
    for case in protocol['cases']:
        expected = Path(case['reference_episode'])
        actual = output/case['controller']/case['case_id']
        actual.parent.mkdir(parents=True, exist_ok=True)
        tape = [json.loads(line) for line in (expected/'actor_intervals.jsonl').read_text().splitlines()]
        command = [sys.executable, '-B', protocol['audit_wrapper'], '--runtime', str(candidate),
            '--output', str(actual), '--fixture', case['fixture'],
            '--reference-plan', protocol['reference_plan'], '--controller', case['controller'], '--ipc']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', MUJOCO_GL='disable',
            OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
        with (actual.parent/(case['case_id']+'.stderr.log')).open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=log, text=True, bufsize=1, env=env)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            actions = 0
            terminal = False
            try:
                while True:
                    write(output/'PROGRESS.json', dict(controller=case['controller'], case_id=case['case_id'],
                        child_pid=child.pid, actions_verified=actions, completed_cases=len(results),
                        planned_cases=len(protocol['cases']), updated_unix=time.time()))
                    if not selector.select(timeout=30):
                        if child.poll() is not None:
                            raise RuntimeError('Candidate exited without terminal event')
                        continue
                    line = child.stdout.readline()
                    if not line:
                        raise RuntimeError('Candidate pipe closed before terminal event')
                    event = json.loads(line)
                    if event['kind'] == 'terminal':
                        if actions != len(tape):
                            raise AssertionError('Candidate action count differs')
                        terminal = True
                        break
                    if event['kind'] != 'observation':
                        raise RuntimeError('Unexpected candidate event: '+str(event))
                    if actions >= len(tape):
                        raise AssertionError('Candidate asks for extra action')
                    target = tape[actions]
                    for key in ('observation', 'interval', 'payload_potential'):
                        if event[key] != target[key]:
                            raise AssertionError(f'Action {actions}: {key} differs')
                    if actions == 0 and sha(actual/'rollout.mjb') != case['model_sha256']:
                        raise AssertionError('Candidate MJB mismatch')
                    child.stdin.write(json.dumps(dict(action=target['action']))+'\n')
                    child.stdin.flush()
                    actions += 1
                # The child records its audit after sending terminal. Keep the
                # same handle alive while that finite flush finishes.
                while child.poll() is None:
                    try:
                        child.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        write(output/'FLUSH_WAIT.json', dict(child_pid=child.pid, updated_unix=time.time()))
                if child.returncode:
                    raise RuntimeError('Candidate exited nonzero after terminal')
                comparison = compare_episode(expected, actual, candidate)
                results.append(dict(controller=case['controller'], case_id=case['case_id'],
                    actions=actions, candidate_episode=str(actual), **comparison))
                write(output/'RESULTS.json', dict(episodes=results, finished=False))
            except BaseException as error:
                write(output/'FAILURE.json', dict(controller=case['controller'], case_id=case['case_id'],
                    actions_verified=actions, child_pid=child.pid, error=repr(error), updated_unix=time.time()))
                # Stop only this failed validation child, never formal jobs.
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=30)
                raise
            finally:
                child.stdin.close()
                selector.close()
                if not terminal and child.poll() is None:
                    child.terminate()
                    child.wait(timeout=30)
    write(output/'FINISHED.json', dict(started_unix=start, ended_unix=time.time(), episodes=results,
        registration_sha256=sha(args.registration), source_sha256=sha(__file__),
        finished=True, optimizer_updates=0, training_runtime_changed=False,
        limitation='Finite 12 archived trajectories; action-tape validation, not new task performance '
        'or online training speed measurement. Deployment still requires a registered stage boundary.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
