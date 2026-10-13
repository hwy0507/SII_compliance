"""Compare the preregistered reference correction; retain all outcome differences."""
import hashlib
import json
import argparse
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def summarize(p):
    result=read(p/'rollout.json');execution=read(p/'execution.json')
    with np.load(p/'rollout.npz') as z,np.load(p/'execution_chain.npz') as c:
        o=z['observation'];t=z['neuron_time'];raw=c['requested_action'][:,1:4]*.32
        actual=o[:,14:17]-o[:,26:29];filtered=c['yield_twist'][:,:3];windows=[]
        for lo,hi in [(11.48,16.68),(16.72,22.68),(10.24,30),(0,55)]:
            m=(t>=lo-1e-7)&(t<hi-1e-7);x=raw[m,0]
            windows.append(dict(start_s=lo,end_s=hi,frames=int(m.sum()),
                x_sign_flips=int(np.sum(x[:-1]*x[1:]<0)),
                x_saturation_fraction=float(np.mean(abs(x)>=.32-1e-8)),
                raw_xyz_step_rms_mps=np.sqrt(np.mean(np.diff(raw[m],axis=0)**2,axis=0)).tolist(),
                filtered_xyz_step_rms_mps=np.sqrt(np.mean(np.diff(filtered[m],axis=0)**2,axis=0)).tolist(),
                measured_xyz_step_rms_mps=np.sqrt(np.mean(np.diff(actual[m],axis=0)**2,axis=0)).tolist(),
                y_position_error_mean_m=float(o[m,21].mean()),
                y_context_clipped_fraction=float(np.mean(abs(o[m,21])>=.32))))
    return dict(input_sha256={n:sha(p/n) for n in ('rollout.json','rollout.npz','checkpoint.npz','rollout.mjb','execution.json','AUDIT.json')},
        task=result['task_success'],strict=result['strict_success'],full_horizon=result['full_task_horizon_completed'],
        stage=result['final_task_stage'],events=result['task_events'],metrics=result['metrics'],stats=result['stats'],
        cup_valid=result['cup_valid'],contact_coverage_valid=result['contact_coverage_valid'],
        destination=result['placement_destination'],schedule=result['schedule'],filter_config=execution['action_filter_config'],
        windows=windows)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,default=ROOT/'outputs/original_esn_reference_fix_20261013')
    args=parser.parse_args()
    output=args.run.resolve()/'COMPARISON.json'
    if output.exists():raise FileExistsError(output)
    before=summarize(ROOT/'outputs/original_esn_old_office_transfer_20261013/episode_v2')
    after=summarize(output.parent/'episode')
    for name in ('checkpoint.npz','rollout.mjb'):assert before['input_sha256'][name]==after['input_sha256'][name]
    for name in ('destination','schedule','filter_config'):assert before[name]==after[name]
    result=dict(source_sha256=sha(Path(__file__)),before=before,after=after,
        interpretation='Single same-seed paired reference ablation, no parameter search. All failure outcomes retained.',
        metric_caveat='RMSE references differ (phase endpoint versus local waypoint); no direct RMSE improvement claim.',
        timing_caveat='Equal wall-clock windows need not have equal contact exposure after reference changes; not a compliance ranking.')
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:{j:v for j,v in r.items() if j in ('task','strict','stage','windows')} for k,r in [('before',before),('after',after)]},indent=2))


if __name__=='__main__':main()
