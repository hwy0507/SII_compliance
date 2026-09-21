"""Physical office test world for the final target-domain benchmark.

The scene contains a real desk, a thick L-shaped desk corner, a bolted
cylindrical post, a free hollow cup, a free ball with restitution, a finite
mass human-hand surrogate, and a separate finite-mass push rod.  Dynamic
apparatus are driven by qfrc_applied in the evaluator and never enter the
student observation.  No weld, mocap, teleport, magnetic grasp, or disabled
collision is used.
"""
from dataclasses import replace
import math
import xml.etree.ElementTree as ET
import numpy as np
from office_contact_scene_20260916 import extend_xml, SceneSpec, numbers, geom


def _body(world,name,pos):
    return ET.SubElement(world,'body',name=name,pos=numbers(pos))


def add_free_cup(world,pos,mass=.30):
    body=_body(world,'office_v5_cup',np.r_[pos,.4055]);ET.SubElement(body,'freejoint',name='office_v5_cup_free')
    geom(body,'office_v5_cup_base','cylinder',[0,0,.004],[.036,.004],[.12,.43,.65,1],mass=str(mass*.35),friction='.65 .02 .002',solref='.002 1',solimp='.95 .99 .001 .5 2')
    for i in range(20):
        a=2*math.pi*i/20
        geom(body,f'office_v5_cup_wall_{i}','box',[.033*math.cos(a),.033*math.sin(a),.058],[.003,.0056,.050],[.16,.49,.71,1],quat=numbers([math.cos(a/2),0,0,math.sin(a/2)]),mass=str(mass*.60/20),solref='.002 1')
    for i,(p0,p1) in enumerate([([0,.033,.082],[0,.058,.082]),([0,.058,.082],[0,.058,.035]),([0,.058,.035],[0,.033,.035])]):
        geom(body,f'office_v5_cup_handle_{i}','capsule',[0,0,0],[.004],[.16,.49,.71,1],fromto=numbers(p0+p1),mass=str(mass*.05/3),solref='.002 1')
    return body


def add_slide_apparatus(world,name,pos,axis,geom_name,rgba,mass,stroke):
    body=_body(world,name,np.asarray(pos,dtype=float))
    ET.SubElement(body,'joint',name=name+'_joint',type='slide',axis=numbers(axis),range=f'0 {stroke}',damping='2',armature='.002')
    geom(body,geom_name,'capsule',[0,0,0],[.025],rgba,fromto=numbers([0,-.045,0,0,.045,0]),mass=str(mass),friction='.55 .02 .002',solref='.004 1',solimp='.95 .99 .001 .5 2')
    return body


def add_pedestrian(world):
    """Reduced human: guided horizontal base, articulated shoulder/elbow/wrist.

    Not a validated biped gait or biomechanical human model. All body parts
    have mass and collision; compliant wrist motion transmits contact forces.
    """
    body=_body(world,'office_v5_person',[1.20,-.19,-.35])
    ET.SubElement(body,'joint',name='office_v5_person_root',type='slide',axis='-1 0 0',range='0 .25',damping='10')
    skin=[.68,.45,.30,1];shirt=[.18,.32,.55,1];pants=[.18,.20,.26,1]
    geom(body,'office_v5_person_torso','capsule',[0,0,0],[.105],shirt,fromto='0 0 .85 0 0 1.20',mass='28')
    geom(body,'office_v5_person_head','sphere',[0,0,1.48],[.105],skin,mass='4.5')
    for side in (-1,1):
        geom(body,f'office_v5_person_leg_{side}','capsule',[0,0,0],[.055],pants,
             fromto=numbers([0,side*.07,.09,0,side*.07,.78]),mass='7')
        geom(body,f'office_v5_person_foot_{side}','box',[-.035,side*.07,.055],[.09,.055,.04],[.12,.13,.15,1],mass='1')
    arm=_body(body,'office_v5_upper_arm',[-.035,0,1.18])
    ET.SubElement(arm,'joint',name='office_v5_shoulder',type='hinge',axis='0 1 0',range='-.45 .45',damping='4')
    geom(arm,'office_v5_upper_arm_geom','capsule',[0,0,0],[.038],shirt,fromto='0 0 0 -.19 0 -.10',mass='1.8')
    forearm=_body(arm,'office_v5_forearm',[-.19,0,-.10])
    ET.SubElement(forearm,'joint',name='office_v5_elbow',type='hinge',axis='0 1 0',range='-.45 .45',damping='3')
    geom(forearm,'office_v5_forearm_geom','capsule',[0,0,0],[.030],skin,fromto='0 0 0 -.19 0 -.12',mass='1.0')
    hand=_body(forearm,'office_v5_human_hand',[-.19,0,-.12])
    ET.SubElement(hand,'joint',name='office_v5_human_hand_joint',type='slide',axis='-1 0 0',range='-.05 .03',
                  stiffness='180',damping='8')
    geom(hand,'office_v5_human_palm','box',[-.037,0,0],[.032,.036,.015],skin,mass='.30',
         solref='.001 1',solimp='.95 .99 .0001 .5 2')
    for i in range(4):
        y=(i-1.5)*.017
        geom(hand,f'office_v5_human_finger_{i}','capsule',[0,0,0],[.007],skin,
             fromto=numbers([-.069,y,0,-.102,y,-.005]),mass='.025',solref='.001 1',solimp='.95 .99 .0001 .5 2')
    geom(hand,'office_v5_human_thumb','capsule',[0,0,0],[.010],skin,
         fromto='-.03 -.04 0 -.064 -.052 -.003',mass='.05',solref='.001 1')
    return body


