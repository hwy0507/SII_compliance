"""Evaluate a pinned official SERL state policy on registered conditions.

No optimizer updates or replay writes. Uses the same frozen episode adapter,
canonical48 scaling, normalized-action mapping, physical models and gates.
Deterministic or externally seeded stochastic actions; frozen MuJoCo interpreter.
Partial condition selection is diagnostic only, never a complete comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random

import numpy as np
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


def case_action_seed(action_seed, case_id):
    if action_seed < 0:
        raise ValueError('Nonnegative external evaluation seed required')
    return int.from_bytes(hashlib.sha256(f'{action_seed}:{case_id}'.encode()).digest()[:4], 'little')


def seeded_action(learner, raw_observation, index, key):
    from serl_state_adapter_20261026 import OBSERVATION_SCALE, execution_action
    raw_observation = np.asarray(raw_observation, np.float32)
    if raw_observation.shape != (48,) or not np.isfinite(raw_observation).all() or not 0 <= index < 1375:
        raise ValueError('Expected finite canonical48 and valid known action index')
    observations = dict(state=np.ascontiguousarray(raw_observation / OBSERVATION_SCALE),
                        clock=np.array([(1375-index)/1375],np.float32))
    key, sample_key = learner.jax.random.split(key)
    raw_action = np.asarray(learner.agent.sample_actions(observations, seed=sample_key))
    return execution_action(raw_action), key


def evaluate(args):
    if args.stochastic != (args.action_seed is not None) or (args.action_seed is not None and args.action_seed < 0):
        raise ValueError('Stochastic evaluation needs an explicit nonnegative external seed')
    torch.set_num_threads(1)
    root, output = args.runtime.resolve(), args.output.resolve()
    protocol = json.loads(args.registration.read_text())
    if protocol['runtime'] != str(root) or protocol['runtime_sha256'] != sha(root/'RUNTIME.json'):
        raise ValueError('Registered runtime mismatch')
    # Resolve the actor adapter from the frozen training runtime, not whichever
    # checkout happens to launch this evaluator in a later session.
    adapter_root = Path(protocol['source_adapter'])
    adapter = adapter_root/'serl_state_adapter_20261026.py'
    for name, expected in protocol['source_adapter_hashes'].items():
        if sha(adapter_root/name) != expected:
            raise ValueError('Frozen SERL adapter mismatch: '+name)
    sys.path.insert(0, str(root/'source/tools'))
    sys.path.insert(0, str(adapter_root))
    sys.path.insert(0,str(Path(__file__).parent))
    for name, expected in {**protocol['multistep_stage']['source_hashes'], **protocol['gather_stage']['source_hashes']}.items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Frozen multistep adapter mismatch: '+name)
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner as PublishedLearner
    from validate_serl_state_20261026 import digest
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
    if controller != 'direct' or algorithm != 'serl_state' or checkpoint['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected complete official SERL Direct checkpoint')
    prior = json.loads((root/'parameter/PRIORS.json').read_text())
    dimension = 7 if controller == 'direct' else prior['methods'][controller]['action_dimension']
    os.sched_setaffinity(0, {args.learner_cpu})
    learner = PublishedLearner(root, dimension=dimension, direct=controller == 'direct',
        seed=checkpoint['seed'], device=args.device, algorithm=algorithm,
        upstream=args.serl_upstream, upstream_manifest=args.serl_manifest,
        **{key: checkpoint['learner'][key] for key in ('critic_layer_norm', 'numerical_amendments', 'critic_clock')
           if key in checkpoint['learner']})
    learner.load_state_dict(checkpoint['learner'])
    initial_updates = learner.learner.num_gradient_steps
    initial_state = digest(learner.state_dict())
    assert initial_state == digest(checkpoint['learner'])
    if args.stochastic:
        # Finite sampling gate: same independent key reproduces actions exactly,
        # different key changes samples, and no training RNG or optimizer moves.
        raw_observation=np.zeros(48,np.float32)
        left=right=learner.jax.random.PRNGKey(case_action_seed(args.action_seed,conditions[0]['id']))
        actions_left=[]
        for index in range(3):
            action,left=seeded_action(learner,raw_observation,index,left)
            again,right=seeded_action(learner,raw_observation,index,right)
            np.testing.assert_array_equal(action,again)
            actions_left.append(action)
        other,_=seeded_action(learner,raw_observation,0,learner.jax.random.PRNGKey(case_action_seed(args.action_seed+1,conditions[0]['id'])))
        assert not np.array_equal(actions_left[0],other)
        assert digest(learner.state_dict())==initial_state
        write(output/'EXTERNAL_ACTION_RNG_GATE.json',dict(passed=True,same_seed_actions_exact=True,different_seed_changes_actions=True,full_state_unchanged=True,optimizer_updates=0,new_physics=0))

    receipt = dict(scope=('training_conditions_independent_stochastic_diagnostic' if args.stochastic
                          else 'training_conditions_independent_deterministic_evaluation'),
        controller=controller, algorithm=algorithm, training_steps=checkpoint['steps'],
        checkpoint_sha256=sha(snapshot), registration_sha256=sha(args.registration),
        runtime_manifest_sha256=sha(root/'RUNTIME.json'), case_ids=[c['id'] for c in conditions],
        complete_registered_matrix=len(conditions) == len(protocol['conditions']),
        deterministic=not args.stochastic, action_seed=args.action_seed,
        action_seed_by_case=({c['id']: int.from_bytes(hashlib.sha256(
            f"{args.action_seed}:{c['id']}".encode()).digest()[:4], 'little') for c in conditions}
            if args.stochastic else {}),
        optimizer_updates_during_evaluation=0, convergence_claim=False,
        actor_dimension=49 if algorithm == 'cheq' else 48,
        source_sha256=sha(__file__), learner_adapter_sha256=sha(adapter), multistep_adapter_sha256=sha(Path(__file__).with_name('serl_multistep_state_adapter_20261026.py')),
        serl_source=learner.source_receipt, sampler_python=str(args.sampler_python),
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
        if args.stochastic:
            external_key=learner.jax.random.PRNGKey(case_action_seed(args.action_seed,condition['id']))
        learner.reset_episode()
        folder = output/condition['id']
        command = ['taskset', '-c', str(args.physics_cpu), str(args.sampler_python),
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
                    if args.stochastic:
                        action, external_key = seeded_action(learner, event['observation'], actions, external_key)
                    else:
                        _, _, action, _ = learner.act(event['observation'], step=checkpoint['steps'], deterministic=True)
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
    unchanged = digest(learner.state_dict()) == initial_state
    write(output/'POLICY_UNCHANGED.json', dict(full_learner_state_unchanged=unchanged,
        initial_state_digest=initial_state, final_state_digest=digest(learner.state_dict()),
        new_optimizer_updates=learner.learner.num_gradient_steps-initial_updates))
    if not unchanged:
        raise AssertionError('Deterministic evaluation modified learner state')
    if learner.learner.num_gradient_steps != initial_updates:
        raise AssertionError('Evaluation unexpectedly changed optimizer step count')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serl-upstream', type=Path, required=True)
    parser.add_argument('--serl-manifest', type=Path, required=True)
    parser.add_argument('--sampler-python', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--learner-cpu', type=int, required=True)
    parser.add_argument('--physics-cpu', type=int, required=True)
    parser.add_argument('--case-id', action='append')
    parser.add_argument('--stochastic', action='store_true',
        help='Registered action-sampling diagnostic; leaves physical fixture seeds unchanged')
    parser.add_argument('--action-seed', type=int)
    parser.add_argument('--audit-substeps', action='store_true',
        help='Record coincident human contact/torque for independent physical audit')
    evaluate(parser.parse_args())
