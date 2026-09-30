"""Controller invariants independent of any simulated fixture or contact."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_panel_impedance_reference_20260923 import MovingEquilibrium, ReferenceImpedanceConfig


def test_initial_equilibrium_is_measured_pose_without_position_jump():
    controller = MovingEquilibrium(ReferenceImpedanceConfig())
    position = np.array([.4, -.1, .6])
    rotation = Rotation.from_rotvec([.3, -.4, .2]).as_matrix()
    error, velocity = controller.update(position, rotation, np.full(6, 100.), .002)
    np.testing.assert_allclose(controller.position, position, atol=1.e-12)
    np.testing.assert_allclose(controller.rotation, rotation, atol=1.e-12)
    np.testing.assert_allclose(error, 0., atol=1.e-12)
    assert np.linalg.norm(velocity[:3]) <= .35 + 1.e-12
    assert np.linalg.norm(velocity[3:]) <= 1.2 + 1.e-12


def test_blocked_robot_cannot_wind_up_equilibrium_or_exceed_speed_bounds():
    cfg = ReferenceImpedanceConfig()
    controller = MovingEquilibrium(cfg)
    dt = .01
    for _ in range(80):
        old_p = None if controller.position is None else controller.position.copy()
        old_r = None if controller.rotation is None else controller.rotation.copy()
        error, _ = controller.update(np.zeros(3), np.eye(3), np.full(6, 99.), dt)
        assert np.linalg.norm(error[:3]) <= cfg.max_position_error + 1.e-10
        assert np.linalg.norm(error[3:]) <= cfg.max_rotation_error + 1.e-10
        if old_p is not None:
            assert np.linalg.norm(controller.position - old_p) <= cfg.max_linear_speed * dt + 1.e-10
            delta = Rotation.from_matrix(controller.rotation @ old_r.T).as_rotvec()
            assert np.linalg.norm(delta) <= cfg.max_angular_speed * dt + 1.e-10
    assert np.linalg.norm(controller.position) <= cfg.max_position_error + 1.e-10
    assert controller.position_limited_steps > 0
    assert controller.rotation_limited_steps > 0


def test_zero_pose_and_twist_errors_give_zero_residual_wrench():
    controller = MovingEquilibrium(ReferenceImpedanceConfig())
    desired_twist = np.array([.1, -.03, .02, .2, .1, -.2])
    error, bounded_twist = controller.update(np.ones(3), np.eye(3), desired_twist, .002)
    wrench = controller.wrench(error, bounded_twist, desired_twist)
    np.testing.assert_allclose(wrench, np.zeros(6), atol=1.e-12)
    jacobian = np.arange(42).reshape(6, 7) / 42
    np.testing.assert_allclose(jacobian.T @ wrench, np.zeros(7), atol=1.e-12)


def test_external_displacement_does_not_rebase_reference_discontinuously():
    cfg = ReferenceImpedanceConfig()
    controller = MovingEquilibrium(cfg)
    controller.update(np.zeros(3), np.eye(3), np.zeros(6), .002)
    old_p, old_r = controller.position.copy(), controller.rotation.copy()
    displaced = Rotation.from_rotvec([0., 0., .8]).as_matrix()
    error, _ = controller.update(np.array([.7, 0., 0.]), displaced, np.zeros(6), .002)
    np.testing.assert_allclose(controller.position, old_p)
    np.testing.assert_allclose(controller.rotation, old_r)
    assert np.linalg.norm(error[:3]) == pytest.approx(cfg.max_position_error)
    assert np.linalg.norm(error[3:]) == pytest.approx(cfg.max_rotation_error)


def test_rotational_integration_uses_world_frame_left_multiplication():
    cfg = ReferenceImpedanceConfig(max_rotation_error=1.)
    controller = MovingEquilibrium(cfg)
    rotation = Rotation.from_rotvec([.3, .2, -.1]).as_matrix()
    omega = np.array([.2, -.1, .4])
    twist = np.r_[np.zeros(3), omega]
    controller.update(np.zeros(3), rotation, twist, .002)
    controller.update(np.zeros(3), rotation, twist, .002)
    np.testing.assert_allclose(controller.rotation,
                               Rotation.from_rotvec(.002 * omega).as_matrix() @ rotation,
                               atol=1.e-12)


@pytest.mark.parametrize('dt', [0., -1., float('nan')])
def test_invalid_dt_is_rejected(dt):
    controller = MovingEquilibrium(ReferenceImpedanceConfig())
    with pytest.raises(ValueError):
        controller.update(np.zeros(3), np.eye(3), np.zeros(6), dt)


def test_installed_hook_captures_same_wbc_and_preserves_torque_projection(monkeypatch):
    import audited_velocity_env as velocity_env
    import current_student_policy_20260921 as loader
    import run_benchmark
    from run_panel_impedance_reference_20260923 import install
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig

    jacobian = np.c_[np.eye(6), np.zeros(6)]
    monkeypatch.setattr(run_benchmark, 'body_jacobian', lambda *args: jacobian)
    monkeypatch.setattr(run_benchmark, 'body_twist', lambda *args: np.zeros(6))
    # Register changes with monkeypatch before install mutates these hooks.
    monkeypatch.setattr(velocity_env, 'safe_velocity_tracking_torque', velocity_env.safe_velocity_tracking_torque)
    monkeypatch.setattr(loader, 'load_current', loader.load_current)
    command = SimpleNamespace(task_twist_world=np.array([.2, 0., 0., 0., 0., 0.]))
    data = SimpleNamespace(time=0., xpos=np.zeros((1, 3)), xmat=np.eye(3).reshape(1, 9))
    env = SimpleNamespace(execution_mode='twist', model=None, data=data, _hand_id=0,
                          _wbc_command=lambda t: command)
    module = SimpleNamespace(create_environment=lambda args: (env, 'task', 'scene'))
    audit = {}
    cfg = ReferenceImpedanceConfig()
    install(module, cfg, audit)
    installed_env, task, scene = module.create_environment(SimpleNamespace())
    assert (installed_env, task, scene) == (env, 'task', 'scene')
    assert env._wbc_command(0.) is command
    safety = VelocityResidualSafetyConfig()
    zero = np.zeros(7)
    limits = np.full(7, 2.)
    dt = .001
    hook = velocity_env.safe_velocity_tracking_torque
    torque, scale = hook(zero, zero, zero, zero, dt, safety, torque_limits=limits)
    # Initial spring error is zero; bounded nominal velocity still produces
    # damping feedforward, which must pass the actual shared box and slew.
    assert torque[0] > 0
    assert 0 <= scale < 1
    assert np.all(np.abs(torque) <= limits)
    assert np.all(np.abs(torque) <= safety.maximum_torque_rate_nmps * dt + 1.e-12)
    np.testing.assert_allclose(audit['integrator'].position, 0.)
    hook(zero, zero, zero, zero, dt, safety, torque_limits=limits)
    assert audit['integrator'].updates == 1  # repeated same-state call
    data.time = dt
    assert env._wbc_command(dt) is command
    hook(zero, zero, zero, torque, dt, safety, torque_limits=limits)
    np.testing.assert_allclose(audit['integrator'].position, [.2 * dt, 0., 0.])
    assert audit['integrator'].updates == 2
    assert loader.load_current(None).kind == 'cartesian_impedance_moving_reference'
