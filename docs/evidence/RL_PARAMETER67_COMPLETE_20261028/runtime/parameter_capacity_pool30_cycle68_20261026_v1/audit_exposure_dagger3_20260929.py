"""Independent replay/metric audit for the exposure-DAgger3 ESN screen."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    import sys;sys.path.insert(0,str(ROOT/'scripts'))
    from current_student_policy_20260921 import load_current
    rows=[]
    for folder in sorted(ROOT.glob('results/exposure_dagger3_dev_*')):
        result_path=folder/'rollout.json';trace_path=folder/'rollout.npz';metric_path=folder/'rollout_metrics/substep_metrics.npz'
        if not (result_path.exists() and trace_path.exists() and metric_path.exists()):continue
        result=json.loads(result_path.read_text());actor=load_current(a.model)
        with np.load(trace_path,allow_pickle=False) as tr:
            actions=np.asarray([actor.act(obs) for obs in tr['observation']]);saved=tr['applied_action'];states=np.asarray([actor.obj.state.copy() for _ in []]) if False else None
            replay_error=float(np.max(np.abs(actions-saved)))
            saved_state=tr['reservoir_state']; actor=load_current(a.model)
            replay_states=[]
            for obs in tr['observation']:
                actor.act(obs);replay_states.append(actor.obj.state.copy())
            state_error=float(np.max(np.abs(np.asarray(replay_states)-saved_state)))
            steps=len(actions)
        with np.load(metric_path,allow_pickle=False) as tr:
            dt=tr['dt'].astype(np.float64);err=tr['error'].astype(np.float64)
            rmse=float(np.sqrt(np.sum(err*err*dt[:,None])/dt.sum()));speed=float(np.max(np.linalg.norm(tr['twist'][:,:3],axis=1)));torque=float(np.max(np.abs(tr['qfrc_actuator'])))
        metrics=result['metrics'];
        if replay_error>=1e-10 or state_error>=1e-10:raise AssertionError(f'replay failed: {folder}')
        np.testing.assert_allclose([rmse,speed,torque],[metrics['position_rmse_3d_m'],metrics['linear_speed_peak_mps'],metrics['generalized_actuator_torque_peak_nm']],rtol=2e-7,atol=1e-8)
        rows.append(dict(case=folder.name,task=bool(result['task_success']),strict=bool(result['strict_success']),final_stage=result['final_task_stage'],waypoint_rmse_mm=1000*rmse,peak_torque_nm=torque,peak_speed_mps=speed,penetration_mm=1000*result['stats']['max_external_penetration_m'],replay_max_abs=replay_error,state_replay_max_abs=state_error,steps=steps,source_sha256=result['source_sha256'],files_sha256={str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    report=dict(candidate_sha256=sha(a.model),episodes=len(rows),task_successes=sum(r['task'] for r in rows),strict_successes=sum(r['strict'] for r in rows),rows=rows,caveats=['Development dt=1e-4 only; no formal dt=5e-5 result.','Pure ESN deployment with hybrid_vmc_blend=0; actor input is canonical48D.','No gate, environment, actuator limit, or failure filtering was changed.'])
    a.output.mkdir(parents=True,exist_ok=True);(a.output/'ESN_JOINT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Exposure-balanced DAgger3 ESN audit','','| case | task | strict | RMSE mm | peak torque Nm | peak speed m/s | penetration mm | action replay | state replay |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['case']} | {r['task']} | {r['strict']} | {r['waypoint_rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.6f} | {r['penetration_mm']:.6f} | {r['replay_max_abs']:.1e} | {r['state_replay_max_abs']:.1e} |")
    lines += ['',f"Task {report['task_successes']}/{report['episodes']}; strict {report['strict_successes']}/{report['episodes']}.",'Independent action/reservoir replay and physical substep recomputation passed.']
    (a.output/'ESN_JOINT_RESULTS.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
if __name__=='__main__':main()
