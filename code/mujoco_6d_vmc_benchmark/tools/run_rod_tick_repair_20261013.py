"""One arm of a frozen-ESN common feedback-timing paired check."""
from pathlib import Path
import os
import numpy as np
import run_continuous_old_office_20261013 as base
from feedback_tick_contract_20261013 import FeedbackTickContract,audit_scale_trace


def main():
    worker=base.prior.worker;original_main=worker.main;original_make=worker.evaluator.make
    original_audit=base.audit;tracers=[];fix=os.environ.get('SII_CURRENT_FEEDBACK_TICK')=='1'
    def make(*a,**k):
        env,task,spec=original_make(*a,**k)
        tracer=FeedbackTickContract(env,fix=fix);tracer.install();tracers.append(tracer)
        return env,task,spec
    def audit(run,config,checkpoint,memory_ablation):
        result=original_audit(run,config,checkpoint,memory_ablation)
        assert len(tracers)==1
        values={k:np.array([r[k] for r in tracers[0].rows]) for k in tracers[0].rows[0]}
        np.savez_compressed(run/'servo_tick_trace.npz',**values)
        with np.load(run/'execution_chain.npz') as chain:
            result['feedback_tick_contract']=audit_scale_trace(values,chain,fix)
        result['servo_tick_trace_sha256']=worker.sha(run/'servo_tick_trace.npz')
        result['common_feedback_timing_fix']=fix
        worker.write(run/'AUDIT.json',result)
        return result
    def configured_main():
        worker.evaluator.make=make
        worker.EXTRA_SOURCE_FILES += [Path(__file__),Path(__file__).with_name('feedback_tick_contract_20261013.py')]
        worker.RUNTIME_PROVENANCE.update(current_feedback_tick=fix,
            only_runtime_difference='Latch current filtered feedback scale before WBC servo consumption; no interpolation or friction feedforward',
            no_esn_parameter_changes=True,no_environment_or_gate_changes=True)
        original_main()
    worker.main=configured_main;base.audit=audit;base.main()


if __name__=='__main__':main()
