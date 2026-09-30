"""Read-only live-contact capture around mj_step; no forward/collision calls."""
from __future__ import annotations
from contextlib import AbstractContextManager
import json
from pathlib import Path
import mujoco
import numpy as np


THRESHOLDS_M=np.array([.00018,.00019,.00020,.00021],dtype=np.float64)
STATE_SPEC=int(mujoco.mjtState.mjSTATE_INTEGRATION)


class ThresholdRuns:
    def __init__(self,n):
        self.count=np.zeros((n,4),dtype=np.int64)
        self.current=np.zeros_like(self.count);self.longest=np.zeros_like(self.count)
    def update(self,depth):
        exceeded=np.asarray(depth)[:,None]>=THRESHOLDS_M[None,:]
        self.count+=exceeded
        self.current=(self.current+1)*exceeded
        self.longest=np.maximum(self.longest,self.current)


def pack_state(model,data):
    state=np.empty(mujoco.mj_stateSize(model,STATE_SPEC),dtype=np.float64)
    mujoco.mj_getState(model,data,state,STATE_SPEC)
    return state


class ContactEpisode:
    def __init__(self,env,directory,chunk_size=8192,event_chunk_size=128):
        self.env=env;self.model=env.model;self.data=env.data
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=False)
        model=self.model
        if int(model.opt.integrator)!=int(mujoco.mjtIntegrator.mjINT_IMPLICITFAST):
            raise ValueError('This protocol supports the frozen implicitfast integrator only')
        self.dt=float(model.opt.timestep);self.stage_names=tuple(env.reference.names)
        self.obstacles={int(g):name for g,name in env.audit_obstacles.items() if name!='target_object_geom'}
        self.ids=sorted(self.obstacles);self.names=[self.obstacles[g] for g in self.ids]
        self.column={g:i for i,g in enumerate(self.ids)}
        self.robot=set(env._push_audit_robot_geom_ids)
        n=len(self.ids);self.chunk_size=chunk_size;self.event_chunk_size=event_chunk_size
        self.buffers=dict(time_before_s=np.empty(chunk_size),time_after_s=np.empty(chunk_size),
            stage=np.empty(chunk_size,dtype=np.int16),depth_m=np.empty((chunk_size,n)),
            pair_geom_ids=np.empty((chunk_size,n,2),dtype=np.int32),
            peak_pair_normal_force_n=np.empty((chunk_size,n)),contact_count=np.empty((chunk_size,n),dtype=np.int16))
        self.count=0;self.used=0;self.chunks=[];self.events=[];self.event_chunks=[];self.event_count=0
        self.runs=ThresholdRuns(n);self.global_runs=ThresholdRuns(1);self.stage_runs={}
        self.peaks=np.zeros(n);self.peak_records=[None]*n;self.last_stage=None
        self.pre_state=np.empty(mujoco.mj_stateSize(model,STATE_SPEC))
        self.before_time=None;self.wrench=np.zeros(6)
        self.geometry={str(g):dict(name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,g),
            body=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,int(model.geom_bodyid[g])),
            body_id=int(model.geom_bodyid[g])) for g in range(model.ngeom)}

    def before_step(self):
        mujoco.mj_getState(self.model,self.data,self.pre_state,STATE_SPEC)
        self.before_time=float(self.data.time)

    def after_step(self):
        model,data=self.model,self.data;n=len(self.ids)
        if self.before_time is None or not np.isclose(data.time-self.before_time,self.dt,rtol=0,atol=1e-10):
            raise ValueError('Expected exactly one physical step')
        depth=np.zeros(n);pairs=np.full((n,2),-1,dtype=np.int32);normal=np.zeros(n);counts=np.zeros(n,dtype=np.int16)
        relevant=[]
        for i in range(data.ncon):
            c=data.contact[i];g1,g2=int(c.geom1),int(c.geom2)
            obstacle=g1 if g1 in self.column and g2 in self.robot else g2 if g2 in self.column and g1 in self.robot else None
            if obstacle is None:continue
            column=self.column[obstacle];counts[column]+=1;value=max(0.,-float(c.dist))
            relevant.append((i,column,g1,g2,value))
            if pairs[column,0]<0 or value>depth[column]:
                depth[column]=value;pairs[column]=[g1,g2]
                mujoco.mj_contactForce(model,data,i,self.wrench);normal[column]=float(self.wrench[0])
        stage=int(self.env.reference.index)
        self.runs.update(depth);self.global_runs.update([float(depth.max(initial=0))])
        if stage not in self.stage_runs:self.stage_runs[stage]=ThresholdRuns(n)
        if self.last_stage!=stage:
            self.stage_runs[stage].current[:]=0
        self.stage_runs[stage].update(depth);self.last_stage=stage
        row=dict(time_before_s=self.before_time,time_after_s=float(data.time),stage=stage,
                 depth_m=depth,pair_geom_ids=pairs,peak_pair_normal_force_n=normal,contact_count=counts)
        for key,value in row.items():self.buffers[key][self.used]=value
        increased=depth>self.peaks
        if np.any(increased) or np.any(depth>=.00019):
            contact_rows=[]
            for i,column,g1,g2,value in relevant:
                c=data.contact[i];mujoco.mj_contactForce(model,data,i,self.wrench)
                contact_rows.append(dict(index=i,obstacle_column=column,geom1=g1,geom2=g2,
                    dist_m=float(c.dist),pos=c.pos.copy().tolist(),frame=c.frame.copy().tolist(),
                    force_contact_frame=self.wrench.copy().tolist(),efc_address=int(c.efc_address),
                    solref=c.solref.copy().tolist(),solimp=c.solimp.copy().tolist(),
                    geom1_xpos=data.geom_xpos[g1].copy().tolist(),geom2_xpos=data.geom_xpos[g2].copy().tolist(),
                    geom1_xmat=data.geom_xmat[g1].copy().tolist(),geom2_xmat=data.geom_xmat[g2].copy().tolist()))
            niter=np.asarray(data.solver_niter).copy()
            stats=[]
            # mjData keeps up to mjNSOLVER iterations per island; do not index
            # beyond the exposed storage or claim these fields are residual bounds.
            for i in range(min(int(niter[0]),int(mujoco.mjNSOLVER),len(data.solver))):
                s=data.solver[i]
                stats.append(dict(iteration=i,improvement=float(s.improvement),gradient=float(s.gradient),
                    lineslope=float(s.lineslope),nactive=int(s.nactive),nchange=int(s.nchange),neval=int(s.neval)))
            metadata=dict(index=self.count,time_before_s=self.before_time,time_after_s=float(data.time),stage=stage,
                new_peak_obstacle_columns=np.flatnonzero(increased).tolist(),threshold_0p19mm=bool(np.any(depth>=.00019)),
                contacts=contact_rows,solver_niter=niter.tolist(),solver_first_island_stats=stats)
            event=dict(metadata=metadata,pre_state=self.pre_state.copy(),post_state=pack_state(model,data),
                post_qacc=data.qacc.copy(),post_qfrc_constraint=data.qfrc_constraint.copy())
            self.events.append(event);event_id=self.event_count;self.event_count+=1
            for column in np.flatnonzero(increased):
                self.peak_records[column]=dict(event_id=event_id,sample_index=self.count,depth_m=float(depth[column]),
                    geom1=int(pairs[column,0]),geom2=int(pairs[column,1]),normal_force_n=float(normal[column]),
                    stage=stage,time_before_s=self.before_time,time_after_s=float(data.time))
            if len(self.events)>=self.event_chunk_size:self.flush_events()
        self.peaks=np.maximum(self.peaks,depth);self.count+=1;self.used+=1
        if self.used==self.chunk_size:self.flush_raw()

    def flush_raw(self):
        if not self.used:return
        name=f'contacts_{len(self.chunks):04d}.npz'
        np.savez_compressed(self.directory/name,**{k:v[:self.used] for k,v in self.buffers.items()})
        self.chunks.append(dict(file=name,samples=self.used));self.used=0

    def flush_events(self):
        if not self.events:return
        name=f'events_{len(self.event_chunks):04d}'
        np.savez_compressed(self.directory/(name+'.npz'),**{k:np.stack([e[k] for e in self.events])
            for k in ('pre_state','post_state','post_qacc','post_qfrc_constraint')})
        (self.directory/(name+'.json')).write_text(json.dumps([e['metadata'] for e in self.events],allow_nan=False)+'\n')
        self.event_chunks.append(dict(file=name,first_event_id=self.event_count-len(self.events),events=len(self.events)))
        self.events.clear()

    def save(self):
        self.flush_raw();self.flush_events()
        def runs(value):return dict(steps_at_or_above=value.count.tolist(),duration_s=(value.count*self.dt).tolist(),
            longest_consecutive_steps=value.longest.tolist(),longest_consecutive_s=(value.longest*self.dt).tolist())
        out=dict(samples=self.count,timestep_s=self.dt,obstacle_geom_ids=self.ids,obstacle_names=self.names,
            geometry=self.geometry,stage_names=self.stage_names,thresholds_m=THRESHOLDS_M.tolist(),
            original_gate='max external penetration <0.0002m; unchanged',
            thresholds=runs(self.runs),global_thresholds=runs(self.global_runs),
            stage_thresholds={str(k):runs(v) for k,v in self.stage_runs.items()},
            max_depth_m=self.peaks.tolist(),peak_records=self.peak_records,raw_chunks=self.chunks,event_chunks=self.event_chunks,
            event_count=self.event_count,state_spec=STATE_SPEC,state_size=len(self.pre_state),
            state_members={k:int(v) for k,v in mujoco.mjtState.__members__.items()},
            model_dimensions={k:int(getattr(self.model,k)) for k in ('nq','nv','nu','na','nbody','nmocap','nuserdata')},
            semantics=dict(engine=mujoco.__version__,integrator='implicitfast',raw_precision='depth/force/state/time float64',
                contact='unmodified live contacts retained from the original completed mj_step; not recomputed',
                time='step input/output bracket; contact geometry evaluation precedes integration, while output qpos is post-integration',
                state='mjSTATE_INTEGRATION pre/post: time, qpos, qvel, act/history, warmstart, ctrl, applied forces, eq_active, mocap, userdata, plugin',
                geometry='event geom_xpos/xmat and contact frame are copied directly from live evaluation arrays',
                events='all samples at depth >=0.19mm OR any obstacle new maximum; both pre/post state retained',
                force='normal force for the deepest retained pair of each obstacle, not sum across contacts',
                solver='stored first-island iteration diagnostics are not certified residual/error bounds',
                model_mutations=False,forward_or_collision_calls=False))
        (self.directory/'summary.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
        return out


class ContactInstrumentation(AbstractContextManager):
    def __init__(self,directory):self.directory=Path(directory);self.current=None;self.episodes=[];self.by_id={}
    def __enter__(self):
        import audited_velocity_env
        self.env_class=audited_velocity_env.PandaWBCVelocityResidualEnv
        self.original_physics=self.env_class._physics_step;self.original_step=mujoco.mj_step;owner=self
        def physics(env,*args,**kwargs):
            if id(env) not in owner.by_id:
                episode=ContactEpisode(env,owner.directory/f'episode_{len(owner.episodes)}')
                owner.by_id[id(env)]=episode;owner.episodes.append(episode)
            previous=owner.current;owner.current=owner.by_id[id(env)]
            try:return owner.original_physics(env,*args,**kwargs)
            finally:owner.current=previous
        def step(model,data,*args,**kwargs):
            episode=owner.current
            if episode is None or data is not episode.data:return owner.original_step(model,data,*args,**kwargs)
            if args or kwargs.get('nstep',1)!=1:raise ValueError('Requires exactly one mj_step')
            episode.before_step();value=owner.original_step(model,data,*args,**kwargs);episode.after_step();return value
        self.env_class._physics_step=physics;mujoco.mj_step=step;return self
    def __exit__(self,*args):
        self.env_class._physics_step=self.original_physics;mujoco.mj_step=self.original_step;return False
