"""Causal RL parameter interface around the unchanged six-axis virtual dynamics.

This module contains no learned policy and performs no simulator integration.
The policy supplies six bounded log-stiffness targets; the original VMC maps
encoder-derived wrench to the shared action7 execution contract.
"""
from __future__ import annotations

import copy
import numpy as np

from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


class Canonical48VMCTuning:
    kind = 'rl_parameter6_vmc_action7_development'
    parameter_dim = 6
    observation_dim = 48
    action_period_s = .04
    log_scale_limit = float(np.log(2.))
    log_scale_rate_per_s = float(np.log(2.)/.20)

    def __init__(self, options):
        # CoreTeacher fills missing K/D from its CLI ContactMemoryConfig,
        # which differs from SixDVirtualDynamics' standalone defaults. Do not
        # silently choose a different nominal controller at this boundary.
        if not all(key in options for key in ('stiffness_6d','damping_6d')):
            raise ValueError('Explicit nominal stiffness_6d and damping_6d are required')
        self.options = copy.deepcopy(options)
        self.base = SixDVirtualDynamics(self.options)
        self.nominal_k = self.base.k.copy()
        self.nominal_d = self.base.b.copy()
        self.log_scale = np.zeros(6)
        self.last_parameters = None

    def reset(self):
        self.base.reset()
        self.base.k = self.nominal_k.copy()
        self.base.b = self.nominal_d.copy()
        self.log_scale.fill(0.)
        self.last_parameters = None

    def act(self, observation, parameter_action):
        """Use raw SI-unit canonical48, never a VecNormalize-transformed vector."""
        obs = np.asarray(observation, dtype=float)
        parameter = np.asarray(parameter_action, dtype=float)
        if obs.shape != (48,) or not np.isfinite(obs).all():
            raise ValueError('Expected finite canonical48 observation')
        if parameter.shape != (6,) or not np.isfinite(parameter).all():
            raise ValueError('Expected finite six-dimensional parameter action')
        if np.any(np.abs(parameter) > 1.):
            raise ValueError('Parameter action must lie in [-1,1]')
        # Validate before mutating the controller. Fixed dt is the canonical
        # 25Hz action period, not the MuJoCo physics integration timestep.
        target = self.log_scale_limit*parameter
        max_change = self.log_scale_rate_per_s*self.action_period_s
        self.log_scale += np.clip(target-self.log_scale, -max_change, max_change)
        scale = np.exp(self.log_scale)
        self.base.k = self.nominal_k*scale
        # Preserve each principal axis' small-offset linearized damping ratio;
        # the saturated spring does not have constant global tangent stiffness.
        self.base.b = self.nominal_d*np.sqrt(scale)
        action = self.base.act(obs[39:45], self.action_period_s)
        self.last_parameters = dict(request=parameter.copy(), log_scale=self.log_scale.copy(),
                                    stiffness=self.base.k.copy(), damping=self.base.b.copy())
        return action

    @classmethod
    def protocol(cls):
        return dict(version='canonical48_parameter6_vmc_v1',
                    policy_observation_dim=48, parameter_action_dim=6, execution_action_dim=7,
                    wrench_observation_slice=[39,45], action_period_s=cls.action_period_s,
                    stiffness_scale_bounds=[.5,2.],
                    log_scale_rate_per_s=cls.log_scale_rate_per_s,
                    damping='D0*sqrt(K/K0); original principal-axis small-offset damping ratios',
                    hidden_state='original VMC filter/offset/velocity plus six log gain states',
                    zero_parameter_meaning='fixed nominal VMC only from reset with all-zero requests',
                    privileged_inputs=[], adapter_input='raw SI-unit canonical48, not normalized policy input',
                    limitations=['parameterization inspired by variable-impedance RL; not Da-VIL reproduction',
                                 'positive gains and rate limiting do not establish passivity for varying gains',
                                 'no learned checkpoint or closed-loop performance established by this adapter'])
