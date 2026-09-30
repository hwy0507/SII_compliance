"""Proprioceptive M-D-K state and shifted-reference WBC residual, without a simulator."""
from __future__ import annotations

import numpy as np


def vector6(value, name):
    value = np.asarray(value, dtype=float)
    if value.shape != (6,) or not np.all(np.isfinite(value)):
        raise ValueError(f'{name} must be a finite six-vector')
    return value


def rotation_offset_and_jacobian(phi):
    """Exp(phi) and SO(3) left Jacobian: omega_world = J_left(phi) phi_dot."""
    x, y, z = phi
    skew = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    theta = float(np.linalg.norm(phi))
    if theta < 1e-6:
        a = 1. - theta**2 / 6.
        b = .5 - theta**2 / 24.
        c = 1./6. - theta**2 / 120.
    else:
        a = np.sin(theta) / theta
        b = (1. - np.cos(theta)) / theta**2
        c = (theta - np.sin(theta)) / theta**3
    return np.eye(3) + a*skew + b*(skew@skew), np.eye(3) + b*skew + c*(skew@skew)


class AdmittanceState:
    """Diagonal virtual dynamics M zdd + D zd + K z = bounded estimated wrench.

    Implicit Euler avoids an unstable explicit update for stiff parameter scans.
    Translation is in world coordinates; rotation uses bounded world rotation
    vector coordinates (a local virtual model, not globally passive SE(3)).
    """
    def __init__(self, mass, stiffness, zeta=1.):
        self.mass = vector6(mass, 'mass').copy()
        self.k = vector6(stiffness, 'stiffness').copy()
        if np.any(self.mass <= 0) or np.any(self.k <= 0) or not np.isfinite(zeta) or zeta <= 0:
            raise ValueError('M, K and damping ratio must be finite and positive')
        self.d = 2.*zeta*np.sqrt(self.mass*self.k)
        self.offset = np.zeros(6)
        self.velocity = np.zeros(6)
        self.wrench_bounds = np.array([30., 30., 30., 3., 3., 3.])
        self.offset_limit = np.array([.08, .08, .08, .25, .25, .25])
        self.speed_limit = np.array([.16, .16, .16, .6, .6, .6])

    def advance(self, wrench, dt):
        wrench = vector6(wrench, 'wrench')
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError('dt must be finite and positive')
        effective = self.wrench_bounds*np.tanh(wrench/self.wrench_bounds)
        h = dt/20.
        for _ in range(20):
            self.velocity = ((self.mass*self.velocity + h*(effective-self.k*self.offset)) /
                             (self.mass+h*self.d+h*h*self.k))
            self.velocity = np.clip(self.velocity, -self.speed_limit, self.speed_limit)
            candidate = self.offset+h*self.velocity
            clipped = np.abs(candidate) > self.offset_limit
            self.offset = np.clip(candidate, -self.offset_limit, self.offset_limit)
            # Do not retain an outward velocity against a virtual travel stop.
            self.velocity[clipped & (self.velocity*self.offset > 0)] = 0.
        return effective

    def virtual_twist(self):
        _, left_jacobian = rotation_offset_and_jacobian(self.offset[3:])
        return np.r_[self.velocity[:3], left_jacobian@self.velocity[3:]]


class ShiftedWBCResidual:
    """Map virtual pose+twist through the same bounded WBC as nominal control.

    evaluate(offset, feedforward) is a pure kinematic WBC evaluation. The common
    panel post-saturation scale is inferred from the observed nominal command,
    without a phase flag. It must multiply the complete nominal command.
    """
    def __init__(self):
        self.scale = 1.
        self.scale_unobservable_steps = 0
        self.last_diagnostic = {}

    def compute(self, observed_nominal, state, evaluate):
        observed = vector6(observed_nominal, 'observed nominal')
        nominal = vector6(evaluate(np.zeros(6), np.zeros(6)), 'nominal WBC')
        denominator = float(nominal@nominal)
        self.last_diagnostic = dict(observed_nominal=observed.tolist(),
                                    reconstructed_nominal=nominal.tolist(),
                                    reconstructed_norm=float(np.sqrt(denominator)),
                                    previous_scale=self.scale)
        if denominator > 1e-16:
            scale = float(observed@nominal/denominator)
            residual = observed-scale*nominal
            self.last_diagnostic.update(fitted_scale=scale, residual=residual.tolist(),
                                        residual_norm=float(np.linalg.norm(residual)))
            if not .01 <= scale <= 1.00001:
                raise ValueError(f'Unsupported nominal WBC scale {scale}')
            if np.linalg.norm(observed-scale*nominal) > 1e-7:
                raise ValueError('Observed nominal is not a scalar multiple of the reconstructed WBC: '
                                 f'scale={scale:.16g}, residual_norm={np.linalg.norm(residual):.16g}, '
                                 f'nominal_norm={np.sqrt(denominator):.16g}')
            self.scale = min(scale, 1.)
        else:
            self.scale_unobservable_steps += 1
            if np.linalg.norm(observed) > 1e-7:
                raise ValueError('Nonzero nominal command with zero reconstructed WBC')
        # Retain the same WBC speed/IK/posture bounds. Dividing feedforward by
        # the shared scale preserves virtual velocity when it is unsaturated.
        shifted = vector6(evaluate(state.offset, state.virtual_twist()/self.scale), 'shifted WBC')
        return self.scale*(shifted-nominal)
