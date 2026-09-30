import numpy as np
import pytest

from admittance_reference_core_20260923 import AdmittanceState, ShiftedWBCResidual


def state():
    return AdmittanceState(np.ones(6), np.full(6, 100.))


def test_zero_force_zero_offset_restores_nominal_exactly():
    s = state()
    nominal = np.array([.02, -.03, .01, 0., 0., 0.])
    for _ in range(20):
        s.advance(np.zeros(6), .04)
    residual = ShiftedWBCResidual().compute(nominal, s, lambda z, v: nominal+2.5*z+v)
    np.testing.assert_array_equal(s.offset, np.zeros(6))
    np.testing.assert_array_equal(residual, np.zeros(6))


@pytest.mark.parametrize('scale', [1., .8])
def test_constant_force_equilibrium_keeps_pose_offset_residual(scale):
    s = state()
    wrench = np.array([1., 0., 0., 0., 0., 0.])
    for _ in range(250):
        effective = s.advance(wrench, .04)
    expected_offset = effective/s.k
    np.testing.assert_allclose(s.offset, expected_offset, atol=1e-10)
    np.testing.assert_allclose(s.velocity, np.zeros(6), atol=1e-10)
    # Robot at the shifted reference: nominal feedback pulls back, whereas
    # the reference adapter must retain a nonzero cancelling residual.
    evaluate = lambda z, v: 2.5*(-expected_offset+z)+v
    nominal = scale*evaluate(np.zeros(6), np.zeros(6))
    residual = ShiftedWBCResidual().compute(nominal, s, evaluate)
    assert residual[0] > .019
    np.testing.assert_allclose(nominal+residual, np.zeros(6), atol=1e-10)


def test_force_release_returns_offset_and_residual_to_zero():
    s = state()
    for _ in range(100):
        s.advance(np.ones(6), .04)
    for _ in range(250):
        s.advance(np.zeros(6), .04)
    np.testing.assert_allclose(s.offset, 0., atol=1e-10)
    residual = ShiftedWBCResidual().compute(np.zeros(6), s, lambda z, v: 2.5*z+v)
    np.testing.assert_allclose(residual, 0., atol=1e-10)


def test_rejects_mismatched_nominal_controller_instead_of_silent_adaptation():
    with pytest.raises(ValueError, match='scalar multiple'):
        ShiftedWBCResidual().compute(np.array([.01, .01, 0., 0., 0., 0.]), state(),
                                    lambda z, v: np.array([.02, 0., 0., 0., 0., 0.]))


@pytest.mark.parametrize('observation_size', [45, 48])
def test_post_mj_step_uses_same_robot_snapshot_without_relaxing_guard(observation_size):
    import mujoco
    from types import SimpleNamespace
    from fixed_panda_wbc import FixedBasePandaWBC
    from run_benchmark import so3_log
    from admittance_reference_core_20260923 import rotation_offset_and_jacobian
    from run_panel_admittance_reference_20260923 import ReferenceAdmittance

    xml = '<mujoco><option timestep="0.00005"/><worldbody>'
    for i in range(7):
        axis = ['1 0 0', '0 1 0', '0 0 1'][i % 3]
        xml += (f'<body name="link{i}" pos="0.1 0 0.05"><joint axis="{axis}"/>'
                '<geom type="sphere" size=".03" mass="1"/>')
    xml += '</body>'*7 + '</worldbody></mujoco>'
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    data.qpos[:] = np.linspace(.1, .7, 7)
    data.qvel[:] = np.linspace(.04, .28, 7)
    mujoco.mj_forward(model, data)
    hand = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'link6')
    wbc = FixedBasePandaWBC(model, hand, data.qpos.copy())
    target = data.xpos[hand].copy() + [.01, -.02, .01]
    rotation = data.xmat[hand].reshape(3, 3).copy()
    mujoco.mj_step(model, data)
    observation = np.zeros(observation_size)
    observation[:7], observation[7:14] = data.qpos, data.qvel
    observation[14:20] = .8*wbc.command(data, target, rotation, np.zeros(6)).task_twist_world
    observation[20:23] = target-data.xpos[hand]
    observation[23:26] = so3_log(rotation@data.xmat[hand].reshape(3, 3).T)

    fresh = mujoco.MjData(model)
    fresh.qpos[:] = data.qpos
    mujoco.mj_kinematics(model, fresh)
    mujoco.mj_comPos(model, fresh)
    fresh_rotation = rotation_offset_and_jacobian(observation[23:26])[0]@fresh.xmat[hand].reshape(3, 3)
    wrong_nominal = wbc.command(fresh, fresh.xpos[hand]+observation[20:23],
                                fresh_rotation, np.zeros(6)).task_twist_world
    scale = observation[14:20]@wrong_nominal/(wrong_nominal@wrong_nominal)
    # This is the original bug: SO(3) log/exp is valid but the Jacobian was
    # reconstructed at a different timestamp than the shared nominal command.
    assert np.linalg.norm(observation[14:20]-scale*wrong_nominal) > 1e-7
    env = SimpleNamespace(model=model, data=data, _hand_id=hand, fixed_wbc=wbc,
        safety_config=SimpleNamespace(maximum_linear_yield_mps=.32, maximum_angular_yield_radps=.8))
    cfg = SimpleNamespace(mass=1., inertia=.08, stiffness=900., rot_stiffness=45., zeta=1.)
    policy = ReferenceAdmittance(cfg, env, .04)
    q_before, xpos_before = data.qpos.copy(), data.xpos.copy()
    np.testing.assert_array_equal(policy.act(observation), np.zeros(7))
    assert abs(policy.mapper.scale-.8) < 1e-12
    assert policy.mapper.last_diagnostic['residual_norm'] < 1e-12
    np.testing.assert_array_equal(data.qpos, q_before)
    np.testing.assert_array_equal(data.xpos, xpos_before)
