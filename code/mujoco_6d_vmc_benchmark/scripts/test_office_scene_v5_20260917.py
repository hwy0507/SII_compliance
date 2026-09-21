"""Regression checks for physical scene structure and honest source splits."""
import unittest
from pathlib import Path
import numpy as np
import mujoco
from audit_office_complex_scene_v5_20260917 import make
from office_complex_scene_v5_20260917 import fixture_flags
from office_task_v4_20260917 import audit_initial
from build_primitive_coverage_protocol_v5_20260917 import build


class OfficeSceneTests(unittest.TestCase):
    def test_thickness_alignment_and_dynamic_bodies(self):
        env,_,_=make(fixture_flags(2026091751));m,d=env.model,env.data
        try:
            audit_initial(m,d)
            gid=lambda n:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,n)
            face=gid('office_v5_corner_face');top=gid('office_v5_corner_top')
            self.assertAlmostEqual(m.geom_pos[face,0]-m.geom_size[face,0],m.geom_pos[top,0]-m.geom_size[top,0])
            self.assertAlmostEqual(m.geom_pos[face,2]+m.geom_size[face,2],m.geom_pos[top,2]-m.geom_size[top,2])
            self.assertAlmostEqual(m.geom_size[face,1],m.geom_size[top,1])
            for name in ('office_v5_cup_free','office_v5_ball_free'):
                j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,name)
                self.assertEqual(m.jnt_type[j],mujoco.mjtJoint.mjJNT_FREE)
                self.assertGreater(m.body_mass[m.jnt_bodyid[j]],0)
            for name in ('office_v5_human_palm','office_v5_push_rod_geom','office_v5_ball_geom'):
                g=gid(name);self.assertGreater(m.geom_contype[g],0);self.assertGreater(m.geom_conaffinity[g],0)
            self.assertEqual(sum((mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith('office_v5_human_finger') for i in range(m.ngeom)),4)
            self.assertGreaterEqual(gid('office_v5_human_thumb'),0)
        finally:env.close()

    def test_coverage_is_a_nonexecuted_source_only_design(self):
        protocol=build();rows=protocol['rows']
        self.assertFalse(protocol['collection_adapter_implemented'])
        self.assertEqual(protocol['actual_teacher_traces_collected'],0)
        self.assertEqual(sum(r['split']=='train' for r in rows),84)
        self.assertEqual(sum(r['split']=='validation' for r in rows),28)
        train={r['fixture_hash'] for r in rows if r['split']=='train'}
        validation={r['fixture_hash'] for r in rows if r['split']=='validation'}
        self.assertFalse(train&validation)
        self.assertEqual({r['scene'] for r in rows},{'ball','push','corner','free'})


if __name__=='__main__':unittest.main()
