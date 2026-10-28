"""Finite paired actual-update validation of Adam step device placement.

Loads checkpoints onto CUDA, exactly as the formal resume entrance does.
Two reverse-order trials; state values, moments, RNG, gradients and sampling
must be bitwise equal. Only Adam scalar counter placement may differ.
No auxiliary weights are saved or imported into formal training.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from published_adam_step_device_20261025 import move_adam_steps_to_cpu
from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def optimizer_devices(learner):
    return {name: dict(Counter(str(s['step'].device) for s in opt.state.values() if 'step' in s))
            for name, opt in optimizers(learner).items()}


def optimizers(learner):
    return dict(actor=learner.learner.actor_optimizer, critic=learner.learner.q_optimizer,
                alpha=learner.learner.a_optimizer)


def placement(value, prefix=''):
    if torch.is_tensor(value):
        return {prefix: str(value.device)}
    result = {}
    if isinstance(value, dict):
        for key, child in value.items():
            result.update(placement(child, prefix+'/'+str(key)))
    elif isinstance(value, (list, tuple)):
        for key, child in enumerate(value):
            result.update(placement(child, prefix+'/'+str(key)))
    return result


def main(args):
    protocol = json.loads(args.registration.read_text())
    for name, expected in protocol['source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Validation source drift: '+name)
    os.sched_setaffinity(0, {protocol['cpus'][args.controller]})
    os.nice(10)
    torch.set_num_threads(1)
    root = Path(protocol['runtime'])
    if sha(root/'RUNTIME.json') != protocol['runtime_sha256']:
        raise ValueError('Runtime manifest drift')
    source_hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ('published_compliance_learner_20261025.py', 'published_replay_device_cache_20261025.py',
                 'train_published_compliance_20261025.py', 'published_bellman_minimum_20261025.py'):
        if sha(root/'source/tools'/name) != source_hashes['tools/'+name]:
            raise ValueError('Frozen source drift: '+name)
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from published_replay_device_cache_20261025 import DeviceReplayCache
    from train_published_compliance_20261025 import Replay
    item = protocol['checkpoints'][args.controller]
    if sha(item['path']) != item['sha256']:
        raise ValueError('Checkpoint drift')
    ck = torch.load(item['path'], map_location=args.device, weights_only=False)
    if ck['controller'] != args.controller or ck['boundary'] != 'complete_condition_cycle':
        raise ValueError('Expected immutable same-method complete-cycle checkpoint')
    state, arrays = ck['learner'], ck['replay']['arrays']
    parent_hash, replay_hash = digest(state), digest(ck['replay'])
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=args.controller=='direct',
        seed=protocol['seed'], device=args.device, algorithm=state['algorithm'],
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    replay = Replay(arrays['actions'].shape[1], arrays['observations'].shape[1], protocol['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    cache = DeviceReplayCache(replay, args.device)
    args.output.mkdir(exist_ok=False)
    trials = []
    for trial, order in enumerate([['cuda_steps', 'cpu_steps'], ['cpu_steps', 'cuda_steps']]):
        rows = []
        for variant in order:
            learner.load_state_dict(copy.deepcopy(state))
            for param in learner.learner.agent.parameters():
                param.grad = None
            before = learner.state_dict()
            before_devices = optimizer_devices(learner)
            if any(not devices or set(devices) != {args.device} for devices in before_devices.values()):
                raise AssertionError('Did not reproduce formal CUDA step loading')
            migration = None
            if variant == 'cpu_steps':
                migration = {key: move_adam_steps_to_cpu(opt) for key, opt in optimizers(learner).items()}
            initial = learner.state_dict()
            if digest(before) != digest(initial):
                raise AssertionError('Counter placement changed numerical state')
            old_locations, new_locations = placement(before), placement(initial)
            allowed = {key for key in old_locations if any(key.startswith('/'+name+'/state/')
                       for name in ('actor_optimizer','q_optimizer','alpha_optimizer')) and key.endswith('/step')}
            changed = {key for key in old_locations if old_locations[key] != new_locations[key]}
            if changed != (allowed if variant == 'cpu_steps' else set()):
                raise AssertionError('Unexpected state placement changes')
            replay.rng = np.random.default_rng(protocol['seed'])
            torch.cuda.synchronize(args.device)
            start = time.perf_counter()
            for _ in range(protocol['updates_per_arm']):
                learner.update(cache.sample(protocol['batch_size']))
            torch.cuda.synchronize(args.device)
            elapsed = time.perf_counter()-start
            final = learner.state_dict()
            if final['num_gradient_steps'] - state['num_gradient_steps'] != protocol['updates_per_arm']:
                raise AssertionError('Wrong update count')
            rows.append(dict(variant=variant, elapsed_s=elapsed, initial_state_sha256=digest(initial),
                final_state_sha256=digest(final), field_sha256={key:digest(value) for key,value in final.items()},
                gradient_sha256=digest({key:value.grad for key,value in learner.learner.agent.named_parameters()}),
                sampling_rng_sha256=digest(replay.rng.bit_generator.state),
                step_devices_before=before_devices, step_devices_after=optimizer_devices(learner),
                migration=migration, changed_device_paths=sorted(changed)))
            if digest(state) != parent_hash or digest(ck['replay']) != replay_hash:
                raise AssertionError('Parent state/replay changed')
            write(args.output/'PROGRESS.json', dict(trial=trial, **rows[-1]))
        a, b = rows
        exact = all(a[key] == b[key] for key in ('initial_state_sha256', 'final_state_sha256',
                    'gradient_sha256', 'sampling_rng_sha256'))
        original = next(row for row in rows if row['variant']=='cuda_steps')
        candidate = next(row for row in rows if row['variant']=='cpu_steps')
        trials.append(dict(trial=trial, arms=rows, exact_values_gradients_rng=exact,
                           observed_speedup=original['elapsed_s']/candidate['elapsed_s']))
        write(args.output/f'trial_{trial}.json', trials[-1])
        if not exact:
            raise AssertionError('CPU step placement changed subsequent updates')
    if sha(item['path']) != item['sha256']:
        raise AssertionError('Parent file changed')
    write(args.output/'FINISHED.json', dict(controller=args.controller, trials=trials,
        checkpoint_sha256=item['sha256'], registration_sha256=sha(args.registration),
        finished_unix=time.time(), auxiliary_updates=4*protocol['updates_per_arm'],
        new_physics=0, parent_unchanged=True, auxiliary_weights_saved=False,
        formal_training_changed=False,
        limitation='Finite exact-state evidence with two timing orders on shared hardware; not deployed or online throughput proof.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--controller', required=True)
    parser.add_argument('--device', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True)
        write(args.output/'FAILURE.json', dict(error=repr(error)))
        raise
