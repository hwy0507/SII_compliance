"""Regression tests for bounded metric training costs; raw metrics stay exact."""
import math, random, unittest
from dataclasses import replace
from rewards import OfficeReward, RewardConfig
from test_rewards import interval, NOMINAL
def sample(c, error=0., dt=None, peak=.5):
    v=interval(c,dt=dt,error=error,peak=peak)
    return replace(v,bounded_error_cost=v.elapsed_s/c.horizon_s*error**2/(c.error_scale_m**2+error**2))
class BoundedTests(unittest.TestCase):
    def test_raw_error_is_preserved_and_bounded_cost_monotone(self):
        c=RewardConfig(error_transform="bounded")
        values=[]
        for e in (0.,.012,.12,1.,3.):
            v=sample(c,e)
            _,info=OfficeReward(c)(v,NOMINAL,current_potential=0.,next_potential=0.)
            self.assertAlmostEqual(info["error_cost"],v.elapsed_s/c.horizon_s*(e/c.error_scale_m)**2)
            self.assertAlmostEqual(info["error"],-4*v.bounded_error_cost)
            values.append(-info["error"])
        self.assertEqual(values,sorted(values))
        self.assertLess(values[-1],4*c.control_dt_s/c.horizon_s)
    def test_additive_shared_task_and_terminal_terms(self):
        for terminal in (False,True):
            for success in ((False,True) if terminal else (False,)):
                m=RewardConfig(error_transform="bounded",gamma=.9995)
                t=replace(m,mode="office_task")
                kw=dict(current_potential=.2,next_potential=.4,terminated=terminal,
                        success=success,failure=terminal and not success,
                        terminal_reason="success" if success else "abort" if terminal else None)
                rm,im=OfficeReward(m)(sample(m,.8),[.2]*7,**kw)
                rt,it=OfficeReward(t)(sample(t,.8),[.2]*7,**kw)
                for k in ("task","progress","time"):
                    self.assertEqual(im[k],it[k])
                self.assertAlmostEqual(rm-rt,sum(im[k] for k in ("error","peak_torque","smooth"))+
                    im["failure_continuation"]-it["failure_continuation"])
    def test_all_failure_times_no_escape_from_bounded_future_costs(self):
        rng=random.Random(101)
        for gamma in (.9995,1.):
            c=RewardConfig(error_transform="bounded",horizon_s=.4,gamma=gamma)
            for trial in range(25):
                errors=[rng.uniform(0,3) for _ in range(10)]
                actions=[[rng.uniform(-1,1) for _ in range(7)] for _ in range(10)]
                phis=[rng.random() for _ in range(11)]
                def result(stop):
                    r=OfficeReward(c);total=0.
                    for i in range(stop):
                        end=i==stop-1
                        v,_=r(sample(c,errors[i]),actions[i],current_potential=phis[i],
                            next_potential=phis[i+1],terminated=end,failure=end,
                            terminal_reason="fail" if end else None)
                        total+=gamma**i*v
                    return total
                full=result(10)
                for n in range(1,10): self.assertLessEqual(result(n),full+1e-8)
    def test_55s_early_abort_cannot_create_thousand_scale_penalty(self):
        for gamma in (.9995,1.):
            c=RewardConfig(error_transform="bounded",gamma=gamma)
            value,info=OfficeReward(c)(sample(c,3.,peak=1),[-1]*7,
                current_potential=1.,next_potential=1.,terminated=True,
                failure=True,terminal_reason="unsafe")
            budget=4+8+1+c.smooth_weight*4*7*math.ceil(c.horizon_s/c.control_dt_s)
            self.assertLessEqual(-info["failure_continuation"],budget)
            self.assertGreaterEqual(value,-20-5-budget-1e-8)
    def test_missing_or_invalid_integral_rejected(self):
        c=RewardConfig(error_transform="bounded")
        for cost in (None,-1.,float("nan"),1.):
            with self.assertRaises(ValueError):
                OfficeReward(c)(replace(sample(c),bounded_error_cost=cost),NOMINAL,
                    current_potential=0,next_potential=0)
    def test_timeout_no_continuation_and_no_post_terminal_reuse(self):
        c=RewardConfig(error_transform="bounded",horizon_s=.04)
        r=OfficeReward(c)
        _,info=r(sample(c,.1),NOMINAL,current_potential=.2,next_potential=.3,
                 terminated=True,success=True,terminal_reason="task_physical")
        self.assertEqual(info["task"],20.)
        self.assertEqual(info["failure_continuation"],0.)
        with self.assertRaises(RuntimeError):
            r(sample(c),NOMINAL,current_potential=0,next_potential=0)
if __name__=="__main__":unittest.main(verbosity=2)
