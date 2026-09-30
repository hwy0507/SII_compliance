"""Report every discovered episode, including failure/short diagnostics."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAMPAIGN=ROOT/'outputs/esn_office_recovery_20260927'


def main():
    rows=[]
    for p in sorted(CAMPAIGN.rglob('rollout.json')):
        result=json.loads(p.read_text())
        if 'task_success' not in result:continue
        metrics=result['metrics'];stats=result['stats']
        failures=[]
        if not result['task_success']:failures.append('task_incomplete:'+result['final_task_stage'])
        if not result['physical_valid']:failures.append('external_penetration_or_physics_abort')
        if not result['contact_coverage_valid']:failures.append('insufficient_required_contact_exposure')
        if not result['cup_valid']:failures.append('cup_unstable')
        required_ball=result['arguments']['events'] in ('ball','all')
        if required_ball and not result['ball_rebound']:failures.append('no_ball_rebound')
        rows.append(dict(case=str(p.parent.relative_to(CAMPAIGN)),task_success=result['task_success'],
            strict_success=result['strict_success'],task_and_external_physics_valid=result['task_success'] and result['physical_valid'],
            stage=result['final_task_stage'],duration=result['arguments'].get('physics_probe_s') or result['arguments']['duration'],
            configured_environment_horizon=result['arguments']['duration'],purpose=result['purpose'],seed=result['arguments']['seed'],
            variant=result['arguments']['variant'],dt=result['arguments']['dt'],
            rmse_mm=1000*metrics['position_rmse_3d_m'],peak_torque_nm=metrics['generalized_actuator_torque_peak_nm'],
            peak_speed_mps=metrics['linear_speed_peak_mps'],external_penetration_mm=1000*stats['max_external_penetration_m'],
            contact_duration_s={k:v['duration_s'] for k,v in stats['events'].items()},
            failures=failures,result_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            trajectory_sha256=hashlib.sha256(p.with_suffix('.npz').read_bytes()).hexdigest(),
            model_sha256=result['neural_logging'].get('model_sha256'),
            source_sha256=result['source_sha256']))
    (CAMPAIGN/'all_results.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
    lines=['# Office recovery: all evaluated episodes','',
      'Short diagnostics are not full-task trials. RMSE uses the current stage target; compare only with task completion and stage occupancy. Strict also includes apparatus exposure/rebound and cup stability. All failures are retained.','',
      '| Case | Horizon s | Task | Strict | Last stage | RMSE mm | Torque Nm | Speed m/s | Penetration mm |',
      '|---|---:|---|---|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['duration']:g} | {r['task_success']} | {r['strict_success']} | {r['stage']} | {r['rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.5f} | {r['external_penetration_mm']:.6f} |")
    (CAMPAIGN/'all_results.md').write_text('\n'.join(lines)+'\n')
    print(f'Archived {len(rows)} episodes, including all discovered failures.')


if __name__=='__main__':main()
