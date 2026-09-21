"""Local structured search plus uniform, assembly-aware contact assessment.

Hand contact with a guard's supporting lip is a legitimate rack contact and
is included in force/impulse costs. Contact by upstream links, with the desk,
or with the actuator housing is rejected. The same rules rescore every run.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import json
import os
from pathlib import Path
import numpy as np
import tune_workstation_vmc_20260920 as tuning

ROOT=tuning.ROOT
OUT=ROOT/'outputs/workstation_local_20260920'


def assembly_metrics(dest,fixture,candidate):
    row=ORIGINAL_METRICS(dest,fixture,candidate)
    bad=[];guard_bad=[]
    hand_bodies={'hand','left_finger','right_finger'}
    for name,c in row['contacts'].items():
        if c['peak_point_force_n']<=1.:continue
        if name.startswith(('push_back_guard','push_front_guard','ws_push_')):
            if not set(c['bodies'])<=hand_bodies:guard_bad.append(name)
        elif name.startswith(('ws_','office_')):
            # Low tray edges are part of the picking fixture; record and
            # penalize hand contact there, while rejecting upstream impact.
            if not (name.startswith('ws_tray_') and set(c['bodies'])<=hand_bodies):bad.append(name)
    row['checks']['no_incidental_structure_contact']=not bad
    row['checks']['no_upstream_guard_contact']=not guard_bad
    row['unexpected_structure_contacts']=bad+guard_bad
    row['accepted']=all(row['checks'].values())
    row['assessment_version']='all_fixture_contacts_v1'
    return row


ORIGINAL_METRICS=tuning.metrics


def main():
    OUT.mkdir(parents=True,exist_ok=True);tuning.OUT=OUT;tuning.metrics=assembly_metrics
    base=json.loads(json.loads(tuning.REFERENCE.read_text())['environment']['CORE_VMC_CONFIG'])
    configs={'soft_reference':base}
    def add(name,k,d,**extra):
        cfg=copy.deepcopy(base);cfg.update(stiffness_6d=k,damping_6d=d,**extra);configs[name]=cfg
    add('damped',[600,100,1400,16,16,20],[34,16,65,4.5,4.5,5.5])
    add('vertical',[600,100,1800,16,16,20],[34,16,75,4.5,4.5,5.5])
    add('less_return',[600,100,1400,16,16,20],[34,16,65,4.5,4.5,5.5],offset_tracking_gain_6d=.5)
    add('rotation_stiff',[600,100,1400,36,36,40],[34,16,65,6,6,7])
    add('world_axes',[600,100,1400,16,16,20],[34,16,65,4.5,4.5,5.5],axis_rotation_rpy=[0,0,0])
    add('yield_x',[350,100,1600,16,16,20],[26,16,65,4.5,4.5,5.5])
    add('stiff_x',[1000,100,1600,16,16,20],[45,16,65,4.5,4.5,5.5])
    (OUT/'protocol.json').write_text(json.dumps(dict(fixtures=tuning.FIXTURES,configs=configs,
        contact_rules='Include hand contact with all guard lips and tray edges in force/impulse objectives; reject upstream guard contacts, desk and actuator contacts.',
        physics='same compiled scene rules and native CCD as workstation_search_v2',optimality='finite local search'),indent=2))
    rows=[]
    jobs=[(fixture,name,cfg) for fixture in ('combined','rear','front') for name,cfg in configs.items()]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for future in as_completed([pool.submit(tuning.run_case,*job) for job in jobs]):
            row=future.result();rows.append(row);(OUT/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps({k:row.get(k) for k in ('fixture','candidate','accepted','checks','score','error','wall_s')}),flush=True)
    (OUT/'complete.json').write_text(json.dumps(dict(complete=True,rollouts=len(rows))))


if __name__=='__main__':main()
