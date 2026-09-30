"""Auditable primitive source-domain geometry for the v6 teacher campaign.

Cup is a hollow compound body with a free joint, realistic finite mass and a
handle. Pillar is explicitly bolted to the desk. No visual/collision mismatch,
teleporting obstacle, or controller input is created here.
"""
from dataclasses import dataclass,asdict
import math
import xml.etree.ElementTree as ET
import numpy as np


@dataclass(frozen=True)
class SceneSpec:
    kind: str = "corner"
    yaw: float = 0.
    shift: float = 0.
    along: float = 0.
    width: float = .050
    cup_mass: float = .30
    ball_speed: float = 1.5
    ball_mass: float = .20
    ball_angle: float = 0.
    ball_height_offset: float = 0.
    ball_vertical_speed: float = 1.3
    ball_target_x: float = .54
    ball_target_y: float = 0.
    ball_target_z: float = .62
    push_angle: float = 0.
    push_height: float = .56
    push_stroke: float = .18
    push_target_x: float = .54
    push_target_y: float = 0.
    corner_height: float = .70
    corner_friction: float = .20
    payload_mass: float = .08
    seed: int = 0


def numbers(v):return " ".join(f"{float(x):.9g}" for x in v)


def geom(parent,name,kind,pos,size,rgba,**kwargs):
    attrs=dict(name=name,type=kind,pos=numbers(pos),size=numbers(size),rgba=numbers(rgba),
               contype="32",conaffinity="63",friction=".6 .02 .002",solref=".001 1",
               solimp=".95 .99 .001 .5 2",priority="2")
    attrs.update({k:str(v) for k,v in kwargs.items()})
    return ET.SubElement(parent,"geom",attrs)


def task_layout(spec):
    if spec.kind in ("ball","push","complex","empty"):
        return np.array([.54,0.,.66]),np.array([.54,0.,.425])
    angle=spec.yaw
    center=np.array([.54,-.01])
    direction=np.array([0.,1.]);tangent=np.array([-1.,0.])
    c,s=math.cos(angle),math.sin(angle);rot=np.array([[c,-s],[s,c]])
    direction=rot@direction;tangent=rot@tangent
    start=center-direction*.18
    goal=center+direction*.25
    return np.r_[start,.60],np.r_[goal,.425]


