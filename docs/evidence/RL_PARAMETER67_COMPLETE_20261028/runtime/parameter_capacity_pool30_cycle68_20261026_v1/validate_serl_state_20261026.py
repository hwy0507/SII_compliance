"""Exercise official SERL Bellman semantics, action mapping and exact resume.

Uses bounded synthetic data, no physics or trained weights are promoted.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from serl_state_adapter_20261026 import SerlStateLearner, execution_action


def digest(tree):
    import jax
    leaves, structure = jax.tree_util.tree_flatten(tree)
    h = hashlib.sha256(str(structure).encode())
    for leaf in leaves:
        x = np.asarray(leaf)
        h.update(str(x.dtype).encode())
        h.update(str(x.shape).encode())
        h.update(repr(leaf).encode() if x.dtype.hasobject else x.tobytes())
    return h.hexdigest()


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.time()
    a = SerlStateLearner(args.runtime, upstream=args.upstream,
        upstream_manifest=args.manifest, dimension=7, direct=True, seed=20261026,
        device='cuda:0')
    jax = a.jax
    rng = np.random.default_rng(20261026)
    n = 2048
    arrays = dict(observations=rng.normal(size=(n, 48)).astype('float32'),
        next_observations=rng.normal(size=(n, 48)).astype('float32'),
        actions=rng.uniform(-1, 1, (n, 7)).astype('float32'),
        rewards=rng.normal(size=(n, 1)).astype('float32'),
        dones=rng.integers(0, 2, (n, 1)).astype('float32'))
    batch = a.batch(arrays)
    key = jax.random.PRNGKey(902)
    subkey, action_key = jax.random.split(key)
    actions, _ = a.agent._compute_next_actions(batch, action_key)
    qs = a.agent.forward_target_critic(batch['next_observations'], actions, rng=subkey)
    _, ids_key = jax.random.split(subkey)
    ids = jax.random.randint(ids_key, (2,), 0, 10)
    target = batch['rewards'] + .9995 * batch['masks'] * qs[ids].min(axis=0)
    predicted = a.agent.forward_critic(batch['observations'], batch['actions'], rng=subkey)
    assert predicted.shape == (10, n)
    expected = float(jax.numpy.mean((predicted - target[None])**2))
    actual, info = a.agent.critic_loss_fn(batch, a.agent.state.params, key)
    np.testing.assert_allclose(float(actual), expected, rtol=2e-6)
    terminal = arrays['dones'].reshape(-1) == 1
    np.testing.assert_array_equal(np.asarray(target)[terminal], arrays['rewards'].reshape(-1)[terminal])
    np.testing.assert_array_equal(execution_action(-np.ones(7)), [0, -1, -1, -1, -1, -1, -1])
    np.testing.assert_array_equal(execution_action(np.ones(7)), np.ones(7))
    for raw in arrays['actions'][:100]:
        mapped = execution_action(raw)
        back = mapped.copy(); back[0] = 2 * back[0] - 1
        np.testing.assert_allclose(back, raw, atol=7e-8)
    initial = digest(a.state_dict()['agent']['params'])
    metrics = [a.update(arrays) for _ in range(2)]
    saved = a.state_dict()
    after = digest(saved['agent']['params'])
    assert after != initial
    assert saved['outer_updates'] == 2 and saved['num_gradient_steps'] == 16
    raw = np.zeros(48, 'float32')
    action1 = a.act(raw, step=5000)[1]
    metric1 = a.update(arrays)
    expected_next = a.state_dict()
    a.load_state_dict(copy.deepcopy(saved))
    assert digest(a.state_dict()) == digest(saved)
    action2 = a.act(raw, step=5000)[1]
    metric2 = a.update(arrays)
    np.testing.assert_array_equal(action1, action2)
    assert digest(a.state_dict()) == digest(expected_next)
    assert metric1 == metric2
    report = dict(passed=True, source=a.source_receipt, config=a.agent.config,
        actual_critic_shape=list(predicted.shape), terminal_bootstrap_zero=True,
        independent_bellman_loss=expected, upstream_bellman_loss=float(actual),
        affine_action_mapping=True, exact_state_roundtrip=True,
        subsequent_stochastic_action_and_update_exact=True,
        initial_params_sha256=initial, updated_params_sha256=after,
        synthetic_critic_updates=32, promoted_weights=False, physics_steps=0,
        duration_s=time.time()-start, metrics=metrics + [metric1],
        limitations=['Synthetic update/resume validation, not a physical preflight or convergence evidence'])
    (args.output/'REVIEW.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ['runtime', 'upstream', 'manifest', 'output']:
        p.add_argument('--'+name, type=Path, required=True)
    main(p.parse_args())
