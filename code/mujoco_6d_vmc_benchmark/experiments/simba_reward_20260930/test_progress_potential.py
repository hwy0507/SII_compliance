"""Pure tests for the opt-in shared progress diagnostic."""
import math
import unittest
from progress_potential import dense_progress_potential
from rewards import IntervalMetrics, OfficeReward, RewardConfig

ZERO=(0.,0.,0.)


class DensePotentialTests(unittest.TestCase):
    def phi(self,x,rotation=ZERO,speed=ZERO):
        return dense_progress_potential(0,8,ZERO,ZERO,(x,0.,0.),rotation,speed)

    def test_zero_segment_has_direction_outside_ready_set(self):
        errors=(.12,.08,.05,.025,.013,.012,.011,0.)
        values=[self.phi(e) for e in errors]
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])))
        self.assertGreater(self.phi(.05),self.phi(.08))

    def test_no_ready_threshold_discontinuity(self):
        for threshold in (.012,.048):
            self.assertLess(abs(self.phi(threshold-1e-8)-self.phi(threshold+1e-8)),1e-6)

    def test_velocity_and_orientation_improvement(self):
        self.assertGreater(self.phi(.02,rotation=(.1,0,0)),self.phi(.02,rotation=(.5,0,0)))
        self.assertGreater(self.phi(.02,speed=(.01,0,0)),self.phi(.02,speed=(.1,0,0)))

    def test_bounded_all_stages_and_projection_limits(self):
        for i in range(8):
            for x in (-100.,-.1,0.,.1,100.):
                phi=dense_progress_potential(i,8,ZERO,(.1,0,0),(x,0,0),ZERO,ZERO)
                self.assertGreaterEqual(phi,i/8)
                self.assertLessEqual(phi,(i+1)/8)
                self.assertGreaterEqual(phi,0.)
                self.assertLessEqual(phi,1.)

    def test_terminal_potential_still_zeroed_by_existing_reward(self):
        cfg=RewardConfig(horizon_s=.04,mode="office_task")
        p=self.phi(.01)
        _,info=OfficeReward(cfg)(IntervalMetrics(.04,0.,0.,[0.]*7,0.,1),[0.]*7,
            current_potential=p,next_potential=.99,terminated=True,failure=True,
            terminal_reason="finite_horizon_timeout")
        self.assertEqual(info["effective_next_potential"],0.)
        self.assertAlmostEqual(info["progress"],-cfg.progress_weight*p)

    def test_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):
            self.phi(float("nan"))


if __name__=="__main__":
    unittest.main(verbosity=2)
