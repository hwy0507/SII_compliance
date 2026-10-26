"""Compare official temperature gradients on current, raw-next and n-step states.

Fixed frozen14, existing uniform8192 row IDs, common external random key,
zero optimization/physics. State distribution is the only comparison factor.
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


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    for key in ['checkpoint', 'actor_diagnostic_registration', 'actor_diagnostic_review', 'selected_rows', 'source']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    parent = json.loads(Path(reg['actor_diagnostic_registration']['path']).read_text())
    for ref in parent['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    protocol = json.loads(Path(parent['training_registration']['path']).read_text())
    root = Path(protocol['runtime'])
    sys.path[:0] = [parent['adapter_runtime'], str(root/'source/tools')]
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 14 and ck['boundary'] == 'complete_condition_cycle'
    learner = SerlMultistepLearner(root, upstream=Path(parent['upstream']),
        upstream_manifest=Path(parent['upstream_manifest']), dimension=7, direct=True,
        seed=ck['seed'], device='cuda:0')
    learner.load_state_dict(ck['learner'])
    before = digest(learner.state_dict())
    assert before == digest(ck['learner'])
    jax = learner.jax
    jax.config.update('jax_default_matmul_precision', 'highest')
    agent = learner.agent
    import jax.numpy as jnp
    with np.load(reg['selected_rows']['path']) as data:
        rows = data['uniform'].copy()
    assert len(rows) == 8192
    arrays = ck['replay']['arrays']
    endpoints = ck['replay']['multistep_target_extension']['target_endpoints'][rows]
    observations = dict(current=arrays['observations'][rows],
        raw_next1=arrays['next_observations'][rows],
        derived_next32=arrays['next_observations'][endpoints])
    assert reg['seed'] == 2026102618
    key = jax.random.PRNGKey(reg['seed'])
    _, next_key = jax.random.split(key)
    temperature_key = next(k for k in agent.state.params if 'temperature' in k)
    parameter = float(agent.state.params[temperature_key]['lagrange'])
    alpha = float(agent.forward_temperature())
    target = float(agent.config['target_entropy'])
    evaluate = jax.jit(jax.value_and_grad(agent.temperature_loss_fn, argnums=1, has_aux=True))
    sample = jax.jit(agent._compute_next_actions)
    result = {}
    for name, obs in observations.items():
        batch = jax.device_put(dict(next_observations=dict(
            state=np.ascontiguousarray(obs[:, :48]), clock=np.ascontiguousarray(obs[:, 48:49])),
            rewards=np.zeros(8192, np.float32), actions=np.zeros((8192, 7), np.float32)))
        (_, log_prob) = sample(batch, next_key)
        entropy = float(-log_prob.mean())
        (value, _), gradient = evaluate(batch, agent.state.params, key)
        for k, branch in gradient.items():
            if k != temperature_key:
                assert all(np.count_nonzero(np.asarray(x)) == 0 for x in jax.tree_util.tree_leaves(branch))
        raw_gradient = float(gradient[temperature_key]['lagrange'])
        expected_loss = alpha*(entropy-target)
        expected_gradient = float(jax.nn.sigmoid(jnp.asarray(parameter)))*(entropy-target)
        np.testing.assert_allclose(value, expected_loss, rtol=2e-5, atol=2e-6)
        np.testing.assert_allclose(raw_gradient, expected_gradient, rtol=2e-5, atol=2e-6)
        result[name] = dict(entropy=entropy, entropy_minus_target=entropy-target,
            official_temperature_loss=float(value), raw_softplus_parameter_gradient=raw_gradient,
            negative_gradient_direction='increase_temperature' if raw_gradient < 0 else 'decrease_temperature',
            initial_states=int(np.sum(obs[:, 48] == 1)),
            first32_states=int(np.sum(obs[:, 48] >= np.float32((1375-31)/1375))),
            observation_sha256=hashlib.sha256(obs.tobytes()).hexdigest(),
            analytic_loss_error=float(abs(value-expected_loss)),
            analytic_gradient_error=abs(raw_gradient-expected_gradient))
    assert digest(learner.state_dict()) == before
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    report = dict(time=time.time(), passed=True, checkpoint=reg['checkpoint'],
        rows=8192, row_ids_sha256=hashlib.sha256(rows.tobytes()).hexdigest(),
        temperature=alpha, target_entropy=target, raw_softplus_parameter=parameter,
        states=result, initial_state_digest=before, final_state_digest=digest(learner.state_dict()),
        full_network_optimizer_rng_unchanged=True, optimizer_updates=0, new_physics=0,
        formal_precision_unchanged=True, diagnostic_matmul_precision='highest',
        limitation='Common-noise comparison on one fixed uniform8192 cohort from frozen formal14. Gradient signs describe negative Euclidean gradient direction; actual Adam momentum can differ. No optimizer/state writes or task-improvement claim. Official temperature objective is unchanged; only the input state distribution is varied for diagnosis.',
        convergence_claim=False)
    (args.output/'REVIEW.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        (args.output/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
