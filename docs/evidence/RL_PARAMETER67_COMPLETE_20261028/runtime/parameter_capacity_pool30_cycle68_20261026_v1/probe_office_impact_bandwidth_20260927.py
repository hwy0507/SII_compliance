"""Development-only causal reflex probe, NOT a proposed ESN score.

Same ball/world/initial state and safety threshold. The diagnostic asks if
faster encoder-load feedback can reduce the first impact while respecting
the existing actuator magnitude AND torque-slew limits. No contact truth,
ball geometry/velocity, fixture identity or impact clock enters the reflex.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('MUJOCO_GL','egl')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import mujoco
import numpy as np
import validate_office_apparatus_v5_20260917 as evaluator
from haptic_vmc_teacher_20260916 import JointLoadObserver


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',type=int,default=2026092702);p.add_argument('--variant',type=int,default=-2)
    p.add_argument('--ball-speed',type=float,default=1.85);p.add_argument('--dt',type=float,default=.0000015625)
    p.add_argument('--reflex-gain',type=float,required=True)
    p.add_argument('--sensor-tau',type=float,default=.04)
    p.add_argument('--reflex-period',type=float,default=.00005)
    a=p.parse_args()
    if a.reflex_gain<0 or a.sensor_tau<=0 or a.reflex_period<a.dt:raise ValueError('Invalid reflex configuration')
    original_make=evaluator.make;original_step=mujoco.mj_step
    rows=[];owner={}
    def make(flags):
        env,task,spec=original_make(flags);m,d=env.model,env.data
        obs=JointLoadObserver(d.qvel.copy(),m.dof_frictionloss,filter_tau=a.sensor_tau)
        owner.update(env=env,observer=obs,mass=np.zeros((m.nv,m.nv)),first=True,
                     previous=d.ctrl[:7].copy(),nominal=d.ctrl[:7].copy(),target=d.ctrl[:7].copy(),next_update=0.)
        original_physics=env._physics_step
        def physics(t):
            owner['first']=True
            return original_physics(t)
        env._physics_step=physics
        return env,task,spec
    def step(m,d,*args,**kwargs):
        if not owner or d is not owner['env'].data:return original_step(m,d,*args,**kwargs)
        env=owner['env'];dt=float(m.opt.timestep)
        if owner['first']:
            owner['nominal']=d.ctrl[:7].copy();owner['first']=False
            if not rows:owner['previous']=d.ctrl[:7].copy()
        if d.time+1e-12>=owner['next_update']:
            load=owner['observer'].filtered
            load=np.sign(load)*np.maximum(np.abs(load)-.01,0.)
            owner['target']=np.clip(owner['nominal']+a.reflex_gain*load,-env.torque_limits,env.torque_limits)
            owner['next_update']=float(d.time)+a.reflex_period
        previous=owner['previous'].copy()
        if a.reflex_gain:
            limit=env.safety_config.maximum_torque_rate_nmps*dt
            command=previous+np.clip(owner['target']-previous,-limit,limit)
            d.ctrl[:7]=np.clip(command,-env.torque_limits,env.torque_limits)
        # Gain-zero is an exact instrumentation-only parity control.
        command=d.ctrl[:7].copy();owner['previous']=command
        result=original_step(m,d,*args,**kwargs)
        mujoco.mj_fullM(m,d,owner['mass'])
        owner['observer'].update(d.qvel.copy(),owner['mass'],d.qfrc_bias.copy(),d.qfrc_passive.copy(),d.qfrc_actuator.copy(),dt)
        rows.append((float(d.time),command,owner['observer'].filtered.copy(),owner['target'].copy(),(command-previous)/dt))
        return result
    evaluator.make=make;mujoco.mj_step=step
    try:
        evaluator.run(argparse.Namespace(output=a.output,render=False,events='ball',task='pick_place',
            seed=a.seed,variant=a.variant,duration=6.2,dt=a.dt,ball_speed=a.ball_speed,
            person_stroke=.22,rod_stroke=.24,esn_model=None,esn_mode='shadow',
            disable_selector_pulse=False,teacher='none',physics_probe_s=.2))
    finally:evaluator.make=original_make;mujoco.mj_step=original_step
    trace=a.output.parent/'reflex_substeps.npz'
    np.savez_compressed(trace,time=np.array([r[0] for r in rows]),command=np.array([r[1] for r in rows]),
        estimated_joint_load=np.array([r[2] for r in rows]),target=np.array([r[3] for r in rows]),
        command_rate=np.array([r[4] for r in rows]))
    rates=np.max(np.abs(np.array([r[4] for r in rows])),axis=0)
    record=dict(purpose='causal_bandwidth_diagnostic_not_ESN',arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},
        force_truth_in_reflex=False,fixture_or_clock_in_reflex=False,
        period_clock_semantics='fixed-rate sample clock only; no event schedule',
        joint_load_deadband_nm=.01,
        max_command_rate_nmps=rates.tolist(),rate_limits_nmps=[700,700,700,700,160,160,160],
        rate_bounds_obeyed=bool(np.all(rates<=np.array([700,700,700,700,160,160,160])+1e-6)) if a.reflex_gain else None,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest())
    (a.output.parent/'reflex_manifest.json').write_text(json.dumps(record,indent=2))


if __name__=='__main__':main()
