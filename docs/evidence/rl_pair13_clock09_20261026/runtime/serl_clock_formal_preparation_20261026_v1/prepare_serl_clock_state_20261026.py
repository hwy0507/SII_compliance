"""Migrate reviewed formal SERL8, with exact state/replay and resume gates."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(args):
    os.sched_setaffinity(0, {0})
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    for name, expected in reg['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == expected
    for name in ('serl_state_adapter_20261026.py', 'validate_serl_state_20261026.py'):
        assert sha(Path(reg['adapter_runtime'])/name) == reg['source_hashes'][name]
    for name in ['checkpoint', 'review', 'clock', 'probe_review']:
        assert sha(reg[name]['path']) == reg[name]['sha256']
    assert json.loads(Path(reg['probe_review']['path']).read_text())['passed']
    sys.path.insert(0, reg['adapter_runtime'])
    from serl_state_adapter_20261026 import SerlStateLearner, OBSERVATION_SCALE
    from serl_clock_state_adapter_20261026 import SerlClockLearner, MARKER
    from validate_serl_state_20261026 import digest
    ck = torch.load(reg['checkpoint']['path'], weights_only=False, map_location='cpu')
    assert ck['cycle'] == 8 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['steps'] == 366962 and ck['replay']['size'] == 366962
    state_digest, replay_digest = digest(ck['learner']), digest(ck['replay'])
    options = dict(upstream=Path(reg['upstream']), upstream_manifest=Path(reg['upstream_manifest']),
                   dimension=7, direct=True, seed=20261026, device='cuda:0')
    old = SerlStateLearner(Path(reg['runtime']), **options)
    old.load_state_dict(copy.deepcopy(ck['learner']))
    learner = SerlClockLearner(Path(reg['runtime']), **options)
    learner.import_original_state(copy.deepcopy(ck['learner']))
    migrated = copy.deepcopy(learner.state_dict())
    paths = []
    def strip(node, path=()):
        if isinstance(node, dict):
            if 'clock_kernel' in node:
                assert np.all(node['clock_kernel'] == 0)
                paths.append('/'.join(path + ('clock_kernel',)))
            return {k: strip(v, path+(str(k),)) for k, v in node.items()
                    if k not in ('clock_kernel', 'critic_clock_extension')}
        return node
    assert digest(strip(migrated)) == state_digest and len(paths) == 8
    arrays = ck['replay']['arrays']
    clocks = np.load(reg['clock']['path'])
    assert clocks.shape == (ck['replay']['size'], 2) and clocks.dtype == np.float32
    replay = copy.deepcopy(ck['replay'])
    for index, key in enumerate(('observations', 'next_observations')):
        replay['arrays'][key] = np.concatenate([arrays[key], clocks[:, index:index+1]], axis=1)
        assert np.array_equal(replay['arrays'][key][:, :48], arrays[key])
        assert np.array_equal(replay['arrays'][key][:, 48], clocks[:, index])
    stripped_replay = copy.deepcopy(replay)
    for key in ('observations', 'next_observations'):
        stripped_replay['arrays'][key] = stripped_replay['arrays'][key][:, :48]
    assert digest(stripped_replay) == replay_digest
    del stripped_replay
    # Actual adapter action path, both deterministic and seeded stochastic.
    for deterministic in (True, False):
        old.load_state_dict(copy.deepcopy(ck['learner']))
        learner.load_state_dict(copy.deepcopy(migrated))
        learner.reset_episode(4)
        for index in (0, 1000, 9999):
            raw = arrays['observations'][index] * OBSERVATION_SCALE
            before = old.act(raw, step=ck['steps'], deterministic=deterministic, stream=4)
            after = learner.act(raw, step=ck['steps'], deterministic=deterministic, stream=4)
            for x, y in zip(before[1:3], after[1:3]):
                np.testing.assert_array_equal(x, y)
            np.testing.assert_array_equal(before[0], after[0][:48])
    # Episode clocks advance only on actions; observation reads do not advance.
    learner.reset_episode(12)
    raw = np.zeros(48, np.float32)
    for index in range(1375):
        observation, *_ = learner.act(raw, step=0, warmup=1, stream=12)
        assert observation[48] == np.float32((1375-index)/1375.)
    assert learner.terminal_observation(observation, stream=12)[48] == 0
    assert learner.observation(raw, stream=0)[48] == 1
    try:
        learner.act(raw, step=0, warmup=1, stream=12)
    except ValueError:
        pass
    else:
        raise AssertionError('Beyond-horizon action accepted')
    for bad in [ck['learner'], dict(migrated, critic_clock_extension={})]:
        try:
            learner.load_state_dict(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('Missing/changed clock marker accepted')
    ids = np.random.default_rng(91).integers(ck['replay']['size'], size=32768)
    batch = {key: value[ids] for key, value in replay['arrays'].items()}
    learner.load_state_dict(copy.deepcopy(migrated))
    assert digest(learner.state_dict()) == digest(migrated)
    # Two independent restores must give identical next complete official update.
    outcomes = []
    for _ in range(2):
        learner.load_state_dict(copy.deepcopy(migrated))
        metrics = learner.update(batch)
        outcomes.append((digest(learner.state_dict()), metrics))
    assert outcomes[0] == outcomes[1]
    learner.load_state_dict(copy.deepcopy(migrated))
    assert digest(learner.state_dict()) == digest(migrated)
    assert digest(ck['learner']) == state_digest and digest(ck['replay']) == replay_digest
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    prepared = dict(ck, learner=migrated, replay=replay)
    assert all(digest(prepared[k]) == digest(v) for k, v in ck.items() if k not in ('learner', 'replay'))
    args.output.mkdir(exist_ok=False)
    torch.save(prepared, args.output/'prepared_cycle08.pt')
    result = dict(passed=True, time=time.time(), checkpoint_sha256=reg['checkpoint']['sha256'],
                  prepared_checkpoint_sha256=sha(args.output/'prepared_cycle08.pt'),
                  registration_sha256=sha(args.registration), marker=MARKER,
                  original_full_learner_recovered_exactly=True, added_zero_paths=paths,
                  old_replay_recovered_exactly=True, replay_rows=366962,
                  old_history_and_counters_unchanged=True, full_prepared_state_sha256=digest(migrated),
                  actor_deterministic_and_stochastic_exact=True, clock_full_horizon_and_stream_isolation=True,
                  negative_marker_guards=True, next_official_update_exact_after_restore=True,
                  auxiliary_critic_updates=16, auxiliary_actor_updates=2, formal_optimizer_updates=0,
                  auxiliary_weights_imported=False, new_physics=0)
    (args.output/'REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True)
        (args.output/'FAILURE.json').write_text(json.dumps(dict(error=repr(error)))+'\n')
        raise
