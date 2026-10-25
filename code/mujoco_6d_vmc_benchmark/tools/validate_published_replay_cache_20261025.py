"""Finite paired learner validation of a device replay mirror, off formal runs.

Each update pair appends one existing real row to an auxiliary replay, retaining
the original mask generator. Repeated physical rows are test inputs, not newly
collected experience. All auxiliary weights are discarded.
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    p = json.loads(args.registration.read_text())
    for key, path in [('source', __file__), ('candidate', p['candidate']), ('digest_helper', p['digest_helper'])]:
        if sha(path) != p[key+'_sha256']:
            raise ValueError('Validation source drift: '+key)
    os.sched_setaffinity(0, {p['cpu']}); os.nice(10); torch.set_num_threads(1)
    root = Path(p['runtime'])
    if sha(root/'RUNTIME.json') != p['runtime_sha256']:
        raise ValueError('Runtime drift')
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from train_published_compliance_20261025 import Replay
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
        return value
    Cache = module('replay_candidate', p['candidate']).DeviceReplayCache
    digest = module('digest_helper', p['digest_helper']).digest
    out = Path(p['output']); out.mkdir(parents=True, exist_ok=False)
    report = dict(started_unix=time.time(), formal_state_changed=False,
        new_physical_transitions=0, auxiliary_weights_saved=False, snapshots=[])
    for item in p['snapshots']:
        if sha(item['path']) != item['sha256']:
            raise ValueError('Checkpoint drift')
        ck = torch.load(item['path'], map_location='cpu', weights_only=False)
        if ck['boundary'] != 'complete_condition_cycle' or ck['controller'] != item['method']:
            raise ValueError('Unexpected checkpoint')
        state, arrays = ck['learner'], ck['replay']['arrays']
        immutable = digest(state)
        learner = PublishedLearner(root, dimension=arrays['actions'].shape[1],
            direct=item['method']=='direct', seed=p['seed'], device=p['device'],
            algorithm=state['algorithm'], critic_layer_norm=state['critic_layer_norm'],
            numerical_amendments=state['numerical_amendments'])
        variants = {}
        order = ['cpu', 'device'] if p['cpu_first'] else ['device', 'cpu']
        for name in order:
            learner.load_state_dict(copy.deepcopy(state))
            for param in learner.learner.agent.parameters():
                param.grad = None
            replay = Replay(arrays['actions'].shape[1], arrays['observations'].shape[1], p['seed'])
            replay.load_state_dict(copy.deepcopy(ck['replay']))
            torch.cuda.synchronize(p['device']); init_start = time.perf_counter()
            source = replay if name == 'cpu' else Cache(replay, p['device'])
            torch.cuda.synchronize(p['device']); init_seconds = time.perf_counter()-init_start
            rng = np.random.default_rng(p['seed'])
            incoming = rng.integers(len(arrays['rewards']), size=(p['updates_per_arm']+1)//2)
            torch.cuda.synchronize(p['device']); start = time.perf_counter()
            for update in range(p['updates_per_arm']):
                if update % 2 == 0:
                    source.add(**{k:v[incoming[update//2]] for k,v in arrays.items() if k != 'masks'})
                learner.update(source.sample(p['batch_size']))
            torch.cuda.synchronize(p['device']); elapsed = time.perf_counter()-start
            final = learner.state_dict()
            if final['num_gradient_steps']-state['num_gradient_steps'] != p['updates_per_arm']:
                raise AssertionError('Unexpected update count')
            variants[name] = dict(seconds=elapsed, initialization_seconds=init_seconds,
                state_sha256=digest(final), state_fields={k:digest(v) for k,v in final.items()},
                gradient_sha256=digest({k:v.grad for k,v in learner.learner.agent.named_parameters()}),
                replay_sha256=digest(source.state_dict()),
                cache_bytes=sum(v.numel()*v.element_size() for v in source.arrays.values()) if name=='device' else 0)
            if digest(state) != immutable:
                raise AssertionError('Immutable parent state changed')
            del source, replay, final
            torch.cuda.empty_cache()
        a, b = variants['cpu'], variants['device']
        row = dict(method=item['method'], algorithm=state['algorithm'], cycle=ck['cycle'],
            variants=variants, full_state_exact=a['state_sha256']==b['state_sha256'],
            replay_exact=a['replay_sha256']==b['replay_sha256'],
            gradients_exact=a['gradient_sha256']==b['gradient_sha256'],
            observed_speedup=a['seconds']/b['seconds'])
        (out/(state['algorithm']+'.json')).write_text(json.dumps(row, indent=2)+'\n')
        if not all(row[k] for k in ['full_state_exact','replay_exact','gradients_exact']):
            raise AssertionError('Device mirror changed learning or replay state')
        report['snapshots'].append(row)
        print(json.dumps(dict(method=item['method'],algorithm=state['algorithm'],exact=True,speedup=row['observed_speedup'])),flush=True)
        del learner, ck, state, arrays
        torch.cuda.empty_cache()
    report.update(finished_unix=time.time(), auxiliary_updates=len(p['snapshots'])*2*p['updates_per_arm'],
        registration_sha256=sha(args.registration), limitation='Shared load, one ordered pair per snapshot; not online throughput or GPU utilization evidence.')
    (out/'SUMMARY.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    main(parser.parse_args())
