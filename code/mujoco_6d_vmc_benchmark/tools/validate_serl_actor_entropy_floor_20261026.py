"""Finite full-state/update gates for the actor entropy-floor candidate."""
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
    assert reg['batch_size'] == 65536 and reg['parent_cycle'] == 15
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
    from serl_actor_entropy_floor_candidate_20261026 import convert_agent
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 15 and ck['boundary'] == 'complete_condition_cycle'
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
    wrapped = convert_agent(native, 0.0)
    floored = convert_agent(native, 0.1)
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
    guards = []
    for label, floor in [('negative', -0.1), ('nan', float('nan')), ('inf', float('inf')), ('unregistered', 0.05)]:
        try: convert_agent(native, floor)
        except ValueError: guards.append(label)
        else: raise AssertionError('Invalid floor accepted')
    for label, agent in [('double_conversion', wrapped), ('entropy_backup', native.replace(config=dict(native.config, backup_entropy=True)))]:
        try: convert_agent(agent, 0.1)
        except ValueError: guards.append(label)
        else: raise AssertionError('Invalid agent accepted')
    assert float(wrapped.raw_temperature()) == float(native.forward_temperature())
    assert float(floored.forward_temperature()) == float(np.float32(0.1))
    assert float(floored.raw_temperature()) == float(native.forward_temperature())
    print('full restore, actual65536 batch, six negative guards passed', flush=True)

    # Zero floor must reproduce the native complete next8:1
    # update, including all network/target/optimizer/counter/RNG leaves.
    native_next, native_info = native.update_high_utd(batch, utd_ratio=8)
    alias_next, alias_info = wrapped.update_high_utd(batch, utd_ratio=8)
    def compare(left, right):
        details=[]
        def visit(a,b,path=()):
            if isinstance(a,dict):
                assert set(a)==set(b)
                for k in a:visit(a[k],b[k],path+(str(k),))
            elif isinstance(a,(tuple,list)):
                assert type(a) is type(b) and len(a)==len(b)
                for i,(x,y) in enumerate(zip(a,b)):visit(x,y,path+(str(i),))
            else:
                a,b=np.asarray(a),np.asarray(b);assert a.shape==b.shape and a.dtype==b.dtype
                if not np.issubdtype(a.dtype,np.inexact):
                    assert np.array_equal(a,b),'Nonfloat/counter/RNG mismatch: '+str(path)
                else:
                    assert np.isfinite(a).all() and np.isfinite(b).all()
                    delta=np.abs(a.astype(np.float64)-b.astype(np.float64))
                    details.append(dict(path='/'.join(path),elements=int(a.size),exact=bool(np.array_equal(a,b)),max_abs=float(delta.max()) if a.size else 0.,max_value=float(np.maximum(np.abs(a),np.abs(b)).max()) if a.size else 0.,rmse=float(np.sqrt(np.mean(delta*delta))) if a.size else 0.,close_1e6_1e7=bool(np.allclose(a,b,rtol=1e-6,atol=1e-7))))
        visit(left,right)
        return dict(exact=all(x['exact'] for x in details),nonfloat_counter_rng_exact=True,
            max_abs=max(x['max_abs'] for x in details),all_close_1e6_1e7=all(x['close_1e6_1e7'] for x in details),leaves=details)
    default_comparison=compare(state(native_next),state(alias_next))
    default_metrics=compare(jax.device_get(native_info),jax.device_get(alias_info))
    write(args.output/'DEFAULT_NUMERICAL_COMPARISON.json',dict(state=default_comparison,metrics=default_metrics))
    assert int(native_next.state.step)-int(native.state.step) == 9
    alias_update_digest = digest(state(alias_next))
    del native_next, alias_next
    print('default native/alias full update max_abs',default_comparison['max_abs'],'exact',default_comparison['exact'],flush=True)
    assert default_comparison['exact'] and default_metrics['exact'], 'Zero-floor full update must be bitwise native'
    # Evaluate both inherited official objectives together with common noise;
    # their difference must be exactly the extra entropy coefficient term.
    @jax.jit
    def objective_pair(a, b, values, key):
        la, ia = a.policy_loss_fn(values, a.state.params, key)
        lb, ib = b.policy_loss_fn(values, b.state.params, key)
        expected = -(b.forward_temperature()-a.forward_temperature())*ia['entropy']
        return la, lb, expected, ia['entropy'], ib['entropy']
    la, lb, expected, ha, hb = [float(v) for v in objective_pair(wrapped, floored, batch, jax.random.PRNGKey(2026102621))]
    assert ha == hb and np.isclose(lb-la, expected, rtol=1e-5, atol=1e-5)
    formula = dict(control_loss=la, candidate_loss=lb, expected_difference=expected, actual_difference=lb-la, entropy=ha)
    isolation = {}
    for network in ['critic', 'actor', 'temperature']:
        a, ai = wrapped.update(batch, networks_to_update=frozenset({network}))
        b, bi = floored.update(batch, networks_to_update=frozenset({network}))
        sa, sb = state(a), state(b)
        if network != 'actor':
            assert digest(sa) == digest(sb), network+' changed with actor-only entropy floor'
            assert digest(jax.device_get(ai)) == digest(jax.device_get(bi))
            isolation[network] = dict(full_state_and_metrics_exact=True)
        else:
            assert digest(sa['params']['modules_actor']) != digest(sb['params']['modules_actor'])
            for s in (sa, sb):
                s['params'] = {k: v for k, v in s['params'].items() if k != 'modules_actor'}
                s['opt_states'] = {k: v for k, v in s['opt_states'].items() if k != 'actor'}
            assert digest(sa) == digest(sb), 'Non-actor state changed'
            isolation[network] = dict(only_actor_params_and_optimizer_differ=True,
                baseline_effective_temperature=float(a.forward_temperature()), candidate_effective_temperature=float(b.forward_temperature()),
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
        actual_deployed_first_batch_exact=True, native_alias_complete8to1_update_exact=default_comparison['exact'],
        actor_objective_formula=formula,
        default_numerical_comparison=default_comparison,default_metrics_comparison=default_metrics,
        alias_updated_state_digest=alias_update_digest, isolation=isolation,
        batch_rows_sha256=hashlib.sha256(rows.tobytes()).hexdigest(), formal_default_matmul_precision=True,
        auxiliary_critic_updates=18, auxiliary_actor_updates=4, auxiliary_temperature_updates=4,
        new_physics=0, weights_saved=False, formal_deployment=False, convergence_claim=False,
        limitation='Finite gates on complete formal15 and actual next65536 batch. Default precision; control floor0 bitwise native, exact critic/temperature isolation and only actor params/optimizer differ with floor0.1. Original dual optimization is retained and unconstrained; effective actor entropy coefficient alone is floored. No physics, saved weights or formal deployment.')
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
