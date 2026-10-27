"""Track all1045 fixed34 Impedance terminal rows and the new35 terminals on complete35."""
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
    assert reg['cycle'] == 35 and reg['anchor_cycle'] == 34
    assert reg['focus_replay_index'] == 1432256 and reg['expected_old_terminal_count'] == 1045
    assert sha(__file__) == reg['source_sha256']
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    origin = json.loads(Path(reg['inputs']['anchor_registration']['path']).read_text())
    runtime = Path(origin['runtime'])
    assert sha(runtime/'RUNTIME.json') == origin['runtime_sha256']
    for name, expected in json.loads((runtime/'SOURCE_HASHES.json').read_text()).items():
        assert sha(runtime/'source'/name) == expected
    sys.path[:0] = [str(runtime/'source/tools'), origin['helper_runtime']]
    from published_compliance_learner_20261025 import PublishedLearner
    from validate_published_finite_check_20261025 import digest
    assert sha(Path(origin['helper_runtime'])/'validate_published_finite_check_20261025.py') == origin['digest_helper_sha256']
    health = json.loads(Path(reg['inputs']['health35']['path']).read_text())['methods']['impedance']
    review = json.loads(Path(reg['inputs']['review35']['path']).read_text())
    assert review['passed'] and health['checkpoint_sha256'] == reg['inputs']['checkpoint35']['sha256']
    ck = torch.load(reg['inputs']['checkpoint35']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 35 and ck['boundary'] == 'complete_condition_cycle' and ck['controller'] == 'impedance'
    state, arrays = ck['learner'], ck['replay']['arrays']
    assert state['terminal_loss_weight'] == 128 and state['target_pair_reduction']['target'] == 'minimum'
    terminal = np.flatnonzero(arrays['dones'][:, 0] == 1)
    assert len(terminal) == 1075 == health['terminal_count']
    with np.load(reg['inputs']['anchor_values']['path'], allow_pickle=False) as old:
        indices, old_q, rewards, masks, features = [old[k].copy() for k in ['replay_indices', 'q', 'rewards', 'masks', 'features']]
        old_denominators = old['denominators'].copy()
    assert len(indices) == 1045 and np.array_equal(terminal[:1045], indices)
    np.testing.assert_array_equal(arrays['observations'][indices], features[:, :50])
    np.testing.assert_array_equal(arrays['actions'][indices], features[:, 50:])
    np.testing.assert_array_equal(arrays['rewards'][indices, 0], rewards)
    np.testing.assert_array_equal(arrays['masks'][indices].T, masks)
    learner = PublishedLearner(runtime, dimension=arrays['actions'].shape[1], direct=False,
        seed=42, device='cpu', algorithm=state['algorithm'],
        **{key: state[key] for key in ('critic_layer_norm', 'numerical_amendments', 'critic_clock')})
    agent = learner.learner.agent
    agent.load_state_dict(state['agent'])
    before = digest(agent.state_dict())
    assert before == digest(state['agent'])
    rng = torch.get_rng_state().clone()
    with torch.no_grad():
        obs, action = torch.as_tensor(arrays['observations'][terminal]), torch.as_tensor(arrays['actions'][terminal])
        q = torch.stack([agent.get_q_value(obs, action, i, target=False).reshape(-1) for i in range(5)]).numpy()
    target = arrays['rewards'][terminal, 0]
    native_error = np.abs(q-target[None]).astype(np.float64)
    mask = arrays['masks'][terminal].T.astype(np.float64)
    assert np.isclose(native_error.mean(), health['terminal_q_absolute_error']['mean'], rtol=0, atol=1e-9)
    assert np.isclose(native_error[mask.astype(bool)].mean(), health['terminal_q_in_bag_absolute_error']['mean'], rtol=0, atol=1e-9)
    denominator = arrays['masks'].sum(axis=0, dtype=np.float64)+127*mask.sum(axis=1)
    error = q.astype(np.float64)-target.astype(np.float64)[None]
    contribution = (128*mask*error**2/denominator[:, None]).sum(axis=0)
    old_squared = masks*(old_q-rewards[None])**2
    retained_squared = masks*error[:, :1045]**2
    focus = int(np.flatnonzero(indices == reg['focus_replay_index'])[0])
    assert digest(agent.state_dict()) == before and torch.equal(rng, torch.get_rng_state())
    values = root/'terminal35_values.npz'
    np.savez_compressed(values, indices=terminal, q=q, rewards=target, masks=mask,
        denominators=denominator, contributions=contribution)
    result = dict(passed=True, time=time.time(), cycle=35, fixed_anchor_rows=1045, new_terminal_rows=30,
        original_anchor_observations_actions_rewards_masks_exact=True,
        fixed1045_masked_sse_before=float(old_squared.sum()), fixed1045_masked_sse_after=float(retained_squared.sum()),
        fixed1045_masked_sse_ratio=float(retained_squared.sum()/old_squared.sum()),
        terminal_population_contribution=float(contribution.sum()),
        retained1045_population_contribution=float(contribution[:1045].sum()),
        new30_population_contribution=float(contribution[1045:].sum()),
        fixed1045_contribution_using_old34_denominator=float((128*retained_squared/old_denominators[:, None]).sum()),
        focus=dict(condition='active_short_train_0600', replay_index=reg['focus_replay_index'],
            reward=float(rewards[focus]), masks=masks[:, focus].tolist(),
            q_before=old_q[:, focus].tolist(), q_after=q[:, focus].astype(float).tolist(),
            masked_sse_before=float(old_squared[:, focus].sum()), masked_sse_after=float(retained_squared[:, focus].sum()),
            population_contribution_after=float(contribution[focus])),
        values_sha256=sha(values), agent_weights_and_forward_rng_unchanged=True,
        optimizer_updates=0, new_physics=0, replay_writes=0, convergence_claim=False,
        limitation='Same1045 retained terminal rows under frozen34 and35 critic weights; mask-weighted SSE separates error change from replay-denominator growth. Includes no ordinary TD terms or historical minibatch replay. Only CPU forward weights are restored, not optimizer state. No training or method change. Frozen rollout performance remains separate.')
    for ref in reg['inputs'].values():
        assert sha(ref['path']) == ref['sha256']
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
