"""Explicit development contact layout; no obstacle data enters the actor."""
import xml.etree.ElementTree as ET
from office_complex_scene_v5_20260917 import extend_complex_xml


def extend_contact_layout(xml,spec=None,variant=0):
    root=ET.fromstring(extend_complex_xml(xml,spec,variant))
    # Place actual obstacles beside the unchanged nominal carry segment.
    # Their collision geometry stays physical and is never queried by actor.
    cup=root.find(".//body[@name='office_v5_cup']")
    cup.set('pos',f'.495 {-.015+variant*.008} .4055')
    for geom in cup.findall('geom'):
        if geom.get('name','').startswith('office_v5_cup_wall_'):
            pos=list(map(float,geom.get('pos').split()));size=list(map(float,geom.get('size').split()))
            pos[2]=.083;size[2]=.075
            geom.set('pos',' '.join(map(str,pos)));geom.set('size',' '.join(map(str,size)))
    for name,z in (('office_v5_pillar',.585),('office_v5_pillar_mount',.407)):
        geom=root.find(f".//geom[@name='{name}']")
        geom.set('pos',f'.600 {.095+variant*.010} {z}')
    # Correct the marginal rigid ball/floor support penetration. The ball's
    # robot-contact model and the 0.2 mm physical acceptance bound are unchanged.
    for pair in root.findall('.//contact/pair'):
        if pair.get('geom1')=='office_v5_ball_geom' and pair.get('geom2')=='office_floor':
            pair.set('solref','.00010 .8')
    return ET.tostring(root,encoding='unicode')


def install():
    import audit_office_complex_scene_v5_20260917 as scene
    scene.extend_complex_xml=extend_contact_layout
