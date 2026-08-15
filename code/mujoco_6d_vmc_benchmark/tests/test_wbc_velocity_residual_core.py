from __future__ import annotations

import numpy as np

from wbc_velocity_residual_core import (
    TORQUE_LIMITS_NM,
    VelocityResidualActionFilter,
    VelocityResidualSafetyConfig,
    deployable_authority_gate,
    safe_joint_velocity_command,
    safe_velocity_tracking_torque,
)


def test_zero_action_is_exact_fixed_wbc_command_after_reset() -> None:
    config = VelocityResidualSafetyConfig()
    action_filter = VelocityResidualActionFilter(config)
    action = action_filter.filter(np.zeros(7), 0.04)
    assert action.wbc_scale == 1.0
    assert np.array_equal(action.cartesian_yield_twist, np.zeros(6))
    nominal = np.linspace(-0.08, 0.08, 7)
    command, raw = safe_joint_velocity_command(
        nominal, np.hstack([np.eye(6), np.zeros((6, 1))]), action,
        nominal.copy(), 0.004, config,
    )
    assert np.allclose(raw, nominal)
    assert np.allclose(command, nominal)


def test_action_filter_enforces_amplitude_and_slew() -> None:
    config = VelocityResidualSafetyConfig()
    action_filter = VelocityResidualActionFilter(config)
    filtered = action_filter.filter(np.full(7, 2.0), 0.04)
    assert filtered.amplitude_saturated
    assert filtered.slew_limited
    assert filtered.wbc_scale >= config.minimum_wbc_scale
    assert np.max(np.abs(filtered.cartesian_yield_twist[:3])) <= config.maximum_linear_yield_rate_mps2 * 0.04 + 1e-12
    assert np.max(np.abs(filtered.cartesian_yield_twist[3:])) <= config.maximum_angular_yield_rate_radps2 * 0.04 + 1e-12


def test_deployable_authority_gate_is_smooth_and_bounded() -> None:
    config = VelocityResidualSafetyConfig()
    assert deployable_authority_gate(0.0, config) == 0.0
    assert deployable_authority_gate(config.authority_gate_start_error_m, config) == 0.0
    midpoint = 0.5 * (config.authority_gate_start_error_m + config.authority_gate_full_error_m)
    assert np.isclose(deployable_authority_gate(midpoint, config), 0.5)
    assert deployable_authority_gate(config.authority_gate_full_error_m, config) == 1.0
    assert deployable_authority_gate(1.0, config) == 1.0


def test_joint_velocity_and_torque_safety_are_hard_bounded() -> None:
    config = VelocityResidualSafetyConfig()
    action_filter = VelocityResidualActionFilter(config)
    filtered = action_filter.filter(np.array([1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0]), 1.0)
    command, _ = safe_joint_velocity_command(
        np.full(7, 5.0), np.hstack([np.eye(6), np.ones((6, 1))]), filtered,
        np.zeros(7), 0.004, config,
    )
    assert np.max(np.abs(command)) <= config.maximum_joint_acceleration_radps2 * 0.004 + 1e-12
    torque, scale = safe_velocity_tracking_torque(
        np.zeros(7), np.full(7, -20.0), command, np.zeros(7), 0.004, config,
    )
    assert 0.0 <= scale <= 1.0
    assert np.all(np.abs(torque) <= TORQUE_LIMITS_NM + 1e-12)
    assert np.all(np.abs(torque) <= config.maximum_torque_rate_nmps * 0.004 + 1e-12)
