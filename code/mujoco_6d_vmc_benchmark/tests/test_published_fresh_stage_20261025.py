import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import dispatch_published_fresh_stage_20261025 as dispatch


class FreshStageTests(unittest.TestCase):
    def test_no_contaminated_replay_or_resume_and_no_core_overlap(self):
        methods=['direct','impedance','admittance','vmc']
        protocol=dict(controllers=methods,algorithms=['cheq'],reward=dict(gamma=.9995),
                      learner_batch_size=256,learner_updates_per_transition=1,seeds=[17])
        plan=dict(seed=17,cycles=6,reserved_cpus=[13],coordinator_cpu=14,
                  jobs=[dict(controller=m,cpus=[i*3,i*3+1,i*3+2],workers=2,
                             wait_for=[{'pid':100+i}]) for i,m in enumerate(methods)])
        dispatch.validate(protocol,plan,set(range(15)))
        for key in ('recovered_replay','resume_parent_registration','critic_restart','completed_stage_continuation'):
            changed=dict(protocol,**{key:{'old':'state'}})
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'cannot import'):
                dispatch.validate(changed,plan,set(range(15)))
        for cpu in (3,13,14,20):
            changed=copy.deepcopy(plan);changed['jobs'][0]['cpus'][0]=cpu
            with self.subTest(cpu=cpu),self.assertRaisesRegex(ValueError,'allocation conflict'):
                dispatch.validate(protocol,changed,set(range(15)))

    def test_live_original_waits_even_with_existing_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'FINISHED.json';p.write_text(json.dumps({'updates':100000}))
            job=dict(wait_for=[dict(pid=1,start_ticks='original',finished=str(p),expected={'updates':100000})])
            with patch.object(dispatch,'identity',return_value='original'):
                self.assertFalse(dispatch.resources_released(job))
            with patch.object(dispatch,'identity',return_value='different'):
                with self.assertRaisesRegex(ValueError,'PID reused'):
                    dispatch.resources_released(job)
            with patch.object(dispatch,'identity',return_value=None):
                self.assertTrue(dispatch.resources_released(job))
                p.write_text(json.dumps({'updates':5000}))
                with self.assertRaisesRegex(ValueError,'receipt'):
                    dispatch.resources_released(job)
                p.unlink()
                with self.assertRaisesRegex(RuntimeError,'without successful'):
                    dispatch.resources_released(job)


if __name__=='__main__':unittest.main()
