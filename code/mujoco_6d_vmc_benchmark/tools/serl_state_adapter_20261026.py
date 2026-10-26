"""Thin bridge to pinned official SERL state SAC, not a replacement update.

The factory mirrors utils/launcher.py::make_sac_agent without importing its
unneeded networking, image, TensorFlow dataset or experiment logging services.
Platform adaptations: static canonical48 scaling, seven-dimensional action
mapping, task discount .9995, zero demonstrations and finite-horizon terminals.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import torch

UPSTREAM_COMMIT = '1fa2af7496be042e43d36120a7c8d1b71f1bfb59'
OBSERVATION_SCALE = np.r_[np.full(7, np.pi), np.full(7, 2.),
    [.35]*3+[1.2]*3, [.20]*3+[1.]*3, [.35]*3+[1.2]*3,
    [87.]*4+[12.]*3, [50.]*3+[5.]*3, [1.]*3].astype(np.float32)


def execution_action(action):
    """Bijective map; no CHEQ blending or nominal-policy action is added here."""
    action = np.asarray(action, np.float32)
    if action.shape != (7,) or not np.isfinite(action).all() or np.any(abs(action) > 1.000001):
        raise ValueError('Expected finite bounded SERL action7')
    result = action.copy()
    result[0] = .5 * (result[0] + 1.)
    return result


class SerlStateLearner:
    critic_actor_ratio = 8
    actor_observation_dimension = 48
    replay_observation_dimension = 48
    critic_clock = False
    critic_layer_norm = True
    numerical_amendments = False
    numerical_patch_receipt = None
    bellman_target_count = 2

    def __init__(self, runtime, *, upstream, upstream_manifest, dimension, direct,
                 seed, device, algorithm='serl_state', critic_layer_norm=True,
                 numerical_amendments=False, critic_clock=False):
        if (algorithm != 'serl_state' or not direct or dimension != 7 or
                critic_clock or not critic_layer_norm or numerical_amendments):
            raise ValueError('Unsupported SERL adaptation contract')
        manifest = json.loads(Path(upstream_manifest).read_text())
        if manifest['commit'] != UPSTREAM_COMMIT:
            raise ValueError('Unexpected SERL source version')
        upstream = Path(upstream).resolve()
        for name, digest in manifest['files'].items():
            if hashlib.sha256((upstream / name).read_bytes()).hexdigest() != digest:
                raise ValueError('SERL source drift: ' + name)
        self.source_receipt = dict(commit=UPSTREAM_COMMIT, root=str(upstream),
            manifest_sha256=hashlib.sha256(Path(upstream_manifest).read_bytes()).hexdigest())
        sys.path.insert(0, str(upstream / 'serl_launcher'))
        import jax
        from flax import serialization
        from serl_launcher.agents.continuous.sac import SACAgent
        self.jax, self.serialization = jax, serialization
        # A separate one-GPU process uses CUDA_VISIBLE_DEVICES. Refuse CPU fallback.
        if len(jax.devices()) != 1 or jax.devices()[0].platform != 'gpu':
            raise RuntimeError('SERL process requires exactly one visible GPU')
        self.device = torch.device(device)  # metadata only; all updates use JAX
        self.algorithm = algorithm
        self.rng = np.random.default_rng(seed + 71)
        self.action_rng = jax.random.PRNGKey(seed + 101)
        self.agent = SACAgent.create_states(
            jax.random.PRNGKey(seed), np.zeros(48, np.float32), np.zeros(7, np.float32),
            policy_kwargs=dict(tanh_squash_distribution=True,
                std_parameterization='exp', std_min=1e-5, std_max=5),
            critic_network_kwargs=dict(activations=jax.nn.tanh, use_layer_norm=True,
                                       hidden_dims=[256, 256]),
            policy_network_kwargs=dict(activations=jax.nn.tanh, use_layer_norm=True,
                                       hidden_dims=[256, 256]),
            temperature_init=1e-2, discount=.9995, backup_entropy=False,
            critic_ensemble_size=10, critic_subsample_size=2)
        self.outer_updates = 0
        # Compatibility facade for existing trainer bookkeeping, not an optimizer.
        self.learner = SimpleNamespace(num_gradient_steps=0,
            actor_optimizer=SimpleNamespace(param_groups=[dict(lr=3e-4)]))
        self._finite = jax.jit(lambda state: jax.numpy.all(jax.numpy.stack([
            jax.numpy.all(jax.numpy.isfinite(x)) for x in jax.tree_util.tree_leaves(state)
            if hasattr(x, 'dtype') and jax.numpy.issubdtype(x.dtype, jax.numpy.inexact)])))

    def reset_episode(self, stream=0):
        pass  # State-only feedforward policy; no mixing context or recurrent state.

    def observation(self, raw, stream=0):
        value = np.asarray(raw, np.float32)
        if value.shape != (48,) or not np.isfinite(value).all():
            raise ValueError('Finite canonical48 required')
        return value / OBSERVATION_SCALE

    def terminal_observation(self, previous, stream=0):
        # Frozen sampler marks terminal canonical48 invalid. Bootstrap is zero.
        return np.asarray(previous, np.float32).copy()

    def act(self, raw, *, step, deterministic=False, warmup=5000, stream=0):
        observation = self.observation(raw)
        if step < warmup and not deterministic:
            action = self.rng.uniform(-1, 1, 7).astype(np.float32)
        elif deterministic:
            action = np.asarray(self.agent.sample_actions(observation, argmax=True))
        else:
            self.action_rng, key = self.jax.random.split(self.action_rng)
            action = np.asarray(self.agent.sample_actions(observation, seed=key))
        return observation, action, execution_action(action), None

    def batch(self, arrays):
        return self.jax.device_put(dict(
            observations=np.asarray(arrays['observations'], np.float32),
            next_observations=np.asarray(arrays['next_observations'], np.float32),
            actions=np.asarray(arrays['actions'], np.float32),
            rewards=np.asarray(arrays['rewards'], np.float32).reshape(-1),
            masks=1.-np.asarray(arrays['dones'], np.float32).reshape(-1)))

    def update(self, arrays):
        batch = self.batch(arrays)
        self.agent, info = self.agent.update_high_utd(batch, utd_ratio=self.critic_actor_ratio)
        if not bool(self._finite(self.agent.state)):
            raise FloatingPointError('Nonfinite official SERL learner/optimizer state')
        self.outer_updates += 1
        self.learner.num_gradient_steps += self.critic_actor_ratio
        metrics = {}
        def collect(prefix, value):
            if isinstance(value, dict):
                for name, child in value.items():
                    collect(prefix + '/' + name, child)
            else:
                metrics[prefix] = float(value)
        collect('serl', info)
        if not all(np.isfinite(v) for v in metrics.values()):
            raise FloatingPointError('Nonfinite official SERL diagnostics')
        metrics['serl/outer_updates'] = self.outer_updates
        return metrics

    def state_dict(self):
        return dict(algorithm=self.algorithm, source_receipt=self.source_receipt,
            agent=self.jax.device_get(self.serialization.to_state_dict(self.agent.state)),
            config=self.agent.config, action_rng=np.asarray(self.action_rng),
            local_rng=copy.deepcopy(self.rng.bit_generator.state),
            outer_updates=self.outer_updates, num_gradient_steps=self.learner.num_gradient_steps,
            observation_scale=OBSERVATION_SCALE.copy(), critic_actor_ratio=self.critic_actor_ratio)

    def load_state_dict(self, state):
        if (state['algorithm'] != self.algorithm or state['config'] != self.agent.config or
                state['source_receipt'] != self.source_receipt or
                state['critic_actor_ratio'] != self.critic_actor_ratio or
                not np.array_equal(state['observation_scale'], OBSERVATION_SCALE)):
            raise ValueError('Cannot resume changed SERL contract')
        restored = self.serialization.from_state_dict(self.agent.state, state['agent'])
        self.agent = self.agent.replace(state=self.jax.device_put(restored))
        self.action_rng = self.jax.device_put(state['action_rng'])
        self.rng.bit_generator.state = copy.deepcopy(state['local_rng'])
        self.outer_updates = state['outer_updates']
        self.learner.num_gradient_steps = state['num_gradient_steps']
