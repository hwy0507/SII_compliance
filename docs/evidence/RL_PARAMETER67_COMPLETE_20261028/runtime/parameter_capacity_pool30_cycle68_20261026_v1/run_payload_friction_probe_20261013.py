"""One additional common-servo experiment after the registered path A/B.

Known joint friction feedforward, not contact-force compensation or ESN tuning.
This is a new execution option; historical/fair-comparison runtimes stay intact.
"""
from pathlib import Path
import numpy as np
import run_payload_bridge_20261013 as base
import audited_velocity_env as servo


def friction_feedforward(command, measured, friction, damping, velocity_scale=.005):
    return friction * np.tanh(command / velocity_scale) + damping * measured


def main():
    worker=base.prior.worker
    original_main=worker.main
    original_servo=servo.safe_velocity_tracking_torque
    original_audit=base.audit
    rows=[]

    def compensated(bias_torque, measured_joint_velocity, joint_velocity_command,
                    previous_torque, dt, config, torque_limits=None):
        env=base.RecordedReference.environment
        # Robot model coefficients and encoder/command velocities only. Never
        # read qfrc_constraint, contacts, object state or task/event identity.
        friction=env.model.dof_frictionloss[:7].copy()
        damping=env.model.dof_damping[:7].copy()
        correction=friction_feedforward(joint_velocity_command,measured_joint_velocity,friction,damping)
        torque,scale=original_servo(bias_torque+correction,measured_joint_velocity,
            joint_velocity_command,previous_torque,dt,config,torque_limits)
        rows.append(dict(bias=bias_torque.copy(),correction=correction.copy(),
            measured=measured_joint_velocity.copy(),command=joint_velocity_command.copy(),
            previous_torque=previous_torque.copy(),applied_torque=torque.copy(),
            friction=friction,damping=damping,feasible_scale=scale))
        return torque,scale

    def audit(run,config,checkpoint,memory_ablation):
        row=original_audit(run,config,checkpoint,memory_ablation)
        env=base.RecordedReference.environment
        for r in rows:
            correction=friction_feedforward(r['command'],r['measured'],r['friction'],r['damping'])
            np.testing.assert_array_equal(correction,r['correction'])
            torque,scale=original_servo(r['bias']+correction,r['measured'],r['command'],
                r['previous_torque'],.004,env.safety_config,env.torque_limits)
            np.testing.assert_array_equal(torque,r['applied_torque'])
            assert scale==r['feasible_scale']
            assert np.all(abs(torque)<=env.torque_limits+1e-12)
            assert np.all(abs(torque-r['previous_torque'])<=np.array(env.safety_config.maximum_torque_rate_nmps)*.004+1e-12)
        target=run/'friction_servo.npz'
        np.savez_compressed(target,**{k:np.array([r[k] for r in rows]) for k in rows[0]})
        row.update(common_friction_feedforward=True,friction_servo_steps=len(rows),
            friction_servo_sha256=worker.sha(target),torque_composition_replay_exact=True,
            torque_amplitude_and_slew_audit=True)
        worker.write(run/'AUDIT.json',row)
        return row

    def configured_main():
        worker.EXTRA_SOURCE_FILES.append(Path(__file__))
        worker.RUNTIME_PROVENANCE.update(common_friction_feedforward=True,
            common_friction_formula='known frictionloss*tanh(command/.005)+known damping*encoder_velocity',
            friction_velocity_scale_origin='existing observer .005 rad/s, not fit to this rollout',
            supplementary_run_reason='A has scale1, negligible ESN residual, large nominal/measured velocity deficit near joint stiction',
            scope='New common servo option, not claimed as restoration of historical runtime')
        original_main()
    worker.main=configured_main
    servo.safe_velocity_tracking_torque=compensated
    base.audit=audit
    base.main()


if __name__=='__main__':main()
