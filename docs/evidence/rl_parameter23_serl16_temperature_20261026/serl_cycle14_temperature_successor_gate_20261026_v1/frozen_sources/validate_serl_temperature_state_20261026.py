"""Finite full-state/update gates for the temperature-successor candidate."""
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


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['batch_size'] == 65536 and reg['parent_cycle'] == 14
    for key in ['checkpoint', 'cycle_review', 'health_review', 'training_registration']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    protocol = json.loads(Path(reg['training_registration']['path']).read_text())
    root = Path(protocol['runtime'])
    for name, h in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        assert sha(root/'source'/name) == h
    sys.path[:0] = [str(Path(__file__).parent), reg['adapter_runtime'], str(root/'source/tools')]
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    from serl_temperature_state_candidate_20261026 import convert_agent, augment_batch
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 14 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['protocol_sha256'] == reg['training_registration']['sha256']
    review = json.loads(Path(reg['cycle_review']['path']).read_text())
    health = json.loads(Path(reg['health_review']['path']).read_text())
    assert review['passed'] and health['network_optimizer_rng_unchanged']
    assert review['methods']['direct']['checkpoint_sha256'] == health['checkpoint_sha256'] == reg['checkpoint']['sha256']
    learner = transfer_class(SerlMultistepLearner)(root, upstream=Path(reg['upstream']),
        upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True,
        seed=ck['seed'], device='cuda:0')
    learner.load_state_dict(copy.deepcopy(ck['learner']))
    before = digest(learner.state_dict())
    assert before == digest(ck['learner'])
    replay_digest = digest(ck['replay'])
    jax = learner.jax
    assert jax.config.jax_default_matmul_precision is None, 'Use unchanged formal default precision'
    native = learner.agent
    wrapped = convert_agent(native)
    def state(agent):
        return jax.device_get(learner.serialization.to_state_dict(agent.state))
    assert digest(state(wrapped)) == digest(state(native))
    assert wrapped.config == native.config
    arrays = ck['replay']['arrays']
    extra = ck['replay']['multistep_target_extension']
    assert not extra['pending']
    ready = np.asarray(extra['ready'], np.int64)
    rng = np.random.default_rng()
    rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
    rows = ready[rng.integers(len(ready), size=65536)]
    selected = {k: v[rows] for k, v in arrays.items() if k not in ('rewards', 'next_observations')}
    selected.update(rewards=extra['target_rewards'][rows, None],
        next_observations=arrays['next_observations'][extra['target_endpoints'][rows]],
        _bootstrap=extra['target_bootstrap'][rows])
    replay = optimized_class(replay_class(Replay))(7, 49, ck['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    assert digest(selected) == digest(replay.sample(65536))
    assert digest(rng.bit_generator.state) == digest(replay.rng.bit_generator.state)
    del replay
    batch = learner.batch(selected)
    alias = augment_batch(learner, batch, selected['next_observations'])
    candidate = augment_batch(learner, batch, arrays['next_observations'][rows])
    assert digest(alias['temperature_next_observations']) == digest(batch['next_observations'])
    assert digest(candidate['temperature_next_observations']) != digest(batch['next_observations'])
    for k in batch:
        assert digest(alias[k]) == digest(candidate[k]) == digest(batch[k])
    guards = []
    for label, invalid in [('width48', np.zeros((65536, 48), np.float32)),
        ('wrong_count', np.zeros((65535, 49), np.float32)),
        ('nan', np.full((65536, 49), np.nan, np.float32)),
        ('clock_high', np.full((65536, 49), 1.01, np.float32)),
        ('clock_low', np.full((65536, 49), -.01, np.float32))]:
        try:
            augment_batch(learner, batch, invalid)
        except ValueError:
            guards.append(label)
        else:
            raise AssertionError('Invalid successor accepted: '+label)
    try:
        convert_agent(wrapped)
    except ValueError:
        guards.append('double_conversion')
    else:
        raise AssertionError('Repeated conversion accepted')
    try:
        wrapped.temperature_loss_fn(batch, wrapped.state.params, jax.random.PRNGKey(0))
    except ValueError:
        guards.append('missing_temperature_state')
    else:
        raise AssertionError('Missing temperature input accepted')
    assert digest(learner.state_dict()) == before
    print('restoration, actual batch and7 negative guards passed', flush=True)

    # Same temperature successors must reproduce the native complete next8:1
    # update, including all network/target/optimizer/counter/RNG leaves.
    native_next, native_info = native.update_high_utd(batch, utd_ratio=8)
    alias_next, alias_info = wrapped.update_high_utd(alias, utd_ratio=8)
    assert digest(state(native_next)) == digest(state(alias_next)), 'Aliased full update differs from native'
    assert digest(jax.device_get(native_info)) == digest(jax.device_get(alias_info))
    assert int(native_next.state.step)-int(native.state.step) == 9
    alias_update_digest = digest(state(alias_next))
    del native_next, alias_next
    print('native versus aliased complete8:1 full-state/metrics exact', flush=True)
    isolation = {}
    for network in ['critic', 'actor', 'temperature']:
        a, ai = wrapped.update(alias, networks_to_update=frozenset({network}))
        b, bi = wrapped.update(candidate, networks_to_update=frozenset({network}))
        sa, sb = state(a), state(b)
        if network != 'temperature':
            assert digest(sa) == digest(sb), network+' changed with temperature-only input'
            assert digest(jax.device_get(ai)) == digest(jax.device_get(bi))
            isolation[network] = dict(full_state_and_metrics_exact=True)
        else:
            assert digest(sa['params']['modules_temperature']) != digest(sb['params']['modules_temperature'])
            for s in (sa, sb):
                s['params'] = {k: v for k, v in s['params'].items() if k != 'modules_temperature'}
                s['opt_states'] = {k: v for k, v in s['opt_states'].items() if k != 'temperature'}
            assert digest(sa) == digest(sb), 'Non-temperature state changed'
            isolation[network] = dict(only_temperature_params_and_optimizer_differ=True,
                baseline_temperature=float(a.forward_temperature()), candidate_temperature=float(b.forward_temperature()),
                baseline_metrics=jax.tree_util.tree_map(lambda v: float(v), jax.device_get(ai)),
                candidate_metrics=jax.tree_util.tree_map(lambda v: float(v), jax.device_get(bi)))
        del a, b, sa, sb
        print('isolated', network, 'passed', flush=True)
    assert digest(learner.state_dict()) == before
    assert digest(ck['replay']) == replay_digest
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    report = dict(time=time.time(), passed=True, checkpoint=reg['checkpoint'],
        source_sha256=sha(__file__), initial_learner_digest=before,
        final_original_learner_digest=digest(learner.state_dict()), replay_digest=replay_digest,
        full_original_state_and_replay_unchanged=True, negative_guards=guards,
        actual_deployed_first_batch_exact=True, native_alias_complete8to1_update_exact=True,
        alias_updated_state_digest=alias_update_digest, isolation=isolation,
        batch_rows_sha256=hashlib.sha256(rows.tobytes()).hexdigest(), formal_default_matmul_precision=True,
        auxiliary_critic_updates=18, auxiliary_actor_updates=4, auxiliary_temperature_updates=4,
        new_physics=0, weights_saved=False, formal_deployment=False, convergence_claim=False,
        limitation='Finite implementation gates on complete formal14 full state and actual next65536 batch. Auxiliary updated states are discarded. Gates do not show policy improvement or justify importing candidate weights.')
    write(args.output/'REVIEW.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        write(args.output/'FAILURE.json', dict(time=time.time(), error=repr(error)))
        raise
