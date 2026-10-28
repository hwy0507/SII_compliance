"""Registered A/B: payload-aware path, then common servo interpolation."""
from pathlib import Path
import os,sys
import numpy as np
import run_old_office_reference_fix_20261013 as prior
from payload_clearance_reference_20261013 import PayloadClearanceReference
from servo_action_bridge_20261013 import ServoActionBridge

bridges=[]

class RecordedReference(PayloadClearanceReference):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);prior.instances.append(self)

def audit(run,config,checkpoint,memory_ablation):
    row=prior.audit(run,config,checkpoint,memory_ablation)
    ref=prior.instances[0];trace=np.array(ref.progress_records)
    delta=np.diff(np.r_[0.,trace[:,0]])
    assert np.all(delta>=-1e-12) and np.all(delta<=.06*.04+1e-12)
    targets=np.vstack([ref.carry_route[0],trace[:,5:8]])
    np.testing.assert_allclose(trace[:,2:5],np.diff(targets,axis=0)/.04,atol=1e-12)
    row.update(changed_component='known-map payload clearance common path',reference_derivative_audited=True,
               servo_interpolation=bool(bridges))
    if bridges:
        rows=bridges[0].rows
        np.savez_compressed(run/'servo_actions.npz',**{k:np.array([r[k] for r in rows]) for k in rows[0]})
        with np.load(run/'servo_actions.npz') as z,np.load(run/'execution_chain.npz') as c:
            fraction=z['fraction']
            assert len(fraction)==10*len(c['requested_action'])
            np.testing.assert_allclose(z['yield_twist'],(1-fraction[:,None])*z['start_twist']+fraction[:,None]*z['target_twist'],atol=1e-15)
            np.testing.assert_array_equal(z['yield_twist'][9::10],c['yield_twist'])
            np.testing.assert_array_equal(z['wbc_scale'][9::10],c['wbc_scale'])
            assert np.max(abs(np.diff(z['yield_twist'][:,:3],axis=0)))<=1.2*.004+1e-12
        row.update(servo_actions_sha256=prior.worker.sha(run/'servo_actions.npz'),servo_interpolation_replay=True)
    prior.worker.write(run/'AUDIT.json',row)
    return row

def main():
    worker=prior.worker;original_main=worker.main;original_make=worker.evaluator.make
    enabled=os.environ.get('SII_SERVO_INTERPOLATION')=='1'
    def configured_main():
        def make(*args,**kwargs):
            env,task,spec=original_make(*args,**kwargs)
            RecordedReference.environment=env
            if enabled:
                bridge=ServoActionBridge(env);bridges.append(bridge);env._physics_step=bridge
            return env,task,spec
        worker.evaluator.make=make;worker.evaluator.PickPlaceTask=RecordedReference
        worker.AUDIT_FUNCTION=audit
        worker.EXTRA_SOURCE_FILES += [Path(__file__),Path(prior.__file__),
            Path(__file__).with_name('payload_clearance_reference_20261013.py'),
            Path(__file__).with_name('servo_action_bridge_20261013.py'),
            Path(__file__).with_name('old_office_waypoint_reference_20261013.py')]
        worker.RUNTIME_PROVENANCE.update(purpose='Registered frozen-ESN payload path/servo A-B repair',
            common_path='initial known map, payload half-size+existing12mm arrival tolerance+existing2mm planner clearance',
            servo_interpolation=enabled,servo_interpolation_period_s=.04 if enabled else None,
            no_esn_parameters_changed=True,online_obstacle_input_to_actor=False)
        try:original_main()
        finally:
            output=Path(sys.argv[sys.argv.index('--output')+1])
            if output.exists() and prior.instances:worker.write(output/'reference.json',prior.instances[0].metadata())
    worker.main=configured_main;prior.transfer.main()

if __name__=='__main__':main()
