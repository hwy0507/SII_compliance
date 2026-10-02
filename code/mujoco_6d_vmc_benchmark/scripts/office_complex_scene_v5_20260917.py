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


def add_free_cup(world,pos,mass=.30,height_scale=1.0,radial_scale=1.0,wall_friction='.65 .02 .002',contact_handle=False):
    body=_body(world,'office_v5_cup',np.r_[pos,.4055]);ET.SubElement(body,'freejoint',name='office_v5_cup_free')
    hs=float(height_scale)
    rs=float(radial_scale)
    geom(body,'office_v5_cup_base','cylinder',[0,0,.004],[.036*rs,.004],[.12,.43,.65,1],mass=str(mass*.35),friction=wall_friction,solref='.002 1',solimp='.95 .99 .001 .5 2')
    for i in range(20):
        a=2*math.pi*i/20
        geom(body,f'office_v5_cup_wall_{i}','box',[.033*rs*math.cos(a),.033*rs*math.sin(a),.058*hs],[.003,.0056,.050*hs],[.16,.49,.71,1],quat=numbers([math.cos(a/2),0,0,math.sin(a/2)]),mass=str(mass*.60/20),friction=wall_friction,solref='.002 1')
    for i,(p0,p1) in enumerate([([0,.033,.082*hs],[0,.058,.082*hs]),([0,.058,.082*hs],[0,.058,.035*hs]),([0,.058,.035*hs],[0,.033,.035*hs])]):
        geom(body,f'office_v5_cup_handle_{i}','capsule',[0,0,0],[.004],[.16,.49,.71,1],fromto=numbers(p0+p1),mass=str(mass*.05/3),solref='.002 1')
    if contact_handle:
        # A light, negative-y handle extension gives the moving gripper a
        # genuine cup contact during the late carry pass while leaving the
        # supported cup body at its ordinary desk height.
        # Keep a force-bearing brush available during carry, while leaving a
        # conservative clearance from the gripper collision envelope.  This
        # development fixture does not alter the frozen task or actor inputs.
        geom(body,'office_v5_cup_contact_handle','capsule',[0,0,0],[.005],[.16,.49,.71,1],
             fromto=numbers([.030,0,.135,.075,0,.135]),mass='.008',friction='.12 .008 .001',solref='.010 1')
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


