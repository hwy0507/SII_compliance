"""Compare frozen critics on identical replay rows and identical parent actions.

Separate instantaneous reward, entropy and critic-reduction contributions.
These model predictions are not measured returns or a causal bias estimate.
No learner update, replay mutation, physics, or live configuration change.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch

from diagnose_published_soft_targets_20261025 import pair_minimum_expectation, target_terms, summary


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def array_sha(value):
    return hashlib.sha256(np.asarray(value).tobytes()).hexdigest()


def q_summary(q):
    pair = pair_minimum_expectation(q)
    minimum = q.min(axis=0)
    return dict(ensemble_mean=summary(q.mean(axis=0)),
        ensemble_std=summary(q.std(axis=0, ddof=1)),
        expected_pair_minimum=summary(pair), all5_minimum=summary(minimum),
        pair_minus_all5=summary(pair-minimum))


def main(registration):
    p = json.loads(registration.read_text())
    for path, expected in p['source_and_input_hashes'].items():
        if sha(path) != expected:
            raise ValueError('Registered diagnostic input drift: '+path)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    torch.set_num_threads(1)
    root, out = Path(p['runtime']), Path(p['output'])
    out.mkdir(exist_ok=False)
    sys.path.insert(0, str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    result = dict(methods={}, optimizer_updates=0, new_physics=0,
                  live_training_changed=False, convergence_claim=False)
    for method, item in p['methods'].items():
        checkpoints = {}
        for label, selected in item['checkpoints'].items():
            if sha(selected['path']) != selected['sha256']:
                raise ValueError('Checkpoint drift')
            ck = torch.load(selected['path'], map_location='cpu', weights_only=False)
            if (ck['controller'] != method or ck['cycle'] != selected['cycle']
                    or ck['boundary'] != 'complete_condition_cycle'):
                raise ValueError('Expected registered complete-cycle checkpoint')
            checkpoints[label] = ck
        parent = checkpoints['before']
        arrays = parent['replay']['arrays']
        rng = np.random.default_rng(p['seed'])
        ordinary = np.flatnonzero(arrays['dones'].reshape(-1) == 0)
        terminal = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
        selected = rng.choice(ordinary, min(p['sample_size'], len(ordinary)), replace=False)
        if not len(terminal):
            raise ValueError('Missing terminal coverage')
        indices = np.r_[selected, terminal]
        # The new checkpoint retains these exact old replay entries, including
        # Bernoulli masks and context. No distribution change in this comparison.
        later = checkpoints['after']['replay']['arrays']
        if set(arrays) != set(later):
            raise ValueError('Replay field set changed')
        for key in arrays:
            if arrays[key][indices].tobytes() != later[key][indices].tobytes():
                raise AssertionError('Common replay entries changed: '+key)
        inputs = {key: array_sha(value[indices]) for key, value in arrays.items()}
        device = item['device']
        obs, nxt, actions = [torch.as_tensor(arrays[key][selected], device=device)
                            for key in ('observations','next_observations','actions')]
        term_obs, term_actions = [torch.as_tensor(arrays[key][terminal], device=device)
                                 for key in ('observations','actions')]
        rows = {}
        anchor = None
        for label in ('before','after'):
            ck = checkpoints[label]
            state = ck['learner']
            learner = PublishedLearner(root, dimension=arrays['actions'].shape[1],
                direct=method=='direct', seed=p['seed'], device=device, algorithm='cheq',
                critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
            agent = learner.learner.agent
            agent.load_state_dict(state['agent'])
            alpha, gamma = float(state['alpha']), learner.learner.gamma
            count = state.get('bellman_target_count', 2)
            if count != (2 if label=='before' else 5):
                raise ValueError('Expected registered pair9 and all5 cycle10')

            def q_values(observation, action, target=False):
                values = [agent.get_q_value(observation, action, i, target=target)
                          for i in range(agent.ensemble_size)]
                if len(values) != 5 or any(v.shape != (len(observation), 1) for v in values):
                    raise ValueError('Expected five column critic outputs')
                return torch.stack(values).squeeze(-1).cpu().numpy()

            with torch.no_grad():
                replay_q = q_values(obs, actions)
                # Same random seed for both policies. Own policy actions can
                # differ; the parent anchor below is literally the same tensor.
                torch.manual_seed(p['seed']+1)
                next_action, log_pi = agent.get_action_and_log_prob(nxt)
                if anchor is None:
                    anchor = next_action.detach().clone()
                fixed_q = q_values(nxt, anchor, target=True)
                own_q = q_values(nxt, next_action, target=True)
                reward = arrays['rewards'][selected].reshape(-1)
                done = arrays['dones'][selected].reshape(-1)
                log_pi = log_pi.cpu().numpy().reshape(-1)
                terms = {}
                for rule, future in [('pair', pair_minimum_expectation(own_q)),
                                     ('all5', own_q.min(axis=0))]:
                    values = target_terms(reward, done, future, log_pi, alpha, gamma)
                    terms[rule] = dict(components={key:summary(value) for key,value in values.items()},
                        target_minus_replay_mean=summary(values['target']-replay_q.mean(axis=0)),
                        critic_target_mae=summary(abs(replay_q-values['target'])))
                terminal_q = q_values(term_obs, term_actions)
                terminal_reward = arrays['rewards'][terminal].reshape(-1)
                masked = target_terms(terminal_reward, np.ones(len(terminal)),
                    np.zeros(len(terminal)), np.zeros(len(terminal)), alpha, gamma)
                if not np.array_equal(masked['target'], terminal_reward):
                    raise AssertionError('Terminal bootstrap changed')
            if (learner.learner.num_gradient_steps or any(v.grad is not None for v in agent.parameters())
                    or any(not torch.equal(v.cpu(), state['agent'][key].cpu())
                           for key,v in agent.state_dict().items())):
                raise AssertionError('Read-only diagnosis changed learner')
            rows[label] = dict(cycle=ck['cycle'], steps=ck['steps'], alpha=alpha, gamma=gamma,
                registered_bellman_target_count=count, replay_q=summary(replay_q),
                fixed_parent_action_target_critics=q_summary(fixed_q),
                own_policy_action_target_critics=q_summary(own_q),
                next_policy_entropy=summary(-log_pi), target_rules=terms,
                terminal_q=summary(terminal_q), terminal_mae=summary(abs(terminal_q-terminal_reward)),
                terminal_bootstrap_zero=True, network_unchanged=True,
                parent_action_sha256=array_sha(anchor.cpu().numpy()),
                own_policy_action_sha256=array_sha(next_action.cpu().numpy()))
            del learner, agent
        if rows['before']['parent_action_sha256'] != rows['after']['parent_action_sha256']:
            raise AssertionError('Common parent action differs')
        for key in arrays:
            if array_sha(arrays[key][indices]) != inputs[key]:
                raise AssertionError('Parent replay mutated')
        for selected_ck in item['checkpoints'].values():
            if sha(selected_ck['path']) != selected_ck['sha256']:
                raise AssertionError('Immutable checkpoint file changed')
        result['methods'][method] = dict(nonterminal_rows=len(selected), terminal_rows=len(terminal),
            sampled_indices_sha256=array_sha(indices), common_replay_sha256=inputs,
            common_replay_present_in_both=True, checkpoints=item['checkpoints'], rows=rows)
        (out/(method+'.json')).write_text(json.dumps(result['methods'][method],indent=2,allow_nan=False)+'\n')
        print(method+' matched diagnostics complete', flush=True)
        del checkpoints, parent, arrays, later, state, ck, anchor
        torch.cuda.empty_cache()
    result.update(finished_unix=time.time(), registration_sha256=sha(registration), limitations=[
        'Identical retained cycle9 replay rows; no new rollout or optimizer update.',
        'Fixed parent actions isolate critic prediction changes; own-policy actions use matched random noise but differ by policy.',
        'Pair minimum is the exact expectation over all10 pairs, not one sampled training pair.',
        'Target shifts and critic spread are model predictions, not measured value bias or causal attribution.',
        'Entropy-adjusted values can be negative; negative Q alone is not a defect or convergence test.',
        'No final policy ranking, SPT reference, training intervention or convergence claim.'])
    (out/'SUMMARY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True)
    main(parser.parse_args().registration)
