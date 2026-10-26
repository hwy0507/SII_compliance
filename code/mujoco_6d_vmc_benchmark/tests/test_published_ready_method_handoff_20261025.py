"""Independent dispatch guards, without starting learners or physics."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prioritize_published_ready_methods_20261025 import check_retired, validate_plan


class ReadyMethodHandoffTests(unittest.TestCase):
    def setUp(self):
        methods=['direct','impedance','admittance','vmc']
        cpus=[list(range(13)),[14]+list(range(15,26))+[52],list(range(26,39)),list(range(39,52))]
        self.plan=dict(total_cycles=6,coordinator_cpu=54,reserved_cpus=[13,53,54],methods={})
        for i,(m,c) in enumerate(zip(methods,cpus)):
            parents=[dict(role='sac',cpus=c[1:4])]
            if m!='impedance':parents.append(dict(role='fresh',cpus=[c[0],c[-2],c[-1]]))
            self.plan['methods'][m]=dict(allocation=dict(cpus=c,workers=12,gpu=i),parents=parents,never_launched=m=='impedance')

    def test_three_resumes_and_one_fresh_are_valid(self):
        validate_plan(self.plan,set(range(55)))

    def test_missing_or_duplicate_parent_rejected(self):
        for role in ['sac','fresh']:
            plan=copy.deepcopy(self.plan);plan['methods']['direct']['parents']=[p for p in plan['methods']['direct']['parents'] if p['role']!=role]
            with self.subTest(role=role),self.assertRaisesRegex(ValueError,'source parent'):
                validate_plan(plan,set(range(55)))
        self.plan['methods']['impedance']['parents'].append(dict(role='fresh',cpus=[14]))
        with self.assertRaisesRegex(ValueError,'source parent'):
            validate_plan(self.plan,set(range(55)))

    def test_sibling_overlap_or_reserved_core_rejected(self):
        plan=copy.deepcopy(self.plan);plan['methods']['direct']['allocation']['cpus'][2]=13
        with self.assertRaisesRegex(ValueError,'allocation'):
            validate_plan(plan,set(range(55)))
        self.plan['methods']['vmc']['parents'][0]['cpus']=[12]
        with self.assertRaisesRegex(ValueError,'draining sibling'):
            validate_plan(self.plan,set(range(55)))

    def test_live_coordinator_or_unexpected_dispatch_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt=Path(folder)/'DISPATCH_STOPPED.json';receipt.write_text(json.dumps(dict(launched=[dict(controller='direct')])))
            spec=dict(pid=11,stopped_receipt=str(receipt),expected_methods=['direct'])
            with patch('prioritize_published_ready_methods_20261025.identity',return_value='live'):
                with self.assertRaisesRegex(ValueError,'has not exited'):check_retired(spec)
            with patch('prioritize_published_ready_methods_20261025.identity',return_value=None):
                check_retired(spec)
                spec['expected_methods']=[]
                with self.assertRaisesRegex(ValueError,'unexpected learner'):check_retired(spec)


if __name__=='__main__':
    unittest.main()
