"""Extend native IPC telemetry with true torque-slew cost and initial potential.

The observation/action path is unchanged. The template and exact instrumented
source are archived so the new reward reducer can be independently replayed.
"""
from pathlib import Path
import hashlib
import research72_online_worker_20261003 as native


def main():
    template = Path(native.__file__)
    original = template.read_text()
    changes = [
        ("        return dict(elapsed_s=float(dt.sum()),error_integral=float(dt@e2),",
         "        signed_tau=arrays['qfrc_actuator'][begin:end].astype(float)\n"
         "        previous_tau=arrays['qfrc_actuator'][begin-1].astype(float) if begin else np.zeros(7)\n"
         "        changes=np.diff(np.vstack((previous_tau,signed_tau)),axis=0)\n"
         "        rates=np.asarray(metrics.env.safety_config.maximum_torque_rate_nmps)\n"
         "        slew_ratio=changes/(dt[:,None]*rates[None,:])\n"
         "        slew_cost=float(dt@np.sum(slew_ratio**2,axis=1)/55.)\n"
         "        return dict(torque_slew_cost=slew_cost,elapsed_s=float(dt.sum()),error_integral=float(dt@e2),"),
        ("            iv=interval();self.intervals.append(iv)",
         "            if not self.observations:self.initial_potential=potential(self.env)\n"
         "            iv=interval();self.intervals.append(iv)"),
        ("            worker.write(output/'RL_INTERVALS.json',self.intervals)",
         "            worker.write(output/'RL_INTERVALS.json',self.intervals)\n"
         "            worker.write(output/'RL_REWARD_METADATA.json',dict(initial_potential=self.initial_potential,"
         "torque_slew_definition='sum_physics dt/horizon * sum_j ((tau_j-tau_prev_j)/(dt*max_rate_j))**2',"
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
