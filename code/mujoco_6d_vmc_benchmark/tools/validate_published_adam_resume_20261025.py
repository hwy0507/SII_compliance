"""Validate actual candidate adapter, CUDA round trips and next updates.

No physics or promoted weights. The original live-runtime source is read only.
Both paths serialize/reload between updates, comparing gradients including alpha.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_adapter(root, name):
    path = root/'source/tools/published_compliance_learner_20261025.py'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PublishedLearner


def roundtrip(state, device):
    stream = io.BytesIO()
    torch.save(state, stream)
    stream.seek(0)
    return torch.load(stream, map_location=device, weights_only=False)


def counters(learner):
    return [state['step'] for opt in (learner.learner.actor_optimizer,
            learner.learner.q_optimizer, learner.learner.a_optimizer)
            for state in opt.state.values() if 'step' in state]


def capture(learner):
    return dict(state=digest(learner.state_dict()),
                agent_gradients=digest({name: param.grad for name, param in
                                        learner.learner.agent.named_parameters()}),
                alpha_gradient=digest(learner.learner.log_alpha.grad))


def main(args):
    p = json.loads(args.registration.read_text())
    for path, expected in p['source_and_input_hashes'].items():
        if sha(path) != expected:
            raise ValueError('Registered input drift: '+path)
    torch.set_num_threads(1)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    original_root, candidate_root = Path(p['original_runtime']), Path(p['candidate_runtime'])
    # Common upstream modules are identical; the candidate helper is resolved
    # only from the candidate's immutable source snapshot.
    sys.path.insert(0, str(candidate_root/'source/tools'))
    Original = load_adapter(original_root, 'adam_resume_original')
    Candidate = load_adapter(candidate_root, 'adam_resume_candidate')
    results = {}
    for method, item in p['checkpoints'].items():
        if sha(item['path']) != item['sha256']:
            raise ValueError('Parent checkpoint drift')
        ck = torch.load(item['path'], map_location=p['device'], weights_only=False)
        if ck['boundary'] != 'complete_condition_cycle' or ck['controller'] != method:
            raise ValueError('Expected immutable complete same-method parent')
        parent_digest = digest(ck)
        state, arrays = ck['learner'], ck['replay']['arrays']
        kwargs = dict(dimension=arrays['actions'].shape[1], direct=method=='direct', seed=ck['seed'],
            device=p['device'], algorithm='cheq', critic_layer_norm=state['critic_layer_norm'],
            numerical_amendments=state['numerical_amendments'])
        original, candidate = Original(original_root, **kwargs), Candidate(candidate_root, **kwargs)
        # Terminal and nonterminal transitions exercise both bootstrap paths.
        indices = np.r_[np.flatnonzero(arrays['dones'][:,0] == 0)[:120],
                        np.flatnonzero(arrays['dones'][:,0] == 1)[:8]]
        if len(indices) != 128:
            raise ValueError('Missing registered terminal/nonterminal sample coverage')
        batch = {key: value[indices].copy() for key,value in arrays.items()}
        branches = {}
        for name, learner, expected_device in [('original',original,p['device']), ('candidate',candidate,'cpu')]:
            restored = roundtrip(copy.deepcopy(state), p['device'])
            rows = []
            for update in range(2):
                learner.load_state_dict(restored)
                if digest(learner.state_dict()) != digest(restored):
                    raise AssertionError('Actual adapter restore changed numerical state')
                steps = counters(learner)
                if len(steps) != 59 or any(str(step.device) != expected_device for step in steps):
                    raise AssertionError('Wrong counter placement after actual restore')
                for param in learner.learner.agent.parameters():
                    param.grad = None
                learner.learner.log_alpha.grad = None
                metrics = learner.update(batch)
                row = dict(update=update, metrics=metrics, **capture(learner))
                saved = learner.state_dict()
                restored = roundtrip(saved, p['device'])
                if digest(restored) != digest(saved):
                    raise AssertionError('CUDA serialized round trip changed state values')
                rows.append(row)
            branches[name] = rows
        if branches['original'] != branches['candidate']:
            raise AssertionError('Actual candidate updates differ from original')
        if digest(ck) != parent_digest or sha(item['path']) != item['sha256']:
            raise AssertionError('Parent checkpoint/replay changed')
        results[method] = dict(parent_sha256=item['sha256'], initial_and_intermediate_restore_exact=True,
            two_updates_exact=True, agent_and_alpha_gradients_exact=True, original_step_device=p['device'],
            candidate_step_device='cpu', step_tensors=59, parent_unchanged=True, branches=branches)
        del ck, original, candidate
    control = p['sac_control']
    if sha(control['path']) != control['sha256']:
        raise ValueError('SAC control checkpoint drift')
    ck = torch.load(control['path'], map_location=p['device'], weights_only=False)
    state, arrays = ck['learner'], ck['replay']['arrays']
    parent_digest = digest(ck)
    kwargs = dict(dimension=arrays['actions'].shape[1], direct=ck['controller']=='direct', seed=ck['seed'],
        device=p['device'], algorithm='sac', critic_layer_norm=state['critic_layer_norm'],
        numerical_amendments=state['numerical_amendments'])
    control_rows = []
    for cls, root in [(Original, original_root), (Candidate, candidate_root)]:
        learner = cls(root, **kwargs)
        learner.load_state_dict(copy.deepcopy(state))
        control_rows.append(dict(state=digest(learner.state_dict()),
                                 counter_devices=[str(step.device) for step in counters(learner)]))
    if control_rows[0] != control_rows[1] or set(control_rows[1]['counter_devices']) != {p['device']}:
        raise AssertionError('SAC restore was unexpectedly changed')
    if digest(ck) != parent_digest or sha(control['path']) != control['sha256']:
        raise AssertionError('SAC control parent changed')
    value = dict(methods=results, sac_restore_control=dict(unchanged=True,
        checkpoint_sha256=control['sha256'], rows=control_rows),
        auxiliary_updates=4*len(results), new_physics=0,
        auxiliary_weights_saved=False, candidate_deployed=False, finished_unix=time.time(),
        registration_sha256=sha(args.registration))
    with Path(p['output']).open('x') as stream:
        stream.write(json.dumps(value,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    args = parser.parse_args()
    main(args)
