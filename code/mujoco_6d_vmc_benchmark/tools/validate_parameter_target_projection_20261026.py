"""Finite projection contract and disabled-patch full-update equivalence gate."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import torch

from published_finite_target_projection_20261026 import bound, project, install
from published_terminal_loss_weight_20261026 import weighted_class
from diagnose_published_value_bound_20261025 import soft_upper_bound
from validate_published_finite_check_20261025 import digest


def main(args):
    os.sched_setaffinity(0, {13})
    torch.set_num_threads(1)
    n = torch.tensor([[1.], [2.], [275.], [1375.]], device=args.device)
    comparisons = 0
    for dimension in (5, 7):
        for alpha in (0., .001, .05, .2):
            got = bound(alpha, .9995, n, dimension * math.log(2)).cpu().numpy()
            exact = soft_upper_bound(alpha, .9995, n.cpu().numpy(),
                                     -np.ones(dimension), np.ones(dimension))
            assert np.all(got >= exact)
            assert np.all(got-exact <= 2*np.spacing(exact.astype(np.float32)))
            comparisons += len(n)
    obs = torch.zeros((4, 50), device=args.device)
    obs[:, 49:50] = n/1375.
    high = torch.full((4, 1), 10000., device=args.device)
    low = torch.full((4, 1), -10000., device=args.device)
    before_rng = torch.cuda.get_rng_state_all()
    assert project(high, obs, .05, .9995, 5*math.log(2), False) is high
    assert torch.equal(project(low, obs, .05, .9995, 5*math.log(2)), low)
    assert torch.equal(project(high, obs, .05, .9995, 5*math.log(2)),
                       bound(.05, .9995, n, 5*math.log(2)))
    reward = torch.tensor([[25.], [-25.], [0.], [-40.]], device=args.device)
    assert torch.equal(reward + .9995*torch.zeros_like(reward)*project(
        high, obs, .05, .9995, 5*math.log(2)), reward)
    assert all(torch.equal(a,b) for a,b in zip(before_rng,torch.cuda.get_rng_state_all()))
    sys.path.insert(0, str(args.runtime/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from train_published_compliance_20261025 import Replay
    from published_replay_device_cache_20261025 import DeviceReplayCache
    ck = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    state, arrays = ck['learner'], ck['replay']['arrays']
    assert ck['cycle'] == 10 and state['terminal_loss_weight'] == 128
    parent_digest, replay_digest = digest(state), digest(ck['replay'])
    learner = weighted_class(PublishedLearner, 128)(args.runtime,
        dimension=arrays['actions'].shape[1], direct=False, seed=20261026,
        device=args.device, algorithm='cheq', critic_layer_norm=state['critic_layer_norm'],
        numerical_amendments=state['numerical_amendments'], critic_clock=True)
    replay = Replay(arrays['actions'].shape[1], arrays['observations'].shape[1], 20261026)
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    cache = DeviceReplayCache(replay, args.device)
    outcomes = []
    for patched in (False, True):
        learner.load_state_dict(copy.deepcopy(state))
        for parameter in learner.learner.agent.parameters():
            parameter.grad = None
        assert digest(learner.state_dict()) == parent_digest
        replay.rng = np.random.default_rng(20261026)
        if patched:
            receipt = install(learner, False)
        metrics = learner.update(cache.sample(32768))
        outcomes.append((digest(learner.state_dict()), metrics, digest(replay.rng.bit_generator.state)))
    assert outcomes[0] == outcomes[1]
    assert digest(state) == parent_digest and digest(ck['replay']) == replay_digest
    result = dict(passed=True, independent_bound_comparisons=comparisons,
        upward_rounding_passed=True, projection_identity_and_clipping_passed=True,
        terminal_target_unchanged=True, projection_rng_unchanged=True,
        disabled_projection_full_update_identical=True, formal_parent_unchanged=True,
        auxiliary_test_updates=2, formal_updates=0, new_physics=0, patch=receipt)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--device', required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
