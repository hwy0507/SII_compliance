"""Failure-inclusive report for shared resolved physics and extra stress cases."""
import hashlib
import json
import argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--campaign',default='outputs/esn_office_resolved_stress_20260927')
    p.add_argument('--plan',default='configs/esn_office_resolved_stress_20260927.json')
    p.add_argument('--stem',default='RESOLVED_STRESS_RESULTS');a=p.parse_args()
    base=ROOT/a.campaign;plan_path=ROOT/a.plan
    plan=json.loads(plan_path.read_text())
    rows=[];missing=[]
    for job in plan['jobs']:
        p=base/'results'/job['id']/'rollout.json'
        if not p.exists():missing.append(job['id']);continue
        j=json.loads(p.read_text());m=j['metrics'];s=j['stats'];events=s['events']
        fail=[]
        if not j['task_success']:fail.append('task_incomplete:'+j['final_task_stage'])
        if not j['physical_valid']:fail.append('external_penetration_or_abort')
        if not j['contact_coverage_valid']:fail.append('insufficient_contact_exposure')
        if not j['cup_valid']:fail.append('cup_unstable')
        if not j['ball_rebound']:fail.append('ball_rebound_absent')
        rows.append(dict(case=job['id'],task=j['task_success'],strict=j['strict_success'],failure_reasons=fail,
            seed=j['arguments']['seed'],variant=j['arguments']['variant'],arguments=j['arguments'],
            rmse_mm=m['position_rmse_3d_m']*1000,peak_torque_nm=m['generalized_actuator_torque_peak_nm'],
            peak_speed_mps=m['linear_speed_peak_mps'],penetration_mm=s['max_external_penetration_m']*1000,
            person_contact_s=events.get('person_hand',{}).get('duration_s',0),rod_contact_s=events.get('rod',{}).get('duration_s',0),
            physics_resolution=j['physics_resolution'],timestep_sample_counts=m['timestep_sample_counts'],
            model_sha256=j['neural_logging']['model_sha256'],source_sha256=j['source_sha256'],
            result_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            trajectory_sha256=hashlib.sha256(p.with_suffix('.npz').read_bytes()).hexdigest()))
    esn=[r for r in rows if r['model_sha256'] is not None]
    record=dict(complete=not missing,missing=missing,esn_task=sum(r['task'] for r in esn),esn_strict=sum(r['strict'] for r in esn),
        esn_n=len(esn),rows=rows,blind_scenarios_used=False,
        plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (base/(a.stem+'.json')).write_text(json.dumps(record,indent=2))
    lines=['# Shared resolved physics / complete office stress runs','',
      'These runs retain the .2mm gate and the frozen checkpoint listed in each result. Additional rod timings do not replace original failed conditions. No blind layout was used.','',
      '| Case | Task | Strict | RMSE mm | Torque Nm | Speed m/s | Penetration mm | Person s | Rod s |',
      '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['task']} | {r['strict']} | {r['rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.5f} | {r['penetration_mm']:.6f} | {r['person_contact_s']:.3f} | {r['rod_contact_s']:.3f} |")
    lines+=['',f"Complete: {not missing}. Pending/unavailable: {', '.join(missing) or 'none'}. ESN task {record['esn_task']}/{len(esn)}, strict {record['esn_strict']}/{len(esn)}."]
    (base/(a.stem+'.md')).write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':main()
