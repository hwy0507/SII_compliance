"""Audit v5 initial geometry, static cup support and dynamic apparatus reach."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
import mujoco,numpy as np
import run_contact_transfer_20260916 as legacy
from office_complex_scene_v5_20260917 import extend_complex_xml,fixture_flags

ROOT=Path(__file__).resolve().parents[1]


def make(flags):
    original=legacy.extend_xml;original_layout=legacy.task_layout
    legacy.extend_xml=lambda xml,spec:extend_complex_xml(xml,spec,flags['office_variant'])
    legacy.task_layout=lambda spec:(np.array([.54,-.19,.60]),np.array([.54,-.19,.425]))
    a=SimpleNamespace(**dict(flags,push_hold=4.,menagerie=ROOT.parent/'mujoco_menagerie',dt=.0001,settle_only=True,
        stiffness=110.,tangent_speed=None,teacher_profile='none',force_target=1.,normal_gain=.02,
        mixture=0.,model=None,render=False))
    try:return legacy.create_environment(a)
    finally:legacy.extend_xml=original;legacy.task_layout=original_layout


def names(m,d):
    return [mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,int(g)) or str(g) for g in d]


def audit(flags):
    env,task,spec=make(flags);m,d=env.model,env.data
    failures=[];obstacles=[];intended_contacts=[]
    for i in range(d.ncon):
        c=d.contact[i];g=(int(c.geom1),int(c.geom2));n=names(m,g)
        if c.dist<-.00001 and m.geom_bodyid[g[0]]!=m.geom_bodyid[g[1]]:
            failures.append(dict(pair=n,depth_mm=-float(c.dist)*1000))
    cup_body=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'office_v5_cup')
    cup_geom=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_cup_base')
    desk_geom=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_desk_top')
    support=False
    for i in range(d.ncon):
        c=d.contact[i]
        if {int(c.geom1),int(c.geom2)}=={cup_geom,desk_geom}:support=True
    dynamic=[]
    for name in ('office_v5_ball_free','office_v5_cup_free','office_v5_person_root','office_v5_human_hand_joint','office_v5_push_rod_joint'):
        jid=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name)
        dynamic.append(dict(name=name,found=jid>=0,dof=int(m.jnt_dofadr[jid]) if jid>=0 else -1))
    # Drive each rail through its full stroke in an offline probe, checking no
    # generated body intersects robot at the starting pose.
    for name in ('office_v5_person_root','office_v5_human_hand_joint','office_v5_push_rod_joint'):
        jid=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name);dof=int(m.jnt_dofadr[jid]);qadr=int(m.jnt_qposadr[jid])
        lo,hi=map(float,m.jnt_range[jid]);
        for q in np.linspace(lo,hi,21):
            d.qpos[qadr]=q;mujoco.mj_forward(m,d)
            for i in range(d.ncon):
                c=d.contact[i];g=(int(c.geom1),int(c.geom2));n=names(m,g)
                if any('office_v5_human' in x or 'office_v5_push_rod' in x for x in n) and any(x.startswith('fr3_') for x in n):
                    if c.dist<-.0002:obstacles.append(dict(apparatus=name,pair=n,depth_mm=-float(c.dist)*1000))
                    elif c.dist<.004:intended_contacts.append(dict(apparatus=name,pair=n,gap_mm=float(c.dist)*1000))
        d.qpos[qadr]=0.;mujoco.mj_forward(m,d)
    result=dict(flags=flags,initial_overlap=failures,static_cup_support=support,
      apparatus_robot_overlap=obstacles,dynamic_joints=dynamic,initial_geometry_valid=not failures,
      intended_contact_candidates=intended_contacts,
      dynamic_validation_complete=False,
      notes=['cup support is inspected as a real cup-base/desk contact',
             'rail sweep deliberately intersects the robot to screen reach; never a physical penetration measurement',
             'initial cup is above surface; settled support must be checked dynamically'])
    env.close();return result


def main(a):
    rows=[audit(fixture_flags(a.seed+i,i)) for i in range(a.count)]
    out=a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rows,indent=2,allow_nan=False));print(json.dumps(rows,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--count',type=int,default=6);p.add_argument('--seed',type=int,default=2026091751);main(p.parse_args())
