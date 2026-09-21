"""A visibly lidded handleless cup for exterior-contact development tests."""
import xml.etree.ElementTree as ET
from office_recovery_scene_v2_20260918 import extend_layout,install as install_v2


def extend_closed_cup(xml,spec=None,variant=0):
    root=ET.fromstring(extend_layout(xml,spec,variant))
    cup=root.find(".//body[@name='office_v5_cup']")
    for geom in list(cup.findall('geom')):
        if geom.get('name','').startswith('office_v5_cup_handle_'):cup.remove(geom)
    ET.SubElement(cup,'geom',name='office_v5_cup_lid',type='cylinder',
        pos='0 0 .163',size='.037 .005',rgba='.12 .22 .30 1',mass='.04',
        friction='.65 .02 .002',solref='.002 1',solimp='.95 .99 .001 .5 2',
        contype='1',conaffinity='63')
    return ET.tostring(root,encoding='unicode')


def install():
    install_v2()
    import audit_office_complex_scene_v5_20260917 as scene
    scene.extend_complex_xml=extend_closed_cup
