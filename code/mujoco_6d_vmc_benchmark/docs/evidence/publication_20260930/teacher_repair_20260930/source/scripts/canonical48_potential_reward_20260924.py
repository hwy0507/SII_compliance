"""Finite-episode potential shaping of the declared development-gate objective.

Only the reward function uses task-stage and final evaluation labels. Neither
actor nor critic observation is extended. The base reward is terminal only.
"""
from __future__ import annotations

import numpy as np

GAMMA = .995
POSITION_SCALE_M = .30
STAGE_MAX = 3


def potential(observation, stage):
    obs = np.asarray(observation, dtype=float)
    if obs.shape != (48,) or not np.isfinite(obs).all():
        raise ValueError('Potential requires finite canonical48 observation')
    if not isinstance(stage, (int, np.integer)) or not 0 <= stage <= STAGE_MAX:
        raise ValueError('Potential is declared only for the four-stage push task')
    return (stage-min(float(np.linalg.norm(obs[20:23]))/POSITION_SCALE_M, 1.))/STAGE_MAX


def shaped_reward(previous_observation, previous_stage, next_observation, next_stage,
                  *, terminal=False, gate_success=False, invalid_or_upstream=False):
    if not terminal and (gate_success or invalid_or_upstream):
        raise ValueError('Terminal labels must not be supplied before termination')
    if gate_success and invalid_or_upstream:
        raise ValueError('A valid gate cannot pass with invalid/upstream physics')
    before = potential(previous_observation, previous_stage)
    # All terminal states have zero potential. Do not bootstrap or synthesize
    # a final actor observation from private simulator state.
    after = 0. if terminal else potential(next_observation, next_stage)
    base = (5.*float(gate_success)-5.*float(invalid_or_upstream)) if terminal else 0.
    terms = dict(base_terminal=base, potential_before=before, potential_after=after,
                 potential_difference=GAMMA*after-before)
    return base+terms['potential_difference'], terms


def protocol():
    return dict(version='push4_gate_potential_v1', gamma=GAMMA,
                potential='(stage - min(norm(position_error)/0.30,1))/3; terminal potential=0',
                base_reward='terminal +5 development_gate; -5 invalid/upstream; otherwise0',
                removed_terms=['integrated waypoint/rotation/force costs','action/action-change costs','phase bonus'],
                observation_changed=False, actor_privileged_fields=[], critic_privileged_fields=[],
                reward_only_labels=['stage','development_gate','invalid_physics','upstream_contact'],
                property='discounted shaping telescopes to minus initial potential for any completed episode',
                limitations=['new training objective, not equivalent to the previous dense reward',
                             'aligns declared development gate, not office gate or optimal three-metric tradeoff',
                             'correct shaping identity alone does not guarantee PPO learning or convergence'])


def environment_class(base_class):
    """Keep the original single-worker simulator bridge and replace reward only."""
    class PotentialRewardEnv(base_class):
        def reset(self, **kwargs):
            obs, info = super().reset(**kwargs)
            self.reward_previous_observation = self.obs.copy()
            self.reward_previous_stage = int(self.phase)
            return obs, info

        def step(self, action):
            obs, _, terminated, truncated, info = super().step(action)
            if truncated:
                raise ValueError('Unexpected truncation: finite task uses termination, not bootstrap')
            result = self.last_result if terminated else None
            reward, terms = shaped_reward(self.reward_previous_observation,
                self.reward_previous_stage, self.obs, int(self.phase), terminal=terminated,
                gate_success=bool(info['evaluation']['development_gate']) if terminated else False,
                invalid_or_upstream=bool(result['invalid_physics'] or result['upstream_contact']) if terminated else False)
            self.reward_previous_observation = self.obs.copy()
            self.reward_previous_stage = int(self.phase)
            info['reward_terms'] = terms
            info['reward_version'] = 'push4_gate_potential_v1'
            return obs, float(reward), terminated, truncated, info
    return PotentialRewardEnv
