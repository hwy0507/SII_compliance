"""Paired finite-check performance validation, with all learner state compared.

Separate auxiliary updates on frozen replay; never feeds weights into training.
The candidate replaces validation only. Replaying identical updates must retain
all networks, targets, optimizer states, alpha, RNG, metrics and gradients.
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


def digest(value):
    h = hashlib.sha256()
    def visit(v):
        if torch.is_tensor(v):
            visit(v.detach().cpu().numpy())
        elif isinstance(v, np.ndarray):
            h.update(str((v.shape, v.dtype)).encode()); h.update(v.tobytes())
        elif isinstance(v, dict):
            for k in sorted(v, key=repr):
                visit(k); visit(v[k])
        elif isinstance(v, (list, tuple)):
            h.update(type(v).__name__.encode())
            for item in v:
                visit(item)
        else:
            h.update(repr(v).encode()+b'\0')
    visit(value)
    return h.hexdigest()


def main(args):
    p = json.loads(args.registration.read_text())
    for key, path in [('source', __file__), ('candidate', p['candidate'])]:
        if sha(path) != p[key+'_sha256']:
            raise ValueError('Frozen validation input drift: '+key)
    os.sched_setaffinity(0, {p['cpu']}); os.nice(p['nice']); torch.set_num_threads(1)
    root = Path(p['runtime'])
    sys.path.insert(0, str(root/'source/tools'))
    import published_compliance_learner_20261025 as original
    spec = importlib.util.spec_from_file_location('candidate_finite_check_adapter', p['candidate'])
    candidate = importlib.util.module_from_spec(spec); spec.loader.exec_module(candidate)
    old_check = original.assert_finite_parameters
    out = Path(p['output']); out.mkdir(parents=True, exist_ok=False)
    result = dict(methods={}, formal_state_changed=False, new_physical_transitions=0,
                  limitation='Single ordered paired trial on shared CPU/GPU; timing is not isolated online throughput.')
    for item in p['snapshots']:
        if sha(item['checkpoint']) != item['sha256']:
            raise ValueError('Checkpoint drift')
        checkpoint = torch.load(item['checkpoint'], map_location='cpu', weights_only=False)
        state, arrays = checkpoint['learner'], checkpoint['replay']['arrays']
        immutable_state_digest = digest(state)
        if checkpoint['boundary'] != 'complete_condition_cycle':
            raise ValueError('Expected complete cycle')
        learner = original.PublishedLearner(root, dimension=arrays['actions'].shape[1],
            direct=item['method']=='direct', seed=p['seed'], device=item['device'],
            algorithm=state['algorithm'], critic_layer_norm=state['critic_layer_norm'],
            numerical_amendments=state['numerical_amendments'])
        variants = []
        for name, check in [('source_train06', old_check), ('concatenated_finite_check', candidate.assert_finite_parameters)]:
            original.assert_finite_parameters = check
            # Optimizer loading can alias CPU step tensors. A deep copy keeps
            # the second variant's optimizer counters identical to the first.
            learner.load_state_dict(copy.deepcopy(state))
            for param in learner.learner.agent.parameters():
                param.grad = None
            rng = np.random.default_rng(p['seed'])
            torch.cuda.synchronize(item['device']); start = time.perf_counter()
            for _ in range(p['updates_per_variant']):
                index = rng.integers(len(arrays['rewards']), size=p['batch_size'])
                learner.update({k: v[index] for k, v in arrays.items()})
            torch.cuda.synchronize(item['device']); elapsed = time.perf_counter()-start
            final = learner.state_dict()
            if final['num_gradient_steps']-state['num_gradient_steps'] != p['updates_per_variant']:
                raise AssertionError('Wrong auxiliary update count')
            variants.append(dict(name=name, seconds=elapsed, state_sha256=digest(final),
                gradients_sha256=digest({k: v.grad for k, v in learner.learner.agent.named_parameters()}),
                state_field_sha256={k: digest(v) for k, v in final.items()}))
            if digest(state) != immutable_state_digest:
                raise AssertionError('Variant mutated immutable parent optimizer state')
        a, b = variants
        row = dict(variants=variants, all_state_exact=a['state_sha256']==b['state_sha256'],
            gradients_exact=a['gradients_sha256']==b['gradients_sha256'], observed_speedup=a['seconds']/b['seconds'])
        result['methods'][item['method']] = row
        (out/(item['method']+'.json')).write_text(json.dumps(row, indent=2)+'\n')
        if not row['all_state_exact'] or not row['gradients_exact']:
            raise AssertionError('Candidate validation changed learner state or gradients')
        print(json.dumps(dict(method=item['method'], exact=True, observed_speedup=row['observed_speedup'])), flush=True)
        del learner, checkpoint, state, arrays, final
        torch.cuda.empty_cache()
    result.update(finished_unix=time.time(), registration_sha256=sha(args.registration),
                  auxiliary_updates=len(p['snapshots'])*2*p['updates_per_variant'], weights_saved=False)
    (out/'SUMMARY.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
