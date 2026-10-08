"""Frozen-checkpoint critic diagnostics; no optimizer, simulation or selection.

Recorded discounted returns describe the historical behavior, not the current
policy's counterfactual return. Their difference from Q is not alone an estimate
of current-policy bias. This diagnostic can reveal insufficient value learning.
"""
import argparse
from pathlib import Path
import sys
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes


def summary(values):
    v = np.asarray(values)
    assert np.isfinite(v).all()
    return dict(mean=float(v.mean()), min=float(v.min()), max=float(v.max()),
                positive_fraction=float(np.mean(v > 0)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); cp = a.checkpoint.resolve(); assert not a.output.exists()
    before_hashes = checkpoint_hashes(cp)
    protocol = read(cp.parent/'PROTOCOL.json'); cfg = protocol['agent_config']
    state = read(cp.parent/'execution.json')
    expected = next(row for row in state['checkpoint_rows'] if row['path'] == str(cp))
    assert expected['hashes'] == before_hashes
    sys.path.insert(0, protocol['parameter_source'])
    from official_parameter_agent import OfficialParameterAgent
    from research72_adapted_rl_worker_20261003 import normalization_hash
    import jax
    import jax.numpy as jnp
    agent = OfficialParameterAgent(seed=cfg['seed'], total_steps=protocol['maximum_steps'],
        utd=protocol['utd'], gamma=cfg['gamma'], entropy_coef=cfg['temp_target_entropy_coef'],
        initial_temperature=cfg['temp_initial_value'], action_dimension=cfg['action_dimension'])
    agent.load(cp); before = agent.diagnostics(); norm_before = normalization_hash(agent)
    with np.load(cp/'office_replay.npz') as f: data = {k:f[k] for k in f.files}
    n = len(data['reward']); assert n == expected['step'] and data['terminated'][-1]
    # Fixed evenly spaced sample plus all terminal transitions. No outcome-based
    # choice of episodes, parameters or checkpoints.
    indices = np.unique(np.r_[np.linspace(0, n-1, 256, dtype=int), np.flatnonzero(data['terminated'])])
    norm = agent.observation_normalizer
    obs = jnp.asarray(norm._normalize(data['observation'][indices]))
    next_obs = jnp.asarray(norm._normalize(data['next_observation'][indices]))
    raw = agent.raw_agent
    dist, _ = raw._actor(observations=obs, temperature=0.)
    deterministic = dist.sample(seed=jax.random.PRNGKey(2026100901))
    result = dict(created_utc=now(), checkpoint=str(cp), steps=n, source_sha256=sha(__file__),
        sample_rule='256 evenly spaced transition indices plus all terminal transitions, deduplicated',
        sampled_indices=indices.tolist(), diagnostics=before, actions={},
        note='No optimizer or new physics. Replay Monte Carlo returns belong to historical behavior, '
             'not necessarily the current policy. This is a diagnostic, not checkpoint selection or convergence proof.')
    for label, actions in [('replay', data['action'][indices]), ('deterministic_actor', deterministic),
                           ('zero', np.zeros_like(data['action'][indices]))]:
        q, info = raw._critic(observations=obs, actions=jnp.asarray(actions))
        probs = np.exp(np.asarray(info['log_prob']))
        np.testing.assert_allclose(probs.sum(axis=-1), 1., rtol=1e-5, atol=1e-6)
        minimum = np.asarray(q).min(axis=0)
        result['actions'][label] = dict(q_minimum_twin=summary(minimum),
            mean_lower_edge_probability=float(probs[..., 0].mean()),
            mean_upper_edge_probability=float(probs[..., -1].mean()),
            action_abs95_fraction=float(np.mean(np.abs(actions) >= .95)))
        if label == 'replay': replay_q = minimum
    normalized_reward = np.asarray(agent.reward_normalizer._scale_reward(data['reward']))
    returns = np.empty(n, float); carry = 0.
    for i in range(n-1, -1, -1):
        carry = float(normalized_reward[i])+cfg['gamma']*(1-float(data['terminated'][i]))*carry
        returns[i] = carry
    result['historical_behavior_return'] = summary(returns[indices])
    result['replay_q_minus_behavior_return'] = summary(replay_q-returns[indices])
    ndist, _ = raw._actor(observations=next_obs)
    next_action = ndist.sample(seed=jax.random.PRNGKey(2026100902))
    logp = ndist.log_prob(next_action)
    target_q, _ = raw._target_critic(observations=next_obs, actions=next_action)
    alpha = float(raw._temperature())
    backup = normalized_reward[indices]+cfg['gamma']*(1-data['terminated'][indices])*(
        np.asarray(target_q).min(axis=0)-alpha*np.asarray(logp))
    result['unprojected_expected_td_backup'] = summary(backup)
    result['replay_q_minus_expected_td_backup'] = summary(replay_q-backup)
    terminal = data['terminated'][indices].astype(bool)
    result['terminal_q_minus_normalized_reward'] = summary(replay_q[terminal]-normalized_reward[indices][terminal])
    result['temperature'] = alpha
    assert before == agent.diagnostics() and norm_before == normalization_hash(agent)
    assert checkpoint_hashes(cp) == before_hashes
    result['normalization_and_checkpoint_unchanged'] = True
    result['checkpoint_hashes'] = before_hashes
    write(a.output, result)
    print({k:result[k] for k in ['steps','historical_behavior_return','replay_q_minus_behavior_return',
                                'terminal_q_minus_normalized_reward','normalization_and_checkpoint_unchanged']})


if __name__ == '__main__': main()
