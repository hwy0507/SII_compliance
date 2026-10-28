import tempfile
from pathlib import Path
import unittest
from report_rl_longrun_20261011 import verified_node, markdown, write, sha


class LongrunReportingTests(unittest.TestCase):
    def fixture(self, root):
        cp=root/'checkpoint';cp.mkdir();(cp/'weights').write_bytes(b'frozen')
        rows=[dict(condition=str(i),task=False,strict=False,full_horizon=i!=0,
            stage='carry',rmse_mm=20.,peak_torque_nm=40.,peak_speed_mps=.3) for i in range(8)]
        path=root/'audit.json';write(path,dict(status='passed',completed=8,steps=165000,
            task=0,strict=0,rows=rows,checkpoint=dict(path=str(cp),hashes={'weights':sha(cp/'weights')})))
        return dict(audit=str(path),audit_sha256=sha(path),steps=165000,scheduled_limit=165000),{str(i) for i in range(8)}

    def test_physical_early_failure_stays_in_denominator(self):
        with tempfile.TemporaryDirectory() as d:
            entry,ids=self.fixture(Path(d));node=verified_node(entry,ids,{})
            self.assertEqual(node['evaluated'],8);self.assertEqual(node['full_horizon'],7)
            self.assertEqual(node['task'],0)

    def test_checkpoint_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);entry,ids=self.fixture(root);(root/'checkpoint/weights').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Checkpoint changed'):verified_node(entry,ids,{})

    def test_wrong_conditions_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            entry,ids=self.fixture(Path(d))
            with self.assertRaisesRegex(ValueError,'identity'):verified_node(entry,ids-{'0'}|{'test'},{})

    def test_pending_is_not_zero_success(self):
        report=dict(time_utc='now',interpretation='development',methods=[dict(method='pending_method',training=[],development=[])])
        value=markdown(report);self.assertIn('pending',value);self.assertNotIn('0/0',value);self.assertNotIn('0/8',value)


if __name__=='__main__':unittest.main()