def extend_complex_xml(xml,spec=None,variant=0):
    """Return the compiled MJCF source for one held-out office fixture."""
    if spec is None:spec=SceneSpec(kind='empty')
    root=ET.fromstring(extend_xml(xml,replace(spec,kind='empty')));world=root.find('worldbody')
    # Static obstacles are deliberately separated from the pickup/carry line
    # at t=0 and are reached only after lift/carry.
    offset=float(variant)*.018
    geom(world,'office_v5_pillar','cylinder',[.625,.075+offset,.585],[.038,.185],[.27,.29,.32,1],friction='.35 .015 .001',solref='.002 1')
    geom(world,'office_v5_pillar_mount','cylinder',[.625,.075+offset,.407],[.055,.007],[.20,.22,.25,1],friction='.45 .02 .002')
    # Thick L corner: vertical near face x=.688, horizontal underside z=.670.
    # The solids share a body; their touching surfaces, near x face and width
    # coincide after accounting for thickness (no extra protruding lip).
    geom(world,'office_v5_corner_face','box',[.700,.205+offset,.535],[.012,.095,.135],[.50,.32,.18,1],friction='.25 .01 .001',solref='.002 1')
    geom(world,'office_v5_corner_top','box',[.750,.205+offset,.690],[.062,.095,.020],[.57,.37,.20,1],friction='.25 .01 .001',solref='.002 1')
    add_free_cup(world,[.470,.015+offset],mass=float(getattr(spec,'cup_mass',.30)))
    # Free ball; evaluator assigns initial qvel and the ball bounces via
    # solref/solimp restitution against rigid robot/desk geoms.
    ball=_body(world,'office_v5_ball',[.54,-.43,.655]);ET.SubElement(ball,'freejoint',name='office_v5_ball_free')
    geom(ball,'office_v5_ball_geom','sphere',[0,0,0],[.045],[.80,.15,.12,1],mass=str(getattr(spec,'ball_mass',.22)),friction='.12 .005 .0001',solref='.0005 .35',solimp='.99 .999 .0001 .5 2',priority='4')
    contacts=root.find('contact')
    if contacts is None:contacts=ET.SubElement(root,'contact')
    # Dedicated rigid support contacts; the softer ball/robot response is
    # unchanged. Do not let averaged floor compliance bury the rebounding ball.
    for support in ('office_floor','office_desk_top'):
        ET.SubElement(contacts,'pair',geom1='office_v5_ball_geom',geom2=support,
            solref='.00015 .8',solimp='.999 .9999 .00005 .5 2',friction='.12 .12 .005 .0001 .0001')
    # Finite-mass human hand and independent rod, each physically constrained
    # to a rail. They are not mocap bodies and cannot pass through the robot.
    add_pedestrian(world)
    rod=_body(world,'office_v5_push_rod',[.24,-.19,.58])
    ET.SubElement(rod,'joint',name='office_v5_push_rod_joint',type='slide',axis='1 0 0',range='0 .24',damping='3')
    geom(rod,'office_v5_push_rod_geom','capsule',[0,0,0],[.014],[.72,.50,.20,1],
         fromto='-.22 0 0 .045 0 0',mass='.65',solref='.001 1',solimp='.95 .99 .0001 .5 2')
    # A visual-only event marker is forbidden: omit all marker geometry.
    return ET.tostring(root,encoding='unicode')


def fixture_flags(seed,variant=0):
    rng=np.random.default_rng(seed)
    return dict(scene='empty',seed=int(seed),duration=55.,nominal_speed=float(rng.uniform(.045,.070)),
      cup_mass=float(rng.uniform(.24,.36)),ball_mass=float(rng.uniform(.16,.28)),
      ball_speed=float(rng.uniform(1.35,1.85)),yaw=float(rng.uniform(-.10,.10)),
      shift=float(rng.uniform(-.015,.015)),along=float(rng.uniform(-.015,.015)),width=.05,
      office_variant=int(variant),event_seed=int(rng.integers(1,9999999)))
