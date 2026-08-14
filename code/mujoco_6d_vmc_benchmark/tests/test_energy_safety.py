from __future__ import annotations

import numpy as np

from energy_safety import EnergyBudgetSafety, EnergySafetyConfig


def test_energy_tank_does_not_cross_its_declared_bounds() -> None:
    safety = EnergyBudgetSafety(EnergySafetyConfig(initial_energy_j=0.12, minimum_energy_j=0.08, maximum_energy_j=0.20))
    base = np.zeros(3)
    requested = np.array([50.0, 0.0, 0.0])
    for _ in range(100):
        applied, diagnostic = safety.filter_increment(
            base, requested, np.array([0.05, 0.0, 0.0]), np.zeros(3), np.array([1.0, 0.0, 0.0]),
            drive_damping=0.0, dt_s=0.004,
        )
        assert np.linalg.norm(applied) <= np.linalg.norm(requested) + 1e-12
        assert 0.08 <= diagnostic.tank_energy_j <= 0.20


def test_base_drive_is_preserved_when_the_increment_is_energy_limited() -> None:
    safety = EnergyBudgetSafety(EnergySafetyConfig(initial_energy_j=0.08, minimum_energy_j=0.08, maximum_energy_j=0.20))
    base = np.array([2.0, -1.0, 0.5])
    applied, diagnostic = safety.filter_increment(
        base, base + np.array([100.0, 0.0, 0.0]), np.array([0.05, 0.0, 0.0]), np.zeros(3),
        np.array([1.0, 0.0, 0.0]), drive_damping=0.0, dt_s=0.004,
    )
    assert np.allclose(applied, base)
    assert diagnostic.energy_scale == 0.0


def test_directional_smoothing_reduces_a_boost_when_error_is_already_closing() -> None:
    config = EnergySafetyConfig(initial_energy_j=1.2, minimum_energy_j=0.08, maximum_energy_j=1.2, smoothing_time_constant_s=0.004)
    safety = EnergyBudgetSafety(config)
    base = np.zeros(3)
    requested = np.array([10.0, 0.0, 0.0])
    _, growing = safety.filter_increment(
        base, requested, np.array([0.05, 0.0, 0.0]), np.array([0.20, 0.0, 0.0]), np.zeros(3), 0.0, 0.004,
    )
    _, closing = safety.filter_increment(
        base, requested, np.array([0.05, 0.0, 0.0]), np.array([-0.20, 0.0, 0.0]), np.zeros(3), 0.0, 0.004,
    )
    assert closing.direction_scale < growing.direction_scale
