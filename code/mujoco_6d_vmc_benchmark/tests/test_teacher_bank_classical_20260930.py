"""Physical controller distinction and audit integrity without MuJoCo rollouts."""
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tools'))
from teacher_bank_classical_20260930 import (decode, physical_vectors,
    configure_environment, replay_admittance, replay_impedance, SEARCH_DIMENSIONS)


@pytest.mark.parametrize('method', ['admittance', 'impedance'])
def test_physical_search_bounds_and_no_safety_parameters(method):
    dimensions = SEARCH_DIMENSIONS[method]
    for point in (np.zeros(dimensions), np.ones(dimensions), np.full(dimensions, .5)):
        config = decode(point, method)
        mass, stiffness, damping = physical_vectors(config)
        assert len(config) == 7
        assert np.all(mass > 0) and np.all(stiffness > 0) and np.all(damping > 0)
        assert stiffness[0] == stiffness[1]
        assert stiffness[2] / stiffness[0] == config['vertical_stiffness_ratio']
        assert not any('limit' in key or 'gate' in key for key in config)
        if method == 'impedance':
            assert config['mass'] == .5 and config['inertia'] == .06
    for bad in ([0] * (dimensions - 1), [2] * dimensions, [float('nan')] * dimensions):
        with pytest.raises(ValueError):
            decode(bad, method)


def test_admittance_replay_detects_corrupted_state():
    from admittance_reference_core_20260923 import AdmittanceState
    cfg = decode(np.full(7, .5), 'admittance')
    mass, k, damping = physical_vectors(cfg)
    state = AdmittanceState(mass, k)
    state.d = damping
    rows = []
    for i in range(12):
        wrench = np.array([i, 0, -2, 0, .2, 0.])
        effective = state.advance(wrench, .04)
        residual = np.r_[state.velocity[:3], state.velocity[3:]]
        units = np.array([.32] * 3 + [.6] * 3)
        rows.append(dict(wrench=wrench, effective_wrench=effective.copy(), offset=state.offset.copy(),
            velocity=state.velocity.copy(), requested_residual=residual.copy(), action_units=units,
            request=np.r_[0., np.clip(residual / units, -1, 1)]))
    assert replay_admittance(cfg, rows)['max_abs'] == 0
    rows[5]['offset'][0] += .001
    assert replay_admittance(cfg, rows)['max_abs'] >= .000999
    rows[5]['offset'][0] = np.nan
    with pytest.raises(ValueError, match='finite'):
        replay_admittance(cfg, rows)
    rows[5]['offset'] = np.zeros(5)
    with pytest.raises(ValueError, match='shape'):
        replay_admittance(cfg, rows)


def test_impedance_is_real_torque_not_vmc_and_restores_backend(monkeypatch):
    import run_benchmark
    import audited_velocity_env as velocity_env
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig
    safety = VelocityResidualSafetyConfig()
    jacobian = np.c_[np.eye(6), np.zeros(6)]
    monkeypatch.setattr(run_benchmark, 'body_jacobian', lambda *args: jacobian)
    monkeypatch.setattr(run_benchmark, 'body_twist', lambda *args: np.zeros(6))
    data = SimpleNamespace(time=0., xpos=np.zeros((1, 3)), xmat=np.eye(3).reshape(1, 9))
    command = SimpleNamespace(task_twist_world=np.array([.1, 0, 0, 0, 0, 0.]))
    env = SimpleNamespace(execution_mode='twist', model=object(), data=data, _hand_id=0,
        _wbc_command=lambda t: command, torque_limits=np.full(7, 87.))
    original = velocity_env.safe_velocity_tracking_torque
    records = []
    cfg = decode(np.full(5, .5), 'impedance')
    actor = configure_environment(env, cfg, 'impedance', records)
    try:
        np.testing.assert_array_equal(actor.act(np.zeros(48)), np.zeros(7))
        with pytest.raises(ValueError):
            actor.act(np.zeros(6))
        previous = np.zeros(7)
        for i in range(5):
            data.time = i * .004
            env._wbc_command(data.time)
            previous, _ = velocity_env.safe_velocity_tracking_torque(np.zeros(7), np.zeros(7),
                np.zeros(7), previous, .004, safety, torque_limits=env.torque_limits)
        assert previous[0] > 0  # zero action7 nevertheless produces true impedance torque
        result = replay_impedance(cfg, actor.servo_records, safety)
        assert result['max_abs'] == 0
        actor.servo_records[2]['applied_torque'][0] += .1
        assert replay_impedance(cfg, actor.servo_records, safety)['max_abs'] > .09
        actor.servo_records[2]['applied_torque'][0] = np.nan
        with pytest.raises(ValueError, match='finite'):
            replay_impedance(cfg, actor.servo_records, safety)
        actor.servo_records[2]['applied_torque'] = np.zeros(6)
        with pytest.raises(ValueError, match='shape'):
            replay_impedance(cfg, actor.servo_records, safety)
    finally:
        actor.close()
    assert velocity_env.safe_velocity_tracking_torque is original


