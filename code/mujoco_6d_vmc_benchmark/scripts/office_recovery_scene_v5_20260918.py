"""Sequential unknown-object contacts, distinct from the retained pinch test."""
import xml.etree.ElementTree as ET
import numpy as np
from office_recovery_scene_v4_20260918 import install as install_v4
from office_recovery_scene_v3_20260918 import extend_closed_cup


def extend_sequential(xml,spec=None,variant=0):
    root=ET.fromstring(extend_closed_cup(xml,spec,variant))
    for name,z in (('office_v5_pillar',.585),('office_v5_pillar_mount',.407)):
        root.find(f".//geom[@name='{name}']").set('pos',f'.580 {.205+variant*.010} {z}')
    return ET.tostring(root,encoding='unicode')


def install():
    install_v4()
    import audit_office_complex_scene_v5_20260917 as scene
    import office_task_v4_20260917 as task
    scene.extend_complex_xml=extend_sequential
    task.DEST=np.array([.54,.35,.425])
