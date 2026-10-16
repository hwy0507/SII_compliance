"""Read-only train-replay Bellman/actor diagnostics in a bounded local service.

No simulator, gradient update, model save, held-out input or acceptance. Report
projected distributional targets, not behavior Monte Carlo as Q ground truth.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


def target_statistics(probabilities, rewards, done, entropy_term, gamma_n, support):
    """Independent expectation of upstream clipped categorical Bellman atoms.

    Linear projection onto equally spaced support preserves this clipped mean.
    Clipping mass is weighted by probability, not merely a count of atoms.
    """
    import numpy as np
    atoms = rewards[:, None] + gamma_n * (support[None, :] - entropy_term[:, None]) * (1-done[:, None])
    clipped = np.clip(atoms, support[0], support[-1])
    return {
        'target_mean': (probabilities * clipped).sum(axis=1),
        'unclipped_target_mean': (probabilities * atoms).sum(axis=1),
        'clipped_mass': (probabilities * ((atoms < support[0]) | (atoms > support[-1]))).sum(axis=1),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cp = args.checkpoint.resolve()
    out = args.output.resolve()
    from rl_recovery_control_20261016 import verify_checkpoint, read, digest
    from rl_goal_stage_20261016 import write
    import platform
    assert platform.node() == 'airpig'
    assert not out.exists(), 'Preserve all diagnostic receipts'
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 2*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    checked = verify_checkpoint(cp)
    spec = read(cp.parent/'PROTOCOL.json')
    runner = read(cp/'office_runner.json')
    result = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint=str(cp), checkpoint_hashes=checked['hashes'],
        source_sha256=digest(Path(__file__)), protocol_sha256=digest(cp.parent/'PROTOCOL.json'),
        simulation=False, gradient_updates=0, model_saved=False, acceptance=False,
        sample_seed=20261016, sample_rule='1024 uniform replay indices plus last n steps of every train episode; fixed union, not success-selected')
    write(out,result)
    try:
        sys.path.insert(0,spec['parameter_source'])
        import numpy as np
        import jax
        import jax.numpy as jnp
        from official_parameter_agent import OfficialParameterAgent
        from multistep_rl_replay_20261009 import MultiStepReplay
        config = spec['agent_config']
        agent = OfficialParameterAgent(seed=spec['seed'],total_steps=spec['maximum_steps'],utd=spec['utd'],
            gamma=config['gamma'],entropy_coef=config['temp_target_entropy_coef'],
            initial_temperature=config['temp_initial_value'],action_dimension=config['action_dimension'])
        agent.load(cp)
        before = agent.diagnostics()
        rng_before = np.asarray(agent.raw_agent._rng).copy()
        count = runner['step']
        n = config['n_step']
        replay = MultiStepReplay(count,config['action_dimension'],20261016,n_step=n,gamma=config['gamma'])
        with np.load(cp/'office_replay.npz',allow_pickle=False) as raw:
            assert set(raw.files) == set(replay.data)
            for key in replay.data:
                assert raw[key].shape == replay.data[key].shape
                replay.data[key][:] = raw[key]
        replay.count = count
        terminal = replay.data['terminated'].astype(bool)
        assert terminal[-1] and not replay.data['truncated'].any()
        replay.last_terminal = count-1
        terminals = np.flatnonzero(terminal)
        distance = np.empty(count,int)
        mc = np.empty(count,float)
        remaining = 0
        ret = 0.
        for i in range(count-1,-1,-1):
            if terminal[i]:
                remaining = 0
                ret = 0.
            distance[i] = remaining
            ret = float(replay.data['reward'][i]) + config['gamma']*ret
            mc[i] = ret
            remaining += 1
        tail = np.flatnonzero(distance < n)
        ids = np.unique(np.r_[np.random.default_rng(20261016).integers(count,size=1024),tail])
        values = {key:[] for key in ('q','target_mean','unclipped_target_mean','clipped_mass',
            'reward_n','actor_q','policy_saturated_fraction','behavior_saturated_fraction',
            'policy_behavior_abs_difference','entropy','discounted_entropy_correction')}
        support = np.linspace(config['critic_min_v'],config['critic_max_v'],config['critic_num_bins'])
        temperature = float(agent.raw_agent._temperature())
        for offset in range(0,len(ids),256):
            chosen = ids[offset:offset+256]
            batch = replay.at(chosen)
            obs = jnp.asarray(agent.observation_normalizer._normalize(batch['observation']))
            nxt = jnp.asarray(agent.observation_normalizer._normalize(batch['next_observation']))
            q, _ = agent.raw_agent._critic(observations=obs,actions=jnp.asarray(batch['action']))
            dist, _ = agent.raw_agent._actor(observations=nxt)
            actions = dist.sample(seed=jax.random.PRNGKey(20261016+offset))
            logp = dist.log_prob(actions)
            next_q, info = agent.raw_agent._target_critic(observations=nxt,actions=actions)
            which = np.asarray(next_q).argmin(axis=0)
            probabilities = np.exp(np.asarray(info['log_prob'])[which,np.arange(len(chosen)),:])
            np.testing.assert_allclose(probabilities.sum(axis=1),1,atol=1e-5)
            reward_n = np.asarray(agent.reward_normalizer._scale_reward(batch['reward']))
            entropy_term = temperature*np.asarray(logp)
            targets = target_statistics(probabilities,reward_n,batch['terminated'],entropy_term,
                config['gamma']**n,support)
            policy_dist, _ = agent.raw_agent._actor(observations=obs)
            policy_action = policy_dist.sample(seed=jax.random.PRNGKey(20262016+offset))
            policy_q, _ = agent.raw_agent._critic(observations=obs,actions=policy_action)
            current = dict(q=np.asarray(q).min(axis=0),**targets,reward_n=reward_n,
                actor_q=np.asarray(policy_q).min(axis=0),
                policy_saturated_fraction=(np.abs(np.asarray(policy_action))>.95).mean(axis=1),
                behavior_saturated_fraction=(np.abs(batch['action'])>.95).mean(axis=1),
                policy_behavior_abs_difference=np.abs(np.asarray(policy_action)-batch['action']).mean(axis=1),
                entropy=-np.asarray(policy_dist.log_prob(policy_action)),
                discounted_entropy_correction=-(config['gamma']**n)*entropy_term*(1-batch['terminated']))
            for key in values:
                values[key].append(current[key])
        values = {key:np.concatenate(chunks) for key,chunks in values.items()}
        values['projected_td_residual'] = values['q']-values['target_mean']
        values['actor_minus_behavior_q'] = values['actor_q']-values['q']
        values['normalized_behavior_mc'] = mc[ids]/before['reward_scale_denominator']
        def stats(x):
            assert np.isfinite(x).all()
            return dict(n=int(x.size),mean=float(x.mean()),mean_absolute=float(np.abs(x).mean()),
                minimum=float(x.min()),maximum=float(x.max()),p10=float(np.quantile(x,.1)),p90=float(np.quantile(x,.9)))
        latest = ids>(terminals[-2] if len(terminals)>1 else -1)
        terminal_window = distance[ids]<n
        groups = dict(all=np.ones(len(ids),bool),terminal=distance[ids]==0,
            within_n_step_terminal=distance[ids]<n,far_from_terminal=distance[ids]>=n,
            latest_episode=latest,
            latest_episode_terminal_window=latest & terminal_window,
            earlier_episode_terminal_windows=~latest & terminal_window)
        result.update(status='passed', actual_n_step=n,temperature=temperature,
            sample_count=len(ids),replay_count=count,replay_episodes=len(terminals),
            diagnostics=before,groups={group:{key:stats(x[mask]) for key,x in values.items()}
                for group,mask in groups.items() if mask.any()},
            diagnostics_unchanged=before==agent.diagnostics(),
            rng_unchanged=bool(np.array_equal(rng_before,np.asarray(agent.raw_agent._rng))),
            checkpoint_hashes_unchanged=all(digest(cp/key)==value for key,value in checked['hashes'].items()),
            terminal_window_caveat='The last n transitions become terminal-backed only when the terminal is observed. At an immediate episode-boundary checkpoint they have had only the terminal-step update opportunity. Earlier versus latest terminal windows separate replay exposure from pooled fitting error; neither group proves policy success.',
            interpretation='Frozen train-only diagnostic. Targets use sampled current actor and saved target critic, with exact clipped support expectation; not an independent true-Q estimate. MC is historical behavior return without entropy and is not soft-Q ground truth. Saturation alone is not proof of a defect. No causal comparison or convergence claim.')
        assert result['diagnostics_unchanged'] and result['rng_unchanged'] and result['checkpoint_hashes_unchanged']
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        result.update(ended_utc=datetime.now(timezone.utc).isoformat(),
            peak_memory_bytes=int((cg/'memory.peak').read_text()),memory_events=(cg/'memory.events').read_text())
        write(out,result)
    print(json.dumps({key:result[key] for key in ('status','actual_n_step','sample_count','temperature','peak_memory_bytes')}))


if __name__ == '__main__':
    main()
