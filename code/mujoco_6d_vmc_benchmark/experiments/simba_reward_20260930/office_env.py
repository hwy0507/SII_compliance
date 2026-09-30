"""Canonical Office adapter; actor sees raw48, reward receives substep audit only."""
from __future__ import annotations
import os, sys, json, queue, threading, traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import gymnasium as gym

ROOT=Path(os.environ.get("STUDY_CANONICAL_ROOT","/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark"))
os.environ.setdefault("MUJOCO_MENAGERIE_PATH","/home/arm1/vmc_mujoco_runtime/mujoco_menagerie")
sys.path.insert(0,str(ROOT/"scripts"))
import validate_office_apparatus_v5_20260917 as validator
from run_benchmark import body_jacobian, body_twist, so3_log
from haptic_vmc_teacher_20260916 import equivalent_tool_wrench

def default_args(output, seed, variant=0, duration=55., physics_dt=.0001, render=False,
                 ball_speed=1.7, person_stroke=.2, rod_stroke=.235, events="all"):
    return SimpleNamespace(output=Path(output),events=events,task="pick_place",seed=int(seed),variant=int(variant),
        duration=duration,dt=physics_dt,ball_speed=ball_speed,person_stroke=person_stroke,rod_stroke=rod_stroke,
        render=render,esn_model=None,esn_mode="control",memory_ablation="none",teacher="none",
        hybrid_vmc_blend=0.,corner_placement=True,combined_thick_corner_pillar_v4=True,
        combined_contact_v2=False,ball_launch_time_s=2.,person_start=3.,rod_start=7.,rod_hold=6.,
        observer_friction_velocity_scale=.005)

class Hooks:
    def __init__(self, save_substeps=False, e_scale=.12, horizon=55.):
        self.save_substeps=save_substeps;self.e_scale=e_scale;self.horizon=horizon;self.start=0
        self.result=None;self.initial=None;self.task_complete=False;self.previous_completion=False
    def attach(self,env,task,observer,metrics):
        self.env,self.task,self.observer,self.metrics=env,task,observer,metrics
        self.initial=env.data.xpos[env._hand_id].copy()
    def potential(self):
        # Monotone task stages, bounded within-stage projection onto the commanded
        # route. No best-so-far position, contact schedule, or obstacle state.
        task=self.task;idx=int(task.index)
        begin=self.initial if idx==0 else np.asarray(task.goals[idx-1])
        end=np.asarray(task.goals[idx]);v=end-begin;length2=float(v@v)
        pos=self.env.data.xpos[self.env._hand_id]
        fraction=(np.clip(float((pos-begin)@v)/length2,0.,1.) if length2>1e-12
                  else np.clip(task.ready/.20,0.,1.))
        return float((idx+fraction)/len(task.goals))
    def take_interval(self):
        m=self.metrics;end=m.count
        a=m.arrays;sl=slice(self.start,end);dt=a["dt"][sl];err=a["error"][sl].astype(float)
        torque=np.abs(a["qfrc_actuator"][sl].astype(float))
        limits=np.asarray(self.env.torque_limits,dtype=float)[:7]
        result=dict(elapsed_s=float(dt.sum()),
            error_cost=float(np.sum(dt*np.sum(err*err,axis=1))/(self.horizon*self.e_scale**2)),
            peak_torque_ratio=float(np.max(torque/limits)) if end>self.start else 0.,
            peak_torque_nm_per_joint=np.max(torque,axis=0).tolist() if end>self.start else [0.]*7,
            max_position_error_m=float(np.max(np.linalg.norm(err,axis=1))) if end>self.start else 0.,
            substeps=end-self.start, time_s=float(self.env.data.time),
            stage=int(self.task.index),potential=self.potential(),
            torque_limits_nm=limits.tolist(),
            filtered_action_physical=np.r_[self.env.applied_action.wbc_scale,self.env.applied_action.cartesian_yield_twist].tolist())
        result["task_complete_before_interval"]=self.previous_completion
        self.previous_completion=self.task_complete
        self.start=end
        return result
    def observation(self):
        env=self.env;d=env.data;m=env.model
        command=env._wbc_command(0.)
        twist=body_twist(m,d,env._hand_id)
        err=np.r_[command.target_position_m-d.xpos[env._hand_id],
            so3_log(command.target_rotation@d.xmat[env._hand_id].reshape(3,3).T)]
        wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),self.observer.filtered)
        return validator.canonical_observation(d.qpos,d.qvel,command.task_twist_world,err,twist,
            self.observer.filtered,wrench,self.task.path_direction)
    def finish(self,result):
        self.result=result
        self.final_interval=self.take_interval()
        self.final_observation=self.observation()

