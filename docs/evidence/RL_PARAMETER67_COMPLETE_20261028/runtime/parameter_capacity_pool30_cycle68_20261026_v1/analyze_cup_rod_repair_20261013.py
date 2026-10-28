"""Audit recorded contact geometry and paired repair outcomes, without physics."""
import hashlib,json
from pathlib import Path
import numpy as np
import mujoco

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_payload_bridge_20261013'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def analyze(p):
    result=read(p/'rollout.json');model=mujoco.MjModel.from_binary_path(str(p/'rollout.mjb'))
    data=mujoco.MjData(model);contacts=[]
    with np.load(p/'rollout.npz') as z,np.load(p/'execution_chain.npz') as chain:
        obs=z['observation'];time=z['neuron_time'];actual=obs[:,14:17]-obs[:,26:29]
        for i,t in enumerate(z['time']):
            for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):getattr(data,k)[:]=z[k][i]
            mujoco.mj_forward(model,data)
            pairs=[]
            for c in data.contact:
                names=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or str(g) for g in (c.geom1,c.geom2)]
                if 'target_object_geom' in names and any('cup' in n for n in names):
                    pairs.append(dict(names=names,distance_m=float(c.dist)))
            if pairs:contacts.append(dict(time_s=float(t),pairs=pairs))
        windows=[]
        for lo,hi in [(12.,18.),(27.,42.),(30.,55.)]:
            m=(time>=lo-1e-7)&(time<hi-1e-7);raw=chain['requested_action'][m,1:4]*.32
            windows.append(dict(start_s=lo,end_s=hi,samples=int(m.sum()),
                actual_xyz_velocity_step_rms_mps=np.sqrt(np.mean(np.diff(actual[m],axis=0)**2,axis=0)).tolist(),
                raw_xyz_step_rms_mps=np.sqrt(np.mean(np.diff(raw,axis=0)**2,axis=0)).tolist(),
                raw_x_flips=int(np.sum(raw[:-1,0]*raw[1:,0]<0)),
                raw_x_saturation_fraction=float(np.mean(abs(raw[:,0])>=.32-1e-8)),
                nominal_mean_xyz_mps=obs[m,14:17].mean(0).tolist(),
                filtered_yield_mean_xyz_mps=chain['yield_twist'][m,:3].mean(0).tolist(),
                filtered_feedback_scale_mean=float(chain['wbc_scale'][m].mean()),
                actual_mean_xyz_mps=actual[m].mean(0).tolist()))
        final_object=z['object_position'][-1].tolist()
    return dict(task=result['task_success'],strict=result['strict_success'],stage=result['final_task_stage'],
        full_horizon=result['full_task_horizon_completed'],events=result['task_events'],
        rmse_m=result['metrics']['position_rmse_3d_m'],
        peak_torque_nm=result['metrics']['generalized_actuator_torque_peak_nm'],
        peak_speed_mps=result['metrics']['linear_speed_peak_mps'],
        penetration_mm=result['stats']['max_external_penetration_m']*1000,
        contact_events=result['stats']['events'],cup_valid=result['cup_valid'],
        cup_shift_m=result['stats']['cup_shift_m'],cup_tilt_deg=result['stats']['cup_tilt_deg'],
        final_object=final_object,windows=windows,
        payload_cup=dict(sampled_contact_frames=len(contacts),
            first_s=contacts[0]['time_s'] if contacts else None,last_s=contacts[-1]['time_s'] if contacts else None,
            span_s=contacts[-1]['time_s']-contacts[0]['time_s'] if contacts else 0.,
            caveat='25Hz saved-pose mj_forward geometry, not a substep duration/force measurement or proof of no contact between frames',samples=contacts),
        hashes={k:sha(p/k) for k in ('rollout.json','rollout.npz','rollout.mjb','checkpoint.npz','execution.json')})

