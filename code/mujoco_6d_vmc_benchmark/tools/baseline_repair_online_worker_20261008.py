"""Extend native IPC telemetry with reward-only safety signals.

The observation/action path is unchanged. The template and exact instrumented
source are archived so the reward reducer can be independently replayed. The
optional SPT human-contact integrals never enter canonical48.
"""
from pathlib import Path
import hashlib
import research72_online_worker_20261003 as native


def main():
    template = Path(native.__file__)
    original = template.read_text()
    changes = [
        ("    def interval():",
         "    def measured_payload_potential(env):\n"
         "        if __import__('os').environ.get('SII_REWARD_PAYLOAD_TELEMETRY')!='1':return None\n"
         "        from payload_reward_potential_20261014 import payload_potential\n"
         "        return payload_potential(env.data.xpos[env._hand_id],env.data.xpos[env._target_body_id],env.reference.destination)\n"
         "    def interval():"),
        ("        return dict(elapsed_s=float(dt.sum()),error_integral=float(dt@e2),",
         "        signed_tau=arrays['qfrc_actuator'][begin:end].astype(float)\n"
         "        previous_tau=arrays['qfrc_actuator'][begin-1].astype(float) if begin else signed_tau[0]\n"
         "        rates=np.asarray(metrics.env.safety_config.maximum_torque_rate_nmps)\n"
         "        from audited_velocity_env import CONTROL_DT\n"
         "        from baseline_repair_reward_clock_20261009 import SERVO_DT,slew_cost_rows\n"
         "        assert CONTROL_DT==SERVO_DT\n"
         "        slew_cost=float(slew_cost_rows(signed_tau,rates,previous_tau).sum())\n"
         "        external_peak=float(metrics.research['external_penetration_m'][begin:end].max())\n"
         "        spt_contact=None\n"
         "        if __import__('os').environ.get('SII_SPT_REWARD_TELEMETRY')=='1':\n"
         "            from spt_rl_reward_20261025 import contact_integrals\n"
         "            spt_contact=contact_integrals(dt,signed_tau,limits,metrics.research['contact_force_sum'][begin:end,2])\n"
         "        return dict(spt_contact=spt_contact,payload_potential=measured_payload_potential(metrics.env),external_penetration_peak_m=external_peak,torque_slew_cost=slew_cost,elapsed_s=float(dt.sum()),error_integral=float(dt@e2),"),
        ("send(dict(kind='observation',observation=observation,interval=iv,potential=potential(self.env)))",
         "send(dict(kind='observation',observation=observation,interval=iv,potential=potential(self.env),payload_potential=measured_payload_potential(self.env)))"),
        ("            iv=interval();self.intervals.append(iv)",
         "            if not self.observations:\n"
         "                self.initial_potential=potential(self.env)\n"
         "                self.initial_payload_potential=measured_payload_potential(self.env)\n"
         "            iv=interval();self.intervals.append(iv)"),
        ("            worker.write(output/'RL_INTERVALS.json',self.intervals)",
         "            worker.write(output/'RL_INTERVALS.json',self.intervals)\n"
         "            worker.write(output/'RL_REWARD_METADATA.json',dict(initial_potential=self.initial_potential,initial_payload_potential=self.initial_payload_potential,"
         "torque_slew_definition='sum_recorded_changes servo_dt/horizon * sum_j ((tau_j-tau_prev_j)/(servo_dt*max_rate_j))**2; servo_dt=.004; first recorded sample excluded because no preceding sample exists',"
         "torque_slew_time_base='executed_motor_torque_changes_at_250Hz_not_physics_dt',"
         "actor_input_unchanged=True,template_sha256=TEMPLATE_SHA))"),
        ("    worker.EXTRA_SOURCE_FILES=[Path(__file__),Path(classical.__file__),Path(office.__file__)]",
         "    worker.EXTRA_SOURCE_FILES=[Path(__file__),TEMPLATE_PATH,Path(classical.__file__),Path(office.__file__)]"),
        ("            (out/'executed_evaluator.py.txt').write_text(executed_evaluator)",
         "            (out/'executed_online_worker.py.txt').write_text(EXECUTED_ONLINE_SOURCE)\n"
         "            (out/'executed_evaluator.py.txt').write_text(executed_evaluator)"),
    ]
    executed = original
    for old, new in changes:
        assert executed.count(old) == 1, old
        executed = executed.replace(old, new)
    native.__file__ = __file__
    native.TEMPLATE_PATH = template
    native.TEMPLATE_SHA = hashlib.sha256(original.encode()).hexdigest()
    native.EXECUTED_ONLINE_SOURCE = executed
    exec(compile(executed, str(template)+'[torque-slew-reward-telemetry]', 'exec'), native.__dict__)
    native.main()


if __name__ == '__main__':
    main()