def extend_complex_xml(xml,spec=None,variant=0,interaction_demo=False,corner_placement=False,combined_demo=False,combined_contact_v2=False,relaxed_pillar=False,combined_thick_corner_pillar_v1=False,combined_thick_corner_pillar_v2=False,combined_thick_corner_pillar_v3=False,combined_thick_corner_pillar_v4=False,unexpected_edge=False,tool_contact=None):
    """Return the compiled MJCF source for one held-out office fixture."""
    if spec is None:spec=SceneSpec(kind='empty')
    root=ET.fromstring(extend_xml(xml,replace(spec,kind='empty')));world=root.find('worldbody')
    # The default fixture is deliberately separated from the nominal pickup /
    # carry line.  The opt-in interaction demo moves the same physical objects
    # onto the corner-placement approach so contact is visible and auditable.
    offset=float(variant)*.018
    if combined_thick_corner_pillar_v4:
        pillar_xy=np.array([.619,-.270+offset]);cup_xy=None
    elif combined_thick_corner_pillar_v3:
        # Independent lift-contact fixture: retain the v1/v2 worlds exactly.
        # The post remains on the carry-side, while the corner's short inner
        # face is placed in the measured payload lift corridor.  The top slab
        # still supports the original corner destination.
        pillar_xy=np.array([.600,-.340+offset])
        cup_xy=None
    elif combined_thick_corner_pillar_v2:
        # Separate development world: keep a visible post and bring the
        # corner face into the measured lift corridor. V1 remains unchanged.
        pillar_xy=np.array([.600,-.340+offset])
        cup_xy=None
    elif combined_thick_corner_pillar_v1:
        # Registered development fixture requested on 2026-09-29.  Keep one
        # rigid obstacle (the pillar) and the thick corner; omit the cup so
        # the contact demonstration has a single visually attributable
        # obstacle.  Geometry is based on the previously audited relaxed
        # pillar/corner route, with no changes to the robot or task limits.
        # Above the payload center and just beside the carry hand: the tool
        # brushes this small, low-friction post while the object remains below
        # it, so contact is visible without pinning the placement load.
        pillar_xy=np.array([.600,-.360+offset])
        cup_xy=None
    elif combined_contact_v2:
        # Registered combined-contact-v2 fixture: the pillar is on the
        # retreat-side of the corner route and the taller, low-friction cup
        # stays desk-supported while exposing its rim to the carry hand.  The
        # pillar is raised above the payload carry envelope so its force-
        # bearing brush occurs during retreat, after supported release.
        # Registered combined-v3 candidate: brush the post-release retreat
        # corridor while remaining separated from the cup at x=.48.
        # Registered combined-v4 candidate from trial46's measured retreat
        # corridor (hand x=.55-.57, y=-.31); keep clear of the cup center.
        # Relaxed-pillar diagnostic: smaller, lower-friction pillar outside the
        # carry corridor; all other combined-v2 geometry remains unchanged.
        pillar_xy=np.array([.620,-.100+offset]) if relaxed_pillar else np.array([.585,-.300+offset]);cup_xy=np.array([.480,-.330+offset])
    elif combined_demo:
        # Combined development fixture: the cup grazes the early carry line;
        # the pillar sits just outside the corner slab and is approached by a
        # dedicated waypoint. Both are finite-mass physical obstacles.
        # The pillar is grazed from the side during carry, outside the ball
        # lane and below the payload center so it cannot pin the final route.
        pillar_xy=np.array([.620,-.100+offset]);cup_xy=np.array([.480,-.330+offset])
    elif interaction_demo:
        # Put the cup just ahead of the carry line.  The previous y=-.255
        # placement overlapped the pickup cube's handle at reset and was
        # correctly rejected by audit_initial.  At y=.050 the cup remains
        # disjoint from the cube and corner slab while the lifted payload
        # passes its rim.  The corner carry waypoint is near y=-.30. Keep
        # this interaction fixture at the previously audited low-force
        # offset; closer cup placements can pin the gripper during align and
        # are retained as failures rather than relabeled as compliant.
        pillar_xy=np.array([.840,.250+offset]);cup_xy=np.array([.520,-.330+offset])
    elif corner_placement:
        # Keep the corner-placement acceptance path clear.  The interaction
        # demo is the separate condition that deliberately exposes these
        # objects to the arm.
        pillar_xy=np.array([.840,.250+offset]);cup_xy=np.array([.470,.015+offset])
    else:
        pillar_xy=np.array([.625,.075+offset]);cup_xy=np.array([.470,.015+offset])
    pillar_friction='.012 .004 .001' if (combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3) else '.001 .001 .001' if (combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v4) else '.012 .004 .001' if relaxed_pillar else '.045 .008 .001' if combined_contact_v2 else '.08 .01 .001' if combined_demo else '.35 .015 .001'
    pillar_solref='.025 1' if (combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3) else '.040 1' if (combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v4) else '.025 1' if relaxed_pillar else '.010 1' if combined_contact_v2 else '.008 1' if combined_demo else '.002 1'
    pillar_center_z=.700 if (combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3) else .750 if (combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v4) else .650 if (relaxed_pillar or combined_demo) else .700 if combined_contact_v2 else .585
    pillar_half_z=.040 if (combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3) else .010 if (combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v4) else .050 if (relaxed_pillar or combined_demo) else .015 if combined_contact_v2 else .185
    pillar_radius=.015 if (combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3) else .004 if (combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v4) else .038 if combined_demo else .010 if relaxed_pillar else .015 if combined_contact_v2 else .038
    pillar_kwargs=dict(friction=pillar_friction,solref=pillar_solref)
    if combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4:pillar_kwargs['solimp']='.99 .999 .002 .5 2'
    geom(world,'office_v5_pillar','cylinder',np.r_[pillar_xy,pillar_center_z],[pillar_radius,pillar_half_z],[.27,.29,.32,1],**pillar_kwargs)
    geom(world,'office_v5_pillar_mount','cylinder',np.r_[pillar_xy,.407],[.055,.007],[.20,.22,.25,1],friction='.45 .02 .002')
    # Thick L corner: vertical near face x=.688, horizontal underside z=.670.
    # The solids share a body; their touching surfaces, near x face and width
    # coincide after accounting for thickness (no extra protruding lip).
    # The development corner is raised above the ordinary desk, while its
    # upper surface stays inside the measured FR3 reach envelope.  The
    # original formal fixture remains unchanged; this is only the opt-in
    # corner-placement presentation geometry.
    corner_x=.640 if combined_thick_corner_pillar_v2 else .650 if corner_placement else .750
    # The development corner top is intentionally within the measured FR3
    # reach envelope.  Its upper surface is z=.535 m; the payload center is
    # placed at z=.560 m so its 25 mm half-height sits on the slab.
    corner_z=.500 if corner_placement else .690
    face_z=.520 if combined_thick_corner_pillar_v4 else (.500 if combined_thick_corner_pillar_v3 else (.440 if corner_placement else .535))
    face_h=.020 if combined_thick_corner_pillar_v4 else (.030 if combined_thick_corner_pillar_v3 else (.080 if corner_placement else .135))
    face_x=.480 if combined_thick_corner_pillar_v4 else (.490 if combined_thick_corner_pillar_v3 else corner_x)
    face_y=(-.150+offset) if combined_thick_corner_pillar_v4 else ((-.190+offset) if combined_thick_corner_pillar_v3 else (.300+offset if corner_placement else .205+offset))
    geom(world,'office_v5_corner_face','box',[face_x,face_y,face_z],[.012 if combined_thick_corner_pillar_v4 else (.008 if combined_thick_corner_pillar_v3 else .012),
         .010 if combined_thick_corner_pillar_v4 else (.025 if combined_thick_corner_pillar_v3 else .095),face_h],[.50,.32,.18,1],friction='.25 .01 .001',solref='.002 1')
    if combined_thick_corner_pillar_v3:
        # Interlocking collision solids make the lift face part of the thick
        # corner, without translating the full support slab into grasp.
        geom(world,'office_v5_corner_bridge','box',[.536,-.190+offset,.480],[.038,.008,.005],
             [.50,.32,.18,1],friction='.25 .01 .001',solref='.002 1')
    top_y=-.100+offset if corner_placement else .205+offset
    top_half_y=.250 if (combined_demo or combined_contact_v2 or combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4) else (.300 if corner_placement else .095)
    top_half_x=.080 if corner_placement else .062
    geom(world,'office_v5_corner_top','box',[corner_x,top_y,corner_z],[top_half_x,top_half_y,.020],[.57,.37,.20,1],friction='.25 .01 .001',solref='.002 1')
    if cup_xy is not None:
        add_free_cup(world,cup_xy,mass=float(getattr(spec,'cup_mass',.30)),
                     height_scale=1.0,radial_scale=.80 if combined_contact_v2 else 1.0,
                     wall_friction='.18 .01 .001' if combined_contact_v2 else '.65 .02 .002',
                     contact_handle=bool(combined_contact_v2))
    # Free ball; evaluator assigns initial qvel and the ball bounces via
    # solref/solimp restitution against rigid robot/desk geoms.
    ball_xy=np.array([.58 if (combined_contact_v2 or combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4) else .54,
                      -.50 if combined_demo else -.43,.655])
    if tool_contact:ball_xy=np.array(tool_contact['ball_center_m'])
    ball=_body(world,'office_v5_ball',ball_xy);ET.SubElement(ball,'freejoint',name='office_v5_ball_free')
    geom(ball,'office_v5_ball_geom','sphere',[0,0,0],[tool_contact['ball_radius_m'] if tool_contact else .045],[.80,.15,.12,1],mass=str(tool_contact['ball_mass_kg'] if tool_contact else getattr(spec,'ball_mass',.22)),
         friction='.12 .005 .0001',
         solref='.00040 .55' if (combined_contact_v2 or combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4) else '.0005 .35',
         solimp='.995 .9995 .00005 .5 2' if (combined_contact_v2 or combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4) else '.99 .999 .0001 .5 2',priority='4')
    contacts=root.find('contact')
    if contacts is None:contacts=ET.SubElement(root,'contact')
    # Dedicated rigid support contacts; the softer ball/robot response is
    # unchanged. Do not let averaged floor compliance bury the rebounding ball.
    for support in ('office_floor','office_desk_top'):
        ET.SubElement(contacts,'pair',geom1='office_v5_ball_geom',geom2=support,
            solref='.00012 .85',solimp='.9992 .99992 .00004 .5 2',friction='.12 .12 .005 .0001 .0001')
    # Finite-mass human hand and independent rod, each physically constrained
    # to a rail. They are not mocap bodies and cannot pass through the robot.
    add_pedestrian(world)
    rod_pos=[.24,-.19,.58] if not corner_placement else ([.24,-.28,.58] if (combined_demo or combined_contact_v2 or combined_thick_corner_pillar_v1 or combined_thick_corner_pillar_v2 or combined_thick_corner_pillar_v3 or combined_thick_corner_pillar_v4) else ([.24,-.36,.58] if not interaction_demo else [.24,-.19,.58]))
    if tool_contact:rod_pos=tool_contact['rod_center_m']
    rod=_body(world,'office_v5_push_rod',rod_pos)
    ET.SubElement(rod,'joint',name='office_v5_push_rod_joint',type='slide',axis=numbers(tool_contact.get('rod_axis',[1,0,0])) if tool_contact else '1 0 0',range='0 .24',damping='3')
    geom(rod,'office_v5_push_rod_geom','capsule',[0,0,0],[.014],[.72,.50,.20,1],
         fromto=numbers(tool_contact.get('rod_fromto',[-.22,0,0,.045,0,0])) if tool_contact else '-.22 0 0 .045 0 0',mass='.65',solref=tool_contact.get('rod_solref','.001 1') if tool_contact else '.001 1',solimp='.95 .99 .0001 .5 2')
    if unexpected_edge:
        # Stationary, physically supported lip omitted from the prior map.
        # Never spawned/teleported into the robot; all methods share it.
        geom(world,'office_v5_unexpected_edge','box',[.610,-.250,.555],
             [.010,.045,.035],[.68,.28,.10,1],friction='.6 .01 .001',
             solref='.002 1',solimp='.99 .999 .0001 .5 2')
    # A visual-only event marker is forbidden: omit all marker geometry.
    return ET.tostring(root,encoding='unicode')


