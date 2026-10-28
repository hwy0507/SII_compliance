"""Independent replay and physical metric audit for the joint ESN candidate."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);a=ap.parse_args()
    sys.path.insert(0,str(ROOT/'scripts'))
    from current_student_policy_20260921 import load_current
    plan=json.loads(a.plan.read_text()); rows=[]
    for job in plan['jobs']:
        folder=a.root/'results'/job['id']; result=json.loads((folder/'rollout.json').read_text())
        assert result['neural_logging']['model_sha256']==digest(a.model)
        assert result['model_sha256']==digest(folder/'rollout.mjb')
        actor=load_current(a.model)
        reset_each_observation = result['neural_logging'].get('memory_ablation') == 'reset_each_observation'
        with np.load(folder/'rollout.npz',allow_pickle=False) as tr:
            actions=[]; states=[]
            for obs in tr['observation']:
                if reset_each_observation:
                    actor.reset()
                actions.append(actor.act(obs)); states.append(getattr(actor,'obj',actor).state.copy())
            replay=np.asarray(actions); saved=tr['applied_action']
            replay_error=float(np.max(np.abs(replay-saved)))
            assert replay_error<1e-10
            state_saved=tr['reservoir_state']; state_error=float(np.max(np.abs(np.asarray(states)-state_saved)))
            assert state_error<1e-10
            steps=len(actions)
        with np.load(folder/'rollout_metrics/substep_metrics.npz',allow_pickle=False) as tr:
            dt=tr['dt'].astype(np.float64); err=tr['error'].astype(np.float64)
            rmse=float(np.sqrt(np.sum(err*err*dt[:,None])/dt.sum()))
            speed=float(np.max(np.linalg.norm(tr['twist'][:,:3].astype(np.float64),axis=1)))
            torque=float(np.max(np.abs(tr['qfrc_actuator'])))
            assert abs(float(dt.sum())-55.)<1e-7
        m=result['metrics']; np.testing.assert_allclose([rmse,speed,torque],[m['position_rmse_3d_m'],m['linear_speed_peak_mps'],m['generalized_actuator_torque_peak_nm']],rtol=2e-7,atol=1e-8)
        rows.append(dict(case=job['id'],task=result['task_success'],strict=result['strict_success'],final_stage=result['final_task_stage'],
            waypoint_rmse_mm=1000*rmse,torque_peak_nm=torque,speed_peak_mps=speed,penetration_mm=1000*result['stats']['max_external_penetration_m'],
            rod_duration_s=result['stats']['events'].get('rod',{}).get('duration_s',0),replay_max_abs=replay_error,state_replay_max_abs=state_error,steps=steps,
            model_sha256=result['model_sha256'],source_sha256=result['source_sha256'],files_sha256={str(p.relative_to(folder)):digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    report=dict(candidate_sha256=digest(a.model),plan_sha256=digest(a.plan),episodes=len(rows),task_successes=sum(r['task'] for r in rows),strict_successes=sum(r['strict'] for r in rows),rows=rows,
        caveats=['All six are exposed development conditions; no held-out layout was opened.', 'Action labels were teacher requests submitted to the unchanged executor; physical metrics are independently recomputed.', 'This is not a hardware result and does not establish ESN superiority over zero/WBC.'])
    (a.root/'ESN_JOINT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# 第一版全48D ESN闭环审计','','| 条件 | task | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆 s |','|---|---|---|---:|---:|---:|---:|---:|']
    for r in rows: lines.append(f"| {r['case']} | {r['task']} | {r['strict']} | {r['waypoint_rmse_mm']:.3f} | {r['torque_peak_nm']:.3f} | {r['speed_peak_mps']:.6f} | {r['penetration_mm']:.6f} | {r['rod_duration_s']:.3f} |")
    lines += ['',f"任务完成 {report['task_successes']}/{report['episodes']}，严格通过 {report['strict_successes']}/{report['episodes']}。",'固定观测动作重放、储备池状态重放和三项物理子步指标均通过。','']
    (a.root/'ESN_JOINT_RESULTS.md').write_text('\n'.join(lines)); print('\n'.join(lines))

if __name__=='__main__':main()
