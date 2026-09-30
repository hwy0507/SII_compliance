"""Bounded, reproducible fixed-parameter 6D VMC search across contact fixtures.

Every candidate is constant for the whole episode. Contact identities enter
only the offline objective, never the controller. Feasibility precedes Pareto
selection. Shared initial candidates keep contact-specific searches comparable.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'/os.environ.get('WORKSTATION_CAMPAIGN','workstation_vmc_20260920')
REFERENCE=ROOT/'outputs/raised_hand_native_20260920/native_soft/command.json'
FIXTURES={
    'combined':dict(focus='push_back_guard',args={},panel={}),
    'rod':dict(focus='push_rod_geom',args={'push_force':8.,'push_stroke':.17},panel={}),
    'rear':dict(focus='push_back_guard',args={},panel={'lift_goal_x':.505}),
    'front':dict(focus='push_front_guard',args={},panel={'front_inner_x':.582,'lift_goal_x':.580}),
}


def metrics(dest,fixture,candidate):
    r=json.loads(dest.with_suffix('.json').read_text());a=r['panel_audit'];contacts=a['contacts']
    tr=np.load(dest.with_suffix('.npz'));focus=FIXTURES[fixture]['focus']
    env_contacts={n:c for n,c in contacts.items() if n!='target_object_geom'}
    support={n:c for n,c in env_contacts.items() if n.startswith('ws_') or n.startswith('office_')}
    max_pen=max(c['max_penetration_m'] for c in env_contacts.values())
    max_point=max(c['peak_point_force_n'] for c in env_contacts.values())
    robot_contacted_support=[n for n,c in support.items() if c['peak_point_force_n']>1.]
    speed=np.linalg.norm(tr['twist'][:,:3],axis=1)
    accel=np.linalg.norm(np.diff(tr['twist'][:,:3],axis=0)/.04,axis=1)
    first=min((c['first_s'] for c in env_contacts.values() if c['first_s'] is not None),default=0.)
    mask=tr['time']>=first
    rms=float(np.sqrt(np.mean(np.sum((tr['position'][mask]-tr['target'][mask])**2,axis=1))))
    checks=dict(task=r['success'] and a['final_bilateral_grasp'],physics=not r['invalid_physics'] and max_pen<.0002,
        target_contact=contacts[focus]['duration_s']>.015 and contacts[focus]['peak_point_force_n']>1.,
        rod_contact=contacts['push_rod_geom']['duration_s']>.15,
        release=a['final_rod_gap_m']>.002 and contacts['push_rod_geom']['last_s'] is not None and r['duration_s']-contacts['push_rod_geom']['last_s']>1.,
        no_incidental_structure_contact=not robot_contacted_support,
        limited_point_force=max_point<300.,speed=float(speed.max())<.3)
    # Gripper/payload load remains logged, but a useful grasp must not be
    # penalized as if every intended finger contact should vanish.
    scores=[contacts[focus]['peak_resultant_force_n'],max(c['peak_resultant_force_n'] for c in env_contacts.values()),
        sum(c['resultant_impulse_ns'] for c in env_contacts.values()),rms,float(speed.max()),r['peak_torque_nm']]
    balanced=float(np.dot(np.array(scores)/[150.,220.,100.,.15,.2,40.],[.25,.20,.15,.15,.10,.15]))
    return dict(fixture=fixture,candidate=candidate,accepted=all(checks.values()),checks=checks,score=balanced,objectives=scores,
        trajectory_rmse_after_contact_m=rms,endpoint_error_m=r['endpoint_error_m'],speed_peak_mps=float(speed.max()),
        speed_p95_mps=float(np.percentile(speed,95)),acceleration_p95_mps2=float(np.percentile(accel,95)),
        torque_peak_nm=r['peak_torque_nm'],max_penetration_m=max_pen,lift_m=r['lift_m'],
        focus=focus,contacts=contacts,unexpected_structure_contacts=robot_contacted_support,result=str(dest.with_suffix('.json')))


def run_case(fixture,candidate,config):
    dest=OUT/fixture/candidate/'rollout';dest.parent.mkdir(parents=True,exist_ok=True)
    old=json.loads(REFERENCE.read_text());argv=old['argv'];argv[0]=sys.executable
    argv[argv.index('--output')+1]=str(dest)
    for key,val in FIXTURES[fixture]['args'].items():
        flag='--'+key.replace('_','-')
        if flag in argv:argv[argv.index(flag)+1]=str(val)
        else:argv.extend([flag,str(val)])
    env=old['environment'];panel=json.loads(env['PANEL_CONFIG']);panel.update(workstation=True,**FIXTURES[fixture]['panel'])
    env.update(PANEL_CONFIG=json.dumps(panel),CORE_VMC_CONFIG=json.dumps(config))
    (dest.parent/'command.json').write_text(json.dumps(dict(argv=argv,environment=env),indent=2))
    started=time.monotonic()
    with dest.with_suffix('.log').open('w') as log:
        proc=subprocess.run(argv,cwd=ROOT,env=dict(os.environ,**env),stdout=log,stderr=subprocess.STDOUT,timeout=1200)
    if proc.returncode:return dict(fixture=fixture,candidate=candidate,accepted=False,error=dest.with_suffix('.log').read_text()[-1400:],wall_s=time.monotonic()-started)
    row=metrics(dest,fixture,candidate);row['wall_s']=time.monotonic()-started;return row


def pareto(rows):
    result=[]
    for row in rows:
        x=np.asarray(row['objectives'])
        if not any(np.all(np.asarray(other['objectives'])<=x) and np.any(np.asarray(other['objectives'])<x) for other in rows):result.append(row)
    return sorted(result,key=lambda r:r['score'])


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    old=json.loads(REFERENCE.read_text());base=json.loads(old['environment']['CORE_VMC_CONFIG'])
    rng=np.random.default_rng(20260920)
    count=int(os.environ.get('VMC_INITIAL_CANDIDATES','10'));refine=int(os.environ.get('VMC_REFINE_PER_FIXTURE','4'))
    if os.environ.get('VMC_SMOKE')=='1':count=1;refine=0
    configs={'base':base}
    for i in range(1,count):
        cfg=copy.deepcopy(base)
        scales=np.exp(rng.uniform(np.log(.6),np.log(1.6),6))
        cfg['stiffness_6d']=(np.asarray(base['stiffness_6d'])*scales).tolist()
        cfg['damping_6d']=(np.asarray(base['damping_6d'])*np.sqrt(scales)*rng.uniform(.75,1.4,6)).tolist()
        cfg['mass_6d']=(np.asarray(base['mass_6d'])*rng.uniform(.65,1.45,6)).tolist()
        cfg['wrench_limit_6d']=(np.asarray(base['wrench_limit_6d'])*rng.uniform(.8,1.25,6)).tolist()
        cfg['offset_tracking_gain_6d']=float(rng.uniform(.45,1.25));cfg['filter_tau']=float(rng.uniform(.010,.04))
        cfg['axis_rotation_rpy']=[float(rng.uniform(-.15,.15)),float(rng.uniform(-.12,.12)),float(rng.uniform(-.3,0.))]
        configs[f'initial_{i:02d}']=cfg
    protocol=dict(fixtures=FIXTURES,initial_candidates=count,refine_per_fixture=refine,seed=20260920,
        policy='fixed 6D VMC per episode; no contact identity, geometry or event clock input',
        selection='feasibility then Pareto over focus force, worst resultant force, impulse, tracking RMSE, speed peak and torque peak',
        optimality='best observed in the recorded finite search, not a global optimum',configs=configs)
    (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2))
    # Archive the exact source used by this campaign.
    import shutil
    snapshots=OUT/'source';snapshots.mkdir(exist_ok=True)
    for name in ('run_panel_push_20260920.py','workstation_scene_20260920.py','run_vmc_6d_constrained_push_20260918.py',Path(__file__).name):shutil.copy2(ROOT/'scripts'/name,snapshots/name)
    rows=[]
    def execute(jobs):
        with ThreadPoolExecutor(max_workers=int(os.environ.get('VMC_WORKERS','10'))) as pool:
            for f in as_completed([pool.submit(run_case,*j) for j in jobs]):
                row=f.result();rows.append(row);(OUT/'results.json').write_text(json.dumps(rows,indent=2))
                print(json.dumps({k:row.get(k) for k in ('fixture','candidate','accepted','checks','score','error','wall_s')}),flush=True)
    execute([(fixture,name,cfg) for fixture in FIXTURES for name,cfg in configs.items()])
    next_jobs=[]
    for fixture in FIXTURES:
        valid=sorted([r for r in rows if r['fixture']==fixture and r['accepted']],key=lambda r:r['score'])
        if not valid:continue
        parent=configs[valid[0]['candidate']]
        for i in range(refine):
            cfg=copy.deepcopy(parent)
            cfg['stiffness_6d']=(np.asarray(parent['stiffness_6d'])*np.exp(rng.normal(0,.13,6))).tolist()
            cfg['damping_6d']=(np.asarray(parent['damping_6d'])*np.exp(rng.normal(0,.10,6))).tolist()
            cfg['offset_tracking_gain_6d']=float(parent['offset_tracking_gain_6d']*np.exp(rng.normal(0,.10)))
            name=f'{fixture}_refine_{i:02d}';configs[name]=cfg;next_jobs.append((fixture,name,cfg))
    protocol['configs']=configs;(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2))
    execute(next_jobs)
    chosen={}
    for fixture in FIXTURES:
        front=pareto([r for r in rows if r['fixture']==fixture and r['accepted']])
        chosen[fixture]=dict(valid_count=sum(r['accepted'] for r in rows if r['fixture']==fixture),
            evaluated=sum(r['fixture']==fixture for r in rows),pareto_candidates=[r['candidate'] for r in front],
            selected=front[0] if front else None,config=configs[front[0]['candidate']] if front else None)
    (OUT/'selected.json').write_text(json.dumps(chosen,indent=2))
    (OUT/'complete.json').write_text(json.dumps(dict(complete=True,rollouts=len(rows),covered=[k for k,v in chosen.items()if v['selected']],all_covered=all(v['selected'] for v in chosen.values())),indent=2))


if __name__=='__main__':main()
