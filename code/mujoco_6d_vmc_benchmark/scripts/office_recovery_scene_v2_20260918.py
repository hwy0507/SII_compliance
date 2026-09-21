"""Filled cup, downstream pillar and load-confirmed common placement task."""
import xml.etree.ElementTree as ET
import numpy as np
from office_recovery_scene_20260918 import extend_contact_layout


def extend_layout(xml,spec=None,variant=0):
    root=ET.fromstring(extend_contact_layout(xml,spec,variant))
    cup=root.find(".//body[@name='office_v5_cup']")
    # A filled mug: double each part's mass, preserving contact/friction law.
    for geom in cup.findall('geom'):
        if geom.get('mass'):geom.set('mass',str(2*float(geom.get('mass'))))
    # A downstream post on the other side of the nominal carry line. The
    # actor sees contact loads only; no route is planned around this post.
    for name,z in (('office_v5_pillar',.585),('office_v5_pillar_mount',.407)):
        root.find(f".//geom[@name='{name}']").set('pos',f'.455 {.085+variant*.010} {z}')
    return ET.tostring(root,encoding='unicode')


def install():
    import audit_office_complex_scene_v5_20260917 as scene
    import office_task_v4_20260917 as task
    from run_benchmark import so3_log
    scene.extend_complex_xml=extend_layout
    class LoadConfirmedPlacement(task.PickPlaceTask):
        def update(self,q,dq,pos,rot,twist,wrench):
            if self.index!=5:return super().update(q,dq,pos,rot,twist,wrench)
            error=np.asarray(pos)-self.goals[5]
            self.release_load_change=float(wrench[2])-(self.carry_load or 0.)
            # A grasp can settle by millimetres in the fingers. Requiring
            # the palm to hit one absolute z after support can command the
            # held rigid object through the desktop and deadlock release.
            # Keep precise xy alignment; confirm physical load transfer and
            # a stationary hand inside the known placement height envelope.
            ready=(np.linalg.norm(error[:2])<.012 and -.012<error[2]<.035
                and np.linalg.norm(so3_log(self.rotation@rot.T))<.12
                and np.linalg.norm(twist[:3])<.025
                and self.carry_load is not None and self.release_load_change>.4)
            self.ready=self.ready+task.DT if ready else 0.
            if self.ready>=.20-1e-9:
                self.previous_goal=self.goals[self.index].copy();self.index+=1
                self.ready=0.;self.path_direction=self.direction();return True
            return False
    task.PickPlaceTask=LoadConfirmedPlacement
