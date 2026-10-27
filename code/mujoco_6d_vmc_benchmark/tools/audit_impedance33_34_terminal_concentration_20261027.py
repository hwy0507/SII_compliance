"""Frozen Impedance33/34 terminal error concentration and retained-row tracking, without updates.

Population terminal contributions use the actual per-critic mask/weight
denominators. They are not minibatch losses or estimates of nonterminal TD loss.
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


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['controller'] == 'impedance' and reg['cycles'] == [33, 34]
    assert reg['optimizer_updates'] == reg['new_physics'] == 0
    assert sha(__file__) == reg['source_sha256']
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    runtime = Path(reg['runtime'])
    assert sha(runtime/'RUNTIME.json') == reg['runtime_sha256']
    hashes = json.loads((runtime/'SOURCE_HASHES.json').read_text())
    for name, expected in hashes.items():
        assert sha(runtime/'source'/name) == expected
    sys.path[:0] = [str(runtime/'source/tools'), reg['helper_runtime']]
    from published_compliance_learner_20261025 import PublishedLearner
    from validate_published_finite_check_20261025 import digest
    assert sha(Path(reg['helper_runtime'])/'validate_published_finite_check_20261025.py') == reg['digest_helper_sha256']
    maps, results = {}, []
    for cycle in reg['cycles']:
        refs = reg['inputs'][str(cycle)]
        health = json.loads(Path(refs['health']['path']).read_text())['methods']['impedance']
        review = json.loads(Path(refs['review']['path']).read_text())
        assert review['passed'] and health['checkpoint_sha256'] == refs['checkpoint']['sha256']
        ck = torch.load(refs['checkpoint']['path'], map_location='cpu', weights_only=False)
        assert ck['cycle'] == cycle and ck['boundary'] == 'complete_condition_cycle'
        assert ck['controller'] == 'impedance' and ck['replay']['size'] == ck['steps']
        state, arrays = ck['learner'], ck['replay']['arrays']
        assert state['terminal_loss_weight'] == 128
        assert state['target_pair_reduction'] == dict(version=1, target='minimum', actor='minimum', sampled_targets=2)
        assert arrays['observations'].shape == (ck['steps'], 50)
        assert arrays['masks'].shape == (ck['steps'], 5)
        # As in the reviewed CPU health diagnostic, restore all agent weights
        # for forward evaluation only. No optimizer or training RNG is loaded.
        learner = PublishedLearner(runtime, dimension=arrays['actions'].shape[1], direct=False,
            seed=42, device='cpu', algorithm=state['algorithm'],
            **{key: state[key] for key in ('critic_layer_norm', 'numerical_amendments', 'critic_clock')})
        agent = learner.learner.agent
        agent.load_state_dict(state['agent'])
        before = digest(agent.state_dict())
        assert before == digest(state['agent'])
        random_before = torch.get_rng_state().clone()
        terminal = np.flatnonzero(arrays['dones'][:, 0] == 1)
        assert len(terminal) == health['terminal_count'] == {33: 1015, 34: 1045}[cycle]
        with torch.no_grad():
            obs = torch.as_tensor(arrays['observations'][terminal])
            actions = torch.as_tensor(arrays['actions'][terminal])
            q = torch.stack([agent.get_q_value(obs, actions, i, target=False).reshape(-1)
                             for i in range(agent.ensemble_size)]).numpy().astype(np.float64)
        reward = arrays['rewards'][terminal, 0].astype(np.float64)
        mask = arrays['masks'][terminal].T.astype(np.float64)
        assert q.shape == mask.shape == (5, len(terminal))
        assert np.isin(mask, [0., 1.]).all() and np.isfinite(q).all()
        error = q-reward[None]
        # The existing health report subtracts in float32 before its float64
        # summary. Reproduce that order for the exact comparison; use explicit
        # float64 arithmetic only for the population contribution below.
        health_error = np.abs(q.astype(np.float32)-reward.astype(np.float32)[None]).astype(np.float64)
        comparison = dict(health_mae=health['terminal_q_absolute_error']['mean'],
            reproduced_float32_error_mae=float(health_error.mean()),
            float64_error_mae=float(np.abs(error).mean()),
            health_inbag_mae=health['terminal_q_in_bag_absolute_error']['mean'],
            reproduced_float32_inbag_mae=float(health_error[mask.astype(bool)].mean()))
        (root/f'cycle{cycle}_NUMERICAL_COMPARISON.json').write_text(json.dumps(comparison, indent=2)+'\n')
        assert np.isclose(health_error.mean(), comparison['health_mae'], rtol=0, atol=1e-9)
        assert np.isclose(health_error[mask.astype(bool)].mean(), comparison['health_inbag_mae'], rtol=0, atol=1e-9)
        denominator = arrays['masks'].sum(axis=0, dtype=np.float64)+127*mask.sum(axis=1)
        contributions = (128*mask*error**2/denominator[:, None]).sum(axis=0)
        assert np.isfinite(contributions).all() and (contributions >= 0).all()
        terms = {}
        with Path(refs['transitions']['path']).open() as stream:
            for line in stream:
                t = json.loads(line)
                assert t['cycle'] == cycle
                if t['done']:
                    terms[t['condition']] = dict(replay_index=t['step']-1, reward=t['reward'])
        assert len(terms) == 30
        maps[cycle] = terms
        positions = {int(v): i for i, v in enumerate(terminal)}
        for item in terms.values():
            assert item['replay_index'] in positions
            assert abs(float(arrays['rewards'][item['replay_index'], 0])-item['reward']) < 3e-6
        features = np.concatenate([arrays['observations'][terminal], arrays['actions'][terminal]], axis=1)
        assert np.isfinite(features).all()
        order = np.argsort(-contributions)
        total = float(contributions.sum())
        current_set = {v['replay_index'] for v in terms.values()}
        current = np.asarray([int(v) in current_set for v in terminal])
        ranked = []
        for i in order[:20]:
            ranked.append(dict(replay_index=int(terminal[i]), reward=float(reward[i]),
                q=q[:, i].tolist(), masks=mask[:, i].tolist(), contribution=float(contributions[i]),
                fraction=float(contributions[i]/total), current_cycle=bool(current[i]),
                current_condition=next((case for case, item in terms.items() if item['replay_index'] == int(terminal[i])), None)))
        retained_tracking = None
        if cycle == 34:
            with np.load(root/'cycle33_terminal_values.npz', allow_pickle=False) as previous:
                count = len(previous['replay_indices'])
                np.testing.assert_array_equal(terminal[:count], previous['replay_indices'])
                np.testing.assert_array_equal(reward[:count], previous['rewards'])
                np.testing.assert_array_equal(mask[:, :count], previous['masks'])
                np.testing.assert_array_equal(features[:count], previous['features'])
                old_sse = (previous['masks']*(previous['q']-previous['rewards'][None])**2).sum()
                now_sse = (mask[:, :count]*error[:, :count]**2).sum()
                old_denominator_contribution = (128*mask[:, :count]*error[:, :count]**2/previous['denominators'][:, None]).sum()
                retained_tracking = dict(retained_terminal_count=count,
                    masked_sse_at33=float(old_sse), masked_sse_at34=float(now_sse),
                    retained_loss_at34_using33_denominators=float(old_denominator_contribution),
                    retained_loss_at34_using34_denominators=float(contributions[:count].sum()),
                    new34_terminal_loss_contribution=float(contributions[count:].sum()),
                    new34_terminal_count=len(terminal)-count,
                    retained_rewards_and_masks_exact=True)
                assert len(terminal)-count == 30
        assert digest(agent.state_dict()) == before and torch.equal(random_before, torch.get_rng_state())
        np.savez_compressed(root/f'cycle{cycle}_terminal_values.npz', replay_indices=terminal, q=q,
            rewards=reward, masks=mask, features=features, denominators=denominator, contributions=contributions)
        results.append(dict(cycle=cycle, checkpoint_sha256=refs['checkpoint']['sha256'], terminal_count=len(terminal),
            terminal_population_loss_contribution=total, per_critic_denominator=denominator.tolist(),
            top1_fraction=float(contributions[order[:1]].sum()/total),
            top5_fraction=float(contributions[order[:5]].sum()/total),
            top10_fraction=float(contributions[order[:10]].sum()/total),
            current30_fraction=float(contributions[current].sum()/total), top20=ranked,
            retained_terminal_tracking=retained_tracking,
            recent1000_logged_q_loss=health['recent_optimizer']['agent_train/q_loss']['mean'],
            agent_weights_and_forward_rng_unchanged=True,
            values_sha256=sha(root/f'cycle{cycle}_terminal_values.npz')))
        del learner, agent, ck, arrays
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    report = dict(passed=True, time=time.time(), cycles=results, optimizer_updates=0, new_physics=0,
        replay_writes=0, original_checkpoints_unchanged=True, convergence_claim=False,
        formula='Sum across5 critics of terminal row128*mask*(Q-reward)^2 divided by that critic full-replay sum(mask*(1+127*done)).',
        limitation='Terminal-only contribution to a frozen full-replay weighted loss; excludes ordinary TD terms and differs from random minibatch denominator expectation and logged online loss. No target-pair/entropy sampling is needed for terminal labels. CPU inference matches prior health diagnostics, but does not replay historical GPU batches. Retained-row tracking fixes the previous terminal identities, rewards and masks; both old and current denominators are reported so replay growth is not mistaken for better fitting. No condition is selected for further optimization. No weight/LR/feature change is authorized by this diagnostic.')
    (root/'REVIEW.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
