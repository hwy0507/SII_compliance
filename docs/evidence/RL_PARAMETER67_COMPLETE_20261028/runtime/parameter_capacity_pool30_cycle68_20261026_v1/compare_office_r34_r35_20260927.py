"""Matched R34/R35 development regression, preserving exposure failures."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from office_task_v4_20260917 import DEST


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-version',choices=('r35','r36'),default='r35')
    parser.add_argument('--require-identical-source',action='store_true')
    args=parser.parse_args();candidate=args.candidate_version
    base=ROOT/f'outputs/esn_office_{candidate}_stress_20260927'
    plan_path=ROOT/f'configs/esn_office_{candidate}_stress_20260927.json'
    plan=json.loads(plan_path.read_text())
    rows=[]
    for job in plan['jobs']:
        suffix=job['id'].removeprefix(candidate+'_');records={};paths={}
        for version in ('r34',candidate):
            path=ROOT/f'outputs/esn_office_{version}_stress_20260927/results/{version}_{suffix}/rollout.json'
            records[version]=json.loads(path.read_text());paths[version]=path
        old,new=records['r34'],records[candidate]
        assert old['model_sha256']==new['model_sha256']
        assert old['fixture']==new['fixture']
        excluded={'output','esn_model','memory_ablation'}
        assert {k:v for k,v in old['arguments'].items() if k not in excluded}=={k:v for k,v in new['arguments'].items() if k not in excluded}
        for source in old['source_sha256']:
            if source!='validate_office_apparatus_v5_20260917.py':
                assert old['source_sha256'][source]==new['source_sha256'][source],source
        if args.require_identical_source:
            assert old['source_sha256']==new['source_sha256']
        assert new['source_sha256']['office_task_v4_20260917.py']==hashlib.sha256((ROOT/'scripts/office_task_v4_20260917.py').read_bytes()).hexdigest()
        row=dict(condition=suffix,matched_scene_args_and_control=True)
        for version,r in records.items():
            m=r['metrics'];events=r['stats']['events']
            with np.load(paths[version].with_suffix('.npz')) as z:
                placement_error=float(np.linalg.norm(z['object_position'][-1,:2]-DEST[:2]))
            row[version]=dict(task=r['task_success'],strict=r['strict_success'],
                waypoint_rmse_mm=1000*m['position_rmse_3d_m'],
                peak_torque_nm=m['generalized_actuator_torque_peak_nm'],
                peak_speed_mps=m['linear_speed_peak_mps'],
                penetration_mm=1000*r['stats']['max_external_penetration_m'],
                person_contact_s=events.get('person_hand',{}).get('duration_s',0),
                rod_contact_s=events.get('rod',{}).get('duration_s',0),
                final_object_xy_error_mm=1000*placement_error,
                retreat_started_s=next((e['time_s'] for e in r['task_events'] if e['stage']=='retreat'),None),
                result_sha256=hashlib.sha256(paths[version].read_bytes()).hexdigest())
        rows.append(row)
    report=dict(complete=True,rows=rows,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                caveat=('All conditions were developer-exposed. R35 used all six histories in distillation; R36 used original R33 histories plus synthetic equilibrium anchors. '
                        'Contact durations differ as an outcome of control; more exposure is not automatically better control.'))
    stem='R34_'+candidate.upper()+'_COMPARISON'
    (base/(stem+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    lines=[f'# R34 → {candidate.upper()} development regression','',
           '| Condition | Task | Strict | Waypoint RMSE mm | Peak torque Nm | Peak speed m/s | Rod s | Final object XY error mm |',
           '|---|---|---|---|---|---|---|---|']
    for row in rows:
        a,b=row['r34'],row[candidate]
        values=[row['condition'],f"{a['task']} → {b['task']}",f"{a['strict']} → {b['strict']}"]
        for key in ('waypoint_rmse_mm','peak_torque_nm','peak_speed_mps','rod_contact_s','final_object_xy_error_mm'):
            values.append(f'{a[key]:.4f} → {b[key]:.4f}')
        lines.append('| '+' | '.join(values)+' |')
    lines+=['',report['caveat']]
    (base/(stem+'.md')).write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__=='__main__':main()