class QueueActor:
    kind="mlp"
    contract="proprio48_direct_rl_action7_v1"
    def __init__(self,owner): self.owner=owner;self.dt=.04
    def act(self,observation):
        self.owner.publish.put(("observation",np.asarray(observation).copy(),self.owner.hooks.take_interval()))
        action=self.owner.receive.get(timeout=600)
        if action is None: raise RuntimeError("episode cancelled")
        return np.asarray(action).copy()

class OfficeEnv(gym.Env):
    def __init__(self, root, rewarder, duration=55., physics_dt=.0001, save_substeps=False):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.rewarder=rewarder;self.duration=duration;self.physics_dt=physics_dt
        self.save_substeps=save_substeps;self.worker=None;self.episode=0;self.actions=[]
        self.action_space=gym.spaces.Box(-1.,1.,(7,),np.float32)
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(48,),np.float32)
    def _next(self):
        event=self.publish.get(timeout=600)
        if event[0]=="error":raise RuntimeError(event[1])
        return event
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed);self.close();options=options or {}
        self.publish=queue.Queue();self.receive=queue.Queue();self.actions=[]
        self.hooks=Hooks(self.save_substeps,horizon=self.duration,
            e_scale=self.rewarder.config.error_scale_m if self.rewarder is not None else .12)
        out=self.root/f"episode_{self.episode:06d}"/"rollout";self.episode+=1
        args=default_args(out,seed,variant=options.get("variant",0),duration=self.duration,
            physics_dt=self.physics_dt,ball_speed=options.get("ball_speed",1.7),
            person_stroke=options.get("person_stroke",.2),rod_stroke=options.get("rod_stroke",.235),
            events=options.get("events","all"),render=options.get("render",False))
        self.args=args
        def worker():
            try:
                result=validator.run(args,policy_override=QueueActor(self),runtime_hooks=self.hooks)
                self.publish.put(("terminal",self.hooks.final_observation,self.hooks.final_interval,result))
            except BaseException:
                self.publish.put(("error",traceback.format_exc()))
        self.worker=threading.Thread(target=worker,daemon=True);self.worker.start()
        event=self._next()
        if event[0]!="observation":raise RuntimeError("No initial observation")
        self.obs=event[1].astype(np.float32);self.initial_interval=event[2]
        return self.obs.copy(),dict(interval=event[2])
    def step_raw(self,action):
        requested=np.asarray(action,dtype=np.float64)
        if requested.shape!=(7,) or not np.isfinite(requested).all():raise ValueError("finite action7 required")
        requested=np.clip(requested,-1.,1.)
        # Same canonical slowdown + Cartesian residual action as ESN/VMC.
        # Negative slowdown is clipped by the common filter; no RL-only envelope.
        self.receive.put(requested.copy())
        event=self._next();done=event[0]=="terminal"
        self.obs=event[1].astype(np.float32);interval=event[2]
        info=dict(interval=interval,requested_action=requested.copy())
        if done:
            info["evaluation"]=event[3];self.worker.join(timeout=60);self.worker=None
        self.actions.append(requested.copy())
        return self.obs.copy(),done,info
    def close(self):
        if self.worker is not None and self.worker.is_alive():
            self.receive.put(None);self.worker.join(timeout=30)
        self.worker=None
