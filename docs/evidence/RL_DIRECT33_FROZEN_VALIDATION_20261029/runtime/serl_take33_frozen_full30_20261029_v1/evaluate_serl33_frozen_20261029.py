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


def seeded_action(learner, raw_observation, index, key, noise_schedule='independent'):
    from serl_state_adapter_20261026 import OBSERVATION_SCALE, execution_action
    raw_observation = np.asarray(raw_observation, np.float32)
    if raw_observation.shape != (48,) or not np.isfinite(raw_observation).all() or not 0 <= index < 1375:
        raise ValueError('Expected finite canonical48 and valid known action index')
    observations = dict(state=np.ascontiguousarray(raw_observation / OBSERVATION_SCALE),
                        clock=np.array([(1375-index)/1375],np.float32))
    if noise_schedule not in ('independent', 'episode_constant'):
        raise ValueError('Unknown registered noise schedule')
    next_key, sample_key = learner.jax.random.split(key)
    raw_action = np.asarray(learner.agent.sample_actions(observations, seed=sample_key))
    # Constant base noise still passes through the state-dependent policy at
    # every action. It does not hold the public action or inject nominal control.
    return execution_action(raw_action), next_key if noise_schedule == 'independent' else key


def evaluate(args):
    if args.stochastic != (args.action_seed is not None) or (args.action_seed is not None and args.action_seed < 0):
        raise ValueError('Stochastic evaluation needs an explicit nonnegative external seed')
    if not args.stochastic and args.noise_schedule != 'independent':
        raise ValueError('A noise schedule applies only to stochastic evaluation')
    if not args.check_only and args.expected_cycle != 33:
        raise ValueError('Physical evaluation is registered only for complete33')
    if args.expected_cycle < 27:
        raise ValueError('Complete recovered take27 or later checkpoints only')
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
    if checkpoint['cycle'] != args.expected_cycle:
        raise ValueError('Exact registered checkpoint cycle required')
    controller, algorithm = checkpoint['controller'], checkpoint['learner']['algorithm']
    if controller != 'direct' or algorithm != 'serl_state' or checkpoint['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected complete official SERL Direct checkpoint')
    # Validate recovery contracts as recorded; never relabel partial25 as complete.
    import resume_serl_take_recovery_continuation_20261027 as continuation
    import resume_serl_recovery26_take27_20261027 as entry
    import resume_serl_interrupted25_20261027 as recovery
    import resume_serl_capacity_reviewed_continuation_20261027 as old
    from train_serl_state_20261026 import Replay
    stage = protocol['recovery_continuation_stage']
    validator = entry if stage['parent_cycle'] == 26 else continuation
    previous = validator.validate_protocol(stage['parent_registration']['sha256'], protocol, sha(args.registration))
    continuation.validate_parent(checkpoint, protocol)
    original = continuation.original_recovery_protocol(protocol)
    interrupted = recovery.validate_protocol(original['interrupted_stream_recovery']['parent_registration']['sha256'], original, '')
    old.validate(interrupted['resume_parent_registration']['sha256'], interrupted, '')
    old.validate_capacity(protocol, previous)
    required_modules = ['resume_serl_recovery26_take27_20261027.py',
        'resume_serl_interrupted25_20261027.py', 'resume_serl_capacity_reviewed_continuation_20261027.py',
        'serl_replay_capacity_20261027.py', 'serl_multistep_state_adapter_20261026.py',
        'serl_multistep_replay_gather_20261026.py', 'train_serl_state_20261026.py',
        'validate_serl_state_20261026.py']
    for name in required_modules:
        if sha(Path(__file__).with_name(name)) != stage['source_hashes'][name]:
            raise ValueError('Frozen recovery dependency drift: '+name)
    for name, expected in stage['source_hashes'].items():
        if sha(Path(stage['runtime'])/name) != expected:
            raise ValueError('Original continuation dependency drift: '+name)
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen source mismatch: '+name)
    if checkpoint['replay'].get('replay_capacity_extension') != protocol['replay_capacity_stage']['marker']:
        raise ValueError('Persisted capacity marker required; evaluation cannot migrate')
    # Bind all930 quarantined tails to the original interrupted snapshot, not just their count.
    interrupted_ref = protocol['interrupted_stream_recovery']['checkpoint']
    if sha(interrupted_ref['path']) != interrupted_ref['sha256']:
        raise ValueError('Original interrupted snapshot hash drift')
    interrupted_checkpoint = torch.load(interrupted_ref['path'], map_location='cpu', weights_only=False)
    recovery.validate_parent(interrupted_checkpoint, protocol['interrupted_stream_recovery'])
    extra = checkpoint['replay']['multistep_target_extension']
    old_extra = interrupted_checkpoint['replay']['multistep_target_extension']
    if digest(extra['pending']) != digest(old_extra['pending']):
        raise ValueError('Original930 pending queues changed')
    pending_indices = np.asarray([i for rows in extra['pending'].values() for i in rows], dtype=np.int64)
    if len(pending_indices) != 930 or len(np.unique(pending_indices)) != 930:
        raise ValueError('Expected930 distinct quarantined rows')
    for name, values in interrupted_checkpoint['replay']['arrays'].items():
        np.testing.assert_array_equal(checkpoint['replay']['arrays'][name][pending_indices], values[pending_indices])
    for name in ['target_rewards','target_bootstrap','target_endpoints','target_lengths']:
        np.testing.assert_array_equal(extra[name][pending_indices], old_extra[name][pending_indices])
    if not np.all(extra['target_endpoints'][pending_indices] == -1) or set(pending_indices).intersection(extra['ready']):
        raise ValueError('Quarantined pending row became mature/sampleable')
    if checkpoint['cycles'][:len(interrupted_checkpoint['cycles'])] != interrupted_checkpoint['cycles']:
        raise ValueError('Pre-interruption complete-cycle history changed')
    recovery_state = dict(quarantined_pending=930, original_pending_exact=True,
        original_pending_raw_derived_exact=True, pending_not_mature_or_sampleable=True,
        original_interrupted_checkpoint_sha256=interrupted_ref['sha256'],
        pending_digest=digest(extra['pending']), complete25_invented=False,
        complete_cycles_after_recovery=[c['cycle'] for c in checkpoint['cycles'] if c['cycle'] >= 25])
    del interrupted_checkpoint, old_extra
    expanded = old.capacity_replay(Replay, protocol, checkpoint)
    guarded = recovery.quarantine_replay(expanded, extra['pending'])
    replay = guarded(7, 49, 20261079)
    replay.load_state_dict(checkpoint['replay'])
    replay_digest = digest(replay.state_dict())
    if replay_digest != digest(checkpoint['replay']):
        raise ValueError('Full expanded replay restoration changed state')
    history_digest = digest(checkpoint['cycles'])
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
            action,left=seeded_action(learner,raw_observation,index,left,args.noise_schedule)
            again,right=seeded_action(learner,raw_observation,index,right,args.noise_schedule)
            np.testing.assert_array_equal(action,again)
            actions_left.append(action)
        other,_=seeded_action(learner,raw_observation,0,learner.jax.random.PRNGKey(case_action_seed(args.action_seed+1,conditions[0]['id'])))
        assert not np.array_equal(actions_left[0],other)
        if args.noise_schedule == 'episode_constant':
            for action in actions_left[1:]:
                np.testing.assert_array_equal(action, actions_left[0])
        else:
            assert not np.array_equal(actions_left[0], actions_left[1])
        assert digest(learner.state_dict())==initial_state
        write(output/'EXTERNAL_ACTION_RNG_GATE.json',dict(passed=True,same_seed_actions_exact=True,different_seed_changes_actions=True,noise_schedule=args.noise_schedule,temporal_sampling_gate_passed=True,full_state_unchanged=True,optimizer_updates=0,new_physics=0))

    write(output/'FULL_STATE_RESTORE.json', dict(passed=True,
        checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle'],
        full_learner_state_exact=True, full_replay_state_exact=True,
        learner_digest=initial_state, replay_digest=replay_digest,
        history_digest=history_digest, recovery_state=recovery_state, replay_capacity=replay.capacity,
        replay_size=replay.size, historical_capacity_entry=23,
        optimizer_updates=0, new_physics=0, replay_writes=0))
    if args.check_only:
        assert digest(replay.state_dict()) == replay_digest
        assert digest(learner.state_dict()) == initial_state
        write(output/'CHECK_ONLY_REVIEW.json', dict(passed=True,
            full_learner_state_exact=True, full_replay_state_exact=True,
            external_action_rng_gate=bool(args.stochastic),
            optimizer_updates=0, new_physics=0, replay_writes=0,
            checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle'], recovery_state=recovery_state))
        return
    receipt = dict(scope=('training_conditions_independent_stochastic_diagnostic' if args.stochastic
                          else 'training_conditions_independent_deterministic_evaluation'),
        controller=controller, algorithm=algorithm, training_steps=checkpoint['steps'],
        checkpoint_sha256=sha(snapshot), registration_sha256=sha(args.registration),
        runtime_manifest_sha256=sha(root/'RUNTIME.json'), case_ids=[c['id'] for c in conditions],
        complete_registered_matrix=len(conditions) == len(protocol['conditions']),
        deterministic=not args.stochastic, action_seed=args.action_seed, noise_schedule=args.noise_schedule,
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
                        action, external_key = seeded_action(learner, event['observation'], actions, external_key, args.noise_schedule)
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
    replay_unchanged = digest(replay.state_dict()) == replay_digest
    assert replay_unchanged and digest(checkpoint['cycles']) == history_digest
    unchanged = digest(learner.state_dict()) == initial_state
    write(output/'POLICY_UNCHANGED.json', dict(full_learner_state_unchanged=unchanged,
        initial_state_digest=initial_state, final_state_digest=digest(learner.state_dict()),
        new_optimizer_updates=learner.learner.num_gradient_steps-initial_updates,
        full_replay_state_unchanged=replay_unchanged, replay_writes=0,
        replay_digest=replay_digest, history_digest=history_digest, recovery_state=recovery_state))
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
    parser.add_argument('--expected-cycle', type=int, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--learner-cpu', type=int, required=True)
    parser.add_argument('--physics-cpu', type=int, required=True)
    parser.add_argument('--case-id', action='append')
    parser.add_argument('--stochastic', action='store_true',
        help='Registered action-sampling diagnostic; leaves physical fixture seeds unchanged')
    parser.add_argument('--action-seed', type=int)
    parser.add_argument('--noise-schedule', choices=['independent', 'episode_constant'], default='independent')
    parser.add_argument('--audit-substeps', action='store_true',
        help='Record coincident human contact/torque for independent physical audit')
    evaluate(parser.parse_args())