def fixture_flags(seed,variant=0,interaction_demo=False,corner_placement=False,combined_demo=False,combined_contact_v2=False,relaxed_pillar=False,combined_thick_corner_pillar_v1=False,combined_thick_corner_pillar_v2=False,combined_thick_corner_pillar_v3=False,combined_thick_corner_pillar_v4=False):
    rng=np.random.default_rng(seed)
    return dict(scene='empty',seed=int(seed),duration=55.,nominal_speed=float(rng.uniform(.045,.070)),
      cup_mass=float(rng.uniform(.24,.36)),ball_mass=float(rng.uniform(.16,.28)),
      ball_speed=float(rng.uniform(1.35,1.85)),yaw=float(rng.uniform(-.10,.10)),
      shift=float(rng.uniform(-.015,.015)),along=float(rng.uniform(-.015,.015)),width=.05,
      office_variant=int(variant),event_seed=int(rng.integers(1,9999999)),
      interaction_demo=bool(interaction_demo),corner_placement=bool(corner_placement),combined_demo=bool(combined_demo),
      combined_contact_v2=bool(combined_contact_v2),relaxed_pillar=bool(relaxed_pillar),
      combined_thick_corner_pillar_v1=bool(combined_thick_corner_pillar_v1),
      combined_thick_corner_pillar_v2=bool(combined_thick_corner_pillar_v2),
      combined_thick_corner_pillar_v3=bool(combined_thick_corner_pillar_v3),
      combined_thick_corner_pillar_v4=bool(combined_thick_corner_pillar_v4))
