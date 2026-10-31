"""Explicit causal-history architecture migration; never imports fitted weights.

Factory bindings are part of the registration, not inferred from a checkpoint.
Environment state is not saved. All episode histories reset on restore, as do
the original clock and CHEQ mixers. Retained replay histories remain intact.
"""
import copy
import hashlib
import types
from pathlib import Path

import numpy as np
import torch
from torch import nn

KEY = 'causal_external_penetration_history'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def marker(binding):
    required = {'method', 'checkpoint_sha256', 'learner_digest', 'replay_digest',
                'sidecar_sha256', 'rows', 'action_dimension'}
    if set(binding) != required or binding['method'] not in ('impedance', 'admittance', 'vmc'):
        raise ValueError('Explicit method and complete parent binding required')
    for key in required - {'method', 'rows', 'action_dimension'}:
        value = binding[key]
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Invalid SHA256 binding: '+key)
    if type(binding['rows']) is not int or not 0 < binding['rows'] <= 4_000_000:
        raise ValueError('Invalid parent replay size')
    if binding['action_dimension'] not in (5, 7):
        raise ValueError('Unsupported parameter action dimension')
    return dict(version=1, parent=copy.deepcopy(binding), observation_dimension=51,
                actor_dimension=49, clock_index=49, history_index=50,
                feature='p/(p+0.0002)', units='meters',
                source='cumulative_external_penetration_before_action',
                boundary='reset_all_streams_environment_not_restored',
                new_weight_and_adam_moments='zero', old_fields='exact')


def feature(peak):
    value = np.asarray(peak, dtype=np.float64)
    if not np.isfinite(value).all() or np.any(value < 0):
        raise ValueError('Finite nonnegative external penetration required')
    result = (value / (value + 0.0002)).astype(np.float32)
    if np.any(result >= 1):
        raise ValueError('History feature rounded out of its registered domain')
    return result


def insert_zero(value):
    return torch.cat((value[:, :50], value.new_zeros((value.shape[0], 1)), value[:, 50:]), dim=1)


def actor_without_clock_or_history(module, args):
    (value,) = args
    if value.shape[-1] != 51:
        raise ValueError('History learner actor entry requires 51 replay features')
    return (value[..., :49],)


def project_with_history(q, observation, alpha, gamma, log_volume, enabled=True):
    from published_finite_target_projection_20261026 import project
    if observation.shape[-1] != 51:
        raise ValueError('History projection requires 51 features')
    return project(q, observation[..., :50], alpha, gamma, log_volume, enabled)


def install_history_projection(wrapper):
    from published_finite_target_projection_20261026 import project
    current = wrapper.learner.train.__func__
    if current.__globals__.get('_project_q') is not project:
        raise ValueError('Expected registered finite projection before history adaptation')
    namespace = dict(current.__globals__, _project_q=project_with_history)
    adapted = types.FunctionType(current.__code__, namespace, current.__name__,
                                 current.__defaults__, current.__closure__)
    wrapper.learner.train = types.MethodType(adapted, wrapper.learner)


def expand_architecture(wrapper):
    from published_critic_clock_20261026 import actor_without_clock
    agent = wrapper.learner.agent
    hooks = agent.actor._forward_pre_hooks
    if len(hooks) != 1 or next(iter(hooks.values())) is not actor_without_clock:
        raise ValueError('Expected exactly the pinned clock isolation hook')
    if agent.actor.latent_pi[0].in_features != 49:
        raise ValueError('Canonical CHEQ actor changed')
    devices = [wrapper.device.index] if wrapper.device.type == 'cuda' else []
    with torch.random.fork_rng(devices=devices):
        for ensemble in (agent.ensemble, agent.ensemble_targets):
            for critic in ensemble:
                old = critic.q_net[0]
                if not isinstance(old, nn.Linear) or old.in_features != 50 + wrapper.spaces.action_space.shape[0]:
                    raise ValueError('Expected clock critic first layer')
                new = nn.Linear(old.in_features+1, old.out_features, bias=old.bias is not None,
                                device=old.weight.device, dtype=old.weight.dtype)
                with torch.no_grad():
                    new.weight.copy_(insert_zero(old.weight))
                    if old.bias is not None:
                        new.bias.copy_(old.bias)
                critic.q_net[0] = new
    if wrapper.learner.q_optimizer.state:
        raise ValueError('Architecture construction must precede optimizer restoration')
    wrapper.learner.q_optimizer = torch.optim.Adam(agent.ensemble.parameters(),
                                                   **wrapper.learner.q_optimizer.defaults)
    agent.ensemble_targets.requires_grad_(False)
    hooks.pop(next(iter(hooks)))
    agent.actor.register_forward_pre_hook(actor_without_clock_or_history)
    wrapper.replay_observation_dimension = 51


