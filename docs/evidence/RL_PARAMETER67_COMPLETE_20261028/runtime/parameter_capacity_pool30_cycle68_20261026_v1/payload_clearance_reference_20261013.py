"""Offline known-map payload clearance; proprioceptive online progression."""
import numpy as np
import mujoco
from planned_hand_corner_20261002 import astar, OFFSET
from office_task_v4_20260917 import PickPlaceTask, DT
from old_office_waypoint_reference_20261013 import LocalCarryReference
from run_benchmark import so3_log


def known_map_plan(model, data, start_hand, end_hand, rotation):
    # Snapshot of the known map at initialization. Dynamic apparatus and all
    # online contacts are excluded. Cup pose is frozen here, never tracked.
    boxes=[]
    for i in range(model.ngeom):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i) or str(i)
        if not (model.geom_contype[i] or model.geom_conaffinity[i]):continue
        if not (model.geom_bodyid[i]==0 or name.startswith('office_v5_cup_')):continue
        if 'floor' in name:continue
        rot=data.geom_xmat[i].reshape(3,3)
        center=data.geom_xpos[i]+rot@model.geom_aabb[i,:3]
        extent=abs(rot)@model.geom_aabb[i,3:]
        boxes.append((name,center.copy(),extent.copy()))
    payload=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
    assert model.geom_type[payload]==mujoco.mjtGeom.mjGEOM_BOX
    half=abs(rotation)@model.geom_size[payload]
    margin=.012  # Existing task arrival tolerance, not fitted to a rollout.
    offset=rotation@OFFSET
    path,expanded=astar(start_hand+offset,end_hand+offset,boxes,half+margin)
    def edge(a,b):
        return all(all(not np.all(abs(p-c)<e+half+margin+.002-1e-8) for _,c,e in boxes)
                   for p in np.linspace(a,b,max(2,int(np.ceil(np.linalg.norm(b-a)/.002))+1)))
    # Deterministic longest visible edge shortcut, using the same swept test.
    simple=[path[0]];index=0
    while index<len(path)-1:
        nxt=next(i for i in range(len(path)-1,index,-1) if edge(path[index],path[i]))
        simple.append(path[nxt]);index=nxt
    hand=np.array(simple)-offset
    assert all(edge(a,b) for a,b in zip(simple,simple[1:]))
    return hand,dict(planner='existing deterministic 26-connected static-map A* plus swept-edge shortcut',
        boxes=[dict(name=n,center=c.tolist(),extent=e.tolist()) for n,c,e in boxes],
        payload_half_m=half.tolist(),tracking_margin_m=margin,existing_planner_clearance_m=.002,
        expanded=expanded,hand_route=hand.tolist(),cup_snapshot_at_initialization_only=True,
        dynamic_apparatus_in_map=False,online_contact_input=False,
        limitations='Payload swept-volume only, no full-arm continuous collision proof; finite tracking margin is not a bound on compliant deviations')


class PayloadClearanceReference(LocalCarryReference):
    environment=None

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        env=self.environment
        self.carry_route,self.plan=known_map_plan(env.model,env.data,self.original_goals[3],self.original_goals[4],self.rotation)
        lengths=np.linalg.norm(np.diff(self.carry_route,axis=0),axis=1)
        assert np.all(lengths>1e-8)
        self.cumulative=np.r_[0.,np.cumsum(lengths)]
        self.length=float(self.cumulative[-1]);self.arc=0.
        self.reference_velocity=np.zeros(3);self.progress_records=[]
        self.goals[4]=self.carry_route[0].copy()

    def at_arc(self,s):
        k=min(len(self.carry_route)-2,int(np.searchsorted(self.cumulative,s,side='right')-1))
        k=max(0,k);delta=self.carry_route[k+1]-self.carry_route[k]
        tangent=delta/np.linalg.norm(delta)
        return self.carry_route[k]+(s-self.cumulative[k])*tangent,tangent,k

    def project(self,pos):
        choices=[]
        for k,(a,b) in enumerate(zip(self.carry_route,self.carry_route[1:])):
            delta=b-a;u=float(np.clip(np.dot(pos-a,delta)/np.dot(delta,delta),0,1))
            point=a+u*delta
            choices.append((float(np.linalg.norm(pos-point)),self.cumulative[k]+u*np.linalg.norm(delta)))
        distance,projection=min(choices)
        return float(projection),distance

    def update(self,q,dq,pos,rot,twist,wrench):
        self.reference_velocity[:]=0.
        if self.index!=4:return PickPlaceTask.update(self,q,dq,pos,rot,twist,wrench)
        if self.arc<self.length:
            projected,distance=self.project(pos)
            can_progress=distance<.08 and np.linalg.norm(so3_log(self.rotation@rot.T))<.12
            next_arc=min(self.length,self.arc+.06*DT,max(self.arc,projected+.012)) if can_progress else self.arc
            previous=self.goals[4].copy()
            self.arc=next_arc
            target,tangent,k=self.at_arc(self.arc)
            self.goals[4]=target if self.arc<self.length else self.original_goals[4].copy()
            self.reference_velocity=(self.goals[4]-previous)/DT
            self.path_direction=tangent;self.carry_cursor=k
            self.ready=0.
            self.progress_records.append([self.arc,projected,*self.reference_velocity,*self.goals[4]])
            return False
        return PickPlaceTask.update(self,q,dq,pos,rot,twist,wrench)

    def sample(self,unused=None):
        pos,rot,_,angular=super().sample(unused)
        return pos,rot,self.reference_velocity.copy() if self.index==4 else np.zeros(3),angular

    def metadata(self):
        value=super().metadata()
        value.update(kind='known-map payload-clearance common reference',plan=self.plan,
            nominal_speed_mps=.06,advance_lead_m=.012,arc_m=self.arc,length_m=self.length,
            collision_aware_planning=True,progress_records=self.progress_records)
        return value
