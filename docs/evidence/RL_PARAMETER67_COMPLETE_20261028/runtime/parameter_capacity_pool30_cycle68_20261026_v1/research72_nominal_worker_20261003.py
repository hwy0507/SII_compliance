"""Nominal shared planner/WBC with zero compliance action; unchanged world/gates.

This remains a feedback WBC, not an open-loop robot. It is a no-yield reference,
never a claim that planning alone has no tracking controller.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import numpy as np
import paper_classical_worker_20261002 as classical

office=classical.office
worker=office.worker


def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input',type=Path,required=True)
    p.add_argument('--physics-dt',type=float,default=.00005)
    a,rest=p.parse_known_args()
    out=Path(rest[rest.index('--output')+1]).resolve()
    class Policy:
        label='nominal shared planner/WBC, zero yield action'
        def __init__(self,env):
            self.obs=[]
        def act(self,obs):
            self.obs.append(obs.copy())
            return np.zeros(7)
        def finish(self,output):
            np.savez_compressed(output/'baseline_policy.npz',observation=np.asarray(self.obs),
                action=np.zeros((len(self.obs),7)))
            return dict(zero_compliance_action=True,shared_feedback_wbc=True)
    evaluator,_,_=classical.install_policy(None,None,{},out,policy_factory=Policy)
    constructor,_=office.install_binary(a.v6_input)
    expected,overrides,provenance=office.evaluation_settings(a.v6_input,a.physics_dt)
    worker.EXPECTED_MJB=expected
    worker.RUNTIME_ARGUMENT_OVERRIDES=dict(overrides,teacher='none')
    worker.EXTRA_SOURCE_FILES=[Path(__file__),Path(classical.__file__),Path(office.__file__)]
    worker.RUNTIME_PROVENANCE=dict(world='office-validation-v6',**provenance,
        nominal_zero_yield=True,shared_feedback_wbc=True,
        executed_evaluator_sha256=hashlib.sha256(evaluator.encode()).hexdigest(),
        executed_constructor_sha256=hashlib.sha256(constructor.encode()).hexdigest())
    office.instrument(out)
    def audit(run,config,checkpoint,ablation):
        assert checkpoint is None and ablation=='none'
        result=worker.audit(run,config,None,ablation,skip_actor_replay=True)
        with np.load(run/'baseline_policy.npz') as policy,np.load(run/'rollout.npz') as trace:
            np.testing.assert_array_equal(policy['observation'],trace['observation'])
            np.testing.assert_array_equal(policy['action'],trace['applied_action'])
            np.testing.assert_array_equal(trace['applied_action'],np.zeros_like(trace['applied_action']))
        result.update(action_replay_max_abs=0.,actor_replay_performed=True,nominal_zero_yield=True)
        worker.write(run/'AUDIT.json',result)
        return result
    worker.AUDIT_FUNCTION=audit
    sys.argv=[sys.argv[0],*rest]
    try:
        worker.main()
    finally:
        if out.exists():
            (out/'executed_evaluator.py.txt').write_text(evaluator)
            (out/'executed_fr3_scene.py.txt').write_text(constructor)


if __name__=='__main__':
    main()
