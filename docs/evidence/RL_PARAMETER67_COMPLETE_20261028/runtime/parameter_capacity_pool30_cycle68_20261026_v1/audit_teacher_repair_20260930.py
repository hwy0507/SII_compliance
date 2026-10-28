"""Independent stage-resolved replay, execution-chain and stability audit."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'outputs/teacher_repair_20260930'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--folder',type=Path,required=True)
    a=parser.parse_args();folder=a.folder.resolve()
    global CAMPAIGN
    CAMPAIGN=folder.parent.parent
    plan=json.loads((CAMPAIGN/'plan.json').read_text())
    for name, expected in plan['sources'].items():
        assert sha(CAMPAIGN/'source'/name)==expected, name
    sys.path.insert(0,str(CAMPAIGN/'source/scripts'))
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig
    result=json.loads((folder/'rollout.json').read_text())
    actor=StableReadoutTeacher(**plan['candidates'][folder.name])
    filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
    maxima={}
    def check(name,left,right):
        error=float(np.max(np.abs(np.asarray(left,dtype=float)-np.asarray(right,dtype=float))))
        maxima[name]=max(error,maxima.get(name,0.))
        if error>1e-12: raise AssertionError((name,error))
    with np.load(folder/'rollout.npz') as z, np.load(folder/'teacher_internal.npz') as internal, np.load(folder/'execution_chain.npz') as chain:
        count=len(z['applied_action'])
        assert count==len(internal['wrench'])==len(chain['submitted_action'])==1375
        for i,obs in enumerate(z['observation']):
            w=obs[39:45];action=actor.act(w)
            check('wrench',w,internal['wrench'][i])
            check('requested_action',action,z['applied_action'][i])
            check('teacher_request',action,internal['requested_action'][i])
            check('effective_wrench',actor.effective_wrench,internal['effective_wrench'][i])
            check('original_readout',actor.raw_action,internal['original_readout'][i])
            for key,attr in [('offset','offset'),('velocity','velocity'),('filtered_wrench','filtered')]:
                check(key,getattr(actor,attr),internal[key][i])
            check('submitted_action',action,chain['submitted_action'][i])
            output=filt.filter(action,.04)
            for key,attr in [('clipped_action','raw_action_clipped'),('yield_twist','cartesian_yield_twist'),('wbc_scale','wbc_scale'),('slew_limited','slew_limited')]:
                check(key,getattr(output,attr),chain[key][i])
        stages={}
        for stage in np.unique(z['stage']):
            mask=z['stage']==stage;actions=z['applied_action'][mask,1:]
            stages[str(int(stage))]=dict(samples=int(mask.sum()),
                start_s=float(z['neuron_time'][mask][0]),end_s=float(z['time'][mask][-1]),
                action_delta_rms=float(np.sqrt(np.mean(np.diff(actions,axis=0)**2))) if len(actions)>1 else 0.,
                action_delta_max=float(np.max(np.abs(np.diff(actions,axis=0)))) if len(actions)>1 else 0.,
                best_position_error_m=float(np.min(z['task_position_error_m'][mask])),
                final_position_error_m=float(z['task_position_error_m'][mask][-1]))
    with np.load(folder/'rollout_metrics/substep_metrics.npz') as z:
        dt=z['dt'].astype(float);error=z['error'].astype(float)
        rmse=float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum()))
        torque=float(np.abs(z['qfrc_actuator']).max())
        speed=np.linalg.norm(z['twist'][:,:3].astype(float),axis=1)
        peak=float(speed.max())
        for stage,row in stages.items():
            mask=z['stage']==int(stage)
            row.update(physical_speed_peak_mps=float(speed[mask].max()),
                       physical_speed_rms_mps=float(np.sqrt(np.sum(speed[mask]**2*dt[mask])/dt[mask].sum())))
    np.testing.assert_allclose([rmse,torque,peak],[result['metrics'][k] for k in ['position_rmse_3d_m','generalized_actuator_torque_peak_nm','linear_speed_peak_mps']],rtol=2e-7,atol=1e-8)
    assert sha(folder/'rollout.mjb')==result['model_sha256']
    report=dict(replay_passed=True,max_abs_error=maxima,stages=stages,
        task=result['task_success'],strict=result['strict_success'],
        independent_waypoint_rmse_m=rmse,independent_peak_torque_nm=torque,independent_peak_speed_mps=peak,
        penetration_mm=1000*result['stats']['max_external_penetration_m'],
        source_manifest_sha256=sha(CAMPAIGN/'plan.json'), audit_source_sha256=sha(Path(__file__)),
        input_sha256={p.name:sha(p) for p in [folder/'rollout.npz',folder/'teacher_internal.npz',folder/'execution_chain.npz']},
        limitation='Paired development simulation and replay; does not establish real hardware stability or generalization.')
    out=folder/'independent_audit.json'
    if out.exists():raise FileExistsError(out)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['stages','input_sha256']},indent=2))


if __name__=='__main__':main()
