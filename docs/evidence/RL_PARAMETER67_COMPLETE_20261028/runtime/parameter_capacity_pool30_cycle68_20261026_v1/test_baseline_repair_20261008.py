"""Targeted numerical regressions for repaired controller contracts; no physics."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root/'scripts'), str(root/'tools')]
    with tempfile.TemporaryDirectory(prefix='sii-repair-contract-') as temporary:
        t = Path(temporary)
        shutil.copytree(a.parameter_source, t/'legacy')
        src = t/'legacy'
        if not (src/'controllers_legacy.py').exists():
            shutil.copy2(src/'controllers.py', src/'controllers_legacy.py')
        sys.path[:0] = [str(root/'tools'), str(src)]
        from baseline_repair_controllers_20261008 import ParameterController, ProjectedEquilibrium, DiskArrayLog
        # Exact archival values, without retaining one Python object per row.
        disk=DiskArrayLog(28)
        for i in range(10000):disk.append(np.arange(28,dtype=float)+i*.125)
        assert len(disk)==10000 and disk
        mapped=np.asarray(disk)
        assert isinstance(mapped.base,np.memmap)
        np.testing.assert_array_equal(mapped[[0,4999,9999]],np.arange(28)[None,:]+np.array([0,4999,9999])[:,None]*.125)
        np.savez_compressed(t/'disk_trace.npz',values=mapped)
        with np.load(t/'disk_trace.npz') as saved:np.testing.assert_array_equal(saved['values'],mapped)
        disk.close()
        from run_panel_impedance_reference_20260923 import ReferenceImpedanceConfig
        from wbc_velocity_residual_core import VelocityResidualSafetyConfig, VelocityResidualActionFilter
        priors = json.loads((src/'PRIORS.json').read_text())['methods']
        safety = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
        fake = SimpleNamespace(safety_config=safety)
        actor = ParameterController(fake, 'vmc', priors['vmc'])
        request = actor.actor.act(np.array([1., 1., 1., .1, .1, .1]), .04)
        expected = actor.actor.R6 @ (actor.actor.velocity_weight * actor.actor.velocity + actor.actor.offset_gain * actor.actor.offset)
        decoded = VelocityResidualActionFilter(safety).filter(request, .04)
        assert not decoded.slew_limited
        np.testing.assert_allclose(decoded.cartesian_yield_twist, expected, atol=1e-14)
        # Unit changes must not alter the simulated virtual plant parameters.
        theta = actor.shield.theta.copy()
        actor.apply(theta)
        np.testing.assert_array_equal(actor.actor.action_limits, [.32, .32, .32, .6, .6, .6])
        integrator = ProjectedEquilibrium(ReferenceImpedanceConfig())
        integrator.update(np.zeros(3), np.eye(3), np.zeros(6), .004)
        integrator.position = np.array([.04, 0., 0.])
        for _ in range(250):
            err, _ = integrator.update(np.zeros(3), np.eye(3), np.array([0., .05, 0., 0., 0., 0.]), .004)
            assert np.linalg.norm(err[:3]) <= .04+1e-12
        assert integrator.position[1] > .025
        for _ in range(100):
            err, _ = integrator.update(np.zeros(3), np.eye(3), np.array([0., 0., 0., 1., .5, 0.]), .004)
            assert np.linalg.norm(err[3:]) <= .2+1e-12
        import audited_velocity_env as backend
        original = backend.safe_velocity_tracking_torque
        jacobian = np.column_stack((np.eye(6), np.zeros(6)))
        fake.model = SimpleNamespace(dof_frictionloss=np.zeros(7))
        fake.data = SimpleNamespace(qpos=np.zeros(7), qvel=np.zeros(7),
            xpos=np.zeros((1, 3)), xmat=np.eye(3).reshape(1, 9), time=0.)
        fake._hand_id = 0
        try:
            with patch('run_benchmark.body_jacobian', return_value=jacobian), patch('run_benchmark.body_twist', return_value=np.zeros(6)):
                impedance = ParameterController(fake, 'impedance', priors['impedance'])
                previous = np.zeros(7)
                qdot = np.full(7, .1)
                torque_history = []
                for i in range(100):
                    fake.data.time = i*.004
                    applied, _ = backend.safe_velocity_tracking_torque(np.zeros(7), np.zeros(7), qdot,
                        previous, .004, safety, torque_limits=np.full(7, 2.))
                    assert np.max(abs(applied)) <= 2.+1e-12
                    assert np.all(abs(applied-previous) <= np.asarray(safety.maximum_torque_rate_nmps)*.004+1e-12)
                    previous = applied.copy(); torque_history.append(applied.copy())
                np.testing.assert_allclose(impedance.last_nominal, jacobian @ qdot)
                commands = np.asarray(impedance.repair_servo)[:, 15:22]
                assert np.max(abs(commands)) <= safety.maximum_joint_speed_radps+1e-12
                assert np.max(abs(np.diff(np.vstack((np.zeros(7), commands)), axis=0))) <= .004*safety.maximum_joint_acceleration_radps2+1e-12
        finally:
            backend.safe_velocity_tracking_torque = original
        result = dict(status='passed', physics_steps=0, vmc_physical_unit_max_abs=float(np.max(abs(decoded.cartesian_yield_twist-expected))),
            projected_tangential_displacement_m=float(integrator.position[1]),
            projected_position_rotation_bounds=True, impedance_consumes_limited_nominal=True,
            impedance_equivalent_command_speed_slew=True, impedance_torque_box_slew=True,
            disk_telemetry_float64_npz_exact=True, tested_controller_source=str(root/'tools/baseline_repair_controllers_20261008.py'))
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open('x') as f:
            json.dump(result, f, indent=2); f.write('\n')
        print(json.dumps(result))


if __name__ == '__main__':
    main()