def extend_xml(xml,spec):
    if spec.kind not in ("ball","push","corner","cup","pillar","cup_pillar","complex","empty"):
        raise ValueError(spec.kind)
    root=ET.fromstring(xml);world=root.find("worldbody")
    gripper=root.find(".//actuator/position[@name='gripper']")
    if gripper is not None:gripper.set("kv","25")
    # Remove only obsolete apparatus. The robot and all of its physical
    # collisions remain present. The office desk replaces the pickup pad.
    for body in list(world.findall("body")):
        if body.get("name") in ("pickup_stage","thick_table_structure"):
            world.remove(body)
        elif body.get("name") in ("nominal_marker","actual_marker"):
            for g in body.findall("geom"):g.set("rgba","0 0 0 0")
    for g in root.iter("geom"):
        if g.get("name")=="hand_ball_proxy":
            g.set("contype","0");g.set("conaffinity","0");g.set("rgba","0 0 0 0")
        kind=g.get("class","")
        if kind=="collision" or kind.startswith("fingertip_pad_collision_"):
            if g.get("name")!="hand_ball_proxy":g.set("conaffinity","63")
    for name in ("target_object_geom","rod_geom"):
        g=root.find(f".//geom[@name='{name}']")
        if name=="target_object_geom":
            g.set("contype","4");g.set("conaffinity","63")
            g.set("priority","4");g.set("solref",".0005 1");g.set("solimp",".99 .999 .0001 .5 2")
            g.set("mass",str(spec.payload_mass))
    if spec.kind in ("push","complex"):
        rod=root.find(".//body[@name='push_rod_support']")
        # Rotate the complete physical pusher (slide direction and cylinder)
        # around world Z.  At zero angle this is exactly the historical -Y
        # push.  The initial centre remains 0.20 m upstream of the nominal
        # hand line, so changing angle changes the true contact direction.
        push_direction=np.array([math.sin(spec.push_angle),-math.cos(spec.push_angle),0.])
        target=np.array([spec.push_target_x,spec.push_target_y,spec.push_height])
        rod.set("pos",numbers(target-push_direction*.32))
        joint=rod.find("joint[@name='push_rod_slide']")
        joint.set("axis",numbers(push_direction))
        travel=max(.20,spec.push_stroke+.025)
        joint.set("range",f"0 {travel:.9g}")
        q=np.array([math.sqrt(.5),-push_direction[1]/math.sqrt(2.),push_direction[0]/math.sqrt(2.),0.])
        rod.find("geom[@name='push_rod_geom']").set("quat",numbers(q))
        actuator=root.find(".//actuator/position[@name='push_rod_driver']")
        actuator.set("ctrlrange",f"0 {travel:.9g}")
    asset=root.find("asset")
    ET.SubElement(asset,"texture",dict(name="office_floor_tex",type="2d",builtin="checker",rgb1=".23 .25 .28",rgb2=".29 .31 .34",width="128",height="128"))
    ET.SubElement(asset,"material",dict(name="office_floor_mat",texture="office_floor_tex",texrepeat="5 5",reflectance=".05"))
    geom(world,"office_floor","plane",[0,0,-.35],[3,3,.05],[.4,.4,.4,1],material="office_floor_mat")
    geom(world,"office_robot_pedestal","box",[0,0,-.175],[.11,.11,.175],[.24,.27,.30,1])
    geom(world,"office_desk_top","box",[.58,0,.375],[.28,.38,.025],[.63,.45,.29,1],friction=".75 .02 .002")
    for x in (.34,.82):
        for y in (-.34,.34):
            geom(world,f"office_leg_{x}_{y}","box",[x,y,.0],[.022,.022,.35],[.16,.18,.20,1])
    # Physical contextual objects outside the nominal manipulation corridor.
    if spec.kind in ("cup","pillar","cup_pillar","complex","empty"):
        geom(world,"office_monitor_foot","box",[.77,.33,.408],[.065,.040,.008],[.1,.11,.13,1])
        geom(world,"office_monitor_stand","box",[.79,.33,.475],[.014,.012,.075],[.15,.16,.18,1])
        geom(world,"office_monitor_screen","box",[.79,.34,.64],[.12,.012,.075],[.06,.08,.11,1])
        geom(world,"office_notebook","box",[.72,-.29,.41],[.07,.045,.01],[.2,.35,.55,1])
        geom(world,"office_keyboard","box",[.72,.315,.409],[.095,.025,.009],[.24,.25,.27,1])
    direction=np.array([0.,1.]);angle=spec.yaw
    rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    normal=rot@direction;tangent=np.array([-normal[1],normal[0]])
    center=np.array([.54,-.01])+spec.shift*tangent+spec.along*normal
    if spec.kind=="complex":
        # Keep the combined office fixtures outside the initial FR3 links;
        # the nominal lift corridor reaches them later through the desk edge.
        center=center+np.array([.20,.15])
    if spec.kind in ("corner","complex"):
        yaw=math.atan2(normal[1],normal[0]);quat=numbers([math.cos(yaw/2),0,0,math.sin(yaw/2)])
        if not .55 <= spec.corner_height <= .78:
            raise ValueError("corner_height must remain above the 0.40 m desk top")
        face_half_height=(spec.corner_height-.40)/2.
        face_center_z=.40+face_half_height
        friction=f"{spec.corner_friction:.9g} .01 .001"
        geom(world,"primitive_corner_face","box",np.r_[center,face_center_z],[.010,spec.width,face_half_height],[.50,.32,.18,1],quat=quat,friction=friction)
        # The face top and shelf underside are analytically identical for all
        # sampled heights; no gap or overlap is introduced by randomisation.
        geom(world,"primitive_corner_top","box",np.r_[center+normal*.06,spec.corner_height+.02],[.070,spec.width,.02],[.57,.37,.20,1],quat=quat,friction=friction)
    if spec.kind in ("pillar","cup_pillar","complex"):
        p=center-tangent*.060+normal*(.10 if spec.kind=="cup_pillar" else .06)
        geom(world,"office_pillar","cylinder",np.r_[p,.585],[.038,.185],[.27,.29,.32,1],friction=".3 .015 .001")
        geom(world,"office_pillar_mount","cylinder",np.r_[p,.407],[.055,.007],[.20,.22,.25,1])
    if spec.kind in ("cup","cup_pillar","complex"):
        p=center+tangent*.005-normal*.06 if spec.kind=="cup_pillar" else center
        # Release the free cup 5 mm above the desktop.  Its base bottom is at
        # body z, so gravity settles it onto the physical desk top z=.400;
        # this avoids an initially interpenetrating support that can later be
        # mistaken for a policy failure.
        body=ET.SubElement(world,"body",name="office_cup",pos=numbers(np.r_[p,.4055]))
        ET.SubElement(body,"freejoint",name="office_cup_free")
        geom(body,"office_cup_base","cylinder",[0,0,.004],[.036,.004],[.12,.43,.65,1],mass=str(spec.cup_mass*.35),friction=".6 .02 .002")
        for i in range(20):
            a=2*math.pi*i/20
            geom(body,f"office_cup_wall_{i}","box",[.033*math.cos(a),.033*math.sin(a),.058],
                 [.003,.0056,.050],[.16,.49,.71,1],quat=numbers([math.cos(a/2),0,0,math.sin(a/2)]),mass=str(spec.cup_mass*.60/20))
        for i,(p0,p1) in enumerate([([0,.033,.082],[0,.058,.082]),([0,.058,.082],[0,.058,.035]),([0,.058,.035],[0,.033,.035])]):
            geom(body,f"office_cup_handle_{i}","capsule",[0,0,0],[.004],[.16,.49,.71,1],fromto=numbers(p0+p1),mass=str(spec.cup_mass*.05/3))
    if spec.kind in ("ball","complex"):
        # Park the event ball outside the workspace.  Its physical launch
        # state is initialized once, at the requested task stage, by the
        # rollout driver.  This avoids a pre-event ball/table contact when a
        # low target height would mathematically imply an unsafe launcher Z.
        body=ET.SubElement(world,"body",name="primitive_free_ball",pos=numbers([1.5,-1.5,.50]))
        ET.SubElement(body,"freejoint",name="primitive_free_ball_joint")
        geom(body,"primitive_free_ball_geom","sphere",[0,0,0],[.05],[.80,.15,.12,1],mass=str(spec.ball_mass),friction=".08 .005 .0001")
        ball_geom=body.find("geom");ball_geom.set("priority","4")
        ball_geom.set("solref",".00025 1");ball_geom.set("solimp",".99 .999 .0001 .5 2")
    # Geometry-only provenance is deliberately not attached to actor inputs.
    return ET.tostring(root,encoding="unicode")
