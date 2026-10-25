"""Evaluate an immutable learner snapshot on registered training conditions.

No optimizer updates or replay writes. Uses the same frozen episode adapter,
canonical observation transform, CHEQ context law, physical models and gates.
Partial condition selection is diagnostic only, never a complete comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys

import torch

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def evaluate(args):
    torch.set_num_threads(1)
    root, output = args.runtime.resolve(), args.output.resolve()
    protocol = json.loads(args.registration.read_text())
    if protocol['runtime'] != str(root) or protocol['runtime_sha256'] != sha(root/'RUNTIME.json'):
        raise ValueError('Registered runtime mismatch')
    # Resolve the actor adapter from the frozen training runtime, not whichever
    # checkout happens to launch this evaluator in a later session.
    adapter = root/'source/tools/published_compliance_learner_20261025.py'
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    if hashes['tools/published_compliance_learner_20261025.py'] != sha(adapter):
        raise ValueError('Frozen learner adapter mismatch')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    if sha(protocol['reference_plan']) != protocol['reference_plan_sha256']:
        raise ValueError('Reference plan mismatch')
    conditions = protocol['conditions']
    if args.case_id:
        if not set(args.case_id).issubset({c['id'] for c in conditions}):
            raise ValueError('Unknown evaluation condition')
        conditions = [c for c in conditions if c['id'] in args.case_id]
    for condition in conditions:
        if sha(condition['path']) != condition['sha256']:
            raise ValueError('Condition definition mismatch')
    for cpu in (args.learner_cpu, args.physics_cpu):
        if cpu not in os.sched_getaffinity(0):
            raise ValueError('CPU outside allocation')
    output.mkdir(parents=True, exist_ok=False)
    # Trainer replaces checkpoints atomically. This open copy refers to one
    # complete inode even if another checkpoint is published during the copy.
    snapshot = output/'checkpoint_frozen.pt'
    with args.checkpoint.open('rb') as source, snapshot.open('xb') as target:
        shutil.copyfileobj(source, target)
    checkpoint = torch.load(snapshot, map_location=args.device, weights_only=False)
    if checkpoint['protocol_sha256'] != sha(args.registration):
        raise ValueError('Checkpoint registration mismatch')
    controller, algorithm = checkpoint['controller'], checkpoint['learner']['algorithm']
    prior = json.loads((root/'parameter/PRIORS.json').read_text())
    dimension = 7 if controller == 'direct' else prior['methods'][controller]['action_dimension']
    os.sched_setaffinity(0, {args.learner_cpu})
    learner = PublishedLearner(root, dimension=dimension, direct=controller == 'direct',
        seed=checkpoint['seed'], device=args.device, algorithm=algorithm,
        **{key: checkpoint['learner'][key] for key in ('critic_layer_norm', 'numerical_amendments')
           if key in checkpoint['learner']})
    learner.load_state_dict(checkpoint['learner'])
    initial_updates = learner.learner.num_gradient_steps
    receipt = dict(scope='training_conditions_independent_deterministic_evaluation',
        controller=controller, algorithm=algorithm, training_steps=checkpoint['steps'],
        checkpoint_sha256=sha(snapshot), registration_sha256=sha(args.registration),
        runtime_manifest_sha256=sha(root/'RUNTIME.json'), case_ids=[c['id'] for c in conditions],
        complete_registered_matrix=len(conditions) == len(protocol['conditions']),
        deterministic=True, optimizer_updates_during_evaluation=0, convergence_claim=False,
        actor_dimension=49 if algorithm == 'cheq' else 48,
        source_sha256=sha(__file__), learner_adapter_sha256=sha(adapter),
        learner_cpu=args.learner_cpu, physics_cpu=args.physics_cpu,
        inference_device=str(learner.device),
        inference_gpu_name=torch.cuda.get_device_name(learner.device) if learner.device.type == 'cuda' else None)
    episode_adapter = root/'source/tools/published_compliance_episode_20261025.py'
    if args.audit_substeps:
        episode_adapter = Path(__file__).with_name('audit_published_episode_20261025.py')
    receipt.update(audit_substeps=args.audit_substeps, episode_entrypoint=str(episode_adapter),
        episode_entrypoint_sha256=sha(episode_adapter))
    write(output/'EVALUATION.json', receipt)
    results = []
    for condition in conditions:
        learner.reset_episode()
        folder = output/condition['id']
        command = ['taskset', '-c', str(args.physics_cpu), sys.executable,
            str(episode_adapter),
            '--runtime', str(root), '--output', str(folder), '--fixture', condition['path'],
            '--reference-plan', protocol['reference_plan'], '--controller', controller, '--ipc']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
            OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='disable')
        with (output/(condition['id']+'.stderr.log')).open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=log, text=True, bufsize=1, env=env)
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            actions = 0
            try:
                while True:
                    if not selector.select(timeout=600):
                        raise TimeoutError('Evaluation sampler has no event for600s')
                    line = child.stdout.readline()
                    if not line:
                        raise RuntimeError('Evaluation sampler exited before terminal event')
                    event = json.loads(line)
                    if event['kind'] == 'error':
                        raise RuntimeError(event['error'])
                    if event['kind'] == 'terminal':
                        if event['model_sha256'] != condition['model_sha256']:
                            raise ValueError('Terminal physical model mismatch')
                        if child.wait(timeout=60):
                            raise RuntimeError('Sampler reported terminal but exited nonzero')
                        results.append(dict(condition=condition['id'], category=condition['category'],
                            actions=actions, **event))
                        write(output/'RESULTS.json', dict(evaluation=receipt, episodes=results,
                            finished=len(results) == len(conditions), physical_substep_audit_completed=False))
                        break
                    if event['kind'] != 'observation':
                        raise ValueError('Unknown evaluation event')
                    if actions == 0 and sha(folder/'rollout.mjb') != condition['model_sha256']:
                        raise ValueError('Frozen model mismatch before first action')
                    _, _, action, _ = learner.act(event['observation'],
                        step=checkpoint['steps'], deterministic=True)
                    child.stdin.write(json.dumps(dict(action=action.tolist()))+'\n')
                    child.stdin.flush()
                    actions += 1
            except BaseException as error:
                write(output/'FAILURE.json', dict(condition=condition['id'], error=repr(error)))
                raise
            finally:
                child.stdin.close()
                selector.close()
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child.wait(timeout=30)
    if learner.learner.num_gradient_steps != initial_updates:
        raise AssertionError('Evaluation unexpectedly changed optimizer step count')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--learner-cpu', type=int, required=True)
    parser.add_argument('--physics-cpu', type=int, required=True)
    parser.add_argument('--case-id', action='append')
    parser.add_argument('--audit-substeps', action='store_true',
        help='Record coincident human contact/torque for independent physical audit')
    evaluate(parser.parse_args())