def main():
    paths=dict(previous=ROOT/'outputs/original_esn_continuous_reference_20261013/episode',
        path_only=OUT/'path_only/episode',path_bridge=OUT/'path_bridge_v2/episode',
        friction_probe=OUT/'path_bridge_friction_probe/episode')
    rows={k:analyze(p) for k,p in paths.items()}
    assert len({r['hashes']['checkpoint.npz'] for r in rows.values()})==1
    assert len({r['hashes']['rollout.mjb'] for r in rows.values()})==1
    e=[read(p/'execution.json') for p in paths.values()]
    assert all(x['status']=='complete' for x in e)
    assert all(x['action_filter_config']==e[0]['action_filter_config'] for x in e)
    meta=[read(p/'rollout.json') for p in paths.values()]
    for key in ('placement_destination','placement_support_geoms','schedule','observer_settings','contact_required','physics_resolution'):
        assert all(x[key]==meta[0][key] for x in meta),key
    plans=[read(paths[k]/'reference.json') for k in ('path_only','path_bridge','friction_probe')]
    assert all(p['plan']==plans[0]['plan'] for p in plans)
    limits=e[-1]['action_filter_config']
    with np.load(paths['path_bridge']/'servo_actions.npz') as z:
        velocity=np.vstack([np.zeros(6),z['yield_twist']])
        scale=np.r_[1.,z['wbc_scale']]
        observed=dict(linear_amplitude=float(abs(velocity[:,:3]).max()),
            angular_amplitude=float(abs(velocity[:,3:]).max()),
            linear_rate=float(abs(np.diff(velocity[:,:3],axis=0)).max()/.004),
            angular_rate=float(abs(np.diff(velocity[:,3:],axis=0)).max()/.004),
            scale_rate=float(abs(np.diff(scale)).max()/.004),minimum_scale=float(scale.min()))
        for name,key in [('linear_amplitude','maximum_linear_yield_mps'),('angular_amplitude','maximum_angular_yield_radps'),
                         ('linear_rate','maximum_linear_yield_rate_mps2'),('angular_rate','maximum_angular_yield_rate_radps2'),
                         ('scale_rate','maximum_scale_rate_per_s')]:
            assert observed[name]<=limits[key]+1e-10,(name,observed[name],limits[key])
        assert observed['minimum_scale']>=limits['minimum_wbc_scale']-1e-12
    failed=OUT/'path_bridge/episode'
    rejection=read(failed/'execution.json')
    assert rejection['status']=='failed_preserved'
    value=dict(runs=rows,source_sha256=sha(Path(__file__)),same_checkpoint_scene_filter_schedule_gates=True,
        excluded_adapter_failure=dict(path=str(failed),execution_sha256=sha(failed/'execution.json'),
            error=rejection['error'],reason='Bridge consumed neutral joint composition scale1 rather than actual feedback scale; full failed trace preserved, not valid B'),
        all_servo_amplitude_rate_bounds_pass=True,observed_servo_bounds=observed,
        paired_A_B_plan_identical=True,
        caveats=['Different contact exposure across repaired trajectories; not a pure policy ranking',
                 'Planning around known cup is not a demonstration of ESN cup compliance',
                 'Actuator interpolation is a new common adapter, not an ESN weight or parameter change',
                 'C is an explicitly added model-friction feedforward diagnostic after A; not a predeclared original A/B arm or evidence of ESN superiority',
                 'Reference RMSE differs after path change; no direct RMSE improvement claim'])
    target=OUT/'COMPARISON.json'
    if target.exists():raise FileExistsError(target)
    target.write_text(json.dumps(value,indent=2)+'\n')
    for k,r in rows.items():print(k,json.dumps({key:r[key] for key in ('task','strict','stage','events','peak_torque_nm','peak_speed_mps','penetration_mm','windows')}))
    print('cup geometry',{k:{j:r['payload_cup'][j] for j in ('sampled_contact_frames','first_s','last_s','span_s')} for k,r in rows.items()})

if __name__=='__main__':main()
