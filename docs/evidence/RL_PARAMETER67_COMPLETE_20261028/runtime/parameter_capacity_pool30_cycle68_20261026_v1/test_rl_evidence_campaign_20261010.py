import unittest
from rl_evidence_campaign_20261010 import cells, assess_phase


class EvidenceTests(unittest.TestCase):
    def rows(self):
        return [dict(cell=c['name'],scheduled_limit=n,completed=8,audit_passed=True,task=0,strict=0)
            for c in cells() for n in (11000,55000)]

    def test_zero_success_never_proves_universality_or_convergence(self):
        result=assess_phase(self.rows())
        self.assertTrue(result['paired_phase_complete'])
        self.assertFalse(result['convergence_demonstrated'])
        self.assertFalse(result['tuning_sufficient'])
        self.assertFalse(result['rl_generally_unsuitable'])

    def test_missing_or_unaudited_cells_are_not_complete(self):
        self.assertFalse(assess_phase(self.rows()[:-1])['paired_phase_complete'])
        rows=self.rows();rows[-1]['audit_passed']=False
        self.assertFalse(assess_phase(rows)['paired_phase_complete'])
        rows=self.rows();rows[-1]['completed']=7
        self.assertFalse(assess_phase(rows)['paired_phase_complete'])

    def test_duplicate_cell_cannot_fill_missing_condition(self):
        rows=self.rows();rows[-1]=rows[0]
        with self.assertRaises(AssertionError):assess_phase(rows)


if __name__=='__main__':unittest.main()
