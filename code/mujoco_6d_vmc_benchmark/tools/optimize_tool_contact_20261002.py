"""Fixed-world teacher/student worker; no scene, task or filter changes."""
from __future__ import annotations
import argparse
import contextlib
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import numpy as np
import mujoco

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import validate_office_apparatus_v5_20260917 as evaluator
import run_vmc_6d_constrained_push_20260918 as vmc
from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig

EXPECTED_MJB='b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def now():return datetime.now(timezone.utc).isoformat()

def write(path,data):
    def encode(value):
        if isinstance(value,np.ndarray):return value.tolist()
        if isinstance(value,np.generic):return value.item()
        raise TypeError(f'Unsupported metadata value: {type(value).__name__}')
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,indent=2,allow_nan=False,default=encode)+'\n');temp.replace(path)

class ParameterTeacher(StableReadoutTeacher):
    def __init__(self,config):
        super().__init__(options=config.get('options',{}),
                         velocity_weight=config.get('velocity_weight',1.),
                         pair_average=config.get('pair_average',False))
        self.channel_gain=np.asarray(config.get('channel_gain',[1.]*7),float)
        if self.channel_gain.shape!=(7,) or not np.isfinite(self.channel_gain).all() or np.any(self.channel_gain<0):
            raise ValueError('Invalid readout gains')
        self.lift_coupling=config.get('lift_coupling')
        self.lift_memory=0.
        self.reference_coupling=config.get('reference_coupling')
        self.reference_memory=0.;self.observation=np.zeros(48)
        self.recovery=config.get('recovery');self.recovery_memory=0.
        if self.recovery:
            c=self.recovery
            required={'threshold_n','attack_s','release_s','offset_m','gain_per_s','velocity_mps'}
            if not set(c)-required<={'activation_mode','progress_distance_m','intent_velocity_mps'} or not required<=set(c) or c.get('activation_mode','envelope') not in ('envelope','integral','progress') or not all(np.isfinite(c[k]) and c[k]>0 for k in required):
                raise ValueError('Invalid bounded reference-relative recovery')
            if c.get('activation_mode')=='progress' and not (np.isfinite(c.get('progress_distance_m',0)) and c.get('progress_distance_m',0)>0):
                raise ValueError('Progress-decayed recovery needs a positive causal travel scale')
            if not (np.isfinite(c.get('intent_velocity_mps',.015)) and c.get('intent_velocity_mps',.015)>0):raise ValueError('Invalid intention velocity normalization')
        if self.lift_coupling:
            c=self.lift_coupling
            if set(c)!={'gain','threshold_n','attack_s','release_s'} or not all(np.isfinite(v) and v>0 for v in c.values()):
                raise ValueError('Invalid proprioceptive virtual coupling')
        if self.reference_coupling:
            c=self.reference_coupling
            required={'mode','gain','threshold_n','attack_s','release_s','integral_rate_nps','max_force_n'}
            if set(c)!=required or c['mode'] not in ('force','stall_integral') or not all(np.isfinite(v) and v>0 for k,v in c.items() if k!='mode'):
                raise ValueError('Invalid reference-aware coupling')
    def observe(self,observation):
        value=np.asarray(observation,dtype=float)
        if value.shape!=(48,) or not np.isfinite(value).all():raise ValueError('Expected canonical proprio48')
        self.observation=value.copy()
    def reset(self):
        super().reset();self.lift_memory=0.;self.reference_memory=0.;self.recovery_memory=0.;self.observation=np.zeros(48)
    def act(self,wrench_world,dt=.04):
        wrench=np.asarray(wrench_world,dtype=float).copy()
        if self.lift_coupling:
            c=self.lift_coupling
            # Active virtual coupling: an estimated opposing x load excites
            # the vertical virtual spring, with a causal release envelope.
            # No time, phase, object, contact identity or distance is read.
            target=max(0.,-wrench[0]-c['threshold_n'])
            tau=c['attack_s'] if target>self.lift_memory else c['release_s']
            self.lift_memory+=(1-np.exp(-dt/tau))*(target-self.lift_memory)
            wrench[2]+=c['gain']*self.lift_memory
        if self.reference_coupling:
            c=self.reference_coupling;obs=self.observation
            path=obs[45:47];horizontal=min(1.,float(np.linalg.norm(path)))
            direction=path/max(float(np.linalg.norm(path)),1e-12)
            command=obs[14:16];actual=command-obs[26:28]
            desired=float(command@direction);progress=float(actual@direction)
            opposition=max(0.,-float(wrench[:2]@direction)-c['threshold_n'])
            intent=float(np.clip(desired/.03,0,1))*horizontal**2
            if c['mode']=='force':
                target=c['gain']*opposition*intent
                tau=c['attack_s'] if target>self.reference_memory else c['release_s']
                self.reference_memory+=(1-np.exp(-dt/tau))*(target-self.reference_memory)
            else:
                stalled=float(np.clip((desired-progress-.005)/.02,0,1))
                evidence=stalled*float(np.clip(opposition,0,1))*intent
                # A bounded virtual-spring excitation integrates only measured
                # resistance plus lack of progress along the nominal command.
                self.reference_memory+=dt*(c['integral_rate_nps']*evidence-self.reference_memory*(1-evidence)/c['release_s'])
            self.reference_memory=float(np.clip(self.reference_memory,0,c['max_force_n']))
            wrench[2]+=self.reference_memory*horizontal**2
        action=super().act(wrench,dt)*self.channel_gain
        if self.recovery:
            c=self.recovery;obs=self.observation
            path=obs[45:47];horizontal=min(1.,float(np.linalg.norm(path)))
            direction=path/max(float(np.linalg.norm(path)),1e-12)
            command=obs[14:17];actual=command-obs[26:29]
            desired=float(command[:2]@direction);progress=float(actual[:2]@direction)
            opposition=max(0.,-float(wrench[:2]@direction)-c['threshold_n'])
            evidence=float(np.clip(opposition,0,1))*float(np.clip((desired-progress)/.015,0,1))*horizontal**2
            if c.get('activation_mode','envelope') in ('integral','progress'):
                rising=evidence/c['attack_s']
                if c['activation_mode']=='progress':
                    intent=float(np.clip(desired/c.get('intent_velocity_mps',.015),0,1))*horizontal**2
                    falling=max(0.,progress)/c['progress_distance_m']+(1-intent)/c['release_s']
                else:falling=(1-evidence)/c['release_s']
                equilibrium=rising/max(rising+falling,1e-12)
                self.recovery_memory+=(1-np.exp(-dt*(rising+falling)))*(equilibrium-self.recovery_memory)
            else:
                tau=c['attack_s'] if evidence>self.recovery_memory else c['release_s']
                self.recovery_memory+=(1-np.exp(-dt/tau))*(evidence-self.recovery_memory)
            activation=self.recovery_memory*horizontal**2
            # Shift the virtual equilibrium relative to the existing reference,
            # never a world pose. Bounded velocity regulation prevents the
            # unbounded lift of a force-only virtual spring. This teacher-only
            # active mechanism has no passivity guarantee; students must learn
            # its dynamics independently and use no teacher at deployment.
            target_velocity=c['gain_per_s']*(c['offset_m']+obs[22])
            correction=np.clip(target_velocity-command[2],-c['velocity_mps'],c['velocity_mps'])
            action[3]=(1-activation)*action[3]+activation*correction/.32
        return np.clip(action,-1.,1.)

