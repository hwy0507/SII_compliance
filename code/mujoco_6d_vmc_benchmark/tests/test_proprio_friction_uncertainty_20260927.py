"""Steady physical balances for the causal friction uncertainty calibration."""
import numpy as np
import pytest
from haptic_vmc_teacher_20260916 import JointLoadObserver


def steady_estimate(force,scale):
    # Unit-inertia joint moving steadily: motor + external - Coulomb friction=0.
    velocity=np.full(7,.001);friction=np.full(7,.4)
    motor=friction-force
    observer=JointLoadObserver(velocity,friction,friction_velocity_scale=scale)
    for _ in range(300):
        result=observer.update(velocity,np.eye(7),np.zeros(7),np.zeros(7),motor,.004)
    return result


def test_smaller_velocity_uncertainty_preserves_more_real_aligned_contact():
    old=steady_estimate(.5,.005);candidate=steady_estimate(.5,.001)
    np.testing.assert_allclose(old,0.,atol=1e-12)
    assert np.all(candidate>.3) and np.all(candidate<.5)


def test_known_friction_without_contact_does_not_create_false_load():
    for scale in (.005,.001):
        np.testing.assert_allclose(steady_estimate(0.,scale),0.,atol=1e-12)


def test_invalid_velocity_uncertainty_is_rejected():
    for scale in (0.,-1.,np.nan,np.inf):
        with pytest.raises(ValueError):
            JointLoadObserver(np.zeros(7),np.ones(7),friction_velocity_scale=scale)
