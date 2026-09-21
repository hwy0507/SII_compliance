"""Causal VMC teacher. No simulator, wall clock, obstacle or event inputs.

The virtual tool obeys M d2x + B dx + K x = estimated external force.
Outputs are the existing seven-channel velocity-residual action, NOT gains.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class HapticVMCConfig:
    mass: float = 2.0
    stiffness: float = 100.0
    damping: float = 35.0
    offset_tracking_gain: float = 2.3
    force_deadband: float = 0.8
    force_limit: float = 60.0
    velocity_limit: float = 0.22
    offset_limit: float = 0.20
    action_velocity_limit: float = 0.32


class HapticVMC:
    def __init__(self, config=HapticVMCConfig()):
        self.config = config
        if any(not np.isfinite(v) or v <= 0 for v in vars(config).values()):
            raise ValueError("All VMC settings must be positive and finite")
        self.offset = np.zeros(3)
        self.velocity = np.zeros(3)

    def act(self, estimated_force_world, dt):
        force = np.asarray(estimated_force_world, dtype=float)
        if force.shape != (3,) or not np.isfinite(force).all() or not 0 < dt <= .04:
            raise ValueError("Expected finite force and a fixed integration interval")
        c = self.config
        norm = np.linalg.norm(force)
        force = force * max(0., 1. - c.force_deadband / max(norm, 1e-12))
        force *= min(1., c.force_limit / max(np.linalg.norm(force), 1e-12))
        for _ in range(20):
            acceleration = (force - c.damping*self.velocity - c.stiffness*self.offset)/c.mass
            self.velocity += acceleration * dt / 20
            self.velocity *= min(1., c.velocity_limit/max(np.linalg.norm(self.velocity), 1e-12))
            self.offset += self.velocity * dt / 20
            if np.linalg.norm(self.offset) > c.offset_limit:
                n = self.offset / np.linalg.norm(self.offset)
                self.offset = n*c.offset_limit
                self.velocity -= max(0., np.dot(self.velocity,n))*n
        residual = self.velocity + c.offset_tracking_gain*self.offset
        action = np.zeros(7)
        action[1:4] = np.clip(residual/c.action_velocity_limit, -1., 1.)
        return action


class JointLoadObserver:
    """Finite-difference inverse-dynamics residual, filtered causally.

    Arguments are encoder velocity, known model terms, and actual motor
    torque/current equivalent. Never uses contact force, qacc, qfrc_constraint,
    obstacle geometry, contact identity, or event time. Accuracy with noisy
    hardware requires a separate calibration; this is ideal-sensor simulation.
    """
    def __init__(self, velocity, frictionloss, filter_tau=.04):
        self.previous_velocity = np.asarray(velocity).copy()
        self.filtered = np.zeros(7)
        self.filter_tau = filter_tau
        self.frictionloss = np.asarray(frictionloss).copy()

    def update(self, velocity, mass_matrix, bias, passive, actuator_torque, dt):
        velocity = np.asarray(velocity)
        acceleration = (velocity-self.previous_velocity)/dt
        residual = (mass_matrix@acceleration + bias-passive-actuator_torque)[:7]
        # MuJoCo frictionloss is a constraint, not qfrc_passive. It is an
        # internal joint load, so compensate moving friction and use its
        # known stiction interval as uncertainty near zero encoder velocity.
        motion = np.tanh(velocity[:7]/.005)
        compensated = residual + self.frictionloss[:7]*motion
        uncertainty = self.frictionloss[:7]*(1.-np.abs(motion))
        residual = np.sign(compensated)*np.maximum(np.abs(compensated)-uncertainty,0.)
        self.previous_velocity = velocity.copy()
        self.filtered += (1.-np.exp(-dt/self.filter_tau))*(residual-self.filtered)
        return self.filtered.copy()


def equivalent_tool_wrench(jacobian, joint_load):
    """EE-wrench approximation for the present hand-push task, not localization."""
    return np.linalg.lstsq(np.asarray(jacobian).T, joint_load, rcond=.03)[0]