def audit(run,config,checkpoint=None,memory_ablation='none'):
    result=json.loads((run/'rollout.json').read_text())
    with np.load(run/'rollout.npz',allow_pickle=False) as z:
        obs=z['observation']; action=z['applied_action']
        if checkpoint:
            from current_student_policy_20260921 import load_current
            actor=load_current(checkpoint);actor.reset()
            states=[];pred=[]
            for o in obs:
                if memory_ablation=='reset_each_observation':actor.reset()
                pred.append(actor.act(o));obj=getattr(actor,'obj',actor)
                if hasattr(obj,'state'):states.append(obj.state.copy())
            state_error=float(np.max(np.abs(np.asarray(states)-z['reservoir_state']))) if states else None
        else:
            actor=ParameterTeacher(config)
            pred=[]
            for o in obs:actor.observe(o);pred.append(actor.act(o[39:45]))
            state_error=None
        action_error=float(np.max(np.abs(np.asarray(pred)-action)))
        if action_error>1e-10 or (state_error is not None and state_error>1e-10):
            raise ValueError('Actor replay mismatch')
        stages={str(int(s)):dict(start_s=float(z['time'][z['stage']==s][0]),
                    end_s=float(z['time'][z['stage']==s][-1]),
                    mean_action=action[z['stage']==s].mean(0).tolist(),
                    median_wrench=np.median(obs[z['stage']==s,39:45],axis=0).tolist()) for s in set(z['stage'])}
    with np.load(run/'execution_chain.npz') as chain:
        np.testing.assert_array_equal(action,chain['requested_action'])
        if len(chain['yield_twist'])!=len(action):raise ValueError('Missing filtered actions')
        filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
        replay=[filt.filter(a,.04) for a in action]
        np.testing.assert_array_equal(np.asarray([v.raw_action_clipped for v in replay]),chain['clipped_action'])
        np.testing.assert_array_equal(np.asarray([v.cartesian_yield_twist for v in replay]),chain['yield_twist'])
        np.testing.assert_array_equal(np.asarray([v.wbc_scale for v in replay]),chain['wbc_scale'])
        filter_replay_max_abs=0.
    with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
        dt=z['dt'].astype(float);error=z['error'].astype(float)
        values=[float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum())),
                float(np.max(np.abs(z['qfrc_actuator']))),
                float(np.max(np.linalg.norm(z['twist'][:,:3].astype(float),axis=1)))]
        if not all(np.isfinite(z[k]).all() for k in z.files):raise ValueError('Nonfinite physical metrics')
        physical_seconds=float(dt.sum())
    keys=['position_rmse_3d_m','generalized_actuator_torque_peak_nm','linear_speed_peak_mps']
    np.testing.assert_allclose(values,[result['metrics'][k] for k in keys],rtol=3e-7,atol=1e-7)
    if result['full_task_horizon_completed']:np.testing.assert_allclose(physical_seconds,55.,atol=1e-7,rtol=0)
    row=dict(task_success=result['task_success'],strict_success=result['strict_success'],
             memory_ablation=memory_ablation,
             full_horizon=result['full_task_horizon_completed'],stage=result['final_task_stage'],
             rmse_mm=values[0]*1000,peak_torque_nm=values[1],peak_speed_mps=values[2],
             penetration_mm=result['stats']['max_external_penetration_m']*1000,
             edge_penetration_mm=result['stats']['unexpected_edge']['max_penetration_m']*1000,
             worst_pair=result['stats']['worst_external_pair'],physical_seconds=physical_seconds,
             max_lift_m=result['max_lift_m'],object_final_position=result.get('object_final_position'),
             placement_error_xy_m=result.get('placement_error_xy_m'),abort_reason=result['abort_reason'],
             action_replay_max_abs=action_error,reservoir_replay_max_abs=state_error,stages=stages,
             common_filter_replay_max_abs=filter_replay_max_abs,
             model_sha256=sha(run/'rollout.mjb'),trace_sha256=sha(run/'rollout.npz'),
             chain_sha256=sha(run/'execution_chain.npz'),metrics_sha256=sha(run/'rollout_metrics/substep_metrics.npz'))
    write(run/'AUDIT.json',row);return row

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--memory-ablation',choices=('none','reset_each_observation'),default='none')
    p.add_argument('--contact-audit',action='store_true',help='Independent read-only per-physics-step penetration trace')
    args=p.parse_args()
    assert mujoco.__version__=='3.11.0'
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    config=json.loads(args.config.read_text());ParameterTeacher(config)
    run=args.output.resolve();run.mkdir(parents=True,exist_ok=False)
    shutil.copy2(args.config,run/'config.json')
    reference=json.loads(args.reference.read_text())
    a=dict(reference['arguments'],output=run/'rollout',render=False,impact_slowmo=False,
           teacher='vmc6d',esn_model=None,esn_mode='shadow',physics_probe_s=None)
    checkpoint=None
    if args.memory_ablation!='none' and not args.checkpoint:raise ValueError('Memory ablation needs an ESN checkpoint')
    if args.checkpoint:
        checkpoint=run/'checkpoint.npz';shutil.copy2(args.checkpoint,checkpoint)
        a.update(teacher='none',esn_model=checkpoint,esn_mode='control',memory_ablation=args.memory_ablation)
    source_files=sorted((ROOT/'scripts').glob('*.py'))+[Path(__file__)]
    sources={str(f.relative_to(ROOT)):sha(f) for f in source_files}
    subprocess.run(['tar','-czf',str(run/'source_overlay.tar.gz'),*sources],cwd=ROOT,check=True)
    record=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=sources,
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_commit_is_base_only=True,source_status='Run-specific overlay hashes are authoritative; not a clean commit execution',host=platform.node(),pid=os.getpid(),
                python=sys.executable,mujoco=mujoco.__version__,memory_max=memory,threads=1,
                reference_sha256=sha(args.reference),config=config,config_sha256=sha(args.config),
                checkpoint_sha256=sha(checkpoint) if checkpoint else None,
                arguments={k:str(v) if isinstance(v,Path) else v for k,v in a.items()})
    write(run/'execution.json',record)
    teacher_rows=[];chain_rows=[];latest_observation=None
    class RecordedTeacher(ParameterTeacher):
        def __init__(self,unused):super().__init__(config)
        def act(self,wrench_world,dt=.04):
            assert latest_observation is not None
            np.testing.assert_array_equal(wrench_world,latest_observation[39:45])
            self.observe(latest_observation)
            action=super().act(wrench_world,dt)
            teacher_rows.append(dict(wrench=np.asarray(wrench_world).copy(),requested_action=action.copy(),
                       effective_wrench=self.effective_wrench.copy(),lift_memory=self.lift_memory,reference_memory=self.reference_memory,recovery_memory=self.recovery_memory,
                       filtered=self.filtered.copy(),offset=self.offset.copy(),velocity=self.velocity.copy()))
            return action
    original_teacher=vmc.SixDVirtualDynamics;original_filter=VelocityResidualActionFilter.filter
    original_observation=evaluator.canonical_observation
    def capture_observation(*values):
        nonlocal latest_observation
        latest_observation=original_observation(*values)
        return latest_observation
    original_save=mujoco.mj_saveModel
    original_metrics=evaluator.EpisodeMetrics
    class ContactAuditMetrics(original_metrics):
        def __init__(self,env,*values,**kwargs):
            super().__init__(env,*values,**kwargs)
            self.contact_rows=np.zeros((self.capacity,2))
            self.robot_flags=np.zeros(env.model.ngeom,dtype=bool)
            self.robot_flags[list(env._push_audit_robot_geom_ids)]=True
            self.edge_id=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_unexpected_edge')
            self.payload_id=mujoco.mj_name2id(env.model,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
        def sample(self):
            super().sample();m=self.env.model;d=self.env.data
            if not d.ncon:return
            g1=d.contact.geom1[:d.ncon];g2=d.contact.geom2[:d.ncon];dist=d.contact.dist[:d.ncon]
            external=(self.robot_flags[g1]^self.robot_flags[g2])&(m.geom_bodyid[g1]!=self.env._target_body_id)&(m.geom_bodyid[g2]!=self.env._target_body_id)
            edge=((g1==self.edge_id)&(self.robot_flags[g2]|(g2==self.payload_id)))|((g2==self.edge_id)&(self.robot_flags[g1]|(g1==self.payload_id)))
            self.contact_rows[self.count-1]=[max(0.,float(np.max(-dist[external],initial=0.))),max(0.,float(np.max(-dist[edge],initial=0.)))]
        def save(self,directory):
            result=super().save(directory)
            np.savez_compressed(run/'independent_contacts.npz',time=self.arrays['time'][:self.count],
                                external_penetration_m=self.contact_rows[:self.count,0],edge_penetration_m=self.contact_rows[:self.count,1])
            return result
    def capture_filter(self,action,dt):
        result=original_filter(self,action,dt)
        if not chain_rows:record['action_filter_config']=asdict(self.config)
        limits=np.r_[np.full(3,self.config.maximum_linear_yield_mps),np.full(3,self.config.maximum_angular_yield_radps)]
        filtered=np.r_[(1-result.wbc_scale)/(1-self.config.minimum_wbc_scale),result.cartesian_yield_twist/limits]
        chain_rows.append(dict(requested_action=np.asarray(action).copy(),
                     clipped_action=result.raw_action_clipped.copy(),yield_twist=result.cartesian_yield_twist.copy(),
                     filtered_action=filtered,wbc_scale=result.wbc_scale,slew_limited=result.slew_limited))
        return result
    def checked_save(model,filename,buffer):
        original_save(model,filename,buffer)
        if sha(filename)!=EXPECTED_MJB:raise ValueError('Frozen environment MJB differs')
    vmc.SixDVirtualDynamics=RecordedTeacher;VelocityResidualActionFilter.filter=capture_filter;mujoco.mj_saveModel=checked_save
    evaluator.canonical_observation=capture_observation
    if args.contact_audit:evaluator.EpisodeMetrics=ContactAuditMetrics
    try:
        with (run/'rollout.log').open('w') as log,contextlib.redirect_stdout(log):evaluator.run(SimpleNamespace(**a))
        for name,rows in [('teacher_internal',teacher_rows),('execution_chain',chain_rows)]:
            if rows:np.savez_compressed(run/(name+'.npz'),**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
        record['audit']=audit(run,config,checkpoint,args.memory_ablation)
        if args.contact_audit:
            with np.load(run/'independent_contacts.npz') as z:
                values=[float(z['external_penetration_m'].max()*1000),float(z['edge_penetration_m'].max()*1000)]
            np.testing.assert_allclose(values,[record['audit']['penetration_mm'],record['audit']['edge_penetration_mm']],rtol=0,atol=1e-12)
            record['independent_contact_audit']=dict(sha256=sha(run/'independent_contacts.npz'),external_penetration_mm=values[0],edge_penetration_mm=values[1])
        assert all(sha(ROOT/k)==v for k,v in sources.items()),'Live source changed'
        record['status']='complete'
    except BaseException as exc:
        record.update(status='failed_preserved',error=repr(exc));raise
    finally:
        vmc.SixDVirtualDynamics=original_teacher;VelocityResidualActionFilter.filter=original_filter;mujoco.mj_saveModel=original_save
        evaluator.canonical_observation=original_observation
        evaluator.EpisodeMetrics=original_metrics
        record['ended_utc']=now();write(run/'execution.json',record)
    print(json.dumps(record['audit'],indent=2))

if __name__=='__main__':main()
