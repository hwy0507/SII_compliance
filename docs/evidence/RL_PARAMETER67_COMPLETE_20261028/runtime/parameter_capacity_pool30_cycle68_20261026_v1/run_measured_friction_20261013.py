"""One full frozen-ESN trial: same-tick control plus encoder-friction servo."""
from pathlib import Path
import os
import numpy as np
import run_rod_tick_repair_20261013 as tick
import audited_velocity_env as servo
from measured_friction_servo_20261013 import measured_friction


def main():
    assert os.environ.get('SII_CURRENT_FEEDBACK_TICK') == '1'
    worker = tick.base.prior.worker
    original_make = worker.evaluator.make
    original_main = worker.main
    original_audit = tick.base.audit
    original_servo = servo.safe_velocity_tracking_torque
    environments, rows = [], []

    def make(*args, **kwargs):
        env, task, spec = original_make(*args, **kwargs)
        environments.append(env)
        return env, task, spec

    def compensated(bias_torque, measured_joint_velocity, joint_velocity_command,
                    previous_torque, dt, config, torque_limits=None):
        assert len(environments) == 1
        env = environments[0]
        friction = env.model.dof_frictionloss[:7].copy()
        damping = env.model.dof_damping[:7].copy()
        correction = measured_friction(measured_joint_velocity, friction, damping)
        torque, scale = original_servo(bias_torque+correction, measured_joint_velocity,
            joint_velocity_command, previous_torque, dt, config, torque_limits)
        rows.append(dict(time_s=float(env.data.time), bias=bias_torque.copy(), correction=correction,
            measured=measured_joint_velocity.copy(), command=joint_velocity_command.copy(),
            previous_torque=previous_torque.copy(), applied_torque=torque.copy(),
            friction=friction, damping=damping, feasible_scale=scale))
        return torque, scale

    def audit(run, config, checkpoint, memory_ablation):
        result = original_audit(run, config, checkpoint, memory_ablation)
        env = environments[0]
        assert len(rows) == 13750
        for row in rows:
            correction = measured_friction(row['measured'], row['friction'], row['damping'])
            np.testing.assert_array_equal(correction, row['correction'])
            torque, scale = original_servo(row['bias']+correction, row['measured'], row['command'],
                row['previous_torque'], .004, env.safety_config, env.torque_limits)
            np.testing.assert_array_equal(torque, row['applied_torque'])
            assert scale == row['feasible_scale']
            assert np.all(abs(torque) <= env.torque_limits+1e-12)
            assert np.all(abs(torque-row['previous_torque']) <= np.array(env.safety_config.maximum_torque_rate_nmps)*.004+1e-12)
        target = run/'motor_friction_trace.npz'
        np.savez_compressed(target, **{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
        result.update(measured_motor_friction=True, motor_steps=len(rows),
            motor_torque_exact_replay=True, amplitude_and_slew_retained=True,
            motor_trace_sha256=worker.sha(target))
        worker.write(run/'AUDIT.json', result)
        return result

    def configured_main():
        worker.EXTRA_SOURCE_FILES += [Path(__file__), Path(__file__).with_name('measured_friction_servo_20261013.py')]
        worker.RUNTIME_PROVENANCE.update(
            purpose='Single frozen-ESN rod opposition repair candidate',
            only_runtime_difference='Same-tick baseline plus encoder-velocity model friction feedforward before unchanged torque projection',
            formula='frictionloss*tanh(measured_qvel/.005)+damping*measured_qvel',
            constants_origin='Robot model and existing JointLoadObserver velocity scale; no fitted parameters',
            no_contact_or_environment_state_used=True, no_actor_changes=True,
            experimental_common_servo=True, not_claimed_as_historical_restoration=True)
        original_main()

    worker.evaluator.make = make
    worker.main = configured_main
    servo.safe_velocity_tracking_torque = compensated
    tick.base.audit = audit
    tick.main()


if __name__ == '__main__':
    main()