def migrated_learner_state(state, binding, wrapper):
    from validate_published_finite_check_20261025 import digest
    if KEY in state or digest(state) != binding['learner_digest']:
        raise ValueError('Only the exact registered complete87 learner may migrate')
    value = copy.deepcopy(state)
    expanded = []
    for name, tensor in value['agent'].items():
        if name.startswith(('ensemble.', 'ensemble_targets.')) and name.endswith('.q_net.0.weight'):
            if tensor.shape[1] != 50 + binding['action_dimension']:
                raise ValueError('Parent critic width mismatch')
            value['agent'][name] = insert_zero(tensor)
            expanded.append(name)
    if len(expanded) != 10:
        raise ValueError('Expected all five online and five target first layers')
    named = list(wrapper.learner.agent.ensemble.named_parameters())
    opt = value['q_optimizer']
    ids = [p for group in opt['param_groups'] for p in group['params']]
    if len(ids) != len(named):
        raise ValueError('Q optimizer parameter order changed')
    for pid, (name, param) in zip(ids, named, strict=True):
        if name.endswith('.q_net.0.weight'):
            for key, tensor in opt['state'].get(pid, {}).items():
                if torch.is_tensor(tensor) and tensor.ndim != 0:
                    if tensor.shape != (param.shape[0], param.shape[1]-1):
                        raise ValueError('Unexpected Adam moment shape')
                    opt['state'][pid][key] = insert_zero(tensor)
    value[KEY] = marker(binding)
    return value


def history_class(base, binding):
    binding = copy.deepcopy(binding)
    expected = marker(binding)

    class HistoryLearner(base):
        def __init__(self, *args, **kwargs):
            self.history_peaks = {}
            self.history_intervals = {}
            super().__init__(*args, **kwargs)
            if not self.critic_clock or self.algorithm != 'cheq' or kwargs['dimension'] != binding['action_dimension']:
                raise ValueError('History amendment requires the bound clock CHEQ learner')
            expand_architecture(self)

        def reset_episode(self, stream=0):
            super().reset_episode(stream=stream)
            self.history_peaks[stream] = 0.
            self.history_intervals[stream] = 0

        def consume_interval(self, interval, stream=0):
            if stream not in self.history_peaks:
                raise ValueError('Unknown episode stream')
            actions = self.episode_actions[stream]
            if interval is None:
                if actions != 0 or self.history_intervals[stream] != 0:
                    raise ValueError('Only the initial observation may have no interval')
                return
            if self.history_intervals[stream] + 1 != actions:
                raise ValueError('Interval must follow exactly one completed action')
            peak = float(interval['external_penetration_peak_m'])
            feature(peak)
            if peak < self.history_peaks[stream]:
                raise ValueError('Cumulative external penetration decreased')
            self.history_peaks[stream] = peak
            self.history_intervals[stream] += 1

        def observation(self, raw, stream=0):
            if self.history_intervals[stream] != self.episode_actions[stream]:
                raise ValueError('Consume completed interval before constructing next observation')
            return np.r_[super().observation(raw, stream=stream), feature(self.history_peaks[stream])].astype(np.float32)

        def terminal_observation(self, previous, stream=0):
            value = np.asarray(previous, np.float32)
            if value.shape != (51,) or self.history_intervals[stream] != self.episode_actions[stream]:
                raise ValueError('Consume terminal interval before terminal observation')
            return np.r_[super().terminal_observation(value[:50], stream=stream), feature(self.history_peaks[stream])].astype(np.float32)

        def load_state_dict(self, state):
            if state.get(KEY) != expected:
                raise ValueError('History state requires its exact persisted marker')
            plain = dict(state)
            plain.pop(KEY)
            self.history_peaks.clear()
            self.history_intervals.clear()
            self.episode_actions.clear()
            self.mixers = {0: self.mixers[0]}
            super().load_state_dict(plain)
            install_history_projection(self)
            # The composed base rebinds foreach to the expanded parameter objects.

        def migrate_parent(self, state):
            self.load_state_dict(migrated_learner_state(state, binding, self))

        def state_dict(self):
            return dict(super().state_dict(), **{KEY: copy.deepcopy(expected)})

    return HistoryLearner


