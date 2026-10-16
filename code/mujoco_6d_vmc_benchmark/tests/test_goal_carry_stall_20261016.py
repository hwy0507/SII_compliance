import importlib.util
from pathlib import Path
import unittest

import numpy as np

path = Path(__file__).parents[1]/'tools/diagnose_goal_carry_stall_20261016.py'
spec = importlib.util.spec_from_file_location('carry_diagnostic', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CarryGateTests(unittest.TestCase):
    def test_plane_crossing_is_distinct_from_radius(self):
        route = np.array([[0., 0., 0.], [.1, 0., 0.], [.2, 0., 0.]])
        hand = np.array([[.095, .02, 0.], [.101, .02, 0.]])
        result = module.waypoint_evidence(hand, route[1]-hand, route, True)
        self.assertEqual(result['radius_ready_count'], 0)
        self.assertEqual(result['rejoin_plane_ready_count'], 1)
        self.assertEqual(module.waypoint_evidence(hand, route[1]-hand, route, False)
                         ['position_or_rejoin_ready_count'], 0)

    def test_final_waypoint_cannot_use_plane_shortcut(self):
        route = np.array([[0., 0., 0.], [.1, 0., 0.]])
        hand = np.array([[.101, .02, 0.]])
        result = module.waypoint_evidence(hand, route[-1]-hand, route, True)
        self.assertEqual(result['position_or_rejoin_ready_count'], 0)

    def test_wrong_time_alignment_rejected(self):
        route = np.array([[0., 0., 0.], [.1, 0., 0.]])
        with self.assertRaisesRegex(ValueError, 'alignment'):
            module.waypoint_evidence(np.array([[.095, 0., 0.]]),
                                     np.array([[.004, 0., 0.]]), route, True)


if __name__ == '__main__':
    unittest.main()
