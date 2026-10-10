"""Evidence-integrity regressions; no MuJoCo steps or final conditions."""
import tempfile
import unittest
from pathlib import Path
from classical_acceptance_20261010 import write, sha
from monitor_classical_search_20261010 import verify_row


class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root/'candidate__development'
        self.run.mkdir()
        for name in ('rollout.npz', 'rollout.mjb'):
            (self.run/name).write_bytes(b'synthetic integrity fixture, not physics')
        audit = dict(task_success=False,strict_success=False,full_horizon=True,physical_seconds=55.,
            stage='carry',abort_reason=None,rmse_mm=25.,peak_torque_nm=40.,peak_speed_mps=.3,
            penetration_mm=.1,placement_error_xy_m=.08,
            trace_sha256=sha(self.run/'rollout.npz'),model_sha256=sha(self.run/'rollout.mjb'))
        write(self.run/'AUDIT.json',audit)
        write(self.run/'execution.json',dict(status='complete'))
        write(self.root/(self.run.name+'.config.json'),dict(parameters=[1.]*7))
        checks = []
        for kind in ('shield','dynamic'):
            path = self.root/(self.run.name+'.'+kind+'.json')
            write(path,dict(status='passed'))
            checks.append(dict(kind=kind,returncode=0,sha256=sha(path)))
        self.row = dict(status='complete',job=dict(name=self.run.name,candidate='candidate',controller='vmc',
            condition_id='development',parameters=[1.]*7),audit=audit,
            audit_sha256=sha(self.run/'AUDIT.json'),trace_sha256=audit['trace_sha256'],checks=checks)
        self.save()

    def save(self):
        write(self.root/(self.run.name+'.execution.json'),self.row)

    def test_full_horizon_stall_is_valid_not_a_monitor_failure(self):
        result = verify_row(self.root,self.row)
        self.assertFalse(result['task'])
        self.assertEqual(result['final_stage'],'carry')

    def test_raw_trace_tampering_is_rejected(self):
        (self.run/'rollout.npz').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Trace hash'):
            verify_row(self.root,self.row)

    def test_missing_dynamic_audit_is_rejected(self):
        self.row['checks'] = self.row['checks'][:1]
        self.save()
        with self.assertRaisesRegex(ValueError,'Missing controller audit'):
            verify_row(self.root,self.row)

    def test_physical_early_failure_is_retained(self):
        self.row['audit'].update(full_horizon=False,physical_seconds=12.,abort_reason='physical_limit')
        write(self.run/'AUDIT.json',self.row['audit'])
        self.row['audit_sha256'] = sha(self.run/'AUDIT.json')
        self.save()
        result = verify_row(self.root,self.row)
        self.assertFalse(result['full_horizon'])
        self.assertEqual(result['abort_reason'],'physical_limit')


if __name__ == '__main__':
    unittest.main()