def test_servo_hold_mapping_uses_physics_interval_start_at_boundary():
    from teacher_bank_rollout_20260930 import audit_impedance_execution
    servo = dict(time=np.array([0., .004]), dt=np.array([.004, .004]),
                 applied_torque=np.array([[1.123456789] * 7, [2.123456789] * 7]))
    physics = dict(time=np.arange(1, 9) * .001, dt=np.full(8, .001),
        qfrc_actuator=np.repeat(servo['applied_torque'], 4, axis=0).astype(np.float32))
    result = audit_impedance_execution(servo, physics)
    assert result['max_abs_nm'] == 0
    assert result['samples_per_hold_min'] == result['samples_per_hold_max'] == 4
    # The sample ENDING at .004 still belongs to command 0, not command 1.
    physics['qfrc_actuator'][3] = servo['applied_torque'][1]
    with pytest.raises(AssertionError):
        audit_impedance_execution(servo, physics)
    physics['qfrc_actuator'][3] = np.nan
    with pytest.raises(AssertionError, match='Nonfinite'):
        audit_impedance_execution(servo, physics)


def test_direct_arm_mapping_rejects_changed_gear_and_dof_order():
    from teacher_bank_rollout_20260930 import direct_arm_mapping
    gear = np.zeros((7, 6));gear[:, 0] = 1
    model = SimpleNamespace(nu=7, actuator_trnid=np.c_[np.arange(7), -np.ones(7)].astype(int),
        jnt_dofadr=np.arange(7), actuator_trntype=np.zeros(7), actuator_gaintype=np.zeros(7),
        actuator_biastype=np.zeros(7), actuator_dyntype=np.zeros(7), actuator_gear=gear,
        actuator_gainprm=np.ones((7, 10)))
    assert direct_arm_mapping(model)['generalized_dof_indices'] == list(range(7))
    model.actuator_gear[0, 0] = 2
    with pytest.raises(AssertionError):
        direct_arm_mapping(model)
    model.actuator_gear[0, 0] = 1
    model.jnt_dofadr = np.arange(7)[::-1]
    with pytest.raises(AssertionError, match='mapping'):
        direct_arm_mapping(model)


@pytest.mark.parametrize('method', ['admittance', 'impedance'])
def test_real_evaluator_classical_adapter_static_smoke(method):
    import validate_office_apparatus_v5_20260917 as evaluator
    from teacher_bank_rollout_20260930 import adapted_run, controller_contract
    isolated = SimpleNamespace(run=evaluator.run, __file__=evaluator.__file__)
    adapted_run(isolated, method)  # Compile real source; do not create a model or run it.
    assert isolated.run is not evaluator.run
    contract = controller_contract(method)
    assert contract['method'] == method
    assert 'wrench[39:45] only' not in contract['input_contract']
    if method == 'impedance':
        assert 'torque backend' in contract['control_location']


def test_npz_columns_are_decompressed_once_before_many_row_replays():
    from teacher_bank_rollout_20260930 import materialize_npz, column_rows

    class ReadOnceArchive:
        files = ('time', 'torque')
        def __init__(self):
            self.reads = {key: 0 for key in self.files}
        def __getitem__(self, key):
            self.reads[key] += 1
            if self.reads[key] > 1:
                raise AssertionError('Repeated whole-column decompression')
            return np.arange(1000.) if key == 'time' else np.ones((1000, 7))

    archive = ReadOnceArchive()
    columns = materialize_npz(archive)
    for _ in range(2):  # Servo replay and physical execution audit reuse columns.
        count = 0
        for row in column_rows(columns):
            assert np.shares_memory(row['torque'], columns['torque'])
            assert row['time'] == count
            count += 1
        assert count == 1000
    assert archive.reads == {'time': 1, 'torque': 1}
    with pytest.raises(ValueError, match='lengths'):
        list(column_rows({'a': np.zeros(2), 'b': np.zeros(3)}))
