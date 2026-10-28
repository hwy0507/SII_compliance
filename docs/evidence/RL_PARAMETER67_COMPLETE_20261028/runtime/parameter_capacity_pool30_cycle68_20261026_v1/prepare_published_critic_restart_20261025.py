"""Explicit CHEQ critic-only restart; never an exact performance continuation.

An immutable parent supplies actor, alpha, their optimizers, RNG and replay.
Independent seeded initialization supplies online critics, matching targets and
an empty critic Adam optimizer. Reward and input/control contracts do not change.
The output checkpoint names the NEW registration and has a separate receipt;
parent cycle history stays in that receipt, not in new-stage plateau detection.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import torch

from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reset_critic_state(parent, fresh):
    if parent['algorithm'] != 'cheq' or fresh['algorithm'] != 'cheq':
        raise ValueError('Registered restart supports CHEQ only')
    if fresh['q_optimizer']['state']:
        raise ValueError('Expected a new empty critic optimizer')
    if parent['q_optimizer']['param_groups'] != fresh['q_optimizer']['param_groups']:
        raise ValueError('Critic reset must retain optimizer hyperparameters')
    if set(parent['agent']) != set(fresh['agent']):
        raise ValueError('Critic architecture changed')
    result = copy.deepcopy(parent)
    replaced = []
    for key, value in fresh['agent'].items():
        if key.startswith(('ensemble.', 'ensemble_targets.')):
            if value.shape != parent['agent'][key].shape or value.dtype != parent['agent'][key].dtype:
                raise ValueError('Critic architecture or dtype changed')
            result['agent'][key] = value.detach().cpu().clone()
            replaced.append(key)
        elif not key.startswith('actor.'):
            raise ValueError('Unexpected agent field: '+key)
    if not replaced:
        raise ValueError('No critics found')
    for key in replaced:
        if key.startswith('ensemble.'):
            target = key.replace('ensemble.', 'ensemble_targets.', 1)
            if not torch.equal(result['agent'][key], result['agent'][target]):
                raise ValueError('Fresh online and target critics differ')
    result['q_optimizer'] = copy.deepcopy(fresh['q_optimizer'])
    for key in parent:
        if key not in ('agent', 'q_optimizer') and digest(result[key]) != digest(parent[key]):
            raise AssertionError('Changed protected learner field: '+key)
    for key in parent['agent']:
        if key.startswith('actor.') and digest(result['agent'][key]) != digest(parent['agent'][key]):
            raise AssertionError('Actor changed')
    if digest(result['agent']) == digest(parent['agent']):
        raise ValueError('Critics were not changed')
    return result, replaced


def prepare(parent_path, registration, output, method):
    protocol = json.loads(Path(registration).read_text())
    spec = protocol['critic_restart']
    if spec['kind'] != 'fresh_critics_targets_optimizer_only':
        raise ValueError('Unsupported scientific restart')
    parent_registration = Path(spec['parent_registration'])
    if sha(parent_registration) != spec['parent_registration_sha256']:
        raise ValueError('Parent registration drift')
    previous = json.loads(parent_registration.read_text())
    descriptive = {'critic_restart', 'resume_parent_registration', 'restart_reason', 'registered_unix'}
    if ({k:v for k,v in previous.items() if k not in descriptive}
            != {k:v for k,v in protocol.items() if k not in descriptive}):
        raise ValueError('Critic-only restart changed another training contract')
    root = Path(protocol['runtime'])
    if sha(root/'RUNTIME.json') != protocol['runtime_sha256']:
        raise ValueError('Runtime drift')
    hashes = json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ('published_compliance_learner_20261025.py', 'published_compliance_numerics_20261025.py'):
        if sha(root/'source/tools'/name) != hashes['tools/'+name]:
            raise ValueError('Learner source drift')
    parent = torch.load(parent_path, map_location='cpu', weights_only=False)
    if (parent['controller'] != method or parent['boundary'] != 'complete_condition_cycle'
            or parent['protocol_sha256'] != spec['parent_registration_sha256']):
        raise ValueError('Expected exact parent complete-cycle checkpoint')
    state = parent['learner']
    if parent['seed'] not in protocol['seeds'] or method not in protocol['controllers']:
        raise ValueError('Unregistered method or training seed')
    original_state, original_replay = digest(state), digest(parent['replay'])
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    torch.set_num_threads(1)
    fresh = PublishedLearner(root, dimension=parent['replay']['arrays']['actions'].shape[1],
        direct=method=='direct', seed=spec['initialization_seed'], device='cpu', algorithm='cheq',
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    replacement, fields = reset_critic_state(state, fresh.state_dict())
    result = dict(parent, learner=replacement, protocol_sha256=sha(registration), cycles=[])
    result['scientific_restart'] = dict(kind=spec['kind'], parent_checkpoint_sha256=sha(parent_path),
        parent_protocol_sha256=parent['protocol_sha256'], initialization_seed=spec['initialization_seed'],
        parent_cycle_history=parent['cycles'], preserved_steps=parent['steps'],
        preserved_update_counter=state['num_gradient_steps'], critic_optimizer_reset=True)
    if digest(parent['learner']) != original_state or digest(parent['replay']) != original_replay:
        raise AssertionError('Immutable parent changed')
    output = Path(output)
    if output.exists() or output.with_suffix('.json').exists():
        raise FileExistsError('Never overwrite restart artifacts')
    torch.save(result, output)
    receipt = dict(parent_checkpoint=str(parent_path), parent_sha256=sha(parent_path),
        output_checkpoint=str(output), output_sha256=sha(output), registration_sha256=sha(registration),
        method=method, replaced_agent_fields=fields, replay_sha256=original_replay,
        parent_learner_unchanged=True, actor_alpha_and_optimizers_rng_preserved=True,
        critic_optimizer_reset=True, new_physical_transitions=0, auxiliary_weights_imported=False,
        parent_cycle_history=parent['cycles'], new_cycle_history_empty=True,
        consequence='CHEQ uncertainty and adaptive mixing may change because critics change; same mixing law',
        convergence_claim=False)
    output.with_suffix('.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--controller', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.parent, args.registration, args.output, args.controller)))
