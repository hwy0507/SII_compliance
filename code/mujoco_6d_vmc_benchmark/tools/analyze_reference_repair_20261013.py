"""Compare fixed-weight reference trials and original deployment/training scope."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'outputs/original_esn_continuous_reference_20261013'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def summarize(path):
    r=read(path/'rollout.json')
    with np.load(path/'rollout.npz') as z, np.load(path/'execution_chain.npz') as c:
        o=z['observation'];t=z['neuron_time'];actual=o[:,14:17]-o[:,26:29]
        windows=[]
        for lo,hi in [(11.48,16.68),(20.,30.),(30.,55.)]:
            m=(t>=lo-1e-7)&(t<hi-1e-7);x=c['requested_action'][m,1]
            windows.append(dict(start_s=lo,end_s=hi,frames=int(m.sum()),
                request_x_flips=int(np.sum(x[:-1]*x[1:]<0)),
                request_x_saturation=float(np.mean(abs(x)>=1.-1e-8)),
                actual_velocity_step_rms_mps=np.sqrt(np.mean(np.diff(actual[m],axis=0)**2,axis=0)).tolist(),
                nominal_xyz_mean_mps=o[m,14:17].mean(0).tolist(),
                filtered_xyz_mean_mps=c['yield_twist'][m,:3].mean(0).tolist(),
                actual_xyz_mean_mps=actual[m].mean(0).tolist(),
                error_xyz_mean_m=o[m,20:23].mean(0).tolist()))
        carry=z['stage']==4
        obs_summary=dict(path_y_range=[float(o[:,46].min()),float(o[:,46].max())],
            carry_positive_y_fraction=float(np.mean(o[carry,46]>.1)),
            carry_duration_s=float(carry.sum()*.04),
            carry_start_hand=z['hand'][np.flatnonzero(carry)[0]].tolist(),
            carry_last_hand=z['hand'][np.flatnonzero(carry)[-1]].tolist())
    plan=r.get('path_plan')
    plan_summary=None
    if plan:
        points=np.array([x['hand'] for x in plan['routes']['4']])
        plan_summary=dict(carry_length_m=float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()),
            start=points[0].tolist(),end=points[-1].tolist(),tilt_degrees=plan['tilt_degrees'])
    return dict(task=r['task_success'],strict=r['strict_success'],stage=r['final_task_stage'],
        metrics=r['metrics'],events=r['task_events'],contacts=r['stats']['events'],
        external_penetration_mm=r['stats']['max_external_penetration_m']*1000,
        destination=r['placement_destination'],plan=plan_summary,
        observation=obs_summary,windows=windows,
        hashes={k:sha(path/k) for k in ['rollout.json','rollout.npz','checkpoint.npz','rollout.mjb','execution.json']})


def main():
    data=ROOT/'outputs/research72_20261003_1149/demonstrations_refined_v1/training_data.npz'
    meta=read(ROOT/'outputs/research72_20261003_1149/context_readout_refit_v1/readout_refit_esn_2026100301/TRAINING_COMPLETE.json')
    assert sha(data)==meta['training_data_sha256']
    with np.load(data) as z:
        o=z['observation'][z['train']]
        train=dict(frames=len(o),path_min_xyz=o[:,45:48].min(0).tolist(),path_max_xyz=o[:,45:48].max(0).tolist(),
            positive_y_path_fraction=float(np.mean(o[:,46]>.1)),
            nominal_xyz_min=o[:,14:17].min(0).tolist(),nominal_xyz_max=o[:,14:17].max(0).tolist(),
            error_xyz_min=o[:,20:23].min(0).tolist(),error_xyz_max=o[:,20:23].max(0).tolist(),sha256=sha(data))
    paths=dict(original_good_002=ROOT/'outputs/paired_baseline_development_20261012_v2/episodes/esn__repair_development_002',
        old_far_target=ROOT/'outputs/original_esn_old_office_transfer_20261013/episode_v2',
        waypoint_v2=ROOT/'outputs/original_esn_reference_fix_20261013_v2/episode',continuous=RUN/'episode')
    rows={k:summarize(p) for k,p in paths.items()}
    assert all(r['hashes']['checkpoint.npz']==meta['checkpoint_sha256'] for r in rows.values())
    assert len({rows[k]['hashes']['rollout.mjb'] for k in ['old_far_target','waypoint_v2','continuous']})==1
    output=RUN/'REFERENCE_ANALYSIS.json'
    if output.exists():raise FileExistsError(output)
    output.write_text(json.dumps(dict(training=train,runs=rows,analysis_source_sha256=sha(Path(__file__)),
        limitations=['Original good002 uses another layout and route, not a paired environment comparison',
                     'Equal clock windows may have different contact exposure',
                     'Phase endpoint, waypoint and continuous-reference RMSE are not one metric',
                     'Positive-y direction is absent from training; this is distribution evidence, not a proof of sole causation']),indent=2)+'\n')
    print(json.dumps({k:{j:v for j,v in row.items() if j in ('task','strict','stage','external_penetration_mm','plan','observation','windows')} for k,row in rows.items()},indent=2))


if __name__=='__main__':main()
