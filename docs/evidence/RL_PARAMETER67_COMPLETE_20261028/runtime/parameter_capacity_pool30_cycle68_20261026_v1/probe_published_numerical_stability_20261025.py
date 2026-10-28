"""Registered finite offline stability study on actual controller replay.

Fresh authors' SAC learners, paired initialization/replay RNG, no simulated
transitions and no baseline ranking. Tests numerical amendments, batch size and
the authors' existing optional critic LayerNorm. Formal learners are not mutated.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    torch.set_num_threads(1)
    protocol = json.loads(args.registration.read_text())
    variant = next(v for v in protocol['variants'] if v['name'] == args.variant)
    root = Path(protocol['runtime'])
    for name, digest in json.loads((root/'CHEQ_HASHES.json').read_text()).items():
        if sha(root/'published_cheq'/name) != digest:
            raise ValueError('Pinned published source mismatch')
    if sha(protocol['replay_checkpoint']) != protocol['replay_checkpoint_sha256']:
        raise ValueError('Frozen real replay checkpoint changed')
    sys.path[:0] = [str(root/'source/tools'), str(root/'published_cheq')]
    from published_compliance_learner_20261025 import Spaces
    # Optional Gym/OpenCV imports can prepend their own utils directory even
    # when an unavailable rendering dependency is caught. Match the production
    # adapter's resolution order after importing Spaces.
    sys.path.insert(0, str(root/'published_cheq'))
    from agents.rl.sac import SAC
    from agents.rl.sac_ensemble import SACEnsemble
    patch = None
    if variant['numerical_amendments']:
        from published_compliance_numerics_20261025 import install
        patch = install()
    random.seed(protocol['seed']); np.random.seed(protocol['seed']); torch.manual_seed(protocol['seed'])
    rng = np.random.default_rng(protocol['seed']+1)
    checkpoint = torch.load(protocol['replay_checkpoint'], map_location='cpu', weights_only=False)
    algorithm = protocol.get('algorithm', 'sac')
    controller = protocol.get('controller', 'direct')
    if checkpoint['learner']['algorithm'] != algorithm or checkpoint['controller'] != controller:
        raise ValueError('Replay algorithm/action/context contract mismatch')
    priors = json.loads((root/'parameter/PRIORS.json').read_text())
    dimension = 7 if controller == 'direct' else priors['methods'][controller]['action_dimension']
    arrays = checkpoint['replay']['arrays']
    if arrays['actions'].shape[1:] != (dimension,) or arrays['observations'].shape[1:] != (48+int(algorithm == 'cheq'),):
        raise ValueError('Replay dimensions disagree with frozen interface')
    learner_type = SACEnsemble if algorithm == 'cheq' else SAC
    extra = dict(ensemble_size=5) if algorithm == 'cheq' else {}
    learner = learner_type(env=Spaces(dimension, controller == 'direct', algorithm == 'cheq'), device=torch.device(args.device),
        gamma=.9995, polyak_factor=.005, policy_lr=3e-4, q_lr=3e-4,
        policy_frequency=2, target_network_frequency=1, actor_hidden_dims=[256, 256],
        critic_hidden_dims=[256, 256], autotune=True, action_noise='white',
        layer_norm_q=variant['critic_layer_norm'], **extra)
    from types import SimpleNamespace
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = dict(started_unix=time.time(), variant=variant, registration_sha256=sha(args.registration),
        source_sha256=sha(__file__), numerical_patch=patch, real_replay_rows=len(arrays['rewards']),
        task='offline_numerical_diagnostic_not_formal_policy_training', convergence_claim=False,
        seed=protocol['seed'], fresh_optimizer=True, algorithm=algorithm,
        controller=controller, action_dimension=dimension)
    (args.output/'REGISTRATION.json').write_text(json.dumps(receipt, indent=2)+'\n')
    terminals = np.flatnonzero(arrays['dones'].reshape(-1) == 1)
    if not len(terminals):
        raise ValueError('Terminal calibration requires real terminal samples')
    with (args.output/'updates.jsonl').open('x', buffering=1) as log:
        for update in range(protocol['updates_per_variant']):
            index = rng.integers(len(arrays['rewards']), size=variant['batch_size'])
            if algorithm == 'cheq':
                from utils.data_utils import BernoulliMaskReplayBufferSamples
                batch = BernoulliMaskReplayBufferSamples(**{k: torch.as_tensor(v[index],
                    device=args.device).unsqueeze(0) for k, v in arrays.items()})
            else:
                batch = SimpleNamespace(**{k: torch.as_tensor(v[index], device=args.device)
                    for k, v in arrays.items() if k != 'masks'})
            values = learner.train(batch)
            metrics = {k: float(v) for k, v in values.items()}
            if not all(math.isfinite(v) for v in metrics.values()):
                raise FloatingPointError('Nonfinite diagnostic optimizer metrics')
            log.write(json.dumps(dict(update=update+1, **metrics), allow_nan=False)+'\n')
            if (update+1) % 100 == 0:
                with torch.no_grad():
                    obs = torch.as_tensor(arrays['observations'][terminals], device=args.device)
                    action = torch.as_tensor(arrays['actions'][terminals], device=args.device)
                    q = (torch.stack([learner.agent.get_q_value(obs, action, i)
                        for i in range(learner.agent.ensemble_size)]) if algorithm == 'cheq'
                        else torch.stack([learner.agent.qf1(obs, action), learner.agent.qf2(obs, action)]))
                    rewards = torch.as_tensor(arrays['rewards'][terminals], device=args.device)
                    terminal_mae = float((q-rewards).abs().mean())
                status = dict(updates=update+1, terminal_q_mae=terminal_mae, alpha=learner.alpha,
                    latest_metrics=metrics, updated_unix=time.time())
                tmp = args.output/'PROGRESS.tmp';tmp.write_text(json.dumps(status, indent=2));tmp.replace(args.output/'PROGRESS.json')
    torch.save(dict(agent=learner.agent.state_dict(), alpha=learner.alpha, updates=learner.num_gradient_steps,
        registration=receipt, usable_as_formal_policy=False), args.output/'diagnostic_weights.pt')
    (args.output/'FINISHED.json').write_text(json.dumps(dict(status='completed_fixed_diagnostic_budget',
        **status, convergence_claim=False), indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--variant', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', default='cuda:0')
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output/'FAILURE.json').write_text(json.dumps(dict(error=repr(error),
            source_sha256=sha(__file__), convergence_claim=False), indent=2)+'\n')
        raise
