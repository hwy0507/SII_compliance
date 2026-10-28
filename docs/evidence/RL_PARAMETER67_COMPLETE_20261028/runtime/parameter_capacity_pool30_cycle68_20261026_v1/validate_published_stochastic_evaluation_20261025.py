"""Validate action-only seeded evaluation on an immutable real checkpoint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

from evaluate_published_compliance_20261025 import seed_evaluation_actions
from validate_published_finite_check_20261025 import digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(registration):
    p = json.loads(registration.read_text())
    for path, expected in p['source_and_input_hashes'].items():
        if sha(path) != expected:
            raise ValueError('Registered source or input drift: '+path)
    os.sched_setaffinity(0, {p['cpu']})
    torch.set_num_threads(1)
    sys.path.insert(0, str(Path(p['runtime'])/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    ck = torch.load(p['checkpoint'], map_location='cpu', weights_only=False)
    learner = PublishedLearner(p['runtime'], dimension=7, direct=True,
        seed=ck['seed'], device='cuda:0', algorithm='cheq',
        critic_layer_norm=ck['learner']['critic_layer_norm'],
        numerical_amendments=ck['learner']['numerical_amendments'])
    learner.load_state_dict(ck['learner'])
    before = digest(learner.learner.agent.state_dict())
    updates = learner.learner.num_gradient_steps
    raw = [json.loads(line)['observation'] for line in
           Path(p['journal']).read_text().splitlines()[:64]]
    if len(raw) != 64:
        raise ValueError('Expected64 archived observations')

    def actions(seed, deterministic):
        seed_evaluation_actions(learner, seed, p['case_id'])
        learner.reset_episode()
        return np.stack([learner.act(obs, step=ck['steps'],
                                    deterministic=deterministic)[2] for obs in raw])

    first = actions(p['seeds'][0], False)
    repeat = actions(p['seeds'][0], False)
    other = actions(p['seeds'][1], False)
    det = actions(p['seeds'][0], True)
    det_other = actions(p['seeds'][1], True)
    if not np.array_equal(first, repeat):
        raise AssertionError('Same action seed did not reproduce exact actions')
    if np.array_equal(first, other):
        raise AssertionError('Different seeds produced an identical action stream')
    if not np.array_equal(det, det_other):
        raise AssertionError('Deterministic actions depended on action seed')
    if digest(learner.learner.agent.state_dict()) != before:
        raise AssertionError('Evaluation changed network state')
    if learner.learner.num_gradient_steps != updates:
        raise AssertionError('Evaluation changed optimizer update count')
    for path, expected in p['source_and_input_hashes'].items():
        if sha(path) != expected:
            raise AssertionError('Registered input changed')
    Path(p['output']).write_text(json.dumps(dict(
        same_seed_exact=True, distinct_seed_changes_actions=True,
        deterministic_seed_invariant=True, network_unchanged=True,
        observations=64, inference_calls=320, optimizer_updates=0, new_physics=0,
        action_stream_sha256=digest(first),
        stochastic_deterministic_mean_absolute_difference_per_axis=
            np.mean(abs(first-det), axis=0).tolist(),
        limitation='Same archived states only; no task-quality or trajectory claim.',
        registration_sha256=sha(registration)), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args().registration)
