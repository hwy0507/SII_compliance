"""Scientific metric regression: failed fast episodes must not set T_ref."""
import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from run_nonrl_spt_matrix_20261025 import aggregate, load_diagnostic_models, sha
from finalize_nonrl_spt_report_20261025 import expected_grid, EXPECTED_CONDITIONS


def row(method, task, strict, time, contact=2., comfort=.5):
    return dict(method=method, task_success=task, strict_success=strict,
                completion_time_s=time, peak_torque_nm=30.,
                comfort=dict(human_contact_duration_s=contact,
                             human_comfort_torque_compliance=comfort,
                             machine_safety_violation=False, machine_safety_violation_reasons=[]))


class SPTTest(unittest.TestCase):
    def test_diagnostic_checkpoint_lineage_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); cp = root/'checkpoint.npz'; cp.write_bytes(b'checkpoint')
            meta = root/'meta.json'
            meta.write_text(json.dumps(dict(family='esn_gradient',seed=1,
                                           checkpoint_sha256=sha(cp),training_data_sha256='data')))
            model = dict(name='esn_constant',family='esn_gradient',seed=1,
                         worker_kind='office',config={},checkpoint=str(cp),checkpoint_sha256=sha(cp),
                         metadata=str(meta),metadata_sha256=sha(meta))
            lock = root/'lock.json'
            lock.write_text(json.dumps(dict(schema='sii-nonrl-learning-diagnostic-lock-v1',
                                            status='frozen',training_data_sha256='data',models=[model])))
            self.assertEqual(load_diagnostic_models(lock)['models'][0]['name'],'esn_constant')
            cp.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'checkpoint hash mismatch'):
                load_diagnostic_models(lock)

    def test_new_grid_cannot_silently_change_conditions(self):
        reg = dict(schema='sii-nonrl-spt-diagnostic-20261026-v1',methods=['a','b'],
                   models=[dict(name='a'),dict(name='b')],conditions=sorted(EXPECTED_CONDITIONS))
        self.assertEqual(expected_grid(reg)[0],{'a','b'})
        reg['conditions'].pop()
        with self.assertRaisesRegex(RuntimeError,'conditions changed'):
            expected_grid(reg)

    def test_fast_unsafe_task_cannot_change_reference(self):
        rows=[row('a',True,False,1.),row('a',True,True,40.),row('b',True,True,50.)]
        result=aggregate(rows)
        self.assertEqual(result['t_ref_s'],40.)
        self.assertEqual([r['spt'] for r in rows],[0.,1.,.8])
        self.assertEqual(result['methods'][0]['spt_mean'],.5)

    def test_no_success_is_explicit_na(self):
        result=aggregate([row('a',False,False,None,contact=0.,comfort=None)])
        self.assertIsNone(result['t_ref_s'])
        self.assertEqual(result['rows'][0]['spt'],0.)
        self.assertIsNone(result['methods'][0]['human_comfort_torque_compliance_contact_time_weighted'])

    def test_comfort_is_weighted_by_contact_time(self):
        result=aggregate([row('a',True,True,40.,1.,1.),row('a',False,False,None,3.,0.)])
        self.assertEqual(result['methods'][0]['human_comfort_torque_compliance_contact_time_weighted'],.25)


if __name__ == '__main__':
    unittest.main()