def history_replay_class(base, binding):
    binding = copy.deepcopy(binding)
    expected = marker(binding)

    class HistoryReplay(base):
        def __init__(self, dimension, observation_dim, seed, capacity=4_000_000):
            if dimension != binding['action_dimension'] or observation_dim != 51:
                raise ValueError('History replay dimensions changed')
            super().__init__(dimension, observation_dim, seed, capacity=capacity)

        def state_dict(self):
            return dict(super().state_dict(), **{KEY: copy.deepcopy(expected)})

        def load_state_dict(self, state):
            if state.get(KEY) != expected:
                raise ValueError('History replay marker changed or absent')
            for name in ('observations', 'next_observations'):
                value = state['arrays'][name]
                if value.ndim != 2 or value.shape[1] != 51 or np.any(value[:, 50] < 0) or np.any(value[:, 50] >= 1):
                    raise ValueError('History replay feature outside registered domain')
            if np.any(state['arrays']['next_observations'][:, 50] < state['arrays']['observations'][:, 50]):
                raise ValueError('Replay cumulative history decreased within a transition')
            plain = dict(state)
            plain.pop(KEY)
            super().load_state_dict(plain)

        def migrate_parent(self, state, sidecar_path):
            from validate_published_finite_check_20261025 import digest
            if KEY in state or digest(state) != binding['replay_digest'] or sha(sidecar_path) != binding['sidecar_sha256']:
                raise ValueError('Exact parent replay and reviewed sidecar required')
            history = np.load(sidecar_path, mmap_mode='r', allow_pickle=False)
            if history.dtype != np.float64 or history.shape != (binding['rows'], 2) or state['size'] != binding['rows']:
                raise ValueError('History sidecar shape or dtype changed')
            if np.any(history[:, 1] < history[:, 0]):
                raise ValueError('Sidecar cumulative history decreased')
            arrays = dict(state['arrays'])
            for column, name in enumerate(('observations', 'next_observations')):
                if arrays[name].shape != (state['size'], 50):
                    raise ValueError('Parent replay must contain original 50 columns')
                arrays[name] = np.column_stack((arrays[name], feature(history[:, column])))
            self.load_state_dict(dict(state, arrays=arrays, **{KEY: copy.deepcopy(expected)}))

        def add(self, **row):
            for name in ('observations', 'next_observations'):
                value = np.asarray(row[name])
                if value.shape != (51,) or not np.isfinite(value).all() or not 0 <= value[50] < 1:
                    raise ValueError('Invalid online history observation')
            if row['next_observations'][50] < row['observations'][50]:
                raise ValueError('Online history decreased')
            super().add(**row)

    return HistoryReplay


def transform_trainer(source):
    """Consume each IPC interval once, before next replay obs and next action."""
    seam = "                    previous = state['previous']"
    if source.count(seam) != 1:
        raise ValueError('Pinned trainer event seam changed')
    return source.replace(seam, "                    learner.consume_interval(event['interval'], stream=slot)\n" + seam)
