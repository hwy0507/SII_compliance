"""Scale the recovery equilibrium offset, preserving its regulating feedback.

Unlike scaling the whole recovery blend, this leaves the original positional
and nominal-velocity correction active near the goal. Only the extra lift
offset vanishes with the existing canonical horizontal command intent.
This is a teacher-only active controller, not a passivity/stability proof.
"""
import numpy as np

from optimize_tool_contact_20261002 import ParameterTeacher as LegacyParameterTeacher

VERSION = 'intent_scaled_equilibrium_v1'


class IntentEquilibriumTeacher(LegacyParameterTeacher):
    def __init__(self, config):
        if config.get('teacher_mechanism') != VERSION:
            raise ValueError('Explicit versioned equilibrium configuration required')
        super().__init__(config)
        if not self.recovery or self.recovery.get('activation_mode') != 'progress':
            raise ValueError('Intent equilibrium requires existing progress recovery')
        self.recovery_intent = 0.
        self.recovery_activation = 0.

    def reset(self):
        super().reset()
        self.recovery_intent = 0.
        self.recovery_activation = 0.

    def act(self, wrench_world, dt=.04):
        action = super().act(wrench_world, dt)
        c, obs = self.recovery, self.observation
        path = obs[45:47]
        norm = float(np.linalg.norm(path))
        horizontal = min(1., norm)
        desired = float(obs[14:16]@(path/max(norm, 1e-12)))
        intent = float(np.clip(desired/c.get('intent_velocity_mps', .015), 0., 1.))*horizontal**2
        activation = self.recovery_memory*horizontal**2
        self.recovery_intent = intent
        self.recovery_activation = activation
        if intent == 1. or horizontal == 0.:
            return action
        if self.velocity_weight == 1.:
            base_z = self.raw_action[3]*self.channel_gain[3]
        else:
            residual = self.velocity_weight*self.velocity+self.offset_gain*self.offset
            base_z = np.clip((self.R6@residual/self.action_limits)[2], -1., 1.)*self.channel_gain[3]
        target_velocity = c['gain_per_s']*(c['offset_m']*intent+obs[22])
        correction = np.clip(target_velocity-obs[16], -c['velocity_mps'], c['velocity_mps'])
        action[3] = np.clip((1.-activation)*base_z+activation*correction/.32, -1., 1.)
        return action
