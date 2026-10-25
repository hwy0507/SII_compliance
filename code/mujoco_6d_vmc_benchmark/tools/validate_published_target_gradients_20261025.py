"""Finite paired equivalence/timing test for unused target-gradient suppression.

Two reverse-order trials per interface restore the same immutable full state.
All learner/optimizer/alpha/RNG state and every non-target parameter gradient
must match exactly. Only unused target-parameter gradients intentionally differ.
No weights are saved or promoted and no physical transitions are generated.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from published_target_gradients_20261025 import freeze_target_parameters
from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    p = json.loads(args.registration.read_text())
    for name, expected in p['source_hashes'].items():
        if sha(Path(__file__).with_name(name)) != expected:
            raise ValueError('Frozen validation source drift')
    os.sched_setaffinity(0, {p['cpus'][args.controller]})
    os.nice(10)
    torch.set_num_threads(1)
    root = Path(p['runtime'])
    if sha(root/'RUNTIME.json') != p['runtime_sha256']:
        raise ValueError('Runtime manifest drift')
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ('published_compliance_learner_20261025.py', 'published_replay_device_cache_20261025.py',
                 'train_published_compliance_20261025.py'):
        if sha(root/'source/tools'/name) != hashes['tools/'+name]:
            raise ValueError('Frozen source drift: '+name)
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from published_replay_device_cache_20261025 import DeviceReplayCache
    from train_published_compliance_20261025 import Replay
    item = p['checkpoints'][args.controller]
    if sha(item['path']) != item['sha256']:
        raise ValueError('Checkpoint drift')
    ck = torch.load(item['path'], map_location='cpu', weights_only=False)
    if ck['boundary'] != 'complete_condition_cycle' or ck['controller'] != args.controller:
        raise ValueError('Expected immutable same-method complete cycle')
    state, arrays = ck['learner'], ck['replay']['arrays']
    parent_hash, replay_hash = digest(state), digest(ck['replay'])
    learner = PublishedLearner(root, dimension=arrays['actions'].shape[1], direct=args.controller=='direct',
        seed=p['seed'], device=args.device, algorithm='cheq',
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    actual_adapters = None
    if p.get('candidate_runtime'):
        candidate_root = Path(p['candidate_runtime'])
        if sha(candidate_root/'RUNTIME.json') != p['candidate_runtime_sha256']:
            raise ValueError('Candidate runtime manifest drift')
        candidate_source = candidate_root/'source/tools/published_compliance_learner_20261025.py'
        candidate_hashes = json.loads((candidate_root/'SOURCE_HASHES.json').read_text())
        for name in ('published_compliance_learner_20261025.py','published_target_gradients_20261025.py'):
            if sha(candidate_root/'source/tools'/name) != candidate_hashes['tools/'+name]:
                raise ValueError('Candidate adapter/helper drift')
        if sha(candidate_root/'source/tools/published_target_gradients_20261025.py') != sha(
                Path(__file__).with_name('published_target_gradients_20261025.py')):
            raise ValueError('Validation helper differs from candidate runtime')
        spec = importlib.util.spec_from_file_location('actual_target_freeze_candidate', candidate_source)
        candidate_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate_module)
        candidate = candidate_module.PublishedLearner(candidate_root, dimension=arrays['actions'].shape[1],
            direct=args.controller=='direct', seed=p['seed'], device=args.device, algorithm='cheq',
            critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
        if any(v.requires_grad for v in candidate.learner.agent.ensemble_targets.parameters()):
            raise AssertionError('Candidate constructor did not freeze target parameters')
        if not all(v.requires_grad for v in learner.learner.agent.ensemble_targets.parameters()):
            raise AssertionError('Original constructor unexpectedly freezes target parameters')
        actual_adapters = {'original':learner, 'frozen_targets':candidate}
    replay = Replay(arrays['actions'].shape[1], arrays['observations'].shape[1], p['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    cache = DeviceReplayCache(replay, args.device)
    args.output.mkdir(exist_ok=False)
    results = []
    initial_digest = None
    for trial, order in enumerate([['original', 'frozen_targets'], ['frozen_targets', 'original']]):
        rows = []
        for variant in order:
            if actual_adapters is not None:
                learner = actual_adapters[variant]
            else:
                for param in learner.learner.agent.ensemble_targets.parameters():
                    param.requires_grad_(True)
            learner.load_state_dict(copy.deepcopy(state))
            for param in learner.learner.agent.parameters():
                param.grad = None
            if variant == 'frozen_targets' and actual_adapters is None:
                freeze_target_parameters(learner.learner)
            before = digest(learner.state_dict())
            if initial_digest is None:
                initial_digest = before
            elif before != initial_digest:
                raise AssertionError('Unequal full initial state')
            replay.rng = np.random.default_rng(p['seed'])
            torch.cuda.synchronize(args.device)
            start = time.perf_counter()
            for _ in range(p['updates_per_arm']):
                learner.update(cache.sample(p['batch_size']))
            torch.cuda.synchronize(args.device)
            elapsed = time.perf_counter()-start
            final = learner.state_dict()
            if final['num_gradient_steps']-state['num_gradient_steps'] != p['updates_per_arm']:
                raise AssertionError('Unexpected update count')
            gradients = {k:v.grad for k,v in learner.learner.agent.named_parameters()
                         if not k.startswith('ensemble_targets.')}
            target_gradients = sum(v.grad is not None for v in learner.learner.agent.ensemble_targets.parameters())
            if (variant == 'frozen_targets') != (target_gradients == 0):
                raise AssertionError('Unexpected target-gradient behavior')
            row = dict(trial=trial, variant=variant, elapsed_s=elapsed,
                state_sha256=digest(final), field_sha256={k:digest(v) for k,v in final.items()},
                non_target_gradients_sha256=digest(gradients), target_gradient_tensors=target_gradients,
                sampling_rng_sha256=digest(replay.rng.bit_generator.state))
            rows.append(row)
            if digest(state) != parent_hash or digest(ck['replay']) != replay_hash:
                raise AssertionError('Immutable parent changed')
            write(args.output/'PROGRESS.json', row)
        a,b = rows
        exact = all(a[k] == b[k] for k in ('state_sha256','non_target_gradients_sha256','sampling_rng_sha256'))
        original = next(r for r in rows if r['variant']=='original')
        candidate = next(r for r in rows if r['variant']=='frozen_targets')
        result = dict(trial=trial, arms=rows, all_used_state_exact=exact,
            observed_speedup=original['elapsed_s']/candidate['elapsed_s'])
        results.append(result)
        write(args.output/f'trial_{trial}.json', result)
        if not exact:
            raise AssertionError('Target-gradient suppression changed used learning state')
    write(args.output/'FINISHED.json', dict(controller=args.controller, trials=results,
        finished_unix=time.time(), registration_sha256=sha(args.registration),
        checkpoint_sha256=item['sha256'], updates=4*p['updates_per_arm'], new_physics=0,
        parent_unchanged=True, auxiliary_weights_saved=False, formal_training_changed=False,
        actual_candidate_runtime_tested=p.get('candidate_runtime'),
        limitation='Shared-load timing, two orders, finite exact-state evidence; not online throughput or GPU50% proof'))


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
