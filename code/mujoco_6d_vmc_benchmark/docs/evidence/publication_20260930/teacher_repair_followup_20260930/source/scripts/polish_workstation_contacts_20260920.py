"""Equal four-neighbor local refinement of the two isolated guard teachers."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import json
from pathlib import Path
import tune_workstation_vmc_20260920 as tuning
from calibrate_workstation_contacts_20260920 import isolated_metrics


def main():
    root=tuning.ROOT;out=root/'outputs/workstation_guard_polish_20260920';out.mkdir(parents=True,exist_ok=True)
    summary=json.loads((root/'outputs/workstation_teacher_release_20260920/summary.json').read_text())
    tuning.OUT=out;tuning.metrics=isolated_metrics
    tuning.FIXTURES={
        'rear':dict(focus='push_back_guard',args={'push_stroke':0.},panel={'lift_goal_x':.505}),
        'front':dict(focus='push_front_guard',args={'push_stroke':0.},panel={'lift_goal_x':.565,'lift_goal_z':.765,'front_inner_x':.575})}
    jobs=[];cfgs={}
    for fixture in tuning.FIXTURES:
        base=summary['selected'][fixture]['parameters']['controller']
        for name,ks,ds,gain,flt in [('softer',.7,.9,1.,1.),('damped',1.,1.3,1.,1.),('fast_filter',1.,1.,1.,.7),('less_offset',1.,1.,.75,1.)]:
            cfg=copy.deepcopy(base);cfg['stiffness_6d'][0]*=ks;cfg['damping_6d'][0]*=ds
            cfg['offset_tracking_gain_6d']*=gain;cfg['filter_tau']*=flt
            cfgs[fixture+'/'+name]=cfg;jobs.append((fixture,name,cfg))
    (out/'protocol.json').write_text(json.dumps(dict(fixtures=tuning.FIXTURES,configs=cfgs,neighbors_per_fixture=4),indent=2))
    rows=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for f in as_completed([pool.submit(tuning.run_case,*job) for job in jobs]):
            row=f.result();rows.append(row);(out/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps({k:row.get(k) for k in ('fixture','candidate','accepted','checks','score','error','wall_s')}),flush=True)
    (out/'complete.json').write_text(json.dumps(dict(complete=True,rollouts=len(rows))))


if __name__=='__main__':main()
