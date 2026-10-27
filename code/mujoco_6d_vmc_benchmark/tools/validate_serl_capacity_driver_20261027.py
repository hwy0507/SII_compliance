"""Finite full-state capacity preparation on immutable complete22, not deployment.

Two arms perform exactly one original outer update each (8critic+1actor),
then compare full state and metrics. No weights are saved or promoted.
"""
from pathlib import Path
import argparse
import copy
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
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert sha(__file__) == reg['validator_sha256']
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    sys.path[:0] = [reg['candidate_runtime'], reg['helper_runtime'], reg['source_adapter'], reg['physics_tools']]
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_replay_capacity_20261027 import MARKER
    from resume_serl_capacity_reviewed_continuation_20261027 import capacity_replay, check_replay_restore
    from validate_serl_state_20261026 import digest
    ref = reg['inputs']['checkpoint']
    ck = torch.load(ref['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 22 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['steps'] == ck['replay']['size'] == 935790
    assert ck['learner']['num_gradient_steps'] == 7446328
    raw_digest, learner_digest = digest(ck['replay']), digest(ck['learner'])
    # Function-level fixture binds the real complete22 replay. The formal
    # validate_capacity contract separately fixes entry at complete23.
    fixture = dict(replay_capacity_stage=dict(parent_cycle=22, entry_replay_digest=raw_digest))
    expanded = capacity_replay(Replay, fixture, ck)
    learner_class = transfer_class(SerlMultistepLearner)
    kwargs = dict(upstream=Path(reg['upstream']), upstream_manifest=Path(reg['upstream_manifest']),
                  dimension=7, direct=True, seed=20261026, device='cuda:0')
    first = learner_class(Path(reg['runtime']), **kwargs)
    second = learner_class(Path(reg['runtime']), **kwargs)
    first.load_state_dict(ck['learner']); second.load_state_dict(ck['learner'])
    assert digest(first.state_dict()) == digest(second.state_dict()) == learner_digest
    checks = check_replay_restore(Replay, expanded, ck, first)
    baseline = optimized_class(replay_class(Replay))(7, 49, 20261079)
    candidate = expanded(7, 49, 20261079)
    baseline.load_state_dict(ck['replay']); candidate.load_state_dict(ck['replay'])
    saved = candidate.state_dict()
    # Exercise post-migration restoration using a metadata-only fixture; no
    # synthetic checkpoint is saved, registered as formal, or promoted.
    migrated = dict(ck, replay=saved)
    inherited_fixture = dict(replay_capacity_stage=dict(parent_cycle=21, entry_replay_digest=raw_digest))
    persisted = capacity_replay(Replay, inherited_fixture, migrated)
    restored = persisted(7, 49, 4); restored.load_state_dict(saved)
    assert digest(restored.state_dict()) == digest(saved)
    rejected = 0
    for bad in [dict(ck, replay=dict(ck['replay'], cursor=0)),
                dict(ck, replay=dict(ck['replay'], capacity=2_000_000))]:
        try:
            capacity_replay(Replay, fixture, bad)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('Invalid entry accepted')
    for bad in [ck, dict(migrated, replay=dict(saved, replay_capacity_extension={}))]:
        try:
            capacity_replay(Replay, inherited_fixture, bad)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError('Missing persistent marker accepted')
    a, b = baseline.sample(65536), candidate.sample(65536)
    assert digest(a) == digest(b)
    assert digest(first.batch(a)) == digest(second.batch(b))
    assert digest(baseline.rng.bit_generator.state) == digest(candidate.rng.bit_generator.state)
    before_updates = ck['learner']['num_gradient_steps']
    first_metrics = first.update(a)
    second_metrics = second.update(b)
    assert digest(first_metrics) == digest(second_metrics)
    assert digest(first.state_dict()) == digest(second.state_dict()) != learner_digest
    assert first.state_dict()['num_gradient_steps'] == before_updates+8
    assert first.state_dict()['outer_updates'] == ck['learner']['outer_updates']+1
    assert digest(ck['learner']) == learner_digest and digest(ck['replay']) == raw_digest
    assert all(np.isfinite(v) for v in first_metrics.values())
    for ref2 in reg['inputs'].values():
        assert sha(ref2['path']) == ref2['sha256']
    result = dict(passed=True, time=time.time(), checkpoint=ref,
        driver_sha256=reg['inputs']['driver']['sha256'], helper_sha256=reg['inputs']['helper']['sha256'],
        replay_preparation_sha256=reg['inputs']['replay_preparation']['sha256'],
        full_next_update_state_metrics_rng_exact=True, expanded_restore_next_batch_exact=True,
        check_only_replay_checks=checks, invalid_entry_or_persisted_marker_rejected=rejected,
        exact_original_learner_initial_digest=learner_digest,
        exact_original_replay_digest=raw_digest, next_state_digest=digest(first.state_dict()),
        next_metrics=first_metrics, outer_updates_per_arm=1, critic_updates_per_arm=8,
        actor_updates_per_arm=1, total_auxiliary_critic_updates=16,
        total_auxiliary_actor_updates=2, new_physics=0, weights_saved=False, formal_deployment=False,
        marker=MARKER,
        limitation='Actual immutable full22 predecessor, not complete23 migration parent. Function-level fixture exercises entry/restoration without formal validation or launch. Formal capacity entry requires exact full23 registration/checkpoint/digest and all full-cycle/health reviews; prospective24 preparation and monitors remain separate. No trained auxiliary state is saved or promoted.')
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
