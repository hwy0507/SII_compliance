"""Target-pair mean math and minimum-mode full-state equivalence gate."""
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
    from published_target_pair_mean_20261026 import reduce_pair, install
    first=torch.tensor([[-10.],[2.],[100.]],device=args.device)
    second=torch.tensor([[-6.],[-2.],[60.]],device=args.device)
    rng=torch.cuda.get_rng_state_all()
    assert torch.equal(reduce_pair(first,second,True),torch.tensor([[-8.],[0.],[80.]],device=args.device))
    assert torch.equal(reduce_pair(first,second,False),torch.minimum(first,second))
    assert all(torch.equal(a,b) for a,b in zip(rng,torch.cuda.get_rng_state_all()))
    sys.path.insert(0, str(args.runtime/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from train_published_compliance_20261025 import Replay
    from published_replay_device_cache_20261025 import DeviceReplayCache
    ck = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    state, arrays = ck['learner'], ck['replay']['arrays']
    assert ck['cycle'] == 12 and state['terminal_loss_weight'] == 128
    parent_digest, replay_digest = digest(state), digest(ck['replay'])
    from published_exact_projected_learner_20261026 import exact_class
    learner = exact_class(PublishedLearner)(args.runtime,
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
    result = dict(passed=True, independent_pair_math=True, reducer_rng_unchanged=True,
        minimum_full_update_identical=True, formal_parent_unchanged=True,
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
