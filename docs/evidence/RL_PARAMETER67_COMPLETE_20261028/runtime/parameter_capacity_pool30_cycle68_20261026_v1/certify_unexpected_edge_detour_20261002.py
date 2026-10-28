"""Auditor-only informed static-map detour, never used by a tested actor."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import mujoco
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from office_task_v4_20260917 import PickPlaceTask
from planned_hand_corner_20261002 import build_plan
import planned_hand_corner_20261002 as planner


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--expanded-search',action='store_true',help='Audit fixed side/overhead detours if shortest payload path hits the gripper')
    parser.add_argument('--output',type=Path,help='Independent audit path; never overwrite a prior result')
    args=parser.parse_args();prefix=args.run/'esn_combined_v4'
    m=mujoco.MjModel.from_binary_path(str(prefix.with_suffix('.mjb')));d=mujoco.MjData(m)
    with np.load(prefix.with_suffix('.npz')) as z:d.qpos[:]=z['qpos'][0]
    mujoco.mj_forward(m,d)
    hand=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'hand')
    robot=set()
    for g in range(m.ngeom):
        name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,int(m.geom_bodyid[g])) or ''
        if (name.startswith('fr3_link') or name in ('hand','left_finger','right_finger')) and m.geom_group[g]!=2 and mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g)!='hand_ball_proxy':robot.add(g)
    fingers=[];fdofs=[]
    for name in ('finger_joint1','finger_joint2'):
        j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name);fingers.append(m.jnt_qposadr[j]);fdofs.append(m.jnt_dofadr[j])
    support=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_corner_top')
    base=PickPlaceTask(d.xpos[hand].copy(),fingers,fdofs,source=[.54,-.19,.425],
                       destination=[.582,-.302,.545],support_geoms=(support,),lift_height=.24,
                       carry_waypoint=[.56,-.33,.67])
    env=SimpleNamespace(model=m,data=d,_hand_id=hand,_push_audit_robot_geom_ids=robot)
    record=dict(purpose=__doc__,used_by_tested_policies=False,physics_stepped=False,
                initial_state='first saved 40ms frame',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    original_astar=planner.astar
    attempts=[]
    modes=('positive_y','negative_y','overhead') if args.expanded_search else ('shortest',)
    for mode in modes:
        def routed(start,goal,boxes,half,ignore=()):
            if ignore or mode=='shortest':return original_astar(start,goal,boxes,half,ignore)
            if mode=='overhead':
                height=max(start[2],goal[2],.640)
                points=[start,np.array([start[0],start[1],height]),np.array([goal[0],goal[1],height]),goal]
            else:
                y=-.120 if mode=='positive_y' else -.380
                points=[start,np.array([start[0],y,start[2]]),np.array([goal[0],y,goal[2]]),goal]
            path=[np.asarray(start)];expanded=0
            for a,b in zip(points,points[1:]):
                segment,count=original_astar(a,b,boxes,half,ignore);path.extend(segment[1:]);expanded+=count
            return path,expanded
        planner.astar=routed
        try:
            _,plan=build_plan(env,base,blind_edge=False,allow_lateral_rejoin=True)
            record.pop('reason',None)
            record.update(status='geometrically_feasible',detour=mode,plan=plan,
                          limitation='Payload swept-volume plus robot IK/static waypoint checks; not a dynamic rollout or proof learned compliance succeeds')
            attempts.append(dict(mode=mode,valid=True));break
        except ValueError as exc:
            attempts.append(dict(mode=mode,valid=False,reason=str(exc)))
            record.update(status='not_certified',reason=str(exc))
        finally:planner.astar=original_astar
    record['attempts']=attempts
    output=args.output or args.run/('INFORMED_DETOUR_EXPANDED_AUDIT.json' if args.expanded_search else 'INFORMED_DETOUR_AUDIT.json')
    if output.exists():raise FileExistsError(output)
    output.write_text(json.dumps(record,indent=2))
    print(json.dumps({k:v for k,v in record.items() if k!='plan'},indent=2))


if __name__=='__main__':main()
