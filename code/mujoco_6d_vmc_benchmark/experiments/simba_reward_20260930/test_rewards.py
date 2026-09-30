"""Behavioral invariants for Office reward; standard-library unittest only."""
import math
import random
import unittest
from dataclasses import replace
from rewards import IntervalMetrics, OfficeReward, RewardConfig

NOMINAL = [0., 0., 0., 0., 0., 0., 0.]


def interval(cfg, dt=None, error=0., peak=0.):
    dt = cfg.control_dt_s if dt is None else dt
    limits = [87.,87.,87.,87.,12.,12.,12.]
    return IntervalMetrics(dt, dt/cfg.horizon_s*(error/cfg.error_scale_m)**2,
                           peak, [peak*v for v in limits], error,
                           max(1, round(dt/.00005)))


class RewardTests(unittest.TestCase):
    def test_actual_peak_not_sum_or_endpoint_and_reset(self):
        cfg = RewardConfig()
        r = OfficeReward(cfg)
        total = 0
        for peak in (.2,.8,.3,.6):
            _, info = r(interval(cfg,peak=peak), NOMINAL,
                        current_potential=0.,next_potential=0.)
            total += info["peak_torque_cost_increment"]
        self.assertAlmostEqual(total,.8**2)
        self.assertAlmostEqual(info["peak_torque_nm"],.8*87)
        self.assertEqual(info["peak_torque_nm_per_joint"][-1],.8*12)
        r.reset()
        self.assertEqual(r.peak_torque_ratio,0)
        self.assertEqual(r.peak_torque_nm_per_joint,[0]*7)

    def test_error_integral_independent_of_substep_partition(self):
        cfg = RewardConfig(horizon_s=1.)
        # Identical 0.12m constant error for 0.04s yields integral 0.04,
        # regardless of the simulator partition.
        for count in (1,10,800):
            dt=.04/count
            cost=sum(dt/cfg.horizon_s*(.12/cfg.error_scale_m)**2 for _ in range(count))
            r=OfficeReward(cfg)
            data=IntervalMetrics(.04,cost,0.,[0.]*7,.12,count)
            _,info=r(data,NOMINAL,current_potential=0.,next_potential=0.)
            self.assertAlmostEqual(info["error"],-.16)

    def test_large_error_not_capped_or_contact_gated(self):
        cfg=RewardConfig()
        costs=[]
        for error in (.1,.2,.8):
            _,info=OfficeReward(cfg)(interval(cfg,error=error),NOMINAL,
                current_potential=0.,next_potential=0.)
            costs.append(info["error"])
        self.assertAlmostEqual(costs[1]/costs[0],4.)
        self.assertAlmostEqual(costs[2]/costs[0],64.)

    def test_potential_discounted_telescoping_including_switch_and_terminal(self):
        cfg=RewardConfig(horizon_s=.2)
        potentials=[.1,.25,.12,.50,.90,.93]
        r=OfficeReward(cfg)
        total=0.
        for i in range(5):
            terminal=i==4
            _,info=r(interval(cfg),NOMINAL,
                current_potential=potentials[i],next_potential=potentials[i+1],
                terminated=terminal,success=terminal,
                terminal_reason="strict_success" if terminal else None)
            total += cfg.gamma**i*info["progress"]
        self.assertAlmostEqual(total,-cfg.progress_weight*potentials[0])
        self.assertEqual(info["effective_next_potential"],0.)

    def test_early_failure_cannot_escape_bounded_future_costs(self):
        # Exhaustively test every failure time versus full-horizon failure,
        # with worst-case costs and discount gamma both <1 and =1.
        for gamma in (.995,1.):
            cfg=RewardConfig(gamma=gamma,horizon_s=.4)
            def outcome(stop):
                r=OfficeReward(cfg)
                ret=0.
                for i in range(stop):
                    action=[(-1.)**i]*7
                    terminal=i==stop-1
                    value,_=r(interval(cfg,error=cfg.max_position_error_m,
                                      peak=cfg.max_actual_torque_ratio),
                        action,current_potential=.3,next_potential=.3,
                        terminated=terminal,failure=terminal,
                        terminal_reason="timeout" if stop==10 and terminal else
                                        "unsafe" if terminal else None)
                    ret += gamma**i*value
                return ret
            final=outcome(10)
            for stop in range(1,10):
                self.assertLessEqual(outcome(stop),final+1e-8)

    def test_early_failure_bound_for_random_legal_continuations(self):
        rng=random.Random(1701)
        cfg=RewardConfig(horizon_s=.4)
        for trial in range(25):
            n=10
            actions=[[rng.uniform(-1,1) for _ in range(7)] for _ in range(n)]
            errors=[rng.uniform(0,3) for _ in range(n)]
            peaks=[rng.uniform(0,1) for _ in range(n)]
            phis=[rng.uniform(0,1) for _ in range(n+1)]
            def outcome(stop):
                r=OfficeReward(cfg); result=0.
                for i in range(stop):
                    end=i==stop-1
                    value,_=r(interval(cfg,error=errors[i],peak=peaks[i]),actions[i],
                        current_potential=phis[i],next_potential=phis[i+1],
                        terminated=end,failure=end,terminal_reason="failed" if end else None)
                    result+=cfg.gamma**i*value
                return result
            full=outcome(n)
            for stop in range(1,n):
                self.assertLessEqual(outcome(stop),full+1e-8)

    def test_success_is_explicit_not_potential_or_stage(self):
        cfg=RewardConfig(horizon_s=.04,mode="task_only")
        failure,_=OfficeReward(cfg)(interval(cfg),NOMINAL,
            current_potential=.99,next_potential=1.,terminated=True,failure=True,
            terminal_reason="timeout")
        success,_=OfficeReward(cfg)(interval(cfg),NOMINAL,
            current_potential=.99,next_potential=1.,terminated=True,success=True,
            terminal_reason="strict_success")
        self.assertEqual(failure,-cfg.failure_penalty)
        self.assertEqual(success,cfg.success_reward)

    def test_no_time_or_action_after_success_without_reset(self):
        cfg=RewardConfig(horizon_s=.04)
        r=OfficeReward(cfg)
        r(interval(cfg),NOMINAL,current_potential=0.,next_potential=1.,
          terminated=True,success=True,terminal_reason="strict_success")
        with self.assertRaises(RuntimeError):
            r(interval(cfg),NOMINAL,current_potential=0.,next_potential=0.)

    def test_smoothing_uses_requested_normalized_action(self):
        cfg=RewardConfig()
        r=OfficeReward(cfg)
        _,info=r(interval(cfg),NOMINAL,current_potential=0.,next_potential=0.)
        self.assertEqual(info["smooth_cost"],0.)
        _,info=r(interval(cfg),[-1.,0.,0.,0.,0.,0.,0.],
                 current_potential=0.,next_potential=0.)
        self.assertEqual(info["smooth_cost"],1.)
        self.assertEqual(info["smooth"],-cfg.smooth_weight)
        with self.assertRaises(ValueError):
            r(interval(cfg),[1.1]*7,current_potential=0.,next_potential=0.)

    def test_timeout_continuation_zero_and_config_serializable(self):
        import json
        cfg=RewardConfig(horizon_s=.04)
        _,info=OfficeReward(cfg)(interval(cfg),NOMINAL,current_potential=0.,next_potential=0.,
            terminated=True,failure=True,terminal_reason="timeout")
        self.assertEqual(info["failure_continuation"],0.)
        self.assertEqual(json.loads(json.dumps(cfg.to_dict()))["mode"],"metric")

    def test_support_violation_errors_instead_of_reward_clipping(self):
        cfg=RewardConfig()
        for kwargs in ({"error":3.01},{"peak":1.01}):
            with self.assertRaises(ValueError):
                OfficeReward(cfg)(interval(cfg,**kwargs),NOMINAL,
                    current_potential=0.,next_potential=0.)

    def test_fractional_remaining_duration_bound_finite(self):
        cfg=RewardConfig(horizon_s=.095)
        _,info=OfficeReward(cfg)(interval(cfg),NOMINAL,
            current_potential=0.,next_potential=0.,
            terminated=True,failure=True,terminal_reason="unsafe")
        self.assertTrue(math.isfinite(info["failure_continuation"]))
        self.assertLess(info["failure_continuation"],0.)


    def test_office_task_dense_progress_but_no_metric_penalties(self):
        cfg=RewardConfig(mode="office_task")
        _,info=OfficeReward(cfg)(interval(cfg,error=.5,peak=.9),[1.]*7,
            current_potential=0.,next_potential=.1)
        self.assertGreater(info["progress"],0.)
        self.assertLess(info["time"],0.)
        for key in ("error","peak_torque","smooth"):
            self.assertEqual(info[key],0.)

    def test_office_task_failure_cannot_skip_time_cost(self):
        cfg=RewardConfig(mode="office_task",horizon_s=.4)
        def result(n):
            r=OfficeReward(cfg);out=0.
            for i in range(n):
                end=i==n-1
                v,_=r(interval(cfg),NOMINAL,
                    current_potential=.2,next_potential=.2,
                    terminated=end,failure=end,terminal_reason="failed" if end else None)
                out+=cfg.gamma**i*v
            return out
        for i in range(1,10):
            self.assertLessEqual(result(i),result(10)+1e-8)


    def test_placement_before_interval_stops_only_time_cost(self):
        cfg=RewardConfig()
        _,active=OfficeReward(cfg)(interval(cfg,error=.2,peak=.5),[.2]*7,
            current_potential=.5,next_potential=.6,task_complete_before_interval=False)
        _,placed=OfficeReward(cfg)(interval(cfg,error=.2,peak=.5),[.2]*7,
            current_potential=.5,next_potential=.6,task_complete_before_interval=True)
        self.assertLess(active["time"],0.)
        self.assertEqual(placed["time"],0.)
        self.assertEqual(placed["task"],0.)
        self.assertFalse(placed["success"])
        for key in ("error","peak_torque","progress","smooth"):
            self.assertEqual(active[key],placed[key])


if __name__ == "__main__":
    unittest.main(verbosity=2)
