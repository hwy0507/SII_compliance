"""Validate explicit target-rule checkpoint continuation without online physics."""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

from continue_published_completed_stage_20261025 import prepare_state
from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(registration):
    p = json.loads(registration.read_text())
    for name, expected in p['source_and_input_hashes'].items():
        if sha(name) != expected:
            raise ValueError('Registered input drift: '+name)
    torch.set_num_threads(1)
    os.sched_setaffinity(0, {p['cpu']})
    sys.path.insert(0, str(Path(p['runtime'])/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from published_bellman_minimum_20261025 import install_bellman_minimum
    from train_published_compliance_20261025 import validate_resume_protocol
    candidate = json.loads(Path(p['candidate_protocol']).read_text())
    validate_resume_protocol(candidate['resume_parent_registration']['sha256'],
                             candidate, sha(p['candidate_protocol']))
    results = {}
    for method, item in p['checkpoints'].items():
        ck = torch.load(item['path'], map_location='cpu', weights_only=False)
        if sha(item['path']) != item['sha256'] or ck['cycle'] != 9:
            raise ValueError('Expected immutable cycle9')
        parent_hash = digest(ck)
        prepared, receipt = prepare_state(ck, None, 5)
        state = prepared['learner']
        arrays = ck['replay']['arrays']
        learner = PublishedLearner(p['runtime'], dimension=arrays['actions'].shape[1],
            direct=method == 'direct', seed=ck['seed'], device=p['device'], algorithm='cheq',
            critic_layer_norm=state['critic_layer_norm'],
            numerical_amendments=state['numerical_amendments'])
        learner.load_state_dict(copy.deepcopy(ck['learner']))
        if digest(learner.state_dict()) != digest(ck['learner']):
            raise AssertionError('Legacy pair checkpoint failed exact round trip')
        learner.load_state_dict(copy.deepcopy(state))
        if digest(learner.state_dict()) != digest(state):
            raise AssertionError('Prepared full learner state changed on restore')
        if learner.learner.train.__func__.__code__.co_filename != '<registered_sii_all5_bellman_minimum>':
            raise AssertionError('Checkpoint metadata did not activate registered target rule')
        stream = io.BytesIO()
        torch.save(learner.state_dict(), stream)
        stream.seek(0)
        restored = torch.load(stream, map_location='cpu', weights_only=False)
        learner.load_state_dict(restored)
        if digest(learner.state_dict()) != digest(state):
            raise AssertionError('Serialized candidate failed round trip')
        indices = np.r_[np.flatnonzero(arrays['dones'][:, 0] == 0)[:120],
                        np.flatnonzero(arrays['dones'][:, 0] == 1)[:8]]
        batch = {k: v[indices].copy() for k, v in arrays.items()}
        # Reference is the already verified instance-only offline intervention.
        learner.load_state_dict(copy.deepcopy(ck['learner']))
        for param in learner.learner.agent.parameters():
            param.grad = None
        install_bellman_minimum(learner.learner, 5)
        expected_metrics = learner.update(batch)
        expected_state = learner.state_dict()
        learner.load_state_dict(copy.deepcopy(state))
        for param in learner.learner.agent.parameters():
            param.grad = None
        actual_metrics = learner.update(batch)
        actual_state = learner.state_dict()
        actual_state.pop('bellman_target_count')
        if actual_metrics != expected_metrics or digest(actual_state) != digest(expected_state):
            raise AssertionError('Resumed update differs from registered offline candidate')
        if digest(ck) != parent_hash or sha(item['path']) != item['sha256']:
            raise AssertionError('Parent checkpoint mutated')
        results[method] = dict(preparation=receipt, legacy_restore_exact=True,
            candidate_restore_exact=True, serialized_restore_exact=True,
            actual_update_matches_offline_candidate_exactly=True,
            candidate_q_loss=actual_metrics['agent_train/q_loss'], parent_unchanged=True)
    Path(p['output']).write_text(json.dumps(dict(methods=results,
        auxiliary_updates=8, new_physics=0, auxiliary_weights_saved=False,
        online_stage_launched=False, registration_sha256=sha(registration)),
        indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args().registration)
