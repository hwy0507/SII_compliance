"""Replay parameter shielding and inspect native impedance servo limits.

Uses saved virtual states as inputs to the shield; this does not independently
reconstruct those states or establish robot passivity. Native equivalent-command
bounds are distinct from measured physical joint speed and task success.
"""
import argparse
import copy
from pathlib import Path
import sys
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    sys.path[:0] = [str(a.parameter_source), str(Path(__file__).resolve().parents[1]/'scripts')]
    from controllers import ParameterShield
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig
    repair = read(a.run/'CONTROLLER_REPAIR.json'); method = repair['controller']
    prior = copy.deepcopy(read(a.parameter_source/'PRIORS.json')['methods'][method])
    prior['center'] = repair['prior']
    shield = ParameterShield(method, prior)
    records = read(a.run/'parameter_trace.json')
    errors = {}
    for record in records:
        shield.update(record['raw_action'], record['offset'], record['velocity'])
        actual = shield.records[-1]
        assert set(actual) == set(record)
        for key in record:
            if isinstance(record[key], str):
                assert actual[key] == record[key], (key, actual[key], record[key])
                continue
            error = float(np.max(np.abs(np.asarray(actual[key])-np.asarray(record[key]))))
            errors[key] = max(errors.get(key, 0.), error)
    assert max(errors.values()) < 1e-10, errors
    files = [a.run/'CONTROLLER_REPAIR.json', a.run/'parameter_trace.json',
             a.parameter_source/'PRIORS.json', a.parameter_source/'controllers_legacy.py', Path(__file__)]
    files += [a.parameter_source/name for name in ('controllers.py',
        'baseline_repair_controllers_20261008.py', 'baseline_fullrange_controllers_20261009.py')
        if (a.parameter_source/name).exists()]
    result = dict(status='passed', created_utc=now(), method=method, updates=len(records),
        shield_replay_max_abs=errors, new_physics_steps=0,
        limitation='Shield recurrence replay uses recorded virtual offset/velocity as inputs. '
                   'It is not an independent physical state replay or global passivity proof.')
    if method == 'impedance':
        safety = VelocityResidualSafetyConfig()
        paths = [a.run/'impedance_servo.npz', a.run/'impedance_repair_servo.npz']
        files += paths
        with np.load(paths[0]) as f: servo = f['values']
        with np.load(paths[1]) as f: repair_servo = f['values']
        assert servo.shape == (len(repair_servo), 28) and repair_servo.shape[1] == 36
        np.testing.assert_array_equal(servo[:, 0], repair_servo[:, 0])
        assert np.isfinite(servo).all() and np.isfinite(repair_servo).all()
        dt = np.diff(servo[:, 0]); assert np.all(dt > 0)
        command = repair_servo[:, 15:22]
        actual = servo[:, 20:27]
        rates = np.asarray(safety.maximum_torque_rate_nmps)
        acceleration = np.max(abs(np.diff(command, axis=0))/dt[:, None])
        slew_ratio = np.max(abs(np.diff(actual, axis=0))/(dt[:, None]*rates))
        max_command = float(abs(command).max())
        assert max_command <= safety.maximum_joint_speed_radps+1e-10
        assert acceleration <= safety.maximum_joint_acceleration_radps2+1e-6
        assert slew_ratio <= 1.+1e-6
        spring_position = float(np.linalg.norm(servo[:, 1:4], axis=1).max())
        spring_rotation = float(np.linalg.norm(servo[:, 4:7], axis=1).max())
        assert spring_position <= .04+1e-10 and spring_rotation <= .2+1e-10
        result['native_servo'] = dict(rows=len(servo), max_equivalent_command_radps=max_command,
            max_equivalent_command_acceleration_radps2=float(acceleration),
            max_applied_torque_slew_ratio=float(slew_ratio),
            max_spring_position_m=spring_position, max_spring_rotation_rad=spring_rotation,
            first_torque_difference='Not evaluated: no recorded preceding actuator torque',
            limitation='Checks logged controller output and equivalent commands; actual physical torque/speed have separate substep audits.')
    result['evidence'] = {str(f):sha(f) for f in files}
    write(a.output, result)
    print(result['method'], result.get('native_servo', {}), flush=True)


if __name__ == '__main__': main()
