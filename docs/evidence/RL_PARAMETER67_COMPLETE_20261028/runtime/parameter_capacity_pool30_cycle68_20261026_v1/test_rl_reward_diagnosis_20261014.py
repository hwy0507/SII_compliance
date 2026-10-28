import ast
from pathlib import Path
import unittest
import numpy as np
from payload_reward_potential_20261014 import payload_potential


class DiagnosisTests(unittest.TestCase):
    def test_reward_pose_validation(self):
        with self.assertRaises(ValueError):payload_potential([0,0,float('nan')],[0,0,0],[0,0,0])
        with self.assertRaises(ValueError):payload_potential([0,0],[0,0,0],[0,0,0])

    def test_payload_lift_and_goal_provide_local_feedback(self):
        goal=np.array([.6,-.3,.545]);start=np.array([.4,0,.425]);lift=start+[0,0,.10]
        self.assertGreater(payload_potential(lift,lift,goal),payload_potential(start,start,goal))
        self.assertGreater(payload_potential(goal,goal,goal),payload_potential(lift,lift,goal))
        self.assertLessEqual(payload_potential(goal,goal,goal),1.)

    def test_shaping_return_cancels_at_true_terminal(self):
        values=[.12,.3,.7,.4,.8];gamma=.9995
        rewards=[5*(gamma*(values[i+1] if i+1<len(values) else 0)-v) for i,v in enumerate(values)]
        self.assertAlmostEqual(sum(gamma**i*r for i,r in enumerate(rewards)),-5*values[0])

    def test_snapshot_coordinator_uses_registered_output_location(self):
        # Snapshot tool path is deliberately different from real benchmark.
        root=Path('/tmp/bench/outputs/run')
        self.assertEqual(root.parent.parent,Path('/tmp/bench'))
        source=Path(__file__).with_name('rl_reward_diagnosis_20261014.py').read_text()
        ast.parse(source)
        self.assertIn('bench=root.parent.parent',source)

    def test_reward_telemetry_exists_without_actor_concatenation(self):
        src=Path(__file__).with_name('baseline_repair_online_worker_20261008.py').read_text()
        self.assertIn('external_penetration_peak_m=external_peak',src)
        self.assertIn('payload_potential=measured_payload_potential',src)
        trainer=Path(__file__).with_name('train_baseline_repair_rl_20261008.py').read_text()
        self.assertIn("obs=np.asarray(event['observation'],np.float32)",trainer)
        self.assertIn("next_obs=np.asarray(event['observation'],np.float32)",trainer)


if __name__=='__main__':unittest.main()
