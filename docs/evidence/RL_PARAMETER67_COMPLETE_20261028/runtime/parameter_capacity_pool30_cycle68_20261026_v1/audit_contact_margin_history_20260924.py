"""Read-only contact geometry queries on archived poses; never calls mj_step."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import mujoco
import numpy as np


def read(p): return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def stage_at(times,events):
    stages=np.zeros(len(times),dtype=int)
    for event in events: stages[times>=event['t']-1e-8]=event['stage']
    return stages
def longest(mask):
    best=run=0
    for value in mask:
        run=run+1 if value else 0;best=max(run,best)
    return best


def history_audit(root):
    protocol=read(root/'protocol.json');results=read(root/'FINAL_RESULT.json')
    pairs=[]
    for f in protocol['fixtures']:
        part=sorted([r for r in results['rows'] if r['fixture']['seed']==f['seed']],key=lambda r:r['requested_event_stage'])
        entries=[];traces=[];hashes=[]
        for row in part:
            p=root/'jobs'/row['id']/'rollout';result=read(p/'rollout.json')
            traces.append(dict(np.load(p/'rollout.npz',allow_pickle=False)))
            hashes.append(row['model_mjb_sha256'])
            entries.append(dict(id=row['id'],requested=row['requested_event_stage'],
                trigger_s=result['fixture_trigger_time_s'],first_contact_s=result['contact']['first_s'],
                actual_first_stage=result['contact']['first_stage'],first_payload_held=result['contact']['first_payload_held'],
                rod_first_contact_s=result['panel_audit']['contacts']['push_rod_geom']['first_s'],
                task_success=result['success'],strict_success=row['strict_success']))
        a,b=traces
        delta=np.max(np.abs(a['observation']-b['observation']),axis=1)
        pairs.append(dict(seed=f['seed'],split=f['split'],same_model=len(set(hashes))==1,entries=entries,
            first_observation_difference_record_time_s=float(a['time'][np.flatnonzero(delta>1e-10)[0]]),
            maximum_observation_difference=float(delta.max()),
            differing_arrays=[k for k in a if not np.array_equal(a[k],b[k])]))
    return dict(pairs=pairs,protocol_sha256=sha(root/'protocol.json'),result_sha256=sha(root/'FINAL_RESULT.json'),
        teacher_source_id=protocol['teacher_source_id'],teacher=protocol['teacher'])


def contact_audit(root):
    rows=read(root/'FINAL_RESULT.json')['rows'];records=[];traces={}
    native_bit=int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
    for row in sorted(rows,key=lambda r:(r['candidate']['id'],r['fixture']['seed'])):
        method=row['candidate']['id'];seed=row['fixture']['seed'];p=root/method/str(seed)/'rollout'
        result=read(p/'rollout.json');contacts=result['panel_audit']['contacts']
        ext={k:v for k,v in contacts.items() if k!='target_object_geom'}
        peak_name=max(ext,key=lambda k:ext[k]['max_penetration_m']);peak=ext[peak_name]
        trace=dict(np.load(p/'rollout.npz',allow_pickle=False));traces[(method,seed)]=trace
        states=np.load(p/'physics_states.npz',allow_pickle=False)['state']
        sampled=np.load(p/'contact_samples.npz',allow_pickle=False);names=sampled['names'].tolist();bins=sampled['samples']
        bin_stage=stage_at(bins[:,0]-.04+1e-8,result['events'])
        interval={}
        for name,v in ext.items():
            if v['max_penetration_m']<=0: continue
            i=names.index(name);duration=bins[:,1+2*i];force=bins[:,2+2*i]
            assert abs(duration.sum()-v['duration_s'])<1e-7
            interval[name]=dict(peak_penetration_mm=1000*v['max_penetration_m'],
                margin_to_gate_um=200-1e6*v['max_penetration_m'],bodies_with_force_over_0p05N=v['bodies'],
                contact_duration_s=float(duration.sum()),active_40ms_bins=int((duration>0).sum()),
                longest_active_bin_span_s=.04*longest(duration>0),
                max_force_bin_end_s=float(bins[force.argmax(),0]),max_force_n=float(force.max()),
                contact_duration_by_control_stage_s={str(s):float(duration[bin_stage==s].sum()) for s in np.unique(bin_stage)})
        model=mujoco.MjModel.from_binary_path(str(p/'rollout.mjb'));data=mujoco.MjData(model)
        options={k:float(getattr(model.opt,k)) for k in ('timestep','iterations','tolerance','ccd_iterations','ccd_tolerance','solver','integrator','disableflags')}
        # Native MJB stores the initial masks; runtime sets rod masks and mocap.
        rod=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'push_rod_geom')
        model.geom_contype[rod]=8;model.geom_conaffinity[rod]=15
        geom_names={g:mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,g) or f'unnamed_geom_{g}' for g in range(model.ngeom)}
        bodies={g:mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(model.geom_bodyid[g])) or '' for g in range(model.ngeom)}
        obstacles={g:n for g,n in geom_names.items() if n in ext}
        robot={g for g,b in bodies.items() if (b.startswith('fr3_link') or b in ('hand','left_finger','right_finger'))
               and int(model.geom_group[g])!=2 and geom_names[g]!='hand_ball_proxy'}
        # Match archive environment's externally moved obstacle, excluded from conclusions.
        for b in range(model.nbody):
            name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,b) or ''
            if name=='moving_obstacle' and model.body_mocapid[b]>=0:
                data.mocap_pos[model.body_mocapid[b]]=[3.,3.,3.]
        sparse=[];pairs={};native_sparse=[]
        flags=int(model.opt.disableflags)
        for i,state in enumerate(states):
            data.qpos[:]=state[1:1+model.nq];data.qvel[:]=state[1+model.nq:1+model.nq+model.nv]
            data.time=state[0];mujoco.mj_kinematics(model,data)
            for native in (False,True):
                model.opt.disableflags=flags & ~native_bit if native else flags
                mujoco.mj_collision(model,data)
                worst=dict(depth_m=0.,obstacle=None,robot_geom=None,robot_body=None)
                for c in data.contact:
                    g1,g2=int(c.geom1),int(c.geom2)
                    if g1 in obstacles and g2 in robot: obstacle,rg=g1,g2
                    elif g2 in obstacles and g1 in robot: obstacle,rg=g2,g1
                    else: continue
                    depth=max(0.,-float(c.dist));name=obstacles[obstacle]
                    if name=='moving_obstacle_geom':continue
                    if depth>worst['depth_m']:worst=dict(depth_m=depth,obstacle=name,robot_geom=geom_names[rg],robot_body=bodies[rg])
                    if not native and depth>0:
                        key=name+' × '+geom_names[rg]
                        if key not in pairs or depth>pairs[key]['sampled_peak_depth_m']:
                            pairs[key]=dict(sampled_peak_depth_m=depth,time_s=float(state[0]),stage=int(trace['stage'][i]),robot_body=bodies[rg])
                worst.update(time_s=float(state[0]),stage=int(trace['stage'][i]))
                (native_sparse if native else sparse).append(worst)
            model.opt.disableflags=flags
        depths=np.array([r['depth_m'] for r in sparse]);native_depths=np.array([r['depth_m'] for r in native_sparse])
        worst=sparse[int(depths.argmax())]
        records.append(dict(method=method,seed=seed,task_success=row['task_success'],strict_success=row['strict_success'],
            original_peak_obstacle=peak_name,original_peak_mm=peak['max_penetration_m']*1000,
            original_gate_margin_um=200-1e6*peak['max_penetration_m'],obstacles=interval,
            sparse_worst=worst,sparse_samples_above_gate=int((depths>=.0002).sum()),
            sparse_above_gate_occupancy_proxy_s=.04*float((depths>=.0002).sum()),
            sparse_longest_above_gate_bin_span_s=.04*longest(depths>=.0002),
            sampled_pairs=pairs,collision_options=options,model_sha256=sha(p/'rollout.mjb'),
            fixed_pose_native_ccd_comparison=dict(original_native_enabled=not bool(flags&native_bit),
                native_sampled_peak_mm=1000*float(native_depths.max()),
                largest_absolute_depth_difference_um=1e6*float(np.max(abs(native_depths-depths))),
                differing_gate_classification_samples=int(np.sum((depths>=.0002)!=(native_depths>=.0002)))),
            original_rod_contact_pairs=[pair for pair in result['contact']['pairs'] if 'push_rod_geom' in pair],
            input_sha256={name:sha(p/name) for name in ('rollout.json','rollout.npz','physics_states.npz','contact_samples.npz')},
            sparse_trace=sparse,native_sparse_trace=native_sparse))
        print(json.dumps(dict(audited=method,seed=seed,original_peak=peak_name,original_mm=peak['max_penetration_m']*1000,
            sparse_mm=worst['depth_m']*1000,over_samples=int((depths>=.0002).sum()))),flush=True)
    windows=[]
    for seed in sorted({r['fixture']['seed'] for r in rows}):
        methods=sorted(k[0] for k in traces if k[1]==seed)
        onset=max(float(traces[(method,seed)]['time'][np.flatnonzero(traces[(method,seed)]['stage']==3)[0]]) for method in methods)
        targets=[traces[(method,seed)]['target'][-1] for method in methods]
        assert all(np.array_equal(t,targets[0]) for t in targets)
        for method in methods:
            t=traces[(method,seed)];stages={}
            for name,mask in [('common_loaded_absolute_window',t['time']>=onset-1e-8),('last6s_absolute_window',t['time']>18+1e-8)]:
                assert np.all(t['stage'][mask]==3) and np.all(t['target'][mask]==targets[0])
                errors=t['position'][mask]-targets[0]
                stages[name]=dict(start_s=onset if name.startswith('common') else 18.,samples=int(mask.sum()),
                    rmse_3d_mm=1000*float(np.sqrt(np.mean(np.sum(errors**2,axis=1)))),
                    rmse_xy_mm=1000*float(np.sqrt(np.mean(np.sum(errors[:,:2]**2,axis=1)))),
                    rmse_z_mm=1000*float(np.sqrt(np.mean(errors[:,2]**2))))
            windows.append(dict(method=method,seed=seed,common_final_target_m=targets[0].tolist(),windows=stages))
    return records,windows


def main():
    p=argparse.ArgumentParser();p.add_argument('--validation',type=Path,required=True);p.add_argument('--history',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if mujoco.__version__!='3.11.0':raise RuntimeError('Use matching MuJoCo 3.11.0; no package mutation')
    history=history_audit(args.history);contacts,windows=contact_audit(args.validation)
    summary={}
    for method in sorted({r['method'] for r in contacts}):
        part=[r for r in contacts if r['method']==method];w=[r for r in windows if r['method']==method]
        summary[method]=dict(original_peak_obstacles=dict(Counter(r['original_peak_obstacle'] for r in part)),
            penetration_pass=sum(r['original_gate_margin_um']>0 for r in part),
            margin_um=[r['original_gate_margin_um'] for r in part],
            sparse_above_gate_samples=sum(r['sparse_samples_above_gate'] for r in part),
            sparse_geometry_native_largest_diff_um=max(r['fixed_pose_native_ccd_comparison']['largest_absolute_depth_difference_um'] for r in part),
            windows={name:{metric:float(np.mean([r['windows'][name][metric] for r in w])) for metric in ('rmse_3d_mm','rmse_xy_mm','rmse_z_mm')} for name in w[0]['windows']})
    report=dict(history=history,contacts=contacts,common_windows=windows,summary=summary,
        semantics=dict(simulation_steps_executed=0,geometry_query='mj_kinematics + mj_collision on saved qpos, original and native CCD scratch options',
            engine=mujoco.__version__,query_architecture=platform.machine(),original_architecture='aarch64',
            original_physics_step_s=5e-5,saved_pose_interval_s=.04,
            penetration_time_series_available=False,full_substep_peak_time_and_duration_identifiable=False,
            sparse_time_proxy_is_exact_duration=False,original_gates_unchanged=True,
            contact_duration_bins='exact accumulated force>0.05N physical substeps per obstacle per40ms; not penetration exceedance duration',
            comparison_scope='posthoc diagnostic, not a replacement score, no parameter selection'),
        sources={str(p):sha(p) for p in [args.validation/'FINAL_RESULT.json',args.history/'FINAL_RESULT.json',Path(__file__)]})
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
