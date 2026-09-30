"""Isolated front/rear guard calibration; the pusher remains retracted."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import json
import os
from pathlib import Path
import tune_workstation_vmc_20260920 as tuning
from refine_workstation_vmc_20260920 import assembly_metrics

ROOT=tuning.ROOT;OUT=ROOT/'outputs'/os.environ.get('ISOLATED_CAMPAIGN','workstation_isolated_20260920')


def isolated_metrics(dest,fixture,candidate):
    row=assembly_metrics(dest,fixture,candidate)
    result=json.loads(dest.with_suffix('.json').read_text())
    row['checks']['rod_contact']=row['contacts']['push_rod_geom']['duration_s']==0.
    row['checks']['release']=result['panel_audit']['final_rod_gap_m']>.002
    row['accepted']=all(row['checks'].values())
    row['scenario_note']='Single guard contact calibration; pusher stroke=0 and no rod contact required.'
    return row


def main():
    OUT.mkdir(parents=True,exist_ok=True);tuning.OUT=OUT;tuning.metrics=isolated_metrics
    tuning.FIXTURES={
        'rear':dict(focus='push_back_guard',args={'push_stroke':0.},panel={'lift_goal_x':.505}),
        'front':dict(focus='push_front_guard',args={'push_stroke':0.},panel={'lift_goal_x':.580,'front_inner_x':.590})}
    if os.environ.get('REACHABLE_FRONT')=='1':
        tuning.FIXTURES={'front':dict(focus='push_front_guard',args={'push_stroke':0.},
            panel={'lift_goal_x':.565,'lift_goal_z':.765,'front_inner_x':.575})}
    inherited=json.loads((ROOT/'outputs/workstation_local_20260920/protocol.json').read_text())['configs']
    names=['soft_reference','damped','less_return','rotation_stiff','world_axes','yield_x']
    configs={n:inherited[n] for n in names}
    (OUT/'protocol.json').write_text(json.dumps(dict(fixtures=tuning.FIXTURES,configs=configs,
        interpretation='Identify VMC response to each fixed guard without rod interference; combined condition evaluated separately.'),indent=2))
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f in as_completed([pool.submit(tuning.run_case,scene,name,cfg)for scene in tuning.FIXTURES for name,cfg in configs.items()]):
            row=f.result();rows.append(row);(OUT/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps({k:row.get(k) for k in ('fixture','candidate','accepted','checks','score','error','wall_s')}),flush=True)
    (OUT/'complete.json').write_text(json.dumps(dict(complete=True,rollouts=len(rows))))


if __name__=='__main__':main()
