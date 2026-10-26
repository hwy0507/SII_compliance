"""Read-only conditional actor diagnostics on a complete formal checkpoint.

Compare fixed initial, early32 and uniform replay cohorts. Decompose the exact
official SERL actor loss (mean of all10 critics, plus temperature*log_prob),
without changing any optimizer, replay, RNG or policy. Gradient cosines are
finite sampled Euclidean diagnostics, not Adam updates or task-effect estimates.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['sample_size'] == 8192 and reg['seed'] == 2026102617
    assert reg['optimizer_updates'] == reg['new_physics'] == 0
    for key in ['checkpoint', 'training_registration', 'cycle_review', 'health_review']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    protocol = json.loads(Path(reg['training_registration']['path']).read_text())
    root = Path(protocol['runtime'])
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        assert sha(root/'source'/name) == expected
    sys.path[:0] = [reg['adapter_runtime'], str(root/'source/tools')]
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 14 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['protocol_sha256'] == reg['training_registration']['sha256']
    cycle = json.loads(Path(reg['cycle_review']['path']).read_text())
    health = json.loads(Path(reg['health_review']['path']).read_text())
    assert cycle['passed'] and health['network_optimizer_rng_unchanged']
    assert cycle['methods']['direct']['checkpoint_sha256'] == health['checkpoint_sha256'] == reg['checkpoint']['sha256']
    learner = SerlMultistepLearner(root, upstream=Path(reg['upstream']),
        upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True,
        seed=ck['seed'], device='cuda:0')
    learner.load_state_dict(ck['learner'])
    initial_digest = digest(learner.state_dict())
    assert initial_digest == digest(ck['learner'])
    replay_digest = digest(ck['replay'])
    arrays = ck['replay']['arrays']
    extra = ck['replay']['multistep_target_extension']
    ready = np.asarray(extra['ready'], np.int64)
    assert not extra['pending'] and np.array_equal(np.sort(ready), np.arange(ck['replay']['size']))
    clock = arrays['observations'][:, 48]
    initial_rows = np.flatnonzero(clock == np.float32(1))
    early_rows = np.flatnonzero(clock >= np.float32((1375-31)/1375))
    assert len(initial_rows) == 450 and len(early_rows) == 450*32
    rng = np.random.default_rng(reg['seed'])
    count = reg['sample_size']
    selected = dict(initial=rng.choice(initial_rows, count, replace=True),
        early32=rng.choice(early_rows, count, replace=False),
        uniform=rng.choice(ready, count, replace=False))
    np.savez(args.output/'selected_rows.npz', **selected)
    jax = learner.jax
    import jax.numpy as jnp
    from jax.flatten_util import ravel_pytree
    agent = learner.agent
    params = agent.state.params
    actor_keys = [k for k in params if 'actor' in k]
    assert len(actor_keys) == 1, list(params)
    actor_key = actor_keys[0]
    key = jax.random.PRNGKey(reg['seed'])
    _, policy_key, sample_key, critic_key = jax.random.split(key, 4)
    alpha = agent.forward_temperature()
    gradients = {}
    cohorts = {}

    def flat_actor(tree):
        for name, branch in tree.items():
            if name != actor_key:
                assert all(np.count_nonzero(np.asarray(v)) == 0 for v in jax.tree_util.tree_leaves(branch))
        value, _ = ravel_pytree(tree[actor_key])
        return np.asarray(value, dtype=np.float64)

    for name, rows in selected.items():
        obs = jax.device_put(dict(state=np.ascontiguousarray(arrays['observations'][rows, :48]),
            clock=np.ascontiguousarray(arrays['observations'][rows, 48:49])))
        batch = dict(observations=obs, rewards=jnp.zeros((count,), dtype=jnp.float32))

        def parts(p, current_batch, random_key):
            _, pk, sk, ck = jax.random.split(random_key, 4)
            current_obs = current_batch['observations']
            temperature = agent.forward_temperature()
            distribution = agent.forward_policy(current_obs, rng=pk, grad_params=p)
            action, log_prob = distribution.sample_and_log_prob(seed=sk)
            q = agent.forward_critic(current_obs, action, rng=ck)
            assert q.shape == (10, count)
            # Official SERL policy uses all10-critic mean. Random2/min is only
            # the critic bootstrap, not the policy objective.
            predicted_q = q.mean(axis=0)
            return jnp.stack([-predicted_q.mean(), (temperature*log_prob).mean()])

        component_values = np.asarray(jax.jit(parts)(params, batch, key))
        component_jac = jax.jit(jax.jacrev(parts, argnums=0))(params, batch, key)
        q_gradient = flat_actor(jax.tree_util.tree_map(lambda x: x[0], component_jac))
        entropy_gradient = flat_actor(jax.tree_util.tree_map(lambda x: x[1], component_jac))
        (official_value, info), official_grad = jax.jit(
            jax.value_and_grad(agent.policy_loss_fn, argnums=1, has_aux=True))(batch, params, key)
        official_gradient = flat_actor(official_grad)
        np.testing.assert_allclose(component_values.sum(), np.asarray(official_value), rtol=2e-6, atol=2e-6)
        np.testing.assert_allclose(q_gradient+entropy_gradient, official_gradient, rtol=2e-4, atol=2e-6)
        assert np.isfinite(official_gradient).all()
        distribution = agent.forward_policy(obs, rng=policy_key)
        base = distribution.distribution
        loc, scale = np.asarray(base.mean()), np.asarray(base.stddev())
        mode = np.asarray(distribution.mode())
        assert loc.shape == scale.shape == mode.shape == (count, 7)
        np.testing.assert_allclose(np.tanh(loc), mode, rtol=1e-6, atol=1e-6)
        assert np.all(scale > 0)

        def q_from_action(action):
            return agent.forward_critic(obs, action, rng=critic_key).mean(axis=0).sum()

        action_gradient = np.asarray(jax.jit(jax.grad(q_from_action))(jnp.asarray(mode)))
        gradients[name+'_q'] = q_gradient
        gradients[name+'_entropy'] = entropy_gradient
        gradients[name+'_official'] = official_gradient
        def describe(value):
            return dict(mean=np.mean(value, axis=0).tolist(),
                p05=np.percentile(value, 5, axis=0).tolist(),
                p95=np.percentile(value, 95, axis=0).tolist())
        cohorts[name] = dict(sample_count=count, unique_rows=int(len(np.unique(rows))),
            initial_rows_sampled=int(np.sum(clock[rows] == 1)),
            early_rows_sampled=int(np.sum(clock[rows] >= np.float32((1375-31)/1375))),
            row_ids_sha256=hashlib.sha256(rows.tobytes()).hexdigest(),
            actor_loss=float(official_value), q_loss_term=float(component_values[0]),
            entropy_loss_term=float(component_values[1]), sampled_entropy=float(info['entropy']),
            pre_tanh_mean=describe(loc), pre_tanh_std=describe(scale), raw_mode=describe(mode),
            public0_mode_mean=float(((mode[:, 0]+1)*.5).mean()),
            mode_tanh_derivative=describe(1-mode*mode),
            q_action_gradient=describe(action_gradient),
            q_pre_tanh_mean_gradient=describe(action_gradient*(1-mode*mode)),
            gradient_sum_max_error=float(np.max(np.abs(q_gradient+entropy_gradient-official_gradient))),
            official_loss_exact_formula_verified=True)
        print(name, json.dumps(dict(entropy=cohorts[name]['sampled_entropy'],
            raw_mode_mean=cohorts[name]['raw_mode']['mean'])), flush=True)
    norms = {k: float(np.linalg.norm(v)) for k, v in gradients.items()}
    cosines = {}
    for a in gradients:
        for b in gradients:
            if a < b:
                den = norms[a]*norms[b]
                cosines[a+'__'+b] = float(np.dot(gradients[a], gradients[b])/den) if den else None
    np.savez(args.output/'actor_gradients.npz', **gradients)
    assert digest(learner.state_dict()) == initial_digest
    assert digest(ck['replay']) == replay_digest
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    report = dict(time=time.time(), passed=True, checkpoint=reg['checkpoint'],
        initial_learner_digest=initial_digest, final_learner_digest=digest(learner.state_dict()),
        replay_digest=replay_digest, full_network_optimizer_rng_unchanged=True,
        replay_unchanged=True, temperature=float(alpha), actor_parameter_key=actor_key,
        replay_rows=len(ready), initial_population=len(initial_rows), early32_population=len(early_rows),
        expected_initial_rows_per_formal_actor_batch=65536*len(initial_rows)/len(ready),
        expected_early32_rows_per_formal_actor_batch=65536*len(early_rows)/len(ready),
        cohorts=cohorts, gradient_norms=norms, gradient_cosines=cosines,
        selected_rows_sha256=sha(args.output/'selected_rows.npz'),
        actor_gradients_sha256=sha(args.output/'actor_gradients.npz'),
        new_physics=0, optimizer_updates=0, replay_writes=0, weights_saved=False,
        limitation='Frozen formal14, fixed8192-row cohorts and one registered noise draw. Initial cohort resamples all450 initial rows; early32 and uniform cohorts use no replacement. Cosines describe sampled Euclidean gradients, not actual Adam parameter updates, confidence intervals, or causal policy/task improvement. Pre-tanh normal std is reported directly; transformed distribution.stddev helper is not used. Actor objective is official all10-critic mean; random2/min applies only to critic bootstrap.',
        convergence_claim=False)
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
