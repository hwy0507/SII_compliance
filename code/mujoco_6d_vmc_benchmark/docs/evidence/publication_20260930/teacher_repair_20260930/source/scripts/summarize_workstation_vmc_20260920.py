"""Uniform retrospective assessment and reviewable teacher profiles."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import tune_workstation_vmc_20260920 as tuning
from refine_workstation_vmc_20260920 import assembly_metrics
from calibrate_workstation_contacts_20260920 import isolated_metrics

ROOT=tuning.ROOT;OUT=ROOT/'outputs/workstation_teacher_release_20260920'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    campaigns=['workstation_search_v2_20260920','workstation_local_20260920','workstation_isolated_20260920','workstation_front_reachable_20260920','workstation_guard_polish_20260920']
    records=[];coverage={};configs={}
    for campaign in campaigns:
        folder=ROOT/'outputs'/campaign
        for path in sorted(folder.glob('*/*/rollout.json')):
            fixture=path.parent.parent.name;candidate=path.parent.name
            isolated=campaign in ('workstation_isolated_20260920','workstation_front_reachable_20260920','workstation_guard_polish_20260920')
            assess=isolated_metrics if isolated else assembly_metrics
            row=assess(path.with_suffix(''),fixture,candidate)
            group=fixture if isolated or fixture in ('combined','rod') else fixture+'_combined'
            if fixture=='front' and campaign not in ('workstation_front_reachable_20260920','workstation_guard_polish_20260920'):
                group='front_superseded_target';row['accepted']=False
                row['protocol_note']='Superseded target near/outside fixed-orientation workspace; excluded from algorithm comparison and teacher data.'
            row.update(group=group,campaign=campaign,id=campaign+'/'+fixture+'/'+candidate)
            command=json.loads((path.parent/'command.json').read_text())
            configs[row['id']]=dict(controller=json.loads(command['environment']['CORE_VMC_CONFIG']),
                environment=json.loads(command['environment']['PANEL_CONFIG']),command=command)
            argv=command['argv'];physical_args={argv[i]:argv[i+1] for i in range(2,len(argv)-1,2) if argv[i] not in ('--output','--menagerie')}
            payload=dict(controller=configs[row['id']]['controller'],environment=configs[row['id']]['environment'],arguments=physical_args)
            row['condition_parameter_fingerprint']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
            records.append(row)
    selected={}
    for group in ('rod','rear','front','combined','rear_combined','front_superseded_target'):
        pool=[r for r in records if r['group']==group]
        unique={}
        for row in pool:unique.setdefault(row['condition_parameter_fingerprint'],row)
        valid=[r for r in unique.values() if r['accepted']];front=tuning.pareto(valid)
        coverage[group]=dict(evaluated=len(pool),unique_conditions_and_parameters=len(unique),accepted=len(valid),pareto=len(front))
        if not front:continue
        best=front[0];selected[group]=dict(row=best,parameters=configs[best['id']],pareto_ids=[r['id'] for r in front])
        dest=OUT/'profiles'/group;dest.mkdir(parents=True,exist_ok=True)
        (dest/'controller.json').write_text(json.dumps(configs[best['id']]['controller'],indent=2))
        (dest/'task_and_fixture.json').write_text(json.dumps(configs[best['id']]['environment'],indent=2))
        (dest/'selected_metrics.json').write_text(json.dumps(best,indent=2))
        (dest/'reproduce.json').write_text(json.dumps(configs[best['id']]['command'],indent=2))
    summary=dict(coverage=coverage,selected=selected,completed_campaigns={c:(ROOT/'outputs'/c/'complete.json').exists() for c in campaigns},
        all_primary_contacts_covered=all(k in selected for k in ('rod','rear','front','combined')),
        selection='Feasibility-first Pareto; then fixed normalized weighted score; same assembly-aware audit across all episodes.',
        optimality='Best observed within a finite development search; no global optimality claim.',
        data_scope='Development and teacher-candidate episodes, not frozen generalization test data.')
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    (OUT/'all_assessed.json').write_text(json.dumps(records,indent=2))
    manifest=[];seen=set()
    for r in records:
        fingerprint=r['condition_parameter_fingerprint']
        if not r['accepted'] or fingerprint in seen:continue
        seen.add(fingerprint)
        manifest.append(dict(id=r['id'],group=r['group'],result=r['result'],trace=str(Path(r['result']).with_suffix('.npz')),
            config=configs[r['id']]['controller'],assessment_version=r['assessment_version'],fingerprint=fingerprint,
            pareto=r['id'] in selected.get(r['group'],{}).get('pareto_ids',[])))
    (OUT/'teacher_candidate_manifest.json').write_text(json.dumps(manifest,indent=2))
    (OUT/'teacher_pareto_manifest.json').write_text(json.dumps([r for r in manifest if r['pareto']],indent=2))
    with (OUT/'metrics.csv').open('w',newline='') as stream:
        fields=['group','id','accepted','score','trajectory_rmse_after_contact_m','endpoint_error_m','speed_peak_mps','speed_p95_mps','torque_peak_nm','max_penetration_m','lift_m']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(records)
    print(json.dumps(dict(coverage=coverage,primary_covered=summary['all_primary_contacts_covered'],selected={k:v['row']['id'] for k,v in selected.items()})),flush=True)


if __name__=='__main__':main()
