"""Read-only privileged diagnostics; truth never enters actor or task inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_office_apparatus_v5_20260917 as evaluator
from haptic_vmc_teacher_20260916 import JointLoadObserver,equivalent_tool_wrench
from run_benchmark import body_jacobian


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--condition',choices=('original','hard'),required=True)
    p.add_argument('--probe',action='store_true')
    p.add_argument('--friction-velocity-scale',type=float,default=.005)
    p.add_argument('--actor',choices=('esn','zero'),default='esn')
    a=p.parse_args()
    original_sample=evaluator.EpisodeMetrics.sample
    contact_types=[int(getattr(mujoco.mjtConstraint,k)) for k in
                   ('mjCNSTR_CONTACT_FRICTIONLESS','mjCNSTR_CONTACT_PYRAMIDAL','mjCNSTR_CONTACT_ELLIPTIC')]
    friction_types=[int(getattr(mujoco.mjtConstraint,k)) for k in ('mjCNSTR_FRICTION_DOF','mjCNSTR_FRICTION_TENDON')]
    owner={};rows=[];bins={}

    def sample(metric):
        original_sample(metric)
        env=metric.env;m=env.model;d=env.data;dt=float(m.opt.timestep)
        if not owner:
            # Initial robot velocity is zero in the frozen office reset.
            owner.update(previous=np.zeros(m.nv),mass=np.zeros((m.nv,m.nv)),
                         estimated=JointLoadObserver(np.zeros(m.nv),m.dof_frictionloss,friction_velocity_scale=a.friction_velocity_scale),
                         baseline_observer=JointLoadObserver(np.zeros(m.nv),m.dof_frictionloss,friction_velocity_scale=.005),
                         filtered={key:np.zeros(7) for key in ('contact','friction','other','raw','constraint')},
                         last_tick=0)
            rows.append(dict(time=0.,**{key:np.zeros(7) for key in ('contact','friction','other','raw','constraint','estimated','estimated_scale005')},
                             contact_wrench=np.zeros(6)))
        force=d.efc_force.copy();kind=d.efc_type
        contact=np.zeros(m.nv);friction=np.zeros(m.nv)
        mujoco.mj_mulJacTVec(m,d,contact,force*np.isin(kind,contact_types))
        mujoco.mj_mulJacTVec(m,d,friction,force*np.isin(kind,friction_types))
        mujoco.mj_fullM(m,d,owner['mass'])
        raw=(owner['mass']@((d.qvel-owner['previous'])/dt)+d.qfrc_bias-d.qfrc_passive-d.qfrc_actuator)[:7]
        owner['previous']=d.qvel.copy()
        estimated=owner['estimated'].update(d.qvel.copy(),owner['mass'],d.qfrc_bias.copy(),
                     d.qfrc_passive.copy(),d.qfrc_actuator.copy(),dt)
        estimated_baseline=owner['baseline_observer'].update(d.qvel.copy(),owner['mass'],d.qfrc_bias.copy(),
                     d.qfrc_passive.copy(),d.qfrc_actuator.copy(),dt)
        truth=dict(contact=contact[:7],friction=friction[:7],constraint=d.qfrc_constraint[:7],
                   other=(d.qfrc_constraint-contact-friction)[:7],raw=raw)
        alpha=1.-np.exp(-dt/.04)
        for key,value in truth.items():owner['filtered'][key]+=alpha*(value-owner['filtered'][key])
        filtered=owner['filtered'];error=estimated-filtered['contact']
        # Diagnostic stratification only; neither stage nor truth feeds control.
        label=('contact' if np.linalg.norm(contact[:7])>1e-5 else 'no_contact')
        for group in ('all',label,'stage_'+str(env.reference.index)):
            row=bins.setdefault(group,dict(duration_s=0.,error_integral=np.zeros(7),
                baseline_error_integral=np.zeros(7),
                dynamics_integral=np.zeros(7),friction_integral=np.zeros(7),other_integral=np.zeros(7),
                max_estimation_error_nm=0.))
            row['duration_s']+=dt;row['error_integral']+=dt*error*error
            row['baseline_error_integral']+=dt*(estimated_baseline-filtered['contact'])**2
            row['dynamics_integral']+=dt*(filtered['raw']-filtered['constraint'])**2
            row['friction_integral']+=dt*(estimated-filtered['raw']+filtered['friction'])**2
            row['other_integral']+=dt*filtered['other']**2
            row['max_estimation_error_nm']=max(row['max_estimation_error_nm'],float(np.max(np.abs(error))))
        tick=round(float(d.time)/.04)
        if tick>owner['last_tick'] and abs(float(d.time)-tick*.04)<1e-7:
            owner['last_tick']=tick
            rows.append(dict(time=float(d.time),**{k:v.copy() for k,v in filtered.items()},
                estimated=estimated.copy(),estimated_scale005=estimated_baseline.copy(),
                contact_wrench=equivalent_tool_wrench(body_jacobian(m,d,env._hand_id),filtered['contact'])))

    evaluator.EpisodeMetrics.sample=sample
    hard=a.condition=='hard'
    try:
        evaluator.run(argparse.Namespace(output=a.output,render=False,events='all',task='pick_place',
            seed=2026092702 if hard else 2026091751,variant=-2 if hard else 0,
            duration=55.,dt=.00005,ball_speed=1.85 if hard else 1.7,
            person_stroke=.22 if hard else .20,rod_stroke=.24 if hard else .235,
            esn_model=Path('models/r34.npz') if a.actor=='esn' else None,
            esn_mode='control' if a.actor=='esn' else 'shadow',disable_selector_pulse=False,
            teacher='none',physics_probe_s=.12 if a.probe else None,
            observer_friction_velocity_scale=a.friction_velocity_scale,
            impact_refinement_dt=.0000015625,impact_refinement_until=.2))
    finally:evaluator.EpisodeMetrics.sample=original_sample
    sidecar=a.output.parent/'observer_truth_sidecar.npz'
    np.savez_compressed(sidecar,**{k:np.array([r[k] for r in rows]) for k in rows[0]})
    with np.load(a.output.with_suffix('.npz')) as trace:
        recorded=np.asarray([r['estimated'] for r in rows[:len(trace['observation'])]])
        np.testing.assert_allclose([r['time'] for r in rows[:len(recorded)]],trace['neuron_time'],atol=1e-10,rtol=0)
        error=float(np.max(np.abs(recorded-trace['observation'][:,32:39])))
        assert error<1e-10, error
    summary={}
    for group,row in bins.items():
        summary[group]={k.replace('_integral','_rmse_nm'):(np.sqrt(v/row['duration_s']).tolist() if k.endswith('_integral') else v) for k,v in row.items()}
    manifest=dict(purpose=__doc__,condition=a.condition,diagnostic_truth_used_by_controller=False,
        actor=a.actor,friction_velocity_scale=a.friction_velocity_scale,
        shadow_observer_scale005=True,shadow_observer_used_by_controller=False,
        filters_tau_s=.04,initial_robot_velocity_zero=True,observer_reconstruction_max_abs_nm=error,
        bins=summary,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        sidecar_sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),
        note='Contact truth includes carried payload. Error decomposition terms are correlated; RMSEs do not add. Force/Jacobian are retained from the completed mj_step evaluation.')
    (a.output.parent/'observer_audit.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest))


if __name__=='__main__':main()
