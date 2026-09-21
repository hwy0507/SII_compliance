"""Four accepted scene families: immutable sources, physical groups, Pareto BC.

No learner is trained by this program. All failed trajectories remain audited.
Pareto selection is local to a physical fixture, not a cross-scene score.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import fcntl
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCENES=('ball','push','corner','table_corner')
TEACHER_KEYS=('stiffness','damping','tangent_speed','force_on','contact_tau','release_tau','memory_tau','force_target','normal_gain')


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,indent=2,allow_nan=False));tmp.replace(path)


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def anchors():
    paths=dict(ball=ROOT/'web_demo/assets/primitive_teacher_v7_fixes_20260917/ball_repaired/rollout.json',
        push=ROOT/'web_demo/assets/loaded_push_release_final_20260918/rollout.json',
        corner=ROOT/'web_demo/assets/primitive_teacher_v6_gallery_20260917/corner_approach/rollout.json',
        table_corner=ROOT/'outputs/teacher_protocol_final_20260915/corner_vmc_teacher_final_v2.json')
    out={}
    for scene,path in paths.items():
        d=json.loads(path.read_text())
        if scene=='table_corner':
            manifest=d['reproducibility_manifest'];argv=manifest['argv'][1:];flags={}
            for i in range(0,len(argv),2):flags[argv[i][2:].replace('-','_')]=argv[i+1]
            flags.pop('output');flags.pop('trace_output');flags['menagerie']=str(ROOT.parent/'mujoco_menagerie')
            params={k:float(v)for k,v in flags.items()if k.startswith('vmc_')}
            calibrated=ROOT/'outputs/four_scene_table_calibration_20260918/summary.json'
            if calibrated.exists():
                options=[r for r in json.loads(calibrated.read_text())if r.get('accepted')]
                if options:params=options[0]['params']
            physical={k:v for k,v in flags.items()if k not in params}
            physical['seed']=int(physical['seed']);physical['simulation_time']=float(physical['simulation_time'])
            env=manifest['environment'].copy()
            # Current legacy entry validates an interval even when the old
            # anchor had no recovery-gain schedule. Keep it inactive.
            env.setdefault('CORNER_VMC_RECOVERY_START_S','1000000')
            env.setdefault('CORNER_VMC_RECOVERY_END_S','1000001')
            out[scene]=dict(source=str(path),flags=physical,params=params,environment=env,
                           runner='capture_legacy_teacher45_20260918.py',family='six_dimensional_spring_carriage',teacher_force='proprioceptive_tracking_error',
                           privileged_task_supervisor=True,legacy_task_action_schedule=True)
        else:
            flags={k:v for k,v in d['arguments'].items()if v is not None and k not in ('output','render','settle_only','model')}
            flags['menagerie']=str(ROOT.parent/'mujoco_menagerie')
            params={k:flags.pop(k)for k in TEACHER_KEYS if k in flags}
            environment={};family='force_vmc_with_existing_contact_terms'
            runner='run_primitive_teacher_v7_20260917.py' if scene=='ball' else 'run_primitive_teacher_v6_20260917.py'
            if scene=='push':
                record=json.loads((path.parent/'verification.json').read_text())
                params=dict(core=record['core_config'],legacy_cli=params)
                environment=record['task_environment'];runner='run_loaded_push_audit_20260918.py';family='diagonal_virtual_mass_spring_damper'
            out[scene]=dict(source=str(path),flags=flags,params=params,environment=environment,runner=runner,
                           family=family,teacher_force=flags['teacher_force_source'],privileged_task_supervisor=(scene=='ball'),
                           legacy_task_action_schedule=False)
    return out


def make_fixtures(base,count,seed):
    rng=np.random.default_rng(seed);out=[]
    for scene_index,scene in enumerate(SCENES):
        for i in range(count):
            rng=np.random.default_rng(seed+100000*scene_index+i)
            spec=json.loads(json.dumps(base[scene]));flags=spec['flags'];env=spec['environment']
            # A physical condition belongs to one group before any search.
            split='train' if i%6<4 else 'validation' if i%6==4 else 'test'
            strength=(.35,.7,1.)[i%3]
            flags['seed']=int(rng.integers(10000,99999999))
            if scene!='table_corner':
                env['DATASET_INITIAL_QDELTA']=json.dumps(rng.normal(0,.004*strength,7).tolist())
            if scene=='ball':
                flags.update(ball_mass=float(rng.uniform(.25,.65)),ball_speed=float(rng.uniform(1.6,2.8)),
                    ball_angle=float(rng.uniform(-.35,.35)),ball_height_offset=float(rng.uniform(-.008,.008)),
                    shift=float(rng.uniform(.008,.028)),payload_mass=float(rng.uniform(.07,.13)))
                flags['event_stage']=('approach','pregrasp','loaded_lift')[(i+i//6)%3]
            elif scene=='push':
                flags.update(push_angle=flags['push_angle']+float(rng.uniform(-.12,.12)*strength),
                    push_height=flags['push_height']+float(rng.uniform(-.006,.006)*strength),
                    push_stroke=flags['push_stroke']+float(rng.uniform(-.015,.008)*strength),
                    push_press=flags['push_press']*float(rng.uniform(.9,1.1)),
                    payload_mass=float(rng.uniform(.08,.12)))
                # Persistent blocker, fixed accepted endpoint/speed contract.
                flags['push_hold']=1000000.
                if i%5==4:flags['event_stage']='loaded_lift'
            elif scene=='corner':
                flags.update(yaw=flags['yaw']+float(rng.uniform(-.16,.16)*strength),
                    shift=flags['shift']+float(rng.uniform(-.012,.012)*strength),
                    width=flags['width']*float(rng.uniform(.88,1.12)),
                    corner_height=flags['corner_height']+float(rng.uniform(-.012,.015)*strength),
                    corner_friction=float(rng.uniform(.15,.45)),payload_mass=float(rng.uniform(.075,.13)))
            else:
                env.update(TABLE_X_SHIFT_M=str(-.01+float(rng.uniform(-.012,.012)*strength)),
                           TABLE_HEIGHT_OFFSET_M=str(-.003+float(rng.uniform(-.004,.004)*strength)),
                           INIT_JOINT_PERTURB_STD_RAD=str(float(rng.uniform(.0005,.003)*strength)))
            physical=dict(scene=scene,flags={k:v for k,v in flags.items()if k not in ('seed','duration','simulation_time','esn')},environment=env)
            # Seed is physically effective only for the legacy initial-pose perturbation.
            if scene=='table_corner':physical['initial_pose_seed']=flags['seed']
            spec.update(id=f'{scene}_{i:03d}',scene=scene,split=split,parent_group=f'{scene}_{i:03d}',fixture_hash=digest(physical))
            out.append(spec)
    return out


def perturb_params(scene,base,rng,scale):
    p=json.loads(json.dumps(base))
    if scene=='push':
        c=p['core']
        for name in ('mass','stiffness_xyz','damping_xyz','offset_tracking_gain','filter_tau','velocity_limit','force_limit'):
            value=np.asarray(c[name]);changed=value*np.exp(rng.normal(0,scale,size=value.shape));c[name]=changed.tolist()
        c['mass']=float(np.clip(c['mass'],.10,2.));c['velocity_limit']=float(np.clip(c['velocity_limit'],.05,.22))
    else:
        for key,value in list(p.items()):
            if isinstance(value,(float,int))and value>0:p[key]=float(value*np.exp(rng.normal(0,scale)))
        if scene!='table_corner':
            p['stiffness']=float(np.clip(p['stiffness'],20,300));p['damping']=float(np.clip(p['damping'],10,100))
            if scene=='ball':p['tangent_speed']=0.
        else:
            for kind in ('offset','rate'):
                start=f'vmc_slowdown_{kind}_start';full=f'vmc_slowdown_{kind}_full'
                if start in p:p[full]=max(p[full],p[start]+.001)
            if 'vmc_slowdown_max_action'in p:p['vmc_slowdown_max_action']=min(1.,p['vmc_slowdown_max_action'])
    return p


def execute(spec,params,cid,run_root,runtime):
    started=time.monotonic()
    folder=run_root/'trials'/spec['id']/f'candidate_{cid:03d}';folder.mkdir(parents=True,exist_ok=True)
    prefix=folder/'rollout';scene=spec['scene'];flags=dict(spec['flags'])
    command=[sys.executable,str(runtime/spec['runner'])]
    if scene!='table_corner':command=[sys.executable,str(runtime/'dataset_primitive_initialization_20260918.py'),'--entry',spec['runner']]
    environment=dict(os.environ,**spec['environment'])
    environment.update(MUJOCO_GL='egl',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if scene=='push':flags.update(params['legacy_cli']);environment['CORE_VMC_CONFIG']=json.dumps(params['core'])
    else:flags.update(params)
    if scene=='table_corner':
        flags.update(output=str(prefix.with_suffix('.gif')),trace_output=str(prefix.with_suffix('.legacy.npz')))
        command+=['--no-render']
    else:flags['output']=str(prefix)
    for key,value in flags.items():
        if isinstance(value,bool):
            if value:command+=['--'+key.replace('_','-')]
        else:command+=['--'+key.replace('_','-'),str(value)]
    if (folder/'command.json').exists():
        saved=json.loads((folder/'command.json').read_text())
        if saved['fixture']['fixture_hash']!=spec['fixture_hash']or digest(saved['params'])!=digest(params):
            raise RuntimeError('Incompatible resume: '+str(folder))
    dump(folder/'command.json',dict(argv=command,fixture=spec,params=params,environment=spec['environment']))
    if (folder/'completed.json').exists():return json.loads((folder/'completed.json').read_text())
    if not (folder/'completed.json').exists():
        try:
            with (folder/'execution.log').open('w')as log:
                result=subprocess.run(command,cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        except subprocess.TimeoutExpired:return dict(id=spec['id'],scene=scene,candidate=cid,accepted=False,error='timeout',split=spec['split'])
        if result.returncode:return dict(id=spec['id'],scene=scene,candidate=cid,accepted=False,error=f'exit_{result.returncode}',split=spec['split'],log=str(folder/'execution.log'))
    try:
        row=inspect(spec,params,cid,prefix);row['runtime_s']=time.monotonic()-started;dump(folder/'completed.json',row);return row
    except Exception as exc:return dict(id=spec['id'],scene=scene,candidate=cid,accepted=False,error=repr(exc),split=spec['split'])


def inspect(spec,params,cid,prefix):
    d=json.loads(prefix.with_suffix('.json').read_text());scene=spec['scene']
    raw=prefix.with_suffix('.canonical.npz')if scene=='table_corner'else prefix.with_suffix('.npz')
    with np.load(raw,allow_pickle=False)as z:
        obs=z['observation'].astype(np.float64);action=z['teacher_action'].astype(np.float64)
        pos=z['position'];target=z['target'];vel=z['twist'][:,:3];torque=z['torque']
        time_values=z['time'];error=np.linalg.norm(pos-target,axis=1)
        start=d.get('contact',{}).get('first_s')if scene!='table_corner'else d.get('first_apron_contact_s')
        window=time_values>=start if start is not None else np.ones(len(obs),dtype=bool)
        rmse=float(np.sqrt(np.mean(error[window]**2)));accel=np.linalg.norm(np.diff(vel,axis=0)/.04,axis=1)
        metrics=dict(tracking_rmse_m=rmse,peak_torque_nm=float(np.max(np.abs(torque))),
                     speed_p95_mps=float(np.percentile(np.linalg.norm(vel,axis=1),95)),
                     speed_peak_mps=float(np.max(np.linalg.norm(vel,axis=1))),acceleration_p95_mps2=float(np.percentile(accel,95)))
        finite=obs.shape[1:]==(45,)and action.shape==(len(obs),7)and np.isfinite(obs).all()and np.isfinite(action).all()
        content_hash=hashlib.sha256(obs.tobytes()+action.tobytes()).hexdigest()
        if scene!='table_corner':
            object_speed=np.r_[0.,np.linalg.norm(np.diff(z['object_position'],axis=0)/.04,axis=1)]
            relative=pos[-10:]-z['object_position'][-10:]
            held_geometry=bool(np.max(np.linalg.norm(relative[:,:2],axis=1))<.045 and
                               np.all((relative[:,2]>.075)&(relative[:,2]<.15)))
            stable=(z['stage']==d['final_stage'])&(error<.015)&(np.linalg.norm(vel,axis=1)<.025)&(object_speed<.02)
            if scene=='push':stable&=time_values>=float(d['postgrasp_release']['last_contact_s']or 0)+2.
            completed=next((float(time_values[i])for i in range(len(stable)-4)if stable[i:i+5].all()),float(d['duration_s']))
        if scene=='push'and start is not None:
            first_index=int(np.searchsorted(time_values,start))
            pregrasp=d['contact'].get('first_stage',0)<2
            behavior=(time_values>=start)&((z['stage']<2)if pregrasp else (time_values<=start+6.))
            net=np.linalg.norm(pos[10:]-pos[:-10],axis=1)
            stalled=behavior[10:]&(error[10:]>.012)&(net<.002)
            edges=np.diff(np.r_[False,stalled,False].astype(int))
            stall=float(max(((b-a)*.04+.4 for a,b in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1))),default=0.))
            angle=float(d['arguments']['push_angle']);normal=np.array([np.sin(angle),-np.cos(angle),0.])
            tangential=vel-np.outer(vel@normal,normal);moving=np.linalg.norm(tangential,axis=1)>.015
            reaction=next((float(time_values[i]-start)for i in range(first_index+1,len(moving)-3)
                           if behavior[i]and moving[i:i+4].all()),None)
            metrics.update(reaction_latency_s=reaction,max_position_stall_s=stall)
    if scene=='table_corner':
        physics=d.get('physics_audit',{});gate=d.get('placement_release_gate',{})
        force=float(physics.get('peak_robot_table_pair_force_n')or d.get('peak_table_contact_pair_force_n')or 1e9)
        checks=dict(task=bool(d.get('scenario_success')),placed=bool(d.get('object_placed_on_table')),
            real_contact=d.get('first_apron_contact_s')is not None,release=bool(gate.get('released')),
            margin=float(d.get('final_placement_min_margin_m')or 0)>=.020,
            physics=d.get('max_apron_penetration_m',1)<.0002 and d.get('max_upstream_penetration_m',1)<=1e-8,
            force=force<850,finite=bool(finite))
        duration=float(gate.get('release_time_s')or d['record_duration_s'])
    else:
        c=d['contact'];force=float(max(c['all_external_peak_force_n'],c.get('peak_body_resultant_n',0)))
        if scene=='push':force=max(force,float(d['postgrasp_release']['postgrasp_peak_point_force_n']))
        checks=dict(task=bool(d['success']),real_contact=bool(d['real_contact']),finite=bool(finite),
            physics=not d['invalid_physics']and c['all_external_max_penetration_m']<.0002,
            force=force<dict(ball=300,push=250,corner=650)[scene])
        checks['held_object_geometry']=held_geometry
        if scene=='ball':
            checks.update(rigid_core=c.get('rigid_core_overlap_m',1)<=1e-6,
                          recovery=d.get('impact_metrics',{}).get('recovery_time_s')is not None,
                          event=c.get('first_stage')==d['requested_event_stage_index'])
        if scene=='push':
            release=d['postgrasp_release']
            # Legacy CCD's signed-distance query is unreliable in some
            # configurations. Use the separately recorded native geometry
            # query, which never enters or changes the physical controller.
            geometry=prefix.with_name('geometry_audit.npz')
            final_gap=release['final_min_gap_m']
            if geometry.exists():
                with np.load(geometry)as g:
                    if len(g['geometry']):final_gap=float(g['geometry'][-1,2])
            checks.update(released=release['no_contact_final_two_seconds'],held=release['bilateral_grasp'],
                          clearance=final_gap>=.003,
                          native_geometry=release['loaded_geometry_min_gap_native_m']>=-.0003,
                          payload_contact_force=release['postgrasp_peak_point_force_n']<250)
            checks['event']=c.get('first_stage')==d['requested_event_stage_index']
            checks['prompt_compliance']=metrics.get('reaction_latency_s')is not None and metrics['reaction_latency_s']<=.5
            checks['no_contact_stall']=metrics.get('max_position_stall_s',1e9)<=.5
        duration=completed
    metrics.update(peak_force_n=force,completion_time_s=duration)
    checks['speed']=metrics['speed_peak_mps']<dict(ball=.45,push=.35,corner=.35,table_corner=.50)[scene]
    checks['torque']=metrics['peak_torque_nm']<65.
    return dict(id=spec['id'],scene=scene,split=spec['split'],parent_group=spec['parent_group'],fixture_hash=spec['fixture_hash'],
                candidate=cid,parameter_group=digest(params),params=params,accepted=all(checks.values()),checks=checks,
                metrics=metrics,trace=str(raw),result=str(prefix.with_suffix('.json')),content_hash=content_hash,
                teacher_family=spec['family'],teacher_force=spec['teacher_force'],samples=len(obs))


OBJECTIVES=('tracking_rmse_m','peak_force_n','peak_torque_nm','completion_time_s','acceleration_p95_mps2')


def pareto(rows):
    valid=[r for r in rows if r.get('accepted')]
    if not valid:return []
    values=np.asarray([[r['metrics'][k]for k in OBJECTIVES]for r in valid])
    return [r for i,r in enumerate(valid)if not np.any(np.all(values<=values[i],axis=1)&np.any(values<values[i],axis=1))]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true')
    p.add_argument('--fixtures-per-scene',type=int,default=24);p.add_argument('--workers',type=int,default=16)
    p.add_argument('--scenes',nargs='+',choices=SCENES,default=list(SCENES))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    lock=(a.output/'campaign.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    base=json.loads((a.output/'anchors.json').read_text())if(a.output/'anchors.json').exists()else anchors()
    dump(a.output/'anchors.json',base)
    runtime=a.output/'frozen_runtime/scripts'
    if not runtime.exists():shutil.copytree(ROOT/'scripts',runtime,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    hashes={str(x.relative_to(runtime)):hashlib.sha256(x.read_bytes()).hexdigest()for x in runtime.rglob('*.py')}
    dump(a.output/'source_hashes.json',hashes)
    if a.smoke:
        specs=[dict(v,id=f'{s}_anchor',scene=s,split='calibration',parent_group=f'{s}_anchor',fixture_hash=digest(v['flags']))for s,v in base.items()]
    else:specs=make_fixtures(base,a.fixtures_per_scene,2026091841)
    specs=[s for s in specs if s['scene']in a.scenes]
    if (a.output/'fixtures.json').exists():
        previous_specs=json.loads((a.output/'fixtures.json').read_text())
        if digest(previous_specs)!=digest(specs):raise RuntimeError('Fixture protocol changed; use a new campaign directory')
    dump(a.output/'fixtures.json',specs);rows=[];rng=np.random.default_rng(2026091842)
    rounds=1 if a.smoke else 3
    for round_index in range(rounds):
        jobs=[]
        for spec in specs:
            previous=[r for r in rows if r['id']==spec['id']]
            front=sorted(pareto(previous),key=lambda r:r['parameter_group'])
            for j in range(1 if a.smoke else 8 if round_index==0 else 4):
                center=front[j%len(front)]['params']if front else spec['params']
                scale=(0. if j==0 else .03 if j<4 else .15 if j<6 else .4)if round_index==0 else (.04 if front else .2)
                params=center if scale==0 else perturb_params(spec['scene'],center,rng,scale)
                jobs.append((spec,params,round_index*100+j))
        proposal=a.output/f'proposals_round_{round_index}.json'
        if proposal.exists():
            saved=json.loads(proposal.read_text());lookup={s['id']:s for s in specs}
            jobs=[(lookup[j['id']],j['params'],j['candidate'])for j in saved]
        else:dump(proposal,[dict(id=s['id'],params=c,candidate=i)for s,c,i in jobs])
        with ThreadPoolExecutor(max_workers=a.workers)as pool:
            for f in as_completed([pool.submit(execute,s,c,i,a.output,runtime)for s,c,i in jobs]):
                rows.append(f.result());dump(a.output/'audit.json',rows)
                counts={s:dict(trials=sum(r.get('scene',r['id'].split('_')[0])==s for r in rows),
                               accepted=sum(r.get('accepted',False)for r in rows if r.get('scene')==s))for s in SCENES}
                dump(a.output/'status.json',dict(phase='smoke'if a.smoke else 'collecting',round=round_index,completed=len(rows),counts=counts))
                print(json.dumps(dict(id=rows[-1]['id'],accepted=rows[-1].get('accepted'),error=rows[-1].get('error'))),flush=True)
        dump(a.output/f'pareto_round_{round_index}.json',[r for s in specs for r in pareto([x for x in rows if x['id']==s['id']])])
    if a.smoke:
        dump(a.output/'complete.json',dict(smoke=True,passed=sum(r.get('accepted',False)for r in rows),total=len(rows)));return
    extra=recollect_front(a.output,specs,rows,runtime,a.workers)
    finalize(a.output,specs,rows,extra)


def recollect_front(folder,specs,rows,runtime,workers):
    jobs=[]
    for spec in specs:
        front=pareto([r for r in rows if r['id']==spec['id']])
        if not front:continue
        front=sorted(front,key=lambda r:(r['metrics']['peak_force_n'],r['parameter_group']))
        chosen=[front[0]]
        other=min(front,key=lambda r:r['metrics']['tracking_rmse_m'])
        if other['parameter_group']!=chosen[0]['parameter_group']:chosen.append(other)
        elif len(front)>1:chosen.append(front[-1])
        for j,row in enumerate(chosen):
            s=json.loads(json.dumps(spec));s['id']+=f'_repeat_{j}'
            rng=np.random.default_rng(int(digest(s['id'])[:8],16))
            if s['scene']=='table_corner':
                s['flags']['seed']=int(rng.integers(1000,99999999))
                s['environment']['TABLE_X_SHIFT_M']=str(float(s['environment']['TABLE_X_SHIFT_M'])+float(rng.uniform(-.001,.001)))
            else:
                delta=np.asarray(json.loads(s['environment']['DATASET_INITIAL_QDELTA']))+rng.normal(0,.0005,7)
                s['environment']['DATASET_INITIAL_QDELTA']=json.dumps(delta.tolist())
                s['flags']['payload_mass']*=float(rng.uniform(.99,1.01))
            s['fixture_hash']=digest(dict(flags=s['flags'],environment=s['environment']))
            jobs.append((s,row['params'],900+j))
    dump(folder/'pareto_recollection_protocol.json',[dict(fixture=s,params=p,candidate=i)for s,p,i in jobs])
    extra=[]
    with ThreadPoolExecutor(max_workers=workers)as pool:
        for f in as_completed([pool.submit(execute,s,p,i,folder,runtime)for s,p,i in jobs]):
            row=f.result();row['selection_basis']='parent_empirical_pareto_with_physical_resampling';extra.append(row)
            dump(folder/'recollection_audit.json',extra)
            dump(folder/'status.json',dict(phase='pareto_recollection',completed=len(extra),total=len(jobs)))
    return extra


def finalize(folder,specs,rows,extra):
    front=[r for s in specs for r in pareto([x for x in rows if x['id']==s['id']])]
    dump(folder/'pareto_final.json',front)
    manifest=dict(contract='four_scene_contact45_action7_v1',observation_dim=45,action_dim=7,
                  action_units=dict(minimum_wbc_scale=.2,linear_yield_mps=.32,angular_yield_radps=.6),
                  train=[],validation=[],test=[],test_scope='source-domain held-out physical groups; not office generalization',
                  teacher_families={s:sorted(set(r['teacher_family']for r in front if r['scene']==s))for s in SCENES})
    provenance=json.loads((folder/'anchors.json').read_text())
    manifest['teacher_information']={s:{k:provenance[s][k]for k in ('family','teacher_force','privileged_task_supervisor','legacy_task_action_schedule')}for s in SCENES}
    seen=set();real=[];sum_x=np.zeros(45);sum_x2=np.zeros(45);n_train=0
    for row in front+[r for r in extra if r.get('accepted')and r.get('dataset_eligible',True)]:
        with np.load(row['trace'],allow_pickle=False)as z:
            x=z['observation'].astype(np.float32);y=z['teacher_action'].astype(np.float32)
            time_values=z['time'].copy()
        # Retain a real stability tail; avoid inflating training with long
        # static endings. Raw full-duration physics traces remain untouched.
        keep=time_values<=row['metrics']['completion_time_s']+2.
        x=x[keep];y=y[keep];time_values=time_values[keep]
        h=hashlib.sha256(x.tobytes()+y.tobytes()).hexdigest()
        if h in seen:continue
        seen.add(h)
        path=folder/'dataset/episodes'/row['scene']/f"{row['id']}_{row['candidate']:03d}.npz";path.parent.mkdir(parents=True,exist_ok=True)
        command_time=time_values if row['scene']=='table_corner'else time_values-.04
        np.savez_compressed(path,observation=x,teacher_action=y,command_time_s=command_time,dt_s=.04)
        item=dict(row,raw_trace=row['trace'],trace=str(path),samples=len(x),augmentation=None,canonical_content_hash=h)
        manifest[row['split']].append(item);real.append(item)
        if row['split']=='train':
            sum_x+=x.sum(axis=0,dtype=np.float64);sum_x2+=(x.astype(np.float64)**2).sum(axis=0);n_train+=len(x)
    manifest['train_clean']=list(manifest['train'])
    for row in manifest['train_clean']:
        with np.load(row['trace'])as z:x=z['observation'].copy();y=z['teacher_action'];times=z['command_time_s']
        rng=np.random.default_rng(int(row['canonical_content_hash'][:8],16))
        for variant in range(2):
            augmented=x.copy();gain=float(rng.uniform(.90,1.10));variation=np.zeros(len(x))
            for t in range(1,len(x)):variation[t]=.95*variation[t-1]+rng.normal(0,.003)
            augmented[:,32:42]*=np.clip(gain+variation,.8,1.2)[:,None]
            delay=variant
            if delay:augmented[1:,32:42]=augmented[:-1,32:42].copy()
            target=Path(row['trace']).with_name(Path(row['trace']).stem+f'_aug{variant}.npz')
            np.savez_compressed(target,observation=augmented,teacher_action=y,command_time_s=times,dt_s=.04)
            manifest['train'].append(dict(row,trace=str(target),augmentation=dict(load_gain=gain,
                load_latency_frames=delay,colored_gain_noise=.003),origin=row['trace']))
    if n_train:
        mean=sum_x/n_train;std=np.sqrt(np.maximum(sum_x2/n_train-mean**2,0))
        floors=np.r_[np.full(7,.03),np.full(7,.03),np.full(6,.02),np.full(6,.01),np.full(6,.02),np.full(7,.1),np.full(3,.2),np.full(3,.1)]
        np.savez_compressed(folder/'dataset/normalization_train_only.npz',mean=mean,std=np.maximum(std,floors),samples=n_train)
    groups={s:set(r['parent_group']for r in manifest[s])for s in ('train','validation','test')}
    assert not(groups['train']&groups['validation']or groups['train']&groups['test']or groups['validation']&groups['test'])
    dump(folder/'manifest.json',manifest)
    counts={s:{part:sum(r['scene']==s for r in manifest[part])for part in ('train','validation','test')}for s in SCENES}
    family_counts={s:{part:len({r['parent_group']for r in manifest[part]if r['scene']==s})for part in ('train','validation','test')}for s in SCENES}
    adequate=all(family_counts[s]['train']>=8 and family_counts[s]['validation']>=2 and family_counts[s]['test']>=2 for s in SCENES)
    summary=dict(complete=adequate,counts=counts,physical_groups=family_counts,unique_real_episodes=len(seen),
         augmented_training_episodes=len(manifest['train'])-len(manifest['train_clean']),
         distinct_vmc_parameter_groups=len({r['parameter_group']for r in real}),
         raw_simulation_trials=len(rows)+len(extra),raw_accepted=sum(r.get('accepted',False)for r in rows+extra),
         office_data_used=False,student_training_started=False,normalization_uses_training_only=True,
         note='Empirical Pareto set within sampled parameters, not a proof of global optimality. Source holdout is not the formal office test.')
    dump(folder/'complete.json',summary);dump(folder/'status.json',dict(phase='complete'if adequate else 'coverage_incomplete',**summary))


if __name__=='__main__':main()
