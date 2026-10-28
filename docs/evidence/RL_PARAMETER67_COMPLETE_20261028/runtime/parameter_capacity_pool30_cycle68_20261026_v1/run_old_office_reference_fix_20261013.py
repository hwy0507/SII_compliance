"""One registered frozen-weight episode with the common carry-reference fix."""
import json
from pathlib import Path
import sys
import numpy as np
import transfer_original_esn_old_office_20261013 as transfer
from old_office_waypoint_reference_20261013 import LocalCarryReference

worker=transfer.worker
instances=[]


class RecordedReference(LocalCarryReference):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        instances.append(self)


def audit(run, config, checkpoint, memory_ablation):
    row=transfer.audit(run,config,checkpoint,memory_ablation)
    previous=worker.ROOT/'outputs/original_esn_old_office_transfer_20261013/episode_v2'
    now=json.loads((run/'rollout.json').read_text())
    before=json.loads((previous/'rollout.json').read_text())
    for key in ('placement_destination','placement_support_geoms','schedule','observer_settings','contact_required','physics_resolution'):
        assert now[key]==before[key],key
    for key in ('seed','variant','duration','dt','ball_speed','ball_launch_time_s','person_start','person_stroke','rod_start','rod_hold','rod_stroke'):
        assert now['arguments'][key]==before['arguments'][key],key
    assert len(instances)==1
    task=instances[0]
    for stage in (0,1,2,3,5,6,7):
        np.testing.assert_array_equal(task.goals[stage],task.original_goals[stage])
    np.testing.assert_array_equal(task.carry_route[-1],task.original_goals[4])
    worker.write(run/'reference.json',task.metadata())
    with np.load(run/'rollout.npz') as z,np.load(run/'execution_chain.npz') as c:
        t=z['neuron_time'];o=z['observation'];mask=(t>=11.48-1e-7)&(t<16.68-1e-7)
        x=c['requested_action'][mask,1]
        row['diagnostic_11_48_16_68']=dict(frames=int(mask.sum()),
            x_request_sign_flips=int(np.sum(x[1:]*x[:-1]<0)),x_request_saturation_fraction=float(np.mean(abs(x)>=1-1e-8)),
            y_error_mean_m=float(o[mask,21].mean()),y_feature_saturation_fraction=float(np.mean(abs(o[mask,21])>=.32)))
    row.update(original_environment_checkpoint_schedule_destination_gates_retained=True,
        changed_component='common carry reference only',reference_sha256=worker.sha(run/'reference.json'))
    worker.write(run/'AUDIT.json',row)
    return row


def main():
    original_main=worker.main
    def configured_main():
        worker.evaluator.PickPlaceTask=RecordedReference
        worker.AUDIT_FUNCTION=audit
        worker.EXTRA_SOURCE_FILES += [Path(__file__),Path(__file__).with_name('old_office_waypoint_reference_20261013.py')]
        worker.RUNTIME_PROVENANCE.update(
            purpose='Frozen original ESN; common carry-reference alignment on unchanged old office',
            changed_component='policy-independent carry waypoint reference',
            reference_rule='Existing densify .01m; reached .012m/orientation .12rad; original deployed forward-plane/lateral<.08m rejoin',
            no_checkpoint_or_scaling_changes=True, prior_run='original_esn_old_office_transfer_20261013/episode_v2')
        try:
            original_main()
        finally:
            output=Path(sys.argv[sys.argv.index('--output')+1])
            if output.exists() and instances:
                worker.write(output/'reference.json',instances[0].metadata())
    worker.main=configured_main
    transfer.main()


if __name__=='__main__':main()
