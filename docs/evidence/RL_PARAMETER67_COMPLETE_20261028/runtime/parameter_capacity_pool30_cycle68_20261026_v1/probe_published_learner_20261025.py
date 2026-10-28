"""Exercise official learner updates on real recorded MuJoCo transitions.

A short probe is not training convergence or a task performance result. This
checks finite actual CUDA updates and complete stochastic optimizer restart.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

from published_compliance_learner_20261025 import PublishedLearner
from spt_rl_reward_20261025 import SPTReward


def main(args):
    torch.set_num_threads(1)
    rows = [json.loads(line) for line in (args.episode/'actor_intervals.jsonl').read_text().splitlines()]
    terminal = json.loads((args.episode/'TERMINAL.json').read_text())
    adapter = json.loads((args.episode/'ADAPTER.json').read_text())
    controller = json.loads((args.episode/'rollout.json').read_text())['baseline_policy']['controller']
    dimension = len(rows[0]['action'])
    learner = PublishedLearner(args.runtime, dimension=dimension, direct=controller == 'direct',
                               seed=20261025, device=args.device, algorithm=args.algorithm)
    reward = SPTReward()
    samples = []
    for i, row in enumerate(rows):
        done = i == len(rows)-1
        nxt = terminal if done else rows[i+1]
        labels = terminal['result'] if done else dict(task_success=False, strict_success=False)
        value, terms = reward(current_potential=row['payload_potential'],
            next_potential=nxt['payload_potential'], interval=nxt['interval'], terminated=done,
            task_success=labels['task_success'], strict_success=labels['strict_success'])
        samples.append(dict(observations=learner.observation(row['observation']),
            actions=np.asarray(row['action']), rewards=[value], dones=[float(done)],
            next_observations=learner.observation(row['observation'] if done else nxt['observation']),
            masks=np.ones(5)))
    # All masks select real transitions in this computational probe. A CHEQ
    # probe checks numerical updates only, not equivalence of collected mixed
    # behavior (the input episodes used zero commands without a CHEQ actor).
    rng = np.random.default_rng(42)
    indices = rng.integers(len(samples), size=256)
    batch = {k: np.stack([samples[i][k] for i in indices]) for k in samples[0]}
    initial = {k: v.clone() for k, v in learner.learner.agent.state_dict().items()}
    diagnostics = [learner.update(batch) for _ in range(4)]
    boundary = learner.state_dict()
    metrics_one = learner.update(batch)
    target = learner.state_dict()
    learner.load_state_dict(boundary)
    metrics_two = learner.update(batch)
    restored = learner.state_dict()
    differences = {k: float((target['agent'][k]-restored['agent'][k]).abs().max())
                   for k in target['agent']}
    alpha_error = float((target['log_alpha']-restored['log_alpha']).abs().max())
    if max(differences.values()) != 0 or alpha_error != 0 or metrics_one != metrics_two:
        raise AssertionError('Incomplete deterministic episode-boundary learner resume')
    parameter_change = max(float((v-initial[k]).abs().max()) for k, v in target['agent'].items())
    if parameter_change <= 0:
        raise AssertionError('No actual parameter update')
    report = dict(scope='real-physics-data optimizer smoke; not policy training/convergence',
        algorithm=args.algorithm, controller=controller, device=str(learner.device),
        gpu_name=torch.cuda.get_device_name(learner.device) if learner.device.type == 'cuda' else None,
        physical_transitions=len(samples), unique_sampled_transitions=len(set(indices.tolist())),
        model_sha256=terminal['model_sha256'], probe_seconds=adapter['arguments']['physics_probe_s'],
        physics_terminal=terminal['result'], reward_sum=sum(s['rewards'][0] for s in samples),
        updates=5, max_parameter_change=parameter_change, exact_resume_parameter_max_abs=max(differences.values()),
        exact_resume_log_alpha_abs=alpha_error, diagnostics=diagnostics+[metrics_one])
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k != 'diagnostics'}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--episode', type=Path, required=True)
    p.add_argument('--device', default='cuda:0')
    p.add_argument('--algorithm', choices=('sac', 'cheq'), default='sac')
    p.add_argument('--output', type=Path, required=True)
    main(p.parse_args())
