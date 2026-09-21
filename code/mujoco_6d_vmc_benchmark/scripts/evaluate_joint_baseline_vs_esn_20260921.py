"""Frozen multi-fixture test: joint VMC baseline versus current ESN."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(job):
    kind, seed, angle = job
    out=ROOT/'outputs/joint_baseline_vs_esn_20260921'/kind/f'seed_{seed}'/'rollout'
    out.parent.mkdir(parents=True,exist_ok=True)
    ref=json.loads((ROOT/'web_demo/assets/loaded_push_release_20260918/rollout.json').read_text())['arguments']
    ref={k:v for k,v in ref.items() if v is not None and k not in ('output','render','settle_only')}
    ref.update(seed=seed,event_stage='loaded_lift',push_angle=angle,push_height=.58,duration=24)
    cmd=[sys.executable,str(ROOT/'scripts/run_panel_push_20260920.py'),'--output',str(out)]
    for k,v in ref.items(): cmd += ['--'+k.replace('_','-'),str(v)]
    cmd += ['--push-height','.58']
    panel=dict(layout='raised_hand_rim',pad_bottom_z=.55,pad_top_z=.71,pad_lower_y=-.15,pad_upper_y=-.085,front_inner_x=.595,back_inner_x=.500,pad_thickness=.015,end_effector_only=True,rod_height_m=.58,workstation=True)
    cfg=dict(stiffness_6d=[520,360,1400,12,10,14],damping_6d=[32,27,62,3,2.7,3.3],mass_6d=[.5,.5,.8,.06,.06,.08],wrench_limit_6d=[35,35,50,3,3,3],deadband_6d=[.2,.2,.2,.03,.03,.03],velocity_limit_6d=[.12,.12,.16,.55,.55,.65],offset_limit_6d=[.18,.18,.18,.35,.35,.35],action_limit_6d=[.16,.16,.2,.6,.6,.6],offset_tracking_gain_6d=1.4,filter_tau=.04,axis_rotation_rpy=[.35,0,-.25])
    env=dict(os.environ,CORE_VMC_CONFIG=json.dumps(cfg),PANEL_CONFIG=json.dumps(panel),PANELS_ENABLED='1',MUJOCO_GL='egl',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
    if kind=='esn': cmd += ['--model',str(ROOT/'outputs/current_esn_20260921/best.npz')]
    with out.with_suffix('.log').open('w') as log: p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    if p.returncode or not out.with_suffix('.json').exists(): return dict(kind=kind,seed=seed,angle=angle,success=False,error='runner')
    d=json.load(open(out.with_suffix('.json')));c=d['contact'];bodies=set(c.get('robot_bodies',[]))
    return dict(kind=kind,seed=seed,angle=angle,success=d.get('success'),grasp=d.get('grasp_lift_success'),upstream=bool(bodies&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'}),bodies=sorted(bodies),error_mm=d.get('endpoint_error_m',0)*1000,lift_mm=d.get('lift_m',0)*1000,force_n=c.get('all_external_peak_force_n'),torque_nm=d.get('peak_torque_nm'),speed_p95=d.get('speed_p95_mps'),penetration_mm=c.get('all_external_max_penetration_m',0)*1000,result=str(out.with_suffix('.json')))

def main():
    jobs=[(kind,seed,angle) for seed,angle in [(800,-.15),(801,-.05),(802,.10)] for kind in ('vmc','esn')]
    rows=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        for f in as_completed([pool.submit(run,j) for j in jobs]): rows.append(f.result()); print(json.dumps(rows[-1]),flush=True)
    out=ROOT/'outputs/joint_baseline_vs_esn_20260921';out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'rows':len(rows),'success_by_kind':{k:sum(r['success'] for r in rows if r['kind']==k) for k in ('vmc','esn')}}))

if __name__=='__main__': main()
