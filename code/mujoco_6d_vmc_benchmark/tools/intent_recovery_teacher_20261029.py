"""Versioned teacher-only recovery readout using canonical command intent.

The legacy virtual dynamics and recovery-memory update are preserved. Only
the recovery blend is multiplied by the existing normalized horizontal
command intent. At intent=1 the action is identical to the legacy teacher;
at intent=0 it is the ordinary virtual-dynamics action, even if recovery
memory remains. No stage, clock, geometry, contact identity, or success gate
is read. This active controller has no claimed passivity/stability guarantee.
"""
import numpy as np
from pathlib import Path

from optimize_tool_contact_20261002 import ParameterTeacher as LegacyParameterTeacher

VERSION = 'intent_scaled_recovery_v1'


class IntentScaledRecoveryTeacher(LegacyParameterTeacher):
    def __init__(self, config):
        if config.get('teacher_mechanism') != VERSION:
            raise ValueError('Explicit versioned intent-recovery configuration required')
        super().__init__(config)
        if not self.recovery or self.recovery.get('activation_mode') != 'progress':
            raise ValueError('Intent-scaled readout requires the existing progress recovery')
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
        direction = path/max(norm, 1e-12)
        desired = float(obs[14:16]@direction)
        intent = float(np.clip(desired/c.get('intent_velocity_mps', .015), 0., 1.))*horizontal**2
        self.recovery_intent = intent
        self.recovery_activation = self.recovery_memory*horizontal**2*intent
        # Preserve exact legacy output at full intent, including its clipping.
        if intent == 1. or horizontal == 0.:
            return action
        # Reconstruct the already advanced base readout without a second
        # dynamics step. This is the same expression used by StableReadout.
        if self.velocity_weight == 1.:
            base_z = self.raw_action[3]*self.channel_gain[3]
        else:
            residual = self.velocity_weight*self.velocity+self.offset_gain*self.offset
            base_z = np.clip((self.R6@residual/self.action_limits)[2], -1., 1.)*self.channel_gain[3]
        target_velocity = c['gain_per_s']*(c['offset_m']+obs[22])
        correction = np.clip(target_velocity-obs[16], -c['velocity_mps'], c['velocity_mps'])
        activation = self.recovery_activation
        action[3] = np.clip((1.-activation)*base_z+activation*correction/.32, -1., 1.)
        return action


def make_teacher(config):
    version = config.get('teacher_mechanism')
    if version is None:
        return LegacyParameterTeacher(config)
    if version == VERSION:
        return IntentScaledRecoveryTeacher(config)
    if version == 'intent_scaled_equilibrium_v1':
        from intent_equilibrium_teacher_20261029 import IntentEquilibriumTeacher
        return IntentEquilibriumTeacher(config)
    raise ValueError('Unknown teacher mechanism: '+str(version))


def teacher_extension_path(config):
    names = {VERSION: 'intent_recovery_teacher_20261029.py',
             'intent_scaled_equilibrium_v1': 'intent_equilibrium_teacher_20261029.py'}
    version = config.get('teacher_mechanism')
    if version is None:
        return None
    if version not in names:
        raise ValueError('Unknown teacher mechanism: '+str(version))
    return Path(__file__).with_name(names[version])
