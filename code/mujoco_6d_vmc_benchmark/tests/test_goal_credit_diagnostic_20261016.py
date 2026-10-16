import sys
from pathlib import Path
import unittest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_goal_rl_credit_20261016 import target_statistics


class TargetDiagnosticTests(unittest.TestCase):
    def test_terminal_ignores_bootstrap_and_entropy(self):
        out = target_statistics(np.array([[.2,.3,.5]]),np.array([-2.]),np.array([1.]),
            np.array([999.]),.9,np.array([-5.,0.,5.]))
        np.testing.assert_allclose(out['target_mean'],[-2.])
        np.testing.assert_allclose(out['clipped_mass'],[0.])

    def test_clipping_is_probability_weighted(self):
        # Atoms -1, 4, 9: only the last probability mass .5 clips to 5.
        out = target_statistics(np.array([[.2,.3,.5]]),np.array([4.]),np.array([0.]),
            np.array([0.]),1.,np.array([-5.,0.,5.]))
        np.testing.assert_allclose(out['clipped_mass'],[.5])
        np.testing.assert_allclose(out['target_mean'],[3.5])
        np.testing.assert_allclose(out['unclipped_target_mean'],[5.5])


if __name__ == '__main__':
    unittest.main()
