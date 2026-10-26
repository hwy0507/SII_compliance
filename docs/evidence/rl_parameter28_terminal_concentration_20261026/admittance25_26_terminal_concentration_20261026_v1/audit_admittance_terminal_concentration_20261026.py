"""Frozen25/26 terminal error concentration and input proximity, without updates.

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
    assert reg['cycles'] == [25, 26] and reg['optimizer_updates'] == reg['new_physics'] == 0
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
        health = json.loads(Path(refs['health']['path']).read_text())['methods']['admittance']
        review = json.loads(Path(refs['review']['path']).read_text())
        assert review['passed'] and health['checkpoint_sha256'] == refs['checkpoint']['sha256']
        ck = torch.load(refs['checkpoint']['path'], map_location='cpu', weights_only=False)
        assert ck['cycle'] == cycle and ck['boundary'] == 'complete_condition_cycle'
        assert ck['controller'] == 'admittance' and ck['replay']['size'] == ck['steps']
        state, arrays = ck['learner'], ck['replay']['arrays']
        assert state['terminal_loss_weight'] == 128
        assert state['target_pair_reduction'] == dict(version=1, target='mean', actor='minimum', sampled_targets=2)
        assert arrays['observations'].shape[1] == 50
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
        assert len(terminal) == health['terminal_count']
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
        assert np.isclose(np.abs(error).mean(), health['terminal_q_absolute_error']['mean'], rtol=0, atol=1e-9)
        assert np.isclose(np.abs(error)[mask.astype(bool)].mean(), health['terminal_q_in_bag_absolute_error']['mean'], rtol=0, atol=1e-9)
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
        # L2 in stored normalized critic-observation/action coordinates is a
        # descriptive distance, not a learned metric or proof of aliasing.
        f = features.astype(np.float64)
        distance = np.sqrt(np.maximum(0., ((f[:, None]-f[None, :])**2).sum(axis=2)))
        opposite = (reward[:, None] > 0) != (reward[None, :] > 0)
        opposite_distance = np.where(opposite, distance, np.inf)
        nearest = opposite_distance.argmin(axis=1)
        exact_conflicts = [(int(terminal[i]), int(terminal[j])) for i in range(len(terminal))
                           for j in range(i) if opposite[i, j] and np.array_equal(features[i], features[j])]
        order = np.argsort(-contributions)
        total = float(contributions.sum())
        current_set = {v['replay_index'] for v in terms.values()}
        current = np.asarray([int(v) in current_set for v in terminal])
        ranked = []
        for i in order[:20]:
            j = nearest[i]
            ranked.append(dict(replay_index=int(terminal[i]), reward=float(reward[i]),
                q=q[:, i].tolist(), masks=mask[:, i].tolist(), contribution=float(contributions[i]),
                fraction=float(contributions[i]/total), current_cycle=bool(current[i]),
                nearest_opposite_replay_index=int(terminal[j]),
                nearest_opposite_input_l2=float(opposite_distance[i, j])))
        paired = []
        if cycle == 26:
            for case, old in maps[25].items():
                new = terms[case]
                i, j = positions[old['replay_index']], positions[new['replay_index']]
                if reward[i] > 0 and reward[j] < 0:
                    paired.append(dict(condition=case, old_replay_index=int(terminal[i]), new_replay_index=int(terminal[j]),
                        old_reward=float(reward[i]), new_reward=float(reward[j]),
                        current_q_on_old=q[:, i].tolist(), current_q_on_new=q[:, j].tolist(),
                        old_masks=mask[:, i].tolist(), new_masks=mask[:, j].tolist(),
                        old_contribution=float(contributions[i]), new_contribution=float(contributions[j]),
                        stored_observation_l2=float(np.linalg.norm(f[i, :50]-f[j, :50])),
                        stored_action_l2=float(np.linalg.norm(f[i, 50:]-f[j, 50:])),
                        exact_critic_input_match=bool(np.array_equal(features[i], features[j]))))
        assert digest(agent.state_dict()) == before and torch.equal(random_before, torch.get_rng_state())
        np.savez_compressed(root/f'cycle{cycle}_terminal_values.npz', replay_indices=terminal, q=q,
            rewards=reward, masks=mask, features=features, denominators=denominator, contributions=contributions)
        results.append(dict(cycle=cycle, checkpoint_sha256=refs['checkpoint']['sha256'], terminal_count=len(terminal),
            terminal_population_loss_contribution=total, per_critic_denominator=denominator.tolist(),
            top1_fraction=float(contributions[order[:1]].sum()/total),
            top5_fraction=float(contributions[order[:5]].sum()/total),
            top10_fraction=float(contributions[order[:10]].sum()/total),
            current30_fraction=float(contributions[current].sum()/total), top20=ranked,
            exact_opposite_reward_input_collisions=exact_conflicts, paired_strict_losses=paired,
            agent_weights_and_forward_rng_unchanged=True,
            values_sha256=sha(root/f'cycle{cycle}_terminal_values.npz')))
        del learner, agent, ck, arrays
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    report = dict(passed=True, time=time.time(), cycles=results, optimizer_updates=0, new_physics=0,
        replay_writes=0, original_checkpoints_unchanged=True, convergence_claim=False,
        formula='Sum across5 critics of terminal row128*mask*(Q-reward)^2 divided by that critic full-replay sum(mask*(1+127*done)).',
        limitation='Terminal-only contribution to a frozen full-replay weighted loss; excludes ordinary TD terms and differs from random minibatch denominator expectation and logged online loss. No target-pair/entropy sampling is needed for terminal labels. CPU inference matches prior health diagnostics, but does not replay historical GPU batches. Input L2 is descriptive; proximity is not proof of non-Markov aliasing. Only exact equal critic inputs with incompatible labels would prove that narrow collision. No weight/LR/feature change is authorized by this diagnostic.')
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
