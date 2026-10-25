"""Concurrent physical samplers feeding one pinned published learner per GPU.

Dispatch is grouped into complete, balanced condition cycles. Full learner and
replay checkpoints are written periodically and at cycle boundaries; partial
checkpoints restart physics episodes rather than claiming exact physics resume.
There is no total-step cap. Stop requests drain the current cycle, save replay
and all optimizer/RNG states, and never advertise convergence automatically.
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
import time

import numpy as np
import torch

from published_compliance_learner_20261025 import PublishedLearner
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus


def write(path, data):
    tmp = Path(path).with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_resume_protocol(checkpoint_digest, protocol, current_digest):
    if checkpoint_digest == current_digest:
        return
    parent = protocol.get('resume_parent_registration')
    if not parent or checkpoint_digest != parent['sha256'] or sha(parent['path']) != parent['sha256']:
        raise ValueError('Resume protocol mismatch without verified registered parent')
    previous = json.loads(Path(parent['path']).read_text())
    descriptive = {'runtime', 'runtime_sha256', 'resume_parent_registration',
        'performance_amendment', 'registered_unix', 'restart_reason'}
    if ({k: v for k, v in previous.items() if k not in descriptive}
            != {k: v for k, v in protocol.items() if k not in descriptive}):
        raise ValueError('Performance-only continuation changed the training contract')
    if protocol.get('performance_amendment', {}).get('kind') != 'batched_finite_checks_only':
        raise ValueError('Unrecognized registered continuation amendment')
    old_root, new_root = Path(previous['runtime']), Path(protocol['runtime'])
    for name in ('PARAMETER_HASHES.json', 'ROBOT_ASSET_HASHES.json', 'CHEQ_HASHES.json'):
        if json.loads((old_root/name).read_text()) != json.loads((new_root/name).read_text()):
            raise ValueError('Performance continuation changed runtime contract: '+name)
    old_source = json.loads((old_root/'SOURCE_HASHES.json').read_text())
    new_source = json.loads((new_root/'SOURCE_HASHES.json').read_text())
    permitted = {'tools/'+name+'_20261025.py' for name in (
        'published_compliance_learner', 'train_published_compliance',
        'audit_published_episode', 'evaluate_published_compliance',
        'probe_published_numerical_stability')}
    for name in set(old_source) | set(new_source):
        if old_source.get(name) == new_source.get(name):
            continue
        if name in permitted or (name not in old_source and name.startswith('tools/')):
            continue
        raise ValueError('Performance continuation changed protected runtime source: '+name)


class Replay:
    def __init__(self, dimension, observation_dim, seed, capacity=1_000_000):
        self.capacity, self.size, self.cursor = capacity, 0, 0
        self.rng = np.random.default_rng(seed)
        self.arrays = {k: np.empty((capacity, width), np.float32) for k, width in
            dict(observations=observation_dim, next_observations=observation_dim,
                 actions=dimension, rewards=1, dones=1, masks=5).items()}

    def add(self, **row):
        row['masks'] = self.rng.binomial(1, .8, 5)
        for key, value in row.items():
            if not np.isfinite(value).all():
                raise ValueError('Nonfinite replay field '+key)
            self.arrays[key][self.cursor] = value
        self.size = min(self.size+1, self.capacity)
        self.cursor = (self.cursor+1) % self.capacity

    def sample(self, count=256):
        index = self.rng.integers(self.size, size=count)
        values = {k: v[index] for k, v in self.arrays.items()}
        if np.any(values['masks'].sum(axis=0) == 0):
            return self.sample(count)
        return values

    def state_dict(self):
        return dict(capacity=self.capacity, size=self.size, cursor=self.cursor,
                    arrays={k: v[:self.size] for k, v in self.arrays.items()},
                    rng=self.rng.bit_generator.state)

    def load_state_dict(self, state):
        if state['capacity'] != self.capacity:
            raise ValueError('Replay capacity drift')
        self.size, self.cursor = state['size'], state['cursor']
        for k, v in state['arrays'].items():
            self.arrays[k][:self.size] = v
        self.rng.bit_generator.state = state['rng']


def plateau_status(cycles):
    """A diagnostic flag requiring improvement; final convergence needs review."""
    if len(cycles) < 6:
        return dict(candidate=False, reason='fewer_than_six_complete_condition_cycles')
    means = np.array([c['reward_mean'] for c in cycles])
    recent = means[-3:]
    tolerance = max(.5, .02*abs(float(recent.mean())))
    improvement = float(recent.mean()-means[:2].mean())
    return dict(candidate=bool(improvement >= 2. and np.ptp(recent) <= tolerance),
                improvement_over_initial_cycles=improvement, recent_mean_range=float(np.ptp(recent)),
                tolerance=tolerance, reason='paired_condition_cycle_reward_only_requires_optimizer_and_policy_review')


def main(args):
    torch.set_num_threads(1)
    root, out = args.runtime.resolve(), args.output.resolve()
    protocol = json.loads(args.registration.read_text())
    if protocol['runtime'] != str(root) or protocol['status'] != 'registered':
        raise ValueError('Expected registered runtime')
    if protocol['runtime_sha256'] != sha(root/'RUNTIME.json'):
        raise ValueError('Runtime manifest drift')
    if args.seed not in protocol['seeds'] or args.controller not in protocol['controllers']:
        raise ValueError('Unregistered method/seed')
    if args.algorithm not in protocol['algorithms']:
        raise ValueError('Unregistered published algorithm')
    batch_size = int(protocol.get('learner_batch_size', 256))
    utd = int(protocol.get('learner_updates_per_transition', 1))
    if not 256 <= batch_size <= 32768 or not 1 <= utd <= 8:
        raise ValueError('Unsupported registered learner workload')
    conditions = protocol['conditions']
    if sha(protocol['reference_plan']) != protocol['reference_plan_sha256']:
        raise ValueError('Frozen nominal reference plan drift')
    for c in conditions:
        if sha(c['path']) != c['sha256']:
            raise ValueError('Condition drift')
    cpus = [int(v) for v in args.cpus.split(',')]
    if len(set(cpus)) != len(cpus) or args.workers > len(cpus)-1:
        raise ValueError('Reserve one distinct learner CPU plus one per sampler')
    if not set(cpus).issubset(os.sched_getaffinity(0)):
        raise ValueError('CPU allocation outside affinity')
    os.sched_setaffinity(0, {cpus[0]})
    prior = json.loads((root/'parameter/PRIORS.json').read_text())
    dim = 7 if args.controller == 'direct' else prior['methods'][args.controller]['action_dimension']
    learner = PublishedLearner(root, dimension=dim, direct=args.controller == 'direct',
                               seed=args.seed, device=args.device, algorithm=args.algorithm,
                               critic_layer_norm=protocol.get('critic_layer_norm', False),
                               numerical_amendments=protocol.get('numerical_amendments', False))
    replay = Replay(dim, 49 if args.algorithm == 'cheq' else 48, args.seed+53)
    steps, cycles, start_cycle = 0, [], 0
    pdigest = sha(args.registration)
    imported_replay = protocol.get('recovered_replay', {}).get(args.controller)
    if imported_replay and not args.resume:
        if sha(imported_replay['path']) != imported_replay['sha256']:
            raise ValueError('Recovered physical replay drift')
        with np.load(imported_replay['path'], allow_pickle=False) as archive:
            columns = {k: archive[k] for k in replay.arrays if k != 'masks'}
        for i in range(len(columns['rewards'])):
            replay.add(**{k: column[i] for k, column in columns.items()})
        steps = replay.size
    if args.resume:
        checkpoint = torch.load(args.resume, map_location=args.device, weights_only=False)
        validate_resume_protocol(checkpoint['protocol_sha256'], protocol, pdigest)
        if (checkpoint['controller'], checkpoint['seed']) != (args.controller, args.seed):
            raise ValueError('Resume controller/seed mismatch')
        learner.load_state_dict(checkpoint['learner'])
        replay.load_state_dict(checkpoint['replay'])
        steps, cycles, start_cycle = checkpoint['steps'], checkpoint['cycles'], checkpoint['cycle']+1
    out.mkdir(parents=True, exist_ok=False)
    write(out/'EXECUTION.json', dict(status='running', pid=os.getpid(), protocol_sha256=pdigest,
        controller=args.controller, algorithm=args.algorithm, seed=args.seed, cpus=cpus,
        device=args.device, gpu_name=torch.cuda.get_device_name(learner.device),
        gpu_uuid=str(getattr(torch.cuda.get_device_properties(learner.device), 'uuid', 'unavailable')),
        physics_dt_s=.00005, actor_period_s=.04, workers=args.workers,
        batch_size=batch_size, updates_per_transition=utd,
        recovered_replay=imported_replay, fresh_optimizer_with_imported_replay=bool(imported_replay and not args.resume),
        restart_reason=protocol.get('restart_reason'), critic_layer_norm=learner.critic_layer_norm,
        numerical_amendments=learner.numerical_amendments, numerical_patch_receipt=learner.numerical_patch_receipt,
        python=sys.executable, trainer_sha256=sha(__file__),
        learner_adapter_sha256=sha(Path(__file__).with_name('published_compliance_learner_20261025.py')),
        resumed_from=str(args.resume) if args.resume else None,
        resumed_checkpoint_sha256=sha(args.resume) if args.resume else None,
        resumed_protocol_sha256=checkpoint['protocol_sha256'] if args.resume else None))
    episode_log = (out/'episodes.jsonl').open('x', buffering=1)
    optimizer_log = (out/'optimizer.jsonl').open('x', buffering=1)
    transition_log = (out/'transitions.jsonl').open('x', buffering=1)
    stop = out/'STOP_REQUESTED'
    cycle = start_cycle
    children = {}
    selector = selectors.DefaultSelector()
    last_checkpoint_step = steps

    def checkpoint_now(boundary):
        temporary = out/'checkpoint.tmp'
        torch.save(dict(protocol_sha256=pdigest, controller=args.controller, seed=args.seed,
            cycle=cycle, steps=steps, cycles=cycles, learner=learner.state_dict(),
            replay=replay.state_dict(), boundary=boundary,
            environment_state_saved=False,
            resume_semantics='retain completed transitions and learner state; start new episodes after partial boundary'), temporary)
        temporary.replace(out/'checkpoint_latest.pt')

    try:
        while not stop.exists():
            if shutil.disk_usage(out).free < 20*1024**3:
                raise OSError('Registered 20 GiB free-disk reserve reached')
            # Fixed balanced condition order; no selection by outcomes.
            pending = list(enumerate(conditions))
            returns, successes, completed = [], [], []
            free_slots = list(range(args.workers))

            def launch():
                while pending and free_slots:
                    slot = free_slots.pop(0)
                    index, condition = pending.pop(0)
                    folder = out/f'cycle_{cycle:05d}'/condition['id']
                    folder.parent.mkdir(parents=True, exist_ok=True)
                    error = (folder.parent/(condition['id']+'.stderr.log')).open('x')
                    command = ['taskset', '-c', str(cpus[slot+1]), sys.executable,
                        str(Path(__file__).with_name('published_compliance_episode_20261025.py')),
                        '--runtime', str(root), '--output', str(folder), '--fixture', condition['path'],
                        '--reference-plan', protocol['reference_plan'],
                        '--controller', args.controller, '--ipc']
                    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
                               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='disable')
                    child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=error, text=True, bufsize=1, env=env)
                    learner.reset_episode(stream=slot)
                    state = dict(process=child, error=error, condition=condition, folder=folder,
                                 reward=SPTReward(), previous=None, episode_return=0., steps=0, last_event=time.monotonic())
                    children[slot] = state
                    selector.register(child.stdout, selectors.EVENT_READ, slot)

            launch()
            while children:
                for key, _ in selector.select(timeout=10):
                    slot = key.data
                    state = children[slot]
                    line = key.fileobj.readline()
                    if not line:
                        raise RuntimeError(f'Sampler exited without terminal event: {state["folder"]}')
                    event = json.loads(line)
                    state['last_event'] = time.monotonic()
                    if event['kind'] == 'error':
                        raise RuntimeError(event['error'])
                    done = event['kind'] == 'terminal'
                    if event['kind'] not in ('observation', 'terminal'):
                        raise ValueError('Unexpected IPC event')
                    previous = state['previous']
                    if previous is None:
                        expected = state['condition']['model_sha256']
                        if sha(state['folder']/'rollout.mjb') != expected:
                            raise ValueError('Frozen per-condition model mismatch')
                    if previous is not None:
                        labels = event['result'] if done else dict(task_success=False, strict_success=False)
                        value, terms = state['reward'](current_potential=previous['potential'],
                            next_potential=event['payload_potential'], interval=event['interval'], terminated=done,
                            task_success=labels['task_success'], strict_success=labels['strict_success'])
                        bonus = completion_bonus(task_success=True, strict_success=True,
                            completion_time_s=event['completion_time_s']) if done and labels['strict_success'] else 0.
                        value += bonus
                        terms.update(completion_efficiency=bonus, final_reward=value)
                        nxt = previous['observation'] if done else learner.observation(event['observation'], stream=slot)
                        replay.add(observations=previous['observation'], actions=previous['raw_action'],
                                   next_observations=nxt, rewards=[value], dones=[float(done)])
                        steps += 1
                        state['steps'] += 1
                        state['episode_return'] += value
                        transition_log.write(json.dumps(dict(step=steps, cycle=cycle, condition=state['condition']['id'],
                            reward=value, done=done, context=previous['context'], reward_terms=terms), allow_nan=False)+'\n')
                        if steps >= 5000 and replay.size >= 256:
                            for update_index in range(utd):
                                metrics = learner.update(replay.sample(batch_size))
                                optimizer_log.write(json.dumps(dict(step=steps, update_index=update_index,
                                    **metrics), allow_nan=False)+'\n')
                        if steps-last_checkpoint_step >= 1000:
                            checkpoint_now('partial_episode_valid_replay_reset_environment_on_resume')
                            last_checkpoint_step = steps
                    if done:
                        selector.unregister(key.fileobj)
                        rc = state['process'].wait(timeout=60)
                        if rc:
                            raise RuntimeError(f'Sampler terminal followed by nonzero exit: {rc}')
                        state['error'].close()
                        result = dict(cycle=cycle, condition=state['condition']['id'],
                            category=state['condition']['category'], steps=state['steps'], total_steps=steps,
                            reward=state['episode_return'], **event['result'], completion_time_s=event['completion_time_s'],
                            model_sha256=event['model_sha256'], episode_path=str(state['folder']))
                        episode_log.write(json.dumps(result, allow_nan=False)+'\n')
                        returns.append(result['reward'])
                        successes.append(result['strict_success'])
                        completed.append(result['condition'])
                        del children[slot]
                        free_slots.append(slot)
                        launch()
                    else:
                        obs, raw, action, context = learner.act(event['observation'], step=steps, stream=slot)
                        state['previous'] = dict(observation=obs, raw_action=raw,
                                                 potential=event['payload_potential'], context=context)
                        state['process'].stdin.write(json.dumps(dict(action=action.tolist()))+'\n')
                        state['process'].stdin.flush()
                if any(time.monotonic()-v['last_event'] > 600 for v in children.values()):
                    raise TimeoutError('Sampler produced no observation/terminal for 600 s')
                write(out/'PROGRESS.json', dict(cycle=cycle, steps=steps, completed_conditions=len(completed),
                    running=len(children), pending=len(pending), updates=learner.learner.num_gradient_steps,
                    wall_time_utc=time.time()))
            row = dict(cycle=cycle, steps=steps, reward_mean=float(np.mean(returns)),
                       reward_std=float(np.std(returns)), strict_success_rate=float(np.mean(successes)))
            cycles.append(row)
            checkpoint_now('complete_condition_cycle')
            write(out/'CYCLES.json', dict(cycles=cycles, plateau=plateau_status(cycles),
                 status='training', sufficient_convergence_claim=False))
            cycle += 1
            if args.cycles and cycle-start_cycle >= args.cycles:
                break
        write(out/'FINISHED.json', dict(status='stopped_at_complete_cycle', steps=steps,
              cycles_completed=cycle-start_cycle, convergence_claim=False))
    except BaseException as error:
        write(out/'FAILURE.json', dict(error=repr(error), steps=steps, cycle=cycle))
        try:
            checkpoint_now('failure_valid_replay_reset_environment_on_resume')
        except BaseException as save_error:
            write(out/'CHECKPOINT_FAILURE.json', dict(error=repr(save_error)))
        # Close only this run's action pipes. Each sampler retains its incomplete
        # episode evidence and exits at its next actor boundary.
        for state in children.values():
            try:
                state['process'].stdin.close()
            except (BrokenPipeError, OSError):
                pass
        raise
    finally:
        episode_log.close()
        optimizer_log.close()
        transition_log.close()
        selector.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--registration', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--controller', choices=('direct', 'impedance', 'admittance', 'vmc'), required=True)
    p.add_argument('--algorithm', choices=('sac', 'cheq'), default='cheq')
    p.add_argument('--seed', type=int, default=20261025)
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--cpus', required=True)
    p.add_argument('--workers', type=int, default=9)
    p.add_argument('--cycles', type=int, default=0, help='Optional dispatch stage, never a convergence criterion')
    p.add_argument('--resume', type=Path)
    main(p.parse_args())
