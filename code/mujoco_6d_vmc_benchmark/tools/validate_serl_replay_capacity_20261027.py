"""Bounded replay-only migration checks; no learner update or formal deployment."""
from pathlib import Path
import argparse
import copy
import gc
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert sha(__file__) == reg['validator_sha256']
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    sys.path[:0] = [reg['candidate_runtime'], reg['helper_runtime'], reg['source_adapter'], reg['physics_tools']]
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import replay_class as multistep, MARKER as MULTISTEP
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_replay_capacity_20261027 import replay_class as expand, MARKER
    from validate_serl_state_20261026 import digest
    base = optimized_class(multistep(Replay))
    def normalize(state):
        result = dict(state)
        assert result.pop('replay_capacity_extension') == MARKER
        result['capacity'] = 1_000_000
        return result
    def expect_reject(call):
        try:
            call()
        except (ValueError, TypeError, KeyError, IndexError):
            return
        raise AssertionError('Invalid replay accepted')
    ck = torch.load(reg['inputs']['real_checkpoint']['path'], map_location='cpu', weights_only=False)
    state = ck['replay']
    assert ck['steps'] == state['size'] == 896782 and state['cursor'] == state['size']
    original_digest = digest(state)
    baseline = base(7, 49, 20261079)
    candidate = expand(base, original_digest)(7, 49, 20261079)
    baseline.load_state_dict(state)
    candidate.load_state_dict(state)
    assert digest(normalize(candidate.state_dict())) == digest(baseline.state_dict()) == original_digest
    actual = dict(rows=state['size'], ready=len(baseline.ready),
                  pending=sum(len(q) for q in baseline.pending.values()),
                  legacy_replay_digest=original_digest, sampled_batches=[])
    for count in [1, 32, 256, 65536]:
        assert digest(baseline.sample(count)) == digest(candidate.sample(count))
        assert digest(baseline.rng.bit_generator.state) == digest(candidate.rng.bit_generator.state)
        actual['sampled_batches'].append(count)
    assert digest(state) == original_digest
    del ck, state, baseline, candidate
    gc.collect()

    baseline = base(7, 49, 812)
    empty = Replay(7, 49, 812)
    baseline.import_one_step_state(empty.state_dict(), dict(rewards=np.empty(0, np.float32),
        bootstrap=np.empty(0, np.float32), endpoints=np.empty(0, np.int64), lengths=np.empty(0, np.int32)))
    del empty
    streams, lengths = {}, [4, 35, 66]
    def transition(step, stream, length):
        return dict(observations=np.full(49, step+stream/10, np.float32),
            next_observations=np.full(49, step+1+stream/10, np.float32),
            actions=np.full(7, stream/10, np.float32),
            rewards=np.array([(-1)**step*(step+.1)], np.float32),
            dones=np.array([step == length-1], np.float32))
    for step in range(19):
        for stream, length in enumerate(lengths):
            if step < length:
                streams.setdefault(stream, []).append(baseline.size)
                baseline.add(stream=stream, **transition(step, stream, length))
    entry = copy.deepcopy(baseline.state_dict())
    assert len(entry['multistep_target_extension']['ready']) == 4
    assert sum(map(len, entry['multistep_target_extension']['pending'].values())) == 38
    candidate = expand(base, digest(entry))(7, 49, 812)
    candidate.load_state_dict(entry)
    for step in range(19, 66):
        for stream, length in enumerate(lengths):
            if step < length:
                streams[stream].append(baseline.size)
                row = transition(step, stream, length)
                baseline.add(stream=stream, **row)
                candidate.add(stream=stream, **row)
        if step == 40:
            snapshot = copy.deepcopy(candidate.state_dict())
            restored = expand(base)(7, 49, 999)
            restored.load_state_dict(snapshot)
            assert digest(restored.state_dict()) == digest(snapshot)
            candidate = restored
        assert digest(candidate.sample(16)) == digest(baseline.sample(16))
        assert digest(normalize(candidate.state_dict())) == digest(baseline.state_dict())
    assert candidate.size == 105 and not candidate.pending
    for ids in streams.values():
        for position, index in enumerate(ids):
            end = min(position+32, len(ids))
            selected = ids[position:end]
            value = sum(.9995**j * float(candidate.arrays['rewards'][i, 0]) for j, i in enumerate(selected))
            assert candidate.target_rewards[index] == np.float32(value)
            assert candidate.target_endpoints[index] == selected[-1]
            assert candidate.target_lengths[index] == len(selected)
            expected = 0. if end == len(ids) else .9995**(len(selected)-1)
            assert candidate.target_bootstrap[index] == np.float32(expected)
    valid = copy.deepcopy(candidate.state_dict())
    bad_states = []
    for key in ['replay_capacity_extension', 'multistep_target_extension']:
        bad = copy.deepcopy(valid); bad.pop(key); bad_states.append(bad)
    for key, value in [('capacity', 1_000_000), ('cursor', 0), ('size', 2_000_001)]:
        bad = copy.deepcopy(valid); bad[key] = value; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['replay_capacity_extension']['sampling'] = 'all_rows'; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['arrays']['dones'][0] = .5; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['arrays']['rewards'][0] = np.nan; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['arrays']['observations'] = bad['arrays']['observations'][:, :48]; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['multistep_target_extension']['target_lengths'] = bad['multistep_target_extension']['target_lengths'].astype(np.int64); bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['multistep_target_extension']['target_bootstrap'][0] = 2; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['multistep_target_extension']['ready'].pop(); bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['multistep_target_extension']['target_endpoints'][-1] = 106; bad_states.append(bad)
    bad = copy.deepcopy(valid); bad['rng'] = {}; bad_states.append(bad)
    for bad in bad_states:
        expect_reject(lambda bad=bad: candidate.load_state_dict(bad))
    expect_reject(lambda: expand(base)(7, 49, 812).load_state_dict(entry))
    expect_reject(lambda: expand(base, 'wrong-digest')(7, 49, 812).load_state_dict(entry))
    negative_count = len(bad_states)+2
    del baseline, candidate, restored, valid, snapshot, entry, bad_states
    gc.collect()

    def full_terminal_prefix(size, capacity, expanded):
        arrays = {k: np.zeros((size, width), np.float32) for k, width in
                  dict(observations=49, next_observations=49, actions=7, rewards=1, dones=1).items()}
        arrays['dones'].fill(1)
        result = dict(capacity=capacity, size=size, cursor=size, arrays=arrays,
            rng=np.random.default_rng(944).bit_generator.state,
            multistep_target_extension=dict(marker=copy.deepcopy(MULTISTEP),
                target_rewards=np.zeros(size, np.float32), target_bootstrap=np.zeros(size, np.float32),
                target_endpoints=np.arange(size, dtype=np.int64), target_lengths=np.ones(size, np.int32),
                ready=list(range(size)), pending={}))
        if expanded:
            result['replay_capacity_extension'] = copy.deepcopy(MARKER)
        return result
    boundary = full_terminal_prefix(999999, 1_000_000, False)
    baseline = base(7, 49, 944); baseline.load_state_dict(boundary)
    candidate = expand(base, digest(boundary))(7, 49, 944); candidate.load_state_dict(boundary)
    row = transition(0, 0, 1)
    baseline.add(stream=0, **row)
    candidate.add(stream=0, **row)
    assert baseline.size == candidate.size == 1_000_000 and baseline.cursor == 0 and candidate.cursor == 1_000_000
    expect_reject(lambda: baseline.add(stream=0, **row))
    candidate.add(stream=0, **row)
    assert candidate.size == candidate.cursor == 1_000_001
    for key in boundary['arrays']:
        np.testing.assert_array_equal(candidate.arrays[key][:999999], boundary['arrays'][key])
    del boundary, baseline, candidate
    gc.collect()
    boundary = full_terminal_prefix(1999999, 2_000_000, True)
    candidate = expand(base)(7, 49, 944); candidate.load_state_dict(boundary)
    candidate.add(stream=0, **row)
    assert candidate.size == candidate.cursor == 2_000_000
    final_rng = digest(candidate.rng.bit_generator.state)
    last = {key: value[-1].copy() for key, value in candidate.arrays.items()}
    expect_reject(lambda: candidate.add(stream=0, **row))
    assert candidate.size == candidate.cursor == 2_000_000 and digest(candidate.rng.bit_generator.state) == final_rng
    for key in last:
        np.testing.assert_array_equal(last[key], candidate.arrays[key][-1])
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    result = dict(passed=True, time=time.time(), real_snapshot=actual,
        real_raw_derived_ready_pending_rng_preserved=True, synthetic_interleaved_rows=105,
        pending_roundtrip_exact=True, independent_32step_targets_exact=True,
        rejected_malformed_states=negative_count, old_capacity_crossing_preserves_prefix=True,
        new_capacity_fills_last_slot_then_refuses_overwrite=True,
        new_physics=0, learner_updates=0, weights_saved=False, formal_deployment=False,
        marker=MARKER, limitation='Replay-only candidate validation. Real input is immutable Direct22 startup snapshot with pending rows, not a complete-cycle migration parent. No learner update equivalence or formal24 launch is claimed; exact complete23 registration and driver/monitor checks remain required. Beyond old capacity the previous driver raises, so no whole-algorithm ring-buffer equivalence is claimed.')
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
