"""Thin adapter to the pinned polishing-CHEQ authors' SAC/ensemble code.

No locally substituted SAC update. Platform changes: canonical proprioception,
current project's controller action spaces, finite-horizon terminal masks,
static SI observation scaling, and complete episode-boundary restart state.
CHEQ keeps the ensemble, raw-action replay and adaptive context/mixing law.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import sys
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import torch


OBSERVATION_SCALE = np.r_[np.full(7, np.pi), np.full(7, 2.),
    [.35]*3+[1.2]*3, [.20]*3+[1.]*3, [.35]*3+[1.2]*3,
    [87.]*4+[12.]*3, [50.]*3+[5.]*3, [1.]*3].astype(np.float32)


class Spaces(gym.Env):
    def __init__(self, dimension, direct, context):
        self.horizon = 1375
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, (48+int(context),), dtype=np.float32)
        low = -np.ones(dimension, dtype=np.float32)
        if direct:
            low[0] = 0.
        self.action_space = gym.spaces.Box(low, np.ones(dimension, dtype=np.float32))


class PublishedLearner:
    def __init__(self, runtime, *, dimension, direct, seed, device, algorithm='sac'):
        if algorithm not in ('sac', 'cheq'):
            raise ValueError(algorithm)
        self.runtime = Path(runtime)
        for name, digest in json.loads((self.runtime/'CHEQ_HASHES.json').read_text()).items():
            if hashlib.sha256((self.runtime/'published_cheq'/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Published learner source drift: '+name)
        self.algorithm = algorithm
        self.device = torch.device(device)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        self.rng = np.random.default_rng(seed+71)
        self.spaces = Spaces(dimension, direct, algorithm == 'cheq')
        sys.path.insert(0, str(self.runtime/'published_cheq'))
        common = dict(env=self.spaces, device=self.device, gamma=.9995, polyak_factor=.005,
                      policy_lr=3e-4, q_lr=3e-4, policy_frequency=2, target_network_frequency=1,
                      actor_hidden_dims=[256, 256], critic_hidden_dims=[256, 256],
                      autotune=True, action_noise='white')
        if algorithm == 'sac':
            from agents.rl.sac import SAC
            self.learner = SAC(**common)
            self.hybrid = None
        else:
            from agents.rl.sac_ensemble import SACEnsemble
            from agents.hybrid.hybrid_agent_cheq import CHEQAgent
            self.learner = SACEnsemble(**common, ensemble_size=5)
            device = self.device

            class Nominal:
                def get_action(self, obs):
                    # Zero residual = common nominal WBC / nominal parameters.
                    return torch.zeros(dimension, device=device)

            self.hybrid = CHEQAgent(self.learner, Nominal(), uncertainty_min=.02,
                uncertainty_max=.2, uncertainty_deque=1, weight_min=.2,
                weight_warmup_max=.3, weight_max=1., warmup_steps=5000)
        self.mixers = {0: self.hybrid}
        self.reset_episode()

    def reset_episode(self, stream=0):
        if stream not in self.mixers:
            if self.algorithm == 'cheq':
                from agents.hybrid.hybrid_agent_cheq import CHEQAgent
                template = self.mixers[0]
                self.mixers[stream] = CHEQAgent(self.learner, template.nominal_agent,
                    uncertainty_min=.02, uncertainty_max=.2, uncertainty_deque=1,
                    weight_min=.2, weight_warmup_max=.3, weight_max=1., warmup_steps=5000)
            else:
                self.mixers[stream] = None
        self.hybrid = self.mixers[stream]
        self.learner.agent.reset_action_noise()
        if self.hybrid:
            self.hybrid.reset_mixing_parameter()

    def observation(self, raw, stream=0):
        self.hybrid = self.mixers[stream]
        value = np.asarray(raw, np.float32)
        if value.shape != (48,) or not np.isfinite(value).all():
            raise ValueError('Finite canonical48 required')
        value = value / OBSERVATION_SCALE
        if self.hybrid:
            value = np.r_[value, self.hybrid.get_mixing_parameter()].astype(np.float32)
        return value

    def act(self, raw, *, step, deterministic=False, warmup=5000, stream=0):
        obs = self.observation(raw, stream=stream)
        tensor = torch.as_tensor(obs, device=self.device).unsqueeze(0)
        low, high = self.spaces.action_space.low, self.spaces.action_space.high
        with torch.no_grad():
            if step < warmup and not deterministic:
                # Bounded unbiased exploration in actual platform action units;
                # official white-noise warmup is unbounded before env clipping.
                action = torch.as_tensor(self.rng.uniform(low, high).astype(np.float32),
                                         device=self.device).unsqueeze(0)
                if self.hybrid:
                    self.hybrid.current_obs, self.hybrid.current_rl_action = tensor, action
                    mixed = self.hybrid.weight*action
                else:
                    mixed = action
            elif self.hybrid:
                mixed, action = self.hybrid.get_action(tensor, deterministic=deterministic,
                                                        learning_started=True)
            else:
                action = self.learner.get_action(tensor, deterministic=deterministic)
                mixed = action
            context = float(self.hybrid.weight) if self.hybrid else None
            if self.hybrid:
                # Compute lambda_(t+1) now, so replay's next observation and the
                # next executed decision both contain that same context.
                self.hybrid.update_mixing_parameter(step=step-warmup)
                # The published linear branch returns a NumPy singleton array
                # after warmup. Convert the scalar bridge explicitly before
                # its next multiplication with a CUDA action tensor.
                self.hybrid.weight = float(np.asarray(self.hybrid.weight).item())
        raw_action = action.cpu().numpy().reshape(-1)
        execution = mixed.cpu().numpy().reshape(-1)
        if not np.isfinite(execution).all() or np.any(execution < low-1e-6) or np.any(execution > high+1e-6):
            raise FloatingPointError('Published actor produced invalid action')
        return obs, raw_action, execution, context

    def update(self, arrays):
        # One upstream update per call; the trainer applies registered UTD.
        values = {k: torch.as_tensor(v, dtype=torch.float32, device=self.device)
                  for k, v in arrays.items()}
        if self.hybrid:
            from utils.data_utils import BernoulliMaskReplayBufferSamples
            batch = BernoulliMaskReplayBufferSamples(**{k: v.unsqueeze(0) for k, v in values.items()})
        else:
            batch = SimpleNamespace(**{k: v for k, v in values.items() if k != 'masks'})
        metrics = self.learner.train(batch)
        metrics = {k: float(v.detach().cpu()) if torch.is_tensor(v) else float(v)
                   for k, v in metrics.items()}
        for name, parameter in self.learner.agent.named_parameters():
            if not torch.isfinite(parameter).all() or (parameter.grad is not None and not torch.isfinite(parameter.grad).all()):
                raise FloatingPointError('Nonfinite published parameter/gradient: '+name)
        if not all(np.isfinite(v) for v in metrics.values()):
            raise FloatingPointError('Nonfinite optimization diagnostics')
        return metrics

    def state_dict(self):
        learner = self.learner
        return copy.deepcopy(dict(algorithm=self.algorithm, agent=learner.agent.state_dict(),
            actor_optimizer=learner.actor_optimizer.state_dict(),
            q_optimizer=learner.q_optimizer.state_dict(),
            alpha_optimizer=learner.a_optimizer.state_dict(), log_alpha=learner.log_alpha.detach(),
            alpha=learner.alpha, num_gradient_steps=learner.num_gradient_steps,
            parameters_updated=learner.parameters_updated, step_metrics=learner.step_metrics,
            numpy_rng=np.random.get_state(), local_rng=self.rng.bit_generator.state,
            python_rng=random.getstate(), torch_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
            observation_scale=OBSERVATION_SCALE, boundary='completed_episode_only'))

    def load_state_dict(self, state):
        if state['algorithm'] != self.algorithm or not np.array_equal(state['observation_scale'], OBSERVATION_SCALE):
            raise ValueError('Cannot resume changed learner or observation transform')
        learner = self.learner
        learner.agent.load_state_dict(state['agent'])
        learner.actor_optimizer.load_state_dict(state['actor_optimizer'])
        learner.q_optimizer.load_state_dict(state['q_optimizer'])
        learner.a_optimizer.load_state_dict(state['alpha_optimizer'])
        with torch.no_grad():
            learner.log_alpha.copy_(state['log_alpha'])
        for key in ('alpha', 'num_gradient_steps', 'parameters_updated', 'step_metrics'):
            setattr(learner, key, copy.deepcopy(state[key]))
        self.reset_episode()
        np.random.set_state(state['numpy_rng'])
        self.rng.bit_generator.state = state['local_rng']
        random.setstate(state['python_rng'])
        torch.set_rng_state(state['torch_rng'].cpu())
        if state['cuda_rng']:
            torch.cuda.set_rng_state_all([x.cpu() for x in state['cuda_rng']])
